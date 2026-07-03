"""Agents that turn a premise into a Script. The Writer is a chat() call; parse_script turns its
reply into typed objects, tolerating surrounding prose/fences and raising clear errors on bad output."""
import json

from canon.config import DEFAULT_STYLE, MAX_SHOTS
from canon.schemas import CharacterSheet, Script, Shot

WRITER_SYS = (
    "You are a short-drama writer. Given a premise, output STRICT JSON only (no prose), with keys: "
    '"style" (string), '
    '"characters" (list of {"name": string, "descriptor": short fixed visual description, "seed": integer}), '
    f'"shots" (list of {{"character": name or null, "setting": string, "action": string, '
    f'"dialogue": string}}, max {MAX_SHOTS}). '
    "Seeds are distinct integers. Keep descriptors concrete so the look stays consistent."
)


def parse_script(raw: str, premise: str):
    """Extract the JSON object from a writer reply (tolerating surrounding prose/fences) and build
    a Script plus its CharacterSheets. Raises ValueError with a clear message on malformed output."""
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
            for i, s in enumerate(data["shots"][:MAX_SHOTS])  # cap bounds cost on runaway output
        ]
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"writer JSON missing/invalid fields: {e}") from e

    return Script(premise=premise, style=str(data.get("style", DEFAULT_STYLE)), shots=shots), chars


def write_script(providers, premise: str, known=None):
    """Run the Writer agent over the chat() boundary and parse its reply. For a later episode,
    pass `known` (name -> descriptor) so the Writer reuses the existing cast instead of inventing one."""
    user = premise
    if known:
        roster = "; ".join(f"{n}: {d}" for n, d in known.items())
        user = (
            f"{premise}\n\nThis is a later episode of an existing series. REUSE these exact "
            f"characters (same names and looks), do not invent new ones: {roster}"
        )
    return parse_script(providers.chat(WRITER_SYS, user), premise)


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
