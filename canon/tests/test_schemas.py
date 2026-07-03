from canon.schemas import CharacterSheet, Shot, Script


def test_shot_defaults_and_script_holds_shots():
    c = CharacterSheet(name="Mara", descriptor="red jacket, short black hair", seed=42)
    s = Shot(index=0, character="Mara", setting="hallway", action="runs")
    script = Script(premise="a heist", style="anime", shots=[s])

    assert s.dialogue == "" and s.clip is None
    assert s.prompt == ""
    assert script.shots[0].character == "Mara"
    assert c.ref_image is None


def test_script_shots_default_empty_and_independent():
    a = Script(premise="p", style="anime")
    b = Script(premise="q", style="anime")
    a.shots.append(Shot(index=0, character=None, setting="void", action="drifts"))

    assert a.shots and b.shots == []  # default_factory gives each its own list
