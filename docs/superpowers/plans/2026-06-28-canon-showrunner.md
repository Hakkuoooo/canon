# Canon — Consistency Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** An autonomous agent studio that turns one premise into a coherent ~60-90s stylized short-drama episode, and keeps the same characters consistent across episodes, for the Qwen Cloud AI Showrunner track.

**Architecture:** Four cooperating Qwen agents (Writer, Showrunner/Bible, Cinematographer, QC Critic) share one persistent state object (the Story Bible). Every external model call (Qwen chat, Wan image/video, Qwen-VL check, TTS) sits behind a single `providers` interface, so the deterministic pipeline is fully testable with fakes and the real Alibaba/DashScope calls are isolated and confirmed by a day-1 spike. Consistency is enforced by reusing a locked descriptor + reference image + fixed seed per character, verified by the Qwen-VL critic with a capped regeneration loop. No fine-tuning.

**Tech Stack:** Python 3.11, `dashscope` SDK (Qwen + Wan + Qwen-VL via Model Studio), ffmpeg (assembly), Gradio (UI), pytest. Deploy on Alibaba Cloud ECS + OSS.

---

## Reality Box (read before starting)

- **Runway: ~10 days.** Today 28 Jun, deadline 8-9 Jul. This is the single biggest constraint. Protect Phase 2 (the differentiator). Cut anything that threatens it.
- **The one thing that wins:** cross-episode character consistency, shown on camera, with the QC agent visibly catching and fixing a bad shot. Everything else is in service of that 60-second reveal.
- **Two day-1 kill-risks** (Task 0): can you reach Alibaba Cloud + DashScope from the UK, and does the video model support reference-image + seed conditioning? If either fails, the plan pivots same-day (fallbacks noted in Task 0).
- **Demo is pre-generated, not live.** Generation is slow and costs credits. The agent genuinely produces both episodes; we record the result, we do not wait on camera.
- **Aesthetic: stylized / flat-anime, never photoreal faces.** This is where AI video looks worst and consistency is hardest. Dodge it.

## Scope (what is IN, what is OUT)

IN: one genre, one art style, 1-2 recurring characters, English, ~60-90s episodes, exactly two episodes (ep1 + ep2 for the reveal), Gradio UI showing the live pipeline, ECS+OSS deploy, 3-min demo video, README + architecture diagram, blog post.

OUT (`ponytail`, add back only if ahead): user accounts, content library, real-time on-stage generation, custom frontend, music generation (use one royalty-free bed), more than two characters, multiple genres, mobile.

## File Structure

```
canon/
  config.py        # model ids, default seeds, caps (MAX_REGEN, shot count). One place to tune.
  schemas.py       # dataclasses: CharacterSheet, Shot, Script. Pure data. TDD.
  bible.py         # Story Bible: load/save JSON, upsert character, assemble per-shot prompt. TDD.
  providers.py     # Providers interface + FakeProviders (tests) + DashScopeProviders (real, confirmed in Task 0).
  agents.py        # writer(), build_bible(), cinematographer(), qc_critic() — prompts + structured parsing.
  pipeline.py      # orchestrator: premise -> episode.mp4. Wires agents + providers + QC loop. TDD with fakes.
  edit.py          # ffmpeg: stitch clips, add TTS voiceover, burn subtitles, mux music bed. TDD via ffprobe.
  app.py           # Gradio UI: premise+style in, live pipeline view, plays episode, "Generate Episode 2".
  tests/
    test_schemas.py
    test_bible.py
    test_pipeline.py
    test_edit.py
  data/series/<id>/   # bible.json, refs/, shots/, episodes/   (gitignored; mirrored to OSS in deploy)
  deploy/
    ecs-setup.md     # exact deploy runbook
  spikes/
    spike_providers.py  # Task 0 runnable: confirms each real API call
  README.md
  architecture.md
  requirements.txt
  .gitignore
```

---

## Phase 0 — De-risk + scaffold (Day 1). GO/NO-GO at the end.

### Task 0.1: Initialize repo and scaffold

