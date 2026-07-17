"""Story Bible: the persistent canonical state (style + characters) that every agent reads
and writes. Persisting it is what lets episode 2 reuse episode 1's characters unchanged."""
import json
import os

from canon.schemas import CharacterSheet


class Bible:
    def __init__(self, series_dir: str):
        self.dir = series_dir
        # ponytail: series_dir is trusted (set by our code). When an API lets series_id come from
        # a request, validate it as a plain slug at THAT boundary — os.path.join here would else
        # allow path traversal (../, absolute paths) to read/write outside the data root.
        self.path = os.path.join(series_dir, "bible.json")
        self.style = ""
        self.characters: dict[str, CharacterSheet] = {}
        self.locations: dict[str, str] = {}  # place name -> locked visual descriptor

    def load(self) -> "Bible":
        if not os.path.exists(self.path):
            return self
        with open(self.path, encoding="utf-8") as f:
            raw = f.read().strip()
        if not raw:
            return self
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValueError(f"corrupt bible at {self.path}: {e}") from e
        if not isinstance(data, dict):
            raise ValueError(f"corrupt bible at {self.path}: expected a JSON object")

        self.style = str(data.get("style", ""))
        raw_locs = data.get("locations", {})
        self.locations = {str(k): str(v) for k, v in raw_locs.items()} if isinstance(raw_locs, dict) else {}
        # Rebuild from known fields only: unknown keys are ignored (not injected as attributes)
        # and malformed character data raises a clear error instead of a cryptic one.
        try:
            self.characters = {
                name: CharacterSheet(
                    name=str(c["name"]),
                    descriptor=str(c["descriptor"]),
                    seed=int(c["seed"]),
                    ref_image=c.get("ref_image"),
                )
                for name, c in data.get("characters", {}).items()
            }
        except (AttributeError, KeyError, TypeError, ValueError) as e:
            raise ValueError(f"corrupt bible at {self.path}: bad character data ({e})") from e
        return self

    def save(self) -> None:
        os.makedirs(self.dir, exist_ok=True)
        payload = {
            "style": self.style,
            "locations": self.locations,
            "characters": {name: vars(c) for name, c in self.characters.items()},
        }
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    def upsert(self, sheet: CharacterSheet) -> None:
        self.characters[sheet.name] = sheet

    def prompt_for(self, character_name: str, action: str, setting: str = "") -> str:
        # KeyError if unknown: callers only ask for characters the writer already put in the bible.
        # `setting` anchors the frame to the scripted place; without it the image model reinvents
        # the location on every shot and the episode stops reading as one story.
        c = self.characters[character_name]
        where = f"in {setting}, " if setting else ""
        return f"{self.style}, {c.descriptor}, {where}{action}"
