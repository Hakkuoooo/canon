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


def write_script(providers, premise: str):
    """Run the Writer agent over the chat() boundary and parse its reply."""
    return parse_script(providers.chat(WRITER_SYS, premise), premise)