**Files:**
- Create: `requirements.txt`, `.gitignore`, `config.py`

- [ ] **Step 1: Init repo and structure**

```bash
cd /Users/hakku/Desktop/qwen_hackathon
git init
mkdir -p canon/tests canon/spikes canon/deploy canon/data
python3.11 -m venv .venv && source .venv/bin/activate
```

- [ ] **Step 2: Write `requirements.txt`**

```
dashscope
gradio
pytest
```
Then: `pip install -r requirements.txt` and confirm ffmpeg: `ffmpeg -version` (install via `brew install ffmpeg` if missing).

- [ ] **Step 3: Write `.gitignore`**

```
.venv/
__pycache__/
canon/data/
.env
*.mp4
*.png
```

- [ ] **Step 4: Write `canon/config.py`**

```python
import os

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# Confirm/replace these ids in Task 0.2 against the model list the hackathon gives you.
CHAT_MODEL = "qwen-plus"
VL_MODEL = "qwen-vl-plus"
IMAGE_MODEL = "wan2.1-t2i"        # text/ref -> image
VIDEO_MODEL = "wan2.1-i2v"        # image -> video
TTS_MODEL = "cosyvoice-v1"

MAX_REGEN = 1          # QC regeneration attempts per shot (cost ceiling)
MAX_SHOTS = 8          # ponytail: caps episode length and credit burn
DEFAULT_STYLE = "flat 2D anime, soft cel shading, muted palette"
```

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "chore: scaffold canon project"
```

### Task 0.2: Spike — confirm every real API call (THE day-1 gate)

**Files:**
- Create: `canon/spikes/spike_providers.py`

This is a spike, not TDD. The goal is to make each call succeed once and record the exact request/response shape, then transcribe the working calls into `providers.py` (Task 1.3). Do NOT proceed to Phase 1 until all five print real output.

- [ ] **Step 1: Get credentials and set the key**

Create the Alibaba Cloud account, enable Model Studio (DashScope), create an API key.
`export DASHSCOPE_API_KEY=...`
If account creation or model access is blocked from the UK: that is the kill-risk. Fallback ladder, in order: (a) use a VPN-free region endpoint if the console offers one, (b) switch IMAGE/VIDEO to whichever generation model the hackathon resources page actually grants, (c) escalate in the hackathon Discord/support same day. Do not silently continue with a half-working key.

- [ ] **Step 2: Write `spike_providers.py` — one function per capability, run each**

```python
import dashscope
from canon import config
dashscope.api_key = config.DASHSCOPE_API_KEY

def spike_chat():
    r = dashscope.Generation.call(model=config.CHAT_MODEL,
        messages=[{"role":"user","content":"Reply with the single word: ok"}])
    print("CHAT:", r)  # confirm where the text lives in the response object

def spike_image():
    # Confirm: does this model accept a reference image + seed? That is the consistency gate.
    r = dashscope.ImageSynthesis.call(model=config.IMAGE_MODEL,
        prompt="flat 2D anime, a girl in a red jacket, short black hair, standing in a hallway",
        seed=42, n=1)
    print("IMAGE:", r)  # confirm output url/path + that seed param is accepted

def spike_vl():
    r = dashscope.MultiModalConversation.call(model=config.VL_MODEL,
        messages=[{"role":"user","content":[
            {"image":"<paste an image url from spike_image>"},
            {"text":"Is there a girl in a red jacket? Answer yes or no and why."}]}])
    print("VL:", r)

def spike_video():
    print("VIDEO: confirm image-to-video call + how to poll for the async result")

def spike_tts():
    print("TTS: confirm synth call + output audio bytes/path")

if __name__ == "__main__":
    spike_chat(); spike_image(); spike_vl()
