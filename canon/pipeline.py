"""Orchestrator. render_shot turns one Shot into a clip: it assembles the prompt from the Bible
(locked descriptor + seed + reference), generates, and runs the Qwen-VL QC loop that regenerates
a drifting shot up to MAX_REGEN times. This is the consistency + self-correction mechanism."""
import os

from canon.config import MAX_REGEN


def render_shot(shot, bible, providers, work_dir, max_regen=MAX_REGEN):
    if shot.character:
        c = bible.characters[shot.character]  # writer-created characters are in the bible by now
        shot.prompt = bible.prompt_for(shot.character, shot.action)
        seed, ref = c.seed, c.ref_image
    else:
        shot.prompt = f"{bible.style}, {shot.action}"  # narration / establishing shot
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
