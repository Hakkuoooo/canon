import json

import pytest

from canon.bible import Bible
from canon.schemas import CharacterSheet


def test_bible_persists_and_assembles_prompt(tmp_path):
    b = Bible(str(tmp_path))
    b.style = "flat 2D anime"
    b.upsert(CharacterSheet(name="Mara", descriptor="red jacket, short black hair", seed=42))
    b.save()

    reloaded = Bible(str(tmp_path)).load()
    assert reloaded.characters["Mara"].seed == 42  # persistence = cross-episode consistency

    prompt = reloaded.prompt_for("Mara", "runs down a hall")
    assert "red jacket" in prompt and "flat 2D anime" in prompt and "runs down a hall" in prompt


def test_load_missing_is_empty(tmp_path):
    b = Bible(str(tmp_path)).load()
    assert b.characters == {} and b.style == ""


def test_prompt_for_unknown_character_errors(tmp_path):
    b = Bible(str(tmp_path))
    b.style = "anime"
    with pytest.raises(KeyError):
        b.prompt_for("Ghost", "appears")


def test_load_empty_file_is_empty(tmp_path):
    (tmp_path / "bible.json").write_text("")
    b = Bible(str(tmp_path)).load()
    assert b.characters == {}


def test_load_corrupt_json_raises_clear_valueerror(tmp_path):
    (tmp_path / "bible.json").write_text("{ not json")
    with pytest.raises(ValueError):
        Bible(str(tmp_path)).load()


def test_load_ignores_unknown_character_keys_and_coerces_seed(tmp_path):
    (tmp_path / "bible.json").write_text(
        json.dumps(
            {
                "style": "anime",
                "characters": {
                    "Mara": {"name": "Mara", "descriptor": "red jacket", "seed": "42", "evil": "x"}
                },
            }
        )
    )
    b = Bible(str(tmp_path)).load()
    assert b.characters["Mara"].seed == 42  # coerced from string
    assert not hasattr(b.characters["Mara"], "evil")  # unknown key not injected