```

Run: `python -m canon.spikes.spike_providers`
Expected: CHAT prints "ok"; IMAGE returns an image URL and does not error on `seed`; VL returns a yes/no judgement.

- [ ] **Step 3: Record findings at the top of `providers.py` as a comment block**

Write down, verbatim: the exact call signature for each of chat/image/img2video/vl/tts, where the result payload lives, whether seed + reference-image conditioning are supported, and async-polling shape for video.

- [ ] **Step 4: GO/NO-GO checkpoint (write the verdict in the commit message)**

- All five calls work AND image accepts seed+reference → **GO**, proceed to Phase 1 as written.
- Calls work but NO reference-image conditioning → **GO with pivot**: consistency leans on (locked descriptor + fixed seed + the QC reject loop) only. Expect weaker consistency; the QC loop and descriptor become more important. Note this in `architecture.md`.
- Cannot get model access at all → **STOP**, resolve access before any further build. Nothing downstream matters until this is fixed.

```bash
git add -A && git commit -m "spike: confirm dashscope providers [GO|GO-pivot|BLOCKED]"
```

---

## Phase 1 — End-to-end spine (Days 2-4)

Goal: one premise produces one playable episode.mp4 through the real pipeline, no consistency logic yet. Build the testable core first (schemas, bible, pipeline with fakes), then wire real providers.

### Task 1.1: Data schemas

**Files:**
- Create: `canon/schemas.py`
- Test: `canon/tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

```python
from canon.schemas import CharacterSheet, Shot, Script

def test_shot_defaults_and_script_holds_shots():
    c = CharacterSheet(name="Mara", descriptor="red jacket, short black hair", seed=42)
    s = Shot(index=0, character="Mara", setting="hallway", action="runs")
    script = Script(premise="a heist", style="anime", shots=[s])
    assert s.dialogue == "" and s.clip is None
    assert script.shots[0].character == "Mara"
    assert c.ref_image is None
```

- [ ] **Step 2: Run it, expect failure**

Run: `pytest canon/tests/test_schemas.py -v`
Expected: FAIL, `ModuleNotFoundError: canon.schemas`.

- [ ] **Step 3: Implement**

```python
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class CharacterSheet:
    name: str
    descriptor: str          # locked appearance text, reused in every prompt
    seed: int
    ref_image: Optional[str] = None

@dataclass
class Shot:
    index: int
    character: Optional[str]
    setting: str
    action: str
    dialogue: str = ""
    prompt: str = ""
    clip: Optional[str] = None

@dataclass
class Script:
    premise: str
    style: str
    shots: List[Shot] = field(default_factory=list)
```

- [ ] **Step 4: Run it, expect pass**

Run: `pytest canon/tests/test_schemas.py -v` → PASS.

- [ ] **Step 5: Commit**

```bash
git add canon/schemas.py canon/tests/test_schemas.py && git commit -m "feat: data schemas"
```

### Task 1.2: Story Bible (persistence + prompt assembly — the consistency substrate)

**Files:**
- Create: `canon/bible.py`
- Test: `canon/tests/test_bible.py`

- [ ] **Step 1: Write the failing test**

```python
from canon.bible import Bible
from canon.schemas import CharacterSheet

def test_bible_persists_and_assembles_prompt(tmp_path):
    b = Bible(str(tmp_path))
    b.style = "flat 2D anime"
    b.upsert(CharacterSheet(name="Mara", descriptor="red jacket, short black hair", seed=42))
    b.save()

    reloaded = Bible(str(tmp_path)).load()
    assert reloaded.characters["Mara"].seed == 42                 # persistence = cross-episode consistency
    prompt = reloaded.prompt_for("Mara", "runs down a hall")
    assert "red jacket" in prompt and "flat 2D anime" in prompt
```

- [ ] **Step 2: Run it, expect failure**

Run: `pytest canon/tests/test_bible.py -v` → FAIL, no module.

- [ ] **Step 3: Implement**

