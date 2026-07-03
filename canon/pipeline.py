"""Orchestrator. render_shot turns one Shot into a clip: it assembles the prompt from the Bible
(locked descriptor + seed + reference), generates, and runs the Qwen-VL QC loop that regenerates
a drifting shot up to MAX_REGEN times. This is the consistency + self-correction mechanism."""
import glob
import os
import re

from canon.agents import write_script
from canon.config import MAX_REGEN
from canon.edit import concat


def render_shot(shot, bible, providers, work_dir, max_regen=MAX_REGEN):
    if shot.character and shot.character in bible.characters:
        c = bible.characters[shot.character]
        shot.prompt = bible.prompt_for(shot.character, shot.action)
        seed, ref = c.seed, c.ref_image
    else:
        # narration/establishing shot, or a character the writer named but never defined:
        # degrade to a style+action prompt rather than crashing mid-episode.
        shot.prompt = f"{bible.style}, {shot.action}"
        seed, ref = 0, None

    # Filenames key off the integer shot index, never the model-supplied character name,
    # so a hostile name cannot produce a path outside work_dir.
    img = os.path.join(work_dir, f"shot{shot.index}.png")
    for attempt in range(max_regen + 1):
        providers.gen_image(shot.prompt, seed + attempt * 1000, ref, img)  # nudge seed on retry
        if providers.vl_check(img, shot.prompt)["ok"]:
            break

    clip = os.path.join(work_dir, f"shot{shot.index}.mp4")
    shot.clip = providers.img2video(img, shot.action, clip)
    return shot


def _slug(name):
    """Filesystem-safe slug from a model-supplied character name. Blocks path traversal/injection
    when the name becomes a ref-image filename."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", name).strip("_") or "char"


def establish_refs(bible, providers, series_dir):
    """Generate one canonical reference image per character (idempotent: skips those already set).
    The ref filename is slug(name)_seed.png inside series_dir/refs, so a hostile name can't escape."""
    refs_dir = os.path.join(series_dir, "refs")
    for name, c in bible.characters.items():
        if c.ref_image:
            continue
        path = os.path.join(refs_dir, f"{_slug(name)}_{int(c.seed)}.png")
        prompt = bible.prompt_for(name, "neutral character portrait, front view, plain background")
        providers.gen_image(prompt, c.seed, None, path)
        c.ref_image = path
    bible.save()
    return bible


def render_episode(premise, providers, series_dir, bible):
    """Full episode: Writer -> seed the Bible (episode 1 only) -> canonical refs -> render each shot
    through the QC loop -> stitch. Episodes after the first reuse the existing Bible unchanged, which
    is what keeps characters consistent across episodes."""
    known = {n: c.descriptor for n, c in bible.characters.items()} or None  # ep2+: reuse the cast
    script, chars = write_script(providers, premise, known)
    if not bible.characters:  # episode 1 seeds the canon; later episodes reuse it
        bible.style = script.style
        for c in chars:
            bible.upsert(c)
        bible.save()
    establish_refs(bible, providers, series_dir)

    n = len(glob.glob(os.path.join(series_dir, "episode*.mp4"))) + 1  # next episode number
    work = os.path.join(series_dir, f"work_ep{n}")
    os.makedirs(work, exist_ok=True)
    clips = [render_shot(shot, bible, providers, work).clip for shot in script.shots]
    return concat(clips, os.path.join(series_dir, f"episode{n}.mp4"))
