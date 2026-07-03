# Canon

**An autonomous AI showrunner that turns one premise into a serialized micro-drama, and keeps the same characters consistent across episodes.**

Built for the Global AI Hackathon Series with Qwen Cloud — **AI Showrunner** track.

Most "AI video" tools generate a single disconnected clip. Canon runs the actual showrunner job end to end (script → cast → shot list → generation → self-correcting QC → edit) and its wedge is **cross-episode character consistency**: a persistent Story Bible locks each character's look and seed, and a Qwen-VL critic re-rolls any shot that drifts. Generate episode 1, then episode 2, and the character is the same person.

## How it works

Four cooperating agents share one persistent state object (the Story Bible):

1. **Writer** (Qwen) — premise → structured script + cast.
2. **Story Bible** — persists each character's locked descriptor + seed + reference image. Episode 2+ reuses it unchanged; this is the consistency mechanism.
3. **Cinematographer / Generator** — assembles each shot's prompt from the Bible, generates a keyframe and motion.
4. **QC Critic** (Qwen-VL) — checks each shot against the Bible and regenerates on drift (capped).
5. **Editor** (ffmpeg) — stitches shots, adds voice and subtitles.

See [canon/architecture.md](canon/architecture.md) for diagrams, the data model, the key trade-off, and failure modes.

## Run it

**Offline (no cloud, no key)** — a local ffmpeg-backed provider generates placeholder media so the whole app runs end to end:

```bash
# backend
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn canon.api:app --port 8000      # run from the repo root

# frontend (new terminal)
npm --prefix web install && npm --prefix web run dev   # open http://localhost:5173
```

**With Qwen Cloud** — set the key and the provider factory switches to the real models:

```bash
export DASHSCOPE_API_KEY=...        # from Model Studio (International region)
# then run the backend as above
```

Confirm the models before a full run:

```bash
DASHSCOPE_API_KEY=... .venv/bin/python -m canon.spikes.spike_providers
```

## Tests

```bash
.venv/bin/python -m pytest canon/tests -q
```

## Alibaba Cloud services

- **Model Studio (DashScope)** — Qwen (script/orchestration), Qwen-VL (QC), Wan / HappyHorse (video), CosyVoice (TTS).
- **ECS** — hosts the API + built frontend. See [canon/deploy/ecs-setup.md](canon/deploy/ecs-setup.md).
- **OSS** — stores generated episode assets.

## Layout

```
canon/        engine: schemas, bible, providers, agents, pipeline, edit, api
canon/tests/  the test suite (TDD throughout)
web/          Vite + React + Tailwind studio UI (lucide-react)
```

## License

MIT — see [LICENSE](LICENSE).