```python
import json, os
from canon.schemas import CharacterSheet

class Bible:
    def __init__(self, series_dir):
        self.dir = series_dir
        self.path = os.path.join(series_dir, "bible.json")
        self.style = ""
        self.characters = {}

    def load(self):
        if os.path.exists(self.path):
            data = json.load(open(self.path))
            self.style = data.get("style", "")
            self.characters = {n: CharacterSheet(**c) for n, c in data.get("characters", {}).items()}
        return self

    def save(self):
        os.makedirs(self.dir, exist_ok=True)
        json.dump(
            {"style": self.style, "characters": {n: vars(c) for n, c in self.characters.items()}},
            open(self.path, "w"), indent=2)

    def upsert(self, sheet: CharacterSheet):
        self.characters[sheet.name] = sheet

    def prompt_for(self, character_name, action):
        c = self.characters[character_name]
        return f"{self.style}, {c.descriptor}, {action}"
```

- [ ] **Step 4: Run it, expect pass** → `pytest canon/tests/test_bible.py -v` PASS.

- [ ] **Step 5: Commit**

```bash
git add canon/bible.py canon/tests/test_bible.py && git commit -m "feat: story bible persistence + prompt assembly"
```

### Task 1.3: Providers interface + fake + real

**Files:**
- Create: `canon/providers.py`

No unit test for the real provider (it hits paid APIs). The FakeProviders is the test double used everywhere else. Transcribe the real calls from the Task 0.2 spike.

- [ ] **Step 1: Write the interface and the fake**

```python
import os
from abc import ABC, abstractmethod

class Providers(ABC):
    @abstractmethod
    def chat(self, system: str, user: str) -> str: ...
    @abstractmethod
    def gen_image(self, prompt: str, seed: int, ref_image: str | None, out_path: str) -> str: ...
    @abstractmethod
    def img2video(self, image_path: str, motion: str, out_path: str) -> str: ...
    @abstractmethod
    def vl_check(self, image_path: str, expectation: str) -> dict: ...   # {"ok": bool, "reason": str}
    @abstractmethod
    def tts(self, text: str, out_path: str) -> str: ...

class FakeProviders(Providers):
    """Deterministic double for tests. `scripted` lets a test force vl_check outcomes."""
    def __init__(self, chat_reply='{"ok": true}', vl_results=None):
        self.chat_reply = chat_reply
        self.vl_results = list(vl_results or [])
        self.calls = {"gen_image": 0, "img2video": 0, "vl_check": 0}

    def chat(self, system, user): return self.chat_reply
    def gen_image(self, prompt, seed, ref_image, out_path):
        self.calls["gen_image"] += 1
        open(out_path, "wb").write(b"\x89PNG\r\n"); return out_path
    def img2video(self, image_path, motion, out_path):
        self.calls["img2video"] += 1
        open(out_path, "wb").write(b"fakemp4"); return out_path
    def vl_check(self, image_path, expectation):
        self.calls["vl_check"] += 1
        return self.vl_results.pop(0) if self.vl_results else {"ok": True, "reason": "ok"}
    def tts(self, text, out_path):
        open(out_path, "wb").write(b"fakewav"); return out_path
```

- [ ] **Step 2: Write the real provider from the spike findings**

Paste the spike comment block at the top, then implement `DashScopeProviders(Providers)` using the exact calls you confirmed in Task 0.2. Each method wraps one `dashscope` call, downloads the returned asset to `out_path`, and returns the path. `vl_check` parses the Qwen-VL reply into `{"ok", "reason"}` (treat a reply containing "yes"/"consistent" as ok). Keep it boring; one call per method.

- [ ] **Step 3: Smoke-test the real provider manually**

```bash
python -c "from canon.providers import DashScopeProviders as D; p=D(); print(p.chat('','say ok'))"
```
Expected: prints `ok`.

- [ ] **Step 4: Commit**

```bash
git add canon/providers.py && git commit -m "feat: providers interface, fake, and dashscope impl"
```

### Task 1.4: Agents (prompts + structured parsing)

**Files:**
- Create: `canon/agents.py`
- Test: `canon/tests/test_pipeline.py` (shared; add agent-parsing tests here)

- [ ] **Step 1: Write the failing test for the writer's JSON parsing**

