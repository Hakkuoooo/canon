import json
import os

from canon import pipeline as pipeline_mod
from canon.bible import Bible
from canon.pipeline import render_shot, render_episode, establish_refs, _slug
from canon.providers import FakeProviders
from canon.schemas import CharacterSheet, Shot


def _bible(tmp_path, ref="ref.png"):
    b = Bible(str(tmp_path))
    b.style = "flat 2D anime"
    b.upsert(CharacterSheet("Mara", "red jacket, short black hair", 99, ref_image=ref))
    return b


# ---- render_shot (Task 1.5) ----

def test_render_shot_uses_bible_and_makes_clip(tmp_path):
    p = FakeProviders()
    shot = render_shot(Shot(0, "Mara", "hall", "runs"), _bible(tmp_path), p, str(tmp_path))
    assert os.path.exists(shot.clip)
    assert "red jacket" in shot.prompt and "flat 2D anime" in shot.prompt
    assert p.calls["gen_image"] == 1 and p.calls["img2video"] == 1 and p.calls["vl_check"] == 1


def test_qc_failure_triggers_one_regen(tmp_path):
    p = FakeProviders(vl_results=[{"ok": False, "reason": "jacket drifted"}, {"ok": True, "reason": "ok"}])
    render_shot(Shot(0, "Mara", "hall", "runs"), _bible(tmp_path), p, str(tmp_path), max_regen=1)
    assert p.calls["gen_image"] == 2  # first attempt + one regeneration
    assert p.calls["vl_check"] == 2


def test_qc_regen_is_capped(tmp_path):
    p = FakeProviders(vl_results=[{"ok": False, "reason": "x"}] * 5)  # QC never passes
    render_shot(Shot(0, "Mara", "hall", "runs"), _bible(tmp_path), p, str(tmp_path), max_regen=1)
    assert p.calls["gen_image"] == 2  # capped at 1 + max_regen, does not loop forever


def test_narration_shot_has_no_character(tmp_path):
    b = Bible(str(tmp_path))
    b.style = "flat 2D anime"
    p = FakeProviders()
    shot = render_shot(Shot(0, None, "sky", "rain falls"), b, p, str(tmp_path))
    assert "rain falls" in shot.prompt and "flat 2D anime" in shot.prompt
    assert os.path.exists(shot.clip)


def test_shot_files_use_index_not_character_name(tmp_path):
    b = Bible(str(tmp_path))
    b.style = "flat 2D anime"
    b.upsert(CharacterSheet("../../evil", "red jacket", 1))
    p = FakeProviders()
    shot = render_shot(Shot(3, "../../evil", "hall", "runs"), b, p, str(tmp_path))
    assert shot.clip.endswith("shot3.mp4")  # index-based filename
    assert os.path.dirname(shot.clip) == str(tmp_path)  # stays in work_dir, no traversal
    assert os.path.exists(shot.clip)


# ---- render_episode + establish_refs (Task 1.7 / 2.1) ----

EP1 = json.dumps(
    {
        "style": "flat 2D anime",
        "characters": [
            {"name": "Mara", "descriptor": "crimson jacket", "seed": 40719},
            {"name": "Iven", "descriptor": "ash overcoat", "seed": 20884},
        ],
        "shots": [
            {"character": "Mara", "setting": "vault", "action": "forces the lock", "dialogue": "It opens."},
            {"character": "Iven", "setting": "vault", "action": "reads the ledger", "dialogue": "Careful."},
        ],
    }
)


def _patch_concat(monkeypatch):
    calls = {}

    def fake_concat(clips, out):
        calls["clips"] = list(clips)
        calls["out"] = out
        with open(out, "wb") as f:
            f.write(b"episode")
        return out

    monkeypatch.setattr(pipeline_mod, "concat", fake_concat)  # ffmpeg concat covered by edit tests
    return calls


def test_render_episode_seeds_bible_refs_and_concats(tmp_path, monkeypatch):
    calls = _patch_concat(monkeypatch)
    p = FakeProviders(chat_reply=EP1)
    bible = Bible(str(tmp_path))
    out = render_episode("two siblings, one vault", p, str(tmp_path), bible)

    assert set(bible.characters) == {"Mara", "Iven"} and bible.style == "flat 2D anime"
    for c in bible.characters.values():  # one canonical ref each, inside refs/
        assert c.ref_image and os.path.dirname(c.ref_image) == os.path.join(str(tmp_path), "refs")
    assert len(calls["clips"]) == 2 and calls["out"] == out and os.path.exists(out)


def test_slug_sanitizes_hostile_names():
    assert _slug("../../evil") == "evil"
    assert _slug("Mara!!") == "Mara"
    assert _slug("///") == "char"  # empty after strip -> fallback


def test_establish_refs_contains_hostile_name_in_refs_dir(tmp_path):
    b = Bible(str(tmp_path))
    b.style = "anime"
    b.upsert(CharacterSheet("../../evil", "red jacket", 7))
    establish_refs(b, FakeProviders(), str(tmp_path))
    ref = b.characters["../../evil"].ref_image
    assert os.path.dirname(ref) == os.path.join(str(tmp_path), "refs")  # no traversal
    assert os.path.basename(ref) == "evil_7.png"
    assert os.path.exists(ref)


def test_episode_two_reuses_bible_characters(tmp_path, monkeypatch):
    _patch_concat(monkeypatch)
    p1 = FakeProviders(chat_reply=EP1)
    bible = Bible(str(tmp_path))
    render_episode("premise 1", p1, str(tmp_path), bible)
    mara_seed = bible.characters["Mara"].seed
    mara_ref = bible.characters["Mara"].ref_image

    # episode 2: a fresh Bible loads ep1's canon; ep2 script reuses Mara, invents "X"
    ep2 = json.dumps(
        {
            "style": "ignored",
            "characters": [{"name": "X", "descriptor": "y", "seed": 1}],
            "shots": [{"character": "Mara", "setting": "roof", "action": "escapes"}],
        }
    )
    p2 = FakeProviders(chat_reply=ep2)
    bible2 = Bible(str(tmp_path)).load()
    render_episode("premise 2", p2, str(tmp_path), bible2)

    assert bible2.characters["Mara"].seed == mara_seed  # canon preserved across episodes
    assert bible2.characters["Mara"].ref_image == mara_ref
    assert "X" not in bible2.characters  # ep2's invented character ignored
    assert p2.calls["gen_image"] == 1  # 1 shot only; refs already existed, not regenerated


def test_episodes_get_distinct_output_paths(tmp_path, monkeypatch):
    outs = []

    def rec(clips, out):
        outs.append(out)
        with open(out, "wb") as f:
            f.write(b"e")
        return out

    monkeypatch.setattr(pipeline_mod, "concat", rec)
    render_episode("p1", FakeProviders(chat_reply=EP1), str(tmp_path), Bible(str(tmp_path)))
    render_episode("p2", FakeProviders(chat_reply=EP1), str(tmp_path), Bible(str(tmp_path)).load())
    assert [os.path.basename(o) for o in outs] == ["episode1.mp4", "episode2.mp4"]  # no overwrite
