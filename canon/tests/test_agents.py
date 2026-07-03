import json

import pytest

from canon.agents import (
    direct_shots,
    parse_script,
    plan_edit,
    revise_prompt,
    write_script,
    WRITER_SYS,
)
from canon.config import MAX_SHOTS
from canon.providers import FakeProviders
from canon.schemas import Script, Shot

GOOD = {
    "style": "flat 2D anime",
    "characters": [{"name": "Mara", "descriptor": "red jacket", "seed": 7}],
    "shots": [
        {"character": "Mara", "setting": "hall", "action": "runs", "dialogue": "go"},
        {"character": None, "setting": "sky", "action": "rain falls"},
    ],
}


def test_parse_script_builds_indexed_shots_and_characters():
    script, chars = parse_script(json.dumps(GOOD), premise="a heist")
    assert script.premise == "a heist" and script.style == "flat 2D anime"
    assert [s.index for s in script.shots] == [0, 1]
    assert script.shots[1].character is None  # narration shot, no character
    assert script.shots[0].dialogue == "go"
    assert chars[0].name == "Mara" and chars[0].seed == 7


def test_parse_script_tolerates_prose_and_fences():
    raw = "Sure! Here is your script:\n```json\n" + json.dumps(GOOD) + "\n```\nEnjoy."
    script, chars = parse_script(raw, premise="p")
    assert chars[0].name == "Mara" and len(script.shots) == 2


def test_parse_script_coerces_seed_and_defaults_dialogue():
    data = {
        "style": "s",
        "characters": [{"name": "A", "descriptor": "d", "seed": "42"}],
        "shots": [{"character": "A", "setting": "x", "action": "y"}],
    }
    script, chars = parse_script(json.dumps(data), "p")
    assert chars[0].seed == 42 and script.shots[0].dialogue == ""


def test_parse_script_caps_shots_at_max():
    data = {
        "style": "s",
        "characters": [{"name": "A", "descriptor": "d", "seed": 1}],
        "shots": [{"character": "A", "setting": "x", "action": f"a{i}"} for i in range(MAX_SHOTS + 5)],
    }
    script, _ = parse_script(json.dumps(data), "p")
    assert len(script.shots) == MAX_SHOTS  # runaway model output is bounded


def test_parse_script_no_json_raises():
    with pytest.raises(ValueError):
        parse_script("the model refused to answer", "p")


def test_parse_script_invalid_json_raises():
    with pytest.raises(ValueError):
        parse_script("{ not: valid, json }", "p")


def test_parse_script_missing_field_raises():
    bad = {"style": "s", "characters": [{"name": "A", "seed": 1}], "shots": []}  # no descriptor
    with pytest.raises(ValueError):
        parse_script(json.dumps(bad), "p")


def test_write_script_uses_chat_boundary():
    p = FakeProviders(chat_reply=json.dumps(GOOD))
    script, chars = write_script(p, "a heist")
    assert p.calls["chat"] == 1
    assert chars[0].name == "Mara" and len(script.shots) == 2
    assert WRITER_SYS  # a non-empty system prompt is defined


def test_write_script_injects_known_roster_for_later_episodes():
    class Recording(FakeProviders):
        def chat(self, system, user):
            self.last_user = user
            return super().chat(system, user)

    p = Recording(chat_reply=json.dumps(GOOD))
    write_script(p, "episode 2", known={"Mara": "red jacket"})
    assert "Mara" in p.last_user and "red jacket" in p.last_user
    assert "REUSE" in p.last_user.upper()  # the writer is told to reuse the cast


def _script(n=2):
    return Script(premise="p", style="anime", shots=[Shot(i, "A", "room", f"acts {i}") for i in range(n)])


def test_direct_shots_returns_one_framing_per_shot():
    p = FakeProviders(chat_reply='{"shots": ["wide, low angle", "close-up, push in"]}')
    notes = direct_shots(p, _script(2))
    assert len(notes) == 2 and "wide" in notes[0]


def test_direct_shots_falls_back_when_output_bad():
    p = FakeProviders(chat_reply="the model rambled with no json")
    notes = direct_shots(p, _script(3))
    assert len(notes) == 3 and all(n.strip() for n in notes)  # padded with a neutral note


def test_plan_edit_returns_title_and_logline():
    p = FakeProviders(chat_reply='{"title": "The Vault", "logline": "Two siblings, one lock."}')
    plan = plan_edit(p, _script())
    assert plan["title"] == "The Vault" and "siblings" in plan["logline"]


def test_plan_edit_falls_back_on_bad_output():
    p = FakeProviders(chat_reply="no json here")
    plan = plan_edit(p, _script())
    assert plan["title"] and "logline" in plan


def test_revise_prompt_returns_corrected_text():
    p = FakeProviders(chat_reply="flat 2D anime, red jacket, corrected lighting")
    revised = revise_prompt(p, "flat 2D anime, red jacket", "jacket too dark")
    assert "corrected" in revised