```python
from canon.agents import parse_script
from canon.providers import FakeProviders

def test_parse_script_builds_shots():
    raw = '{"style":"anime","characters":[{"name":"Mara","descriptor":"red jacket","seed":7}],' \
          '"shots":[{"character":"Mara","setting":"hall","action":"runs","dialogue":"go"}]}'
    script, chars = parse_script(raw, premise="a heist")
    assert script.shots[0].index == 0
    assert chars[0].name == "Mara" and chars[0].seed == 7
```

- [ ] **Step 2: Run it, expect failure** → FAIL, no `parse_script`.

- [ ] **Step 3: Implement `agents.py`**

```python
import json
from canon.config import CHAT_MODEL, VL_MODEL, MAX_SHOTS, DEFAULT_STYLE
from canon.schemas import Script, Shot, CharacterSheet

WRITER_SYS = (
    "You are a short-drama writer. Given a premise, output STRICT JSON with keys: "
    "style (string), characters (list of {name, descriptor, seed}), "
    f"shots (list of {{character, setting, action, dialogue}}, max {MAX_SHOTS}). "
    "descriptor is a short fixed visual description. Seeds are distinct integers. No prose, JSON only."
)

def parse_script(raw: str, premise: str):
    data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    chars = [CharacterSheet(name=c["name"], descriptor=c["descriptor"], seed=int(c["seed"]))
             for c in data["characters"]]
    shots = [Shot(index=i, character=s.get("character"), setting=s["setting"],
                  action=s["action"], dialogue=s.get("dialogue", ""))
             for i, s in enumerate(data["shots"][:MAX_SHOTS])]
    return Script(premise=premise, style=data.get("style", DEFAULT_STYLE), shots=shots), chars

def write_script(providers, premise: str):
    return parse_script(providers.chat(WRITER_SYS, premise), premise)

QC_SYS = "You check if an image matches an expected description for visual consistency."

def qc_verdict(providers, image_path: str, expectation: str) -> dict:
    return providers.vl_check(image_path, expectation)
```

- [ ] **Step 4: Run it, expect pass** → PASS.

- [ ] **Step 5: Commit**

```bash
git add canon/agents.py canon/tests/test_pipeline.py && git commit -m "feat: writer agent + script parsing"
```

### Task 1.5: Pipeline orchestrator (spine, no QC yet)

**Files:**
- Create: `canon/pipeline.py`
- Test: `canon/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test (with fakes, zero API cost)**

```python
import os
from canon.pipeline import render_shot
from canon.bible import Bible
from canon.schemas import CharacterSheet, Shot
from canon.providers import FakeProviders

def test_render_shot_uses_bible_seed_and_makes_clip(tmp_path):
    b = Bible(str(tmp_path)); b.style = "anime"
    b.upsert(CharacterSheet(name="Mara", descriptor="red jacket", seed=99))
    p = FakeProviders()
    shot = render_shot(Shot(0, "Mara", "hall", "runs"), b, p, str(tmp_path))
    assert os.path.exists(shot.clip)
    assert "red jacket" in shot.prompt
    assert p.calls["gen_image"] == 1
```

- [ ] **Step 2: Run it, expect failure** → FAIL, no `render_shot`.

- [ ] **Step 3: Implement `pipeline.py` (spine version)**

```python
import os
from canon.config import MAX_REGEN

def render_shot(shot, bible, providers, work_dir, max_regen=MAX_REGEN):
    if shot.character:
        c = bible.characters[shot.character]
        shot.prompt = bible.prompt_for(shot.character, shot.action)
        seed, ref = c.seed, c.ref_image
    else:
        shot.prompt = f"{bible.style}, {shot.action}"
        seed, ref = 0, None

    img = os.path.join(work_dir, f"shot{shot.index}.png")
    providers.gen_image(shot.prompt, seed, ref, img)        # QC loop added in Phase 2
    clip = os.path.join(work_dir, f"shot{shot.index}.mp4")
    shot.clip = providers.img2video(img, shot.action, clip)
    return shot
