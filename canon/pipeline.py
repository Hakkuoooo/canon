"""Orchestrator. render_shot turns one Shot into a clip: it assembles the prompt from the Bible
(locked descriptor + seed + reference), generates, and runs the Qwen-VL QC loop that regenerates
a drifting shot up to MAX_REGEN times. This is the consistency + self-correction mechanism."""
import glob
import json
import os
import re

from canon.agents import direct_shots, plan_edit, revise_prompt, write_script
from canon.config import MAX_REGEN
from canon.edit import concat


def _report(series_dir, **payload):
    """Write the current pipeline stage to progress.json so the API can serve honest progress
    while a render runs (real generation takes minutes per shot). Written atomically (tmp +
    os.replace) so a concurrent GET never reads a half-written file. Data only, no copy: the
    frontend owns the wording."""
    os.makedirs(series_dir, exist_ok=True)
    path = os.path.join(series_dir, "progress.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f)
    os.replace(tmp, path)


def render_shot(shot, bible, providers, work_dir, max_regen=MAX_REGEN, framing="", report=None):
    report = report or (lambda **kw: None)  # progress hook; no-op for direct callers/tests
    if shot.character and shot.character in bible.characters:
        c = bible.characters[shot.character]
        base = bible.prompt_for(shot.character, shot.action)
        seed, ref = c.seed, c.ref_image
    else:
        # narration/establishing shot, or a character the writer named but never defined:
        # degrade to a style+action prompt rather than crashing mid-episode.
        base = f"{bible.style}, {shot.action}"
        seed, ref = 0, None
    shot.prompt = f"{base}, {framing}" if framing else base  # Cinematographer's framing

    # Filenames key off the integer shot index, never the model-supplied character name,
    # so a hostile name cannot produce a path outside work_dir.
    img = os.path.join(work_dir, f"shot{shot.index}.png")
    for attempt in range(max_regen + 1):
        report(phase="render" if attempt == 0 else "rerender")
        providers.gen_image(shot.prompt, seed, ref, img)  # seed stays fixed for consistency
        report(phase="check")
        verdict = providers.vl_check(img, shot.prompt)
        if verdict.get("ok"):
            break
        # Generator agent: revise the prompt to fix the drift the critic flagged, then retry.
        shot.prompt = revise_prompt(providers, shot.prompt, verdict.get("reason", ""))

    report(phase="animate")  # image-to-video, the slow call
    clip = os.path.join(work_dir, f"shot{shot.index}.mp4")
    shot.clip = providers.img2video(img, shot.action, clip)
    return shot


def _slug(name):
    """Filesystem-safe slug from a model-supplied character name. Blocks path traversal/injection
    when the name becomes a ref-image filename."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", name).strip("_") or "char"


def establish_refs(bible, providers, series_dir, report=None):
    """Generate one canonical reference image per character (idempotent: skips those already set).
    The ref filename is slug(name)_seed.png inside series_dir/refs, so a hostile name can't escape."""
    report = report or (lambda **kw: None)
    refs_dir = os.path.join(series_dir, "refs")
    missing = [(name, c) for name, c in bible.characters.items() if not c.ref_image]
    for k, (name, c) in enumerate(missing):
        report(stage="casting", character=name, i=k + 1, n=len(missing))
        path = os.path.join(refs_dir, f"{_slug(name)}_{int(c.seed)}.png")
        prompt = bible.prompt_for(name, "neutral character portrait, front view, plain background")
        providers.gen_image(prompt, c.seed, None, path)
        c.ref_image = path
    bible.save()
    return bible


def render_episode(premise, providers, series_dir, bible, max_shots=None):
    """Full episode: Writer -> seed the Bible (episode 1 only) -> canonical refs -> render each shot
    through the QC loop -> stitch. Episodes after the first reuse the existing Bible unchanged, which
    is what keeps characters consistent across episodes. `max_shots` sets the episode length."""
    def report(**kw):
        _report(series_dir, **kw)  # progress for the UI poller

    report(stage="writer")
    known = {n: c.descriptor for n, c in bible.characters.items()} or None  # ep2+: reuse the cast
    script, chars = write_script(providers, premise, known, max_shots)
    if not bible.characters:  # episode 1 seeds the canon; later episodes reuse it
        bible.style = script.style
        for c in chars:
            bible.upsert(c)
        bible.save()
    establish_refs(bible, providers, series_dir, report=report)

    report(stage="framing")
    framing = direct_shots(providers, script)  # Cinematographer agent: per-shot camera direction
    report(stage="title")
    plan = plan_edit(providers, script)  # Editor agent: episode title + logline

    n = len(glob.glob(os.path.join(series_dir, "episode*.mp4"))) + 1  # next episode number
    work = os.path.join(series_dir, f"work_ep{n}")
    os.makedirs(work, exist_ok=True)
    total = len(script.shots)
    clips = []
    for i, shot in enumerate(script.shots):
        def shot_report(_i=i, **kw):  # default-arg bind: each shot reports its own number
            report(stage="shot", shot=_i + 1, total=total, **kw)

        clips.append(render_shot(shot, bible, providers, work, framing=framing[i], report=shot_report).clip)
    report(stage="stitch")
    out = concat(clips, os.path.join(series_dir, f"episode{n}.mp4"))
    with open(os.path.join(series_dir, f"episode{n}.json"), "w", encoding="utf-8") as f:
        json.dump(plan, f)  # Editor's title/logline, read back by the API
    report(stage="done", episode=n)
    return out
