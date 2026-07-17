"""Agents that turn a premise into a Script. The Writer is a chat() call; parse_script turns its
reply into typed objects, tolerating surrounding prose/fences and raising clear errors on bad output."""
import json

from canon.config import DEFAULT_STYLE, MAX_SHOTS
from canon.schemas import CharacterSheet, Script, Shot

WRITER_SYS = (
    "You are a short-drama writer. Given a premise, output STRICT JSON only (no prose), with keys: "
    '"style" (string), '
    '"locations" (list of {"name": string, "descriptor": 10-20 word fixed visual spec of the place}), '
    '"characters" (list of {"name": string, "descriptor": short fixed visual description, "seed": integer}), '
    f'"shots" (list of {{"character": name or null, "setting": string, "action": string, '
    f'"dialogue": string}}, max {MAX_SHOTS}). '
    "Seeds are distinct integers. The character descriptor is a 15-25 word head-to-toe spec that never "
    "changes: hair, eye colour, face, each garment with colour and construction detail (collar, zip, "
    "belt), trousers, shoes. Concrete nouns only; the same descriptor is reused to redraw the character "
    "in every shot, so vague wording causes visual drift. "
    "Every shot's setting must EXACTLY equal the name of one of your locations; the location descriptor "
    "is reused to redraw the place, so define it concretely (surfaces, light source, one landmark object). "
    "The shots are the user's story told in order as ONE continuous scene sequence: each action is a "
    "concrete physical moment visible in a single frame, caused by the previous shot, and each action "
    "visibly carries one object or state over from the previous shot. For a two-character moment, set "
    "character to the main one and name the other inside the action. Dialogue is one short spoken line, "
    "under 12 words, that advances the story; every character shot has one."
)


def parse_script(raw: str, premise: str, max_shots=None):
    """Extract the JSON object from a writer reply (tolerating surrounding prose/fences) and build
    a Script plus its CharacterSheets. Raises ValueError with a clear message on malformed output."""
    cap = max_shots or MAX_SHOTS
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("writer returned no JSON object")
    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"writer returned invalid JSON: {e}") from e

    try:
        chars = [
            CharacterSheet(name=str(c["name"]), descriptor=str(c["descriptor"]), seed=int(c["seed"]))
            for c in data["characters"]
        ]
        shots = [
            Shot(
                index=i,
                character=s.get("character"),
                setting=str(s["setting"]),
                action=str(s["action"]),
                dialogue=str(s.get("dialogue", "")),
            )
            for i, s in enumerate(data["shots"][:cap])  # cap bounds cost / length
        ]
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"writer JSON missing/invalid fields: {e}") from e

    locations = {
        str(loc["name"]): str(loc["descriptor"])
        for loc in data.get("locations", [])
        if isinstance(loc, dict) and loc.get("name") and loc.get("descriptor")
    }
    return Script(premise=premise, style=str(data.get("style", DEFAULT_STYLE)), shots=shots,
                  locations=locations), chars


SHOWRUNNER_SYS = (
    "You are the showrunner reviewing a draft episode script against the user's premise. The six "
    "shots must tell exactly the user's story, in order, as one continuous cause-and-effect scene "
    "sequence. Fix anything that breaks that: actions that do not follow from the previous shot, "
    "props or people that appear from nowhere, settings that stray from the defined locations, "
    "dialogue that does not advance the story, abstract actions that cannot be seen in a single "
    "frame. Keep the characters, seeds, and locations unchanged. Return the corrected script as "
    "the same STRICT JSON shape only, no prose."
)


def write_script(providers, premise: str, known=None, max_shots=None, known_locations=None):
    """Writer drafts, Showrunner reviews the draft against the premise, then parse. `max_shots`
    sets episode length; `known` / `known_locations` make later episodes reuse the existing canon."""
    cap = max_shots or MAX_SHOTS
    parts = [premise, f"Write exactly {cap} shots."]
    if known:
        roster = "; ".join(f"{n}: {d}" for n, d in known.items())
        parts.append(
            "This is a later episode of an existing series. REUSE these exact characters "
            f"(same names and looks), do not invent new ones: {roster}"
        )
    if known_locations:
        places = "; ".join(f"{n}: {d}" for n, d in known_locations.items())
        parts.append(f"REUSE these exact locations (same names and specs) where the story allows: {places}")
    request = "\n\n".join(parts)
    draft = providers.chat(WRITER_SYS, request)
    reviewed = providers.chat(
        SHOWRUNNER_SYS,
        f"USER PREMISE:\n{request}\n\nDRAFT SCRIPT JSON:\n{draft}\n\nKeep exactly {cap} shots.",
    )
    try:
        return parse_script(reviewed, premise, cap)
    except ValueError:  # a review that breaks the JSON must not cost us the episode
        return parse_script(draft, premise, cap)


def _extract_json(raw):
    return json.loads(raw[raw.find("{") : raw.rfind("}") + 1])


CINE_SYS = (
    "You are a cinematographer. For each numbered shot give ONE short camera direction "
    "(shot size, angle, motion), no prose. Output STRICT JSON {\"shots\": [\"...\", ...]} "
    "with one string per shot, in order."
)


def direct_shots(providers, script):
    """Cinematographer agent: one camera/framing note per shot. Falls back to a neutral note."""
    scenes = "; ".join(f"{i}: {s.setting}, {s.action}" for i, s in enumerate(script.shots))
    try:
        notes = [str(x) for x in _extract_json(providers.chat(CINE_SYS, scenes))["shots"]]
    except (ValueError, KeyError, TypeError):
        notes = []
    return [
        notes[i] if i < len(notes) and notes[i].strip() else "medium shot, eye level"
        for i in range(len(script.shots))
    ]


REVISE_SYS = (
    "You fix an image prompt that failed a consistency check. Return only the corrected prompt "
    "text on one line, keeping the character description intact and addressing the problem."
)


def revise_prompt(providers, prompt, reason):
    """Generator agent: rewrite a prompt to fix a flagged drift. Falls back to the original prompt."""
    try:
        revised = providers.chat(REVISE_SYS, f"Prompt: {prompt}\nProblem: {reason}").strip()
        return revised[:500] or prompt
    except Exception:  # noqa: BLE001 - never let a revision failure abort the render
        return prompt


EDITOR_SYS = (
    "You are an editor naming a short-drama episode. Output STRICT JSON "
    "{\"title\": \"...\", \"logline\": \"one sentence\"}. No prose."
)


def plan_edit(providers, script):
    """Editor agent: episode title + logline. Falls back to defaults on bad output."""
    try:
        data = _extract_json(providers.chat(EDITOR_SYS, f"Premise: {script.premise}. Style: {script.style}."))
        return {"title": (str(data.get("title") or "Untitled Episode"))[:80],
                "logline": (str(data.get("logline") or ""))[:200]}
    except (ValueError, KeyError, TypeError):
        return {"title": "Untitled Episode", "logline": ""}