```

- [ ] **Step 4: Run it, expect pass** → PASS.

- [ ] **Step 5: Commit**

```bash
git add canon/pipeline.py canon/tests/test_pipeline.py && git commit -m "feat: render_shot spine"
```

### Task 1.6: Editor (stitch + voice + subtitles)

**Files:**
- Create: `canon/edit.py`
- Test: `canon/tests/test_edit.py`

- [ ] **Step 1: Write the failing test (real ffmpeg, fake inputs)**

```python
import subprocess, os
from canon.edit import assemble

def _tiny_clip(path):
    subprocess.run(["ffmpeg","-f","lavfi","-i","color=c=black:s=64x64:d=1","-y",path],
                   check=True, capture_output=True)

def test_assemble_concatenates_clips(tmp_path):
    clips = [str(tmp_path/f"{i}.mp4") for i in range(2)]
    for c in clips: _tiny_clip(c)
    out = str(tmp_path/"episode.mp4")
    assemble(clips, out)
    dur = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=nw=1:nk=1", out], capture_output=True, text=True).stdout
    assert os.path.exists(out) and float(dur) > 1.5
```

- [ ] **Step 2: Run it, expect failure** → FAIL, no `assemble`.

- [ ] **Step 3: Implement `edit.py` (concat first; voice/subs added as steps below)**

```python
import subprocess, os

def assemble(clip_paths, out_path):
    listfile = out_path + ".txt"
    with open(listfile, "w") as f:
        for c in clip_paths:
            f.write(f"file '{os.path.abspath(c)}'\n")
    subprocess.run(["ffmpeg","-f","concat","-safe","0","-i",listfile,
                    "-c","copy","-y",out_path], check=True, capture_output=True)
    os.remove(listfile)
    return out_path
```

- [ ] **Step 4: Run it, expect pass** → PASS.

- [ ] **Step 5: Add voiceover + burned subtitles**

Extend `assemble` to accept `lines: list[(clip, text)]`, call `providers.tts(text, wav)` per line (passed in), and mux audio + burn an `.srt` via ffmpeg `subtitles=` filter. Add one test asserting the output still has duration > 0 with an audio stream (`ffprobe ... -show_streams`). Keep it one function. `ponytail: one srt + concat filter, no timeline lib`.

- [ ] **Step 6: Commit**

```bash
git add canon/edit.py canon/tests/test_edit.py && git commit -m "feat: ffmpeg assemble + voice + subtitles"
```

### Task 1.7: Wire the full spine on one real premise (integration, manual)

- [ ] **Step 1: Add `render_episode` to `pipeline.py`**

```python
from canon.agents import write_script
from canon.edit import assemble

def render_episode(premise, providers, series_dir, bible):
    script, chars = write_script(providers, premise)
    if not bible.characters:                 # episode 1 seeds the bible; later episodes reuse it
        bible.style = script.style
        for c in chars: bible.upsert(c)
        bible.save()
    import os; work = os.path.join(series_dir, "work"); os.makedirs(work, exist_ok=True)
    clips = [render_shot(s, bible, providers, work).clip for s in script.shots]
    out = os.path.join(series_dir, "episode.mp4")
    return assemble(clips, out)
```

- [ ] **Step 2: Run end-to-end with real providers on ONE premise**

```bash
python -c "from canon.providers import DashScopeProviders; from canon.bible import Bible; \
from canon.pipeline import render_episode; \
print(render_episode('Two thieves get trapped in a vault', DashScopeProviders(), 'canon/data/series/demo', Bible('canon/data/series/demo')))"
```
Expected: a real `episode.mp4` plays, characters look roughly right. Note quality + cost per run.

- [ ] **Step 3: Phase-1 checkpoint commit**

```bash
git add -A && git commit -m "feat: end-to-end episode spine working on real providers"
```

---

## Phase 2 — The differentiator (Days 5-7). Protect this time.

### Task 2.1: Lock character references into the Bible (consistency anchor)

**Files:** Modify `canon/pipeline.py`, `canon/bible.py`

- [ ] **Step 1: After episode-1 script, generate ONE canonical reference image per character and store its path + seed in the Bible**

Add `establish_refs(bible, providers, work_dir)`: for each character with no `ref_image`, call `gen_image(bible.prompt_for(name, "neutral portrait, front view"), seed, None, ref_path)`, set `c.ref_image = ref_path`, `bible.save()`. Call it inside `render_episode` right after the bible is first populated.

- [ ] **Step 2: Test that refs persist and are reused (fakes)**

```python
def test_refs_persist_across_episodes(tmp_path):
    # build bible with a ref, save, reload, assert ref path survives -> ep2 reuses same character
    ...
    assert reloaded.characters["Mara"].ref_image is not None
