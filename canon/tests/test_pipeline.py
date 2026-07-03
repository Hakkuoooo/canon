import os

from canon.bible import Bible
from canon.pipeline import render_shot
from canon.providers import FakeProviders
from canon.schemas import CharacterSheet, Shot


def _bible(tmp_path, ref="ref.png"):
    b = Bible(str(tmp_path))
    b.style = "flat 2D anime"
    b.upsert(CharacterSheet("Mara", "red jacket, short black hair", 99, ref_image=ref))
    return b


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
    # A hostile character name must not reach the filesystem path.
    b = Bible(str(tmp_path))
    b.style = "flat 2D anime"
    b.upsert(CharacterSheet("../../evil", "red jacket", 1))
    p = FakeProviders()
    shot = render_shot(Shot(3, "../../evil", "hall", "runs"), b, p, str(tmp_path))
    assert shot.clip.endswith("shot3.mp4")  # index-based filename
    assert os.path.dirname(shot.clip) == str(tmp_path)  # stays in work_dir, no traversal
    assert os.path.exists(shot.clip)