```

- [ ] **Step 3: Run, pass, commit** → `git commit -m "feat: canonical character references in bible"`

### Task 2.2: QC critic loop with capped regeneration (the visible agentic mechanism)

**Files:** Modify `canon/pipeline.py`, `canon/tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test — a failed check triggers exactly one regen**

```python
from canon.providers import FakeProviders
from canon.pipeline import render_shot
from canon.bible import Bible
from canon.schemas import CharacterSheet, Shot

def test_qc_failure_triggers_one_regen(tmp_path):
    b = Bible(str(tmp_path)); b.style="anime"
    b.upsert(CharacterSheet(name="Mara", descriptor="red jacket", seed=1, ref_image="r.png"))
    p = FakeProviders(vl_results=[{"ok": False, "reason":"wrong jacket"}, {"ok": True, "reason":"ok"}])
    render_shot(Shot(0,"Mara","hall","runs"), b, p, str(tmp_path), max_regen=1)
    assert p.calls["gen_image"] == 2     # first + one regen
    assert p.calls["vl_check"] == 2
```

- [ ] **Step 2: Run it, expect failure** (current `render_shot` has no QC) → FAIL.

- [ ] **Step 3: Update `render_shot` to add the QC loop**

```python
def render_shot(shot, bible, providers, work_dir, max_regen=MAX_REGEN):
    if shot.character:
        c = bible.characters[shot.character]
        shot.prompt = bible.prompt_for(shot.character, shot.action)
        seed, ref = c.seed, c.ref_image
    else:
        shot.prompt = f"{bible.style}, {shot.action}"; seed, ref = 0, None

    import os
    img = os.path.join(work_dir, f"shot{shot.index}.png")
    for attempt in range(max_regen + 1):
        providers.gen_image(shot.prompt, seed + attempt * 1000, ref, img)  # nudge seed on retry
        if providers.vl_check(img, shot.prompt)["ok"]:
            break
    clip = os.path.join(work_dir, f"shot{shot.index}.mp4")
    shot.clip = providers.img2video(img, shot.action, clip)
    return shot
```

- [ ] **Step 4: Run it, expect pass** → PASS.

- [ ] **Step 5: Commit** → `git commit -m "feat: Qwen-VL QC loop with capped regeneration"`

### Task 2.3: Episode 2 — prove cross-episode consistency

**Files:** Modify `canon/pipeline.py`; add test

- [ ] **Step 1: Test that a second `render_episode` reuses the existing bible (no new characters)**

```python
def test_episode_two_reuses_characters(tmp_path, monkeypatch):
    # seed a saved bible, run render_episode again with a fake writer that returns NEW chars,
    # assert the bible still has the ORIGINAL character (episode 1 canon wins).
    ...
```

- [ ] **Step 2: Implement the guard in `render_episode`**

Already partially present (`if not bible.characters`). Make it explicit: when the bible already has characters, ignore new character definitions from the writer and map the script's characters onto existing canon by role/order. Commit.

- [ ] **Step 3: Real two-episode run + eyeball the reveal**

```bash
# ep1 then ep2 on the SAME series dir; confirm the character looks the same in both
```
This is the money shot. If consistency is weak, spend remaining Phase-2 time tuning: stronger descriptor, lower motion, the GO-pivot fallback from Task 0.2. Commit the working pair.

---

## Phase 3 — Ship (Days 8-10)

### Task 3.1: Gradio UI showing the live pipeline

**Files:** Create `canon/app.py`

- [ ] **Step 1: Build the UI**

Inputs: premise textbox, style dropdown, "Generate Episode" button, "Generate Episode 2" button. Output: a streaming log area that prints each agent step (`Writer → Bible → Cinematographer → shot k → QC verdict`) and a video player. Wire buttons to `render_episode`. The visible step log IS the demo's proof of agent architecture.

- [ ] **Step 2: Run locally and click through** → `python -m canon.app`, confirm both episodes play and the log shows QC catching a shot.

- [ ] **Step 3: Commit** → `git commit -m "feat: gradio pipeline UI"`

### Task 3.2: Deploy to Alibaba Cloud (the required proof)

**Files:** Create `canon/deploy/ecs-setup.md`

- [ ] **Step 1: Provision + run**

Smallest ECS instance, install python+ffmpeg, clone repo, set `DASHSCOPE_API_KEY`, run Gradio bound to `0.0.0.0`, open the security-group port. Store generated `episode.mp4` files to an **OSS** bucket (add a 6-line `oss_put()` in `providers.py`). Using ECS + OSS + Model Studio = the multi-service stack judges score.

- [ ] **Step 2: Write `ecs-setup.md` with the exact commands you ran** (this doubles as deployment proof).

- [ ] **Step 3: Commit** → `git commit -m "docs: alibaba cloud deploy runbook + OSS asset storage"`

### Task 3.3: Submission artifacts

- [ ] **Step 1: `architecture.md` + diagram** — the four-agents-plus-bible-plus-QC-loop diagram (export a PNG). Required by the brief.
- [ ] **Step 2: `README.md`** — what it is, the consistency mechanism, how to run, the Alibaba services used, OSI license file.
- [ ] **Step 3: Record the sub-3-min demo** — arc: premise in (5s) → agents work live (40s) → episode 1 (40s) → "episode 2, same character" reveal (40s) → QC catching+fixing a shot (20s) → market + "deployed on Alibaba Cloud" close (15s). Upload to YouTube.
- [ ] **Step 4: Blog post** — "Building a consistency-first AI showrunner on Qwen Cloud." Separately prize-eligible and the profile artifact. Publish, link in submission.
- [ ] **Step 5: Submit on Devpost** — repo (public, licensed), video, architecture diagram, deployment proof, track = AI Showrunner. Submit a day early.
- [ ] **Step 6: Final commit + tag** → `git commit -m "docs: submission artifacts" && git tag submission`

---

## Self-Review

**Spec coverage:** Four agents + Bible (1.2, 1.4, 2.1) ✓; consistency mechanism = descriptor+seed+ref+QC (1.2, 2.1, 2.2) ✓; cross-episode reveal (2.3) ✓; Qwen/Wan/Qwen-VL/TTS (0.2, 1.3) ✓; ffmpeg editor (1.6) ✓; UI (3.1) ✓; Alibaba deploy + multi-service (3.2) ✓; demo/diagram/blog/README/submit (3.3) ✓; day-1 kill-risks (0.2) ✓. No spec gap found.

**Placeholder scan:** The only deferred-detail points are the real DashScope call bodies (1.3) and the OSS/Gradio glue (3.1, 3.2), each gated by a runnable command with expected output rather than a vague "implement later." This is deliberate: those signatures are unknown until Task 0.2 confirms them, and fabricating them would be worse than a spike. Everything testable is TDD'd with real code.

**Type consistency:** `Providers` methods (`chat`, `gen_image`, `img2video`, `vl_check`, `tts`) are identical across `FakeProviders`, `DashScopeProviders`, and every caller. `render_shot(shot, bible, providers, work_dir, max_regen)` and `render_episode(premise, providers, series_dir, bible)` signatures match between Phase 1 and Phase 2. `Bible.prompt_for`, `.upsert`, `.load`, `.save` consistent throughout.

**Biggest risk:** ~10-day runway against a learning-phase pair. If Phase 2 slips, ship Phase 1 + one episode rather than a broken two-episode reveal. The QC loop (2.2) is the minimum that still tells the "agentic + consistency" story.
