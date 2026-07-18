# Canon

**An autonomous AI showrunner that turns one premise into a serialized micro-drama, and keeps the same characters consistent across episodes.**

Built for the Global AI Hackathon Series with Qwen Cloud — **AI Showrunner** track.

Most "AI video" tools generate a single disconnected clip. Canon runs the actual showrunner job end to end (script → review → cast → shot list → generation → self-correcting QC → edit), and the user's typed premise is the contract: the episode on screen tells that story. Its wedge is **persistent canon**: a Story Bible locks each character's look and seed *and each location's visual spec*, so episode 2 has the same faces in the same rooms as episode 1.

## How it works

Cooperating agents share one persistent state object (the Story Bible):

1. **Writer** (Qwen) — premise → structured script: locked locations, cast with head-to-toe descriptors, and shots that chain cause-to-effect with a spoken line each.
2. **Showrunner** (Qwen) — reviews the draft against the user's premise and repairs broken continuity, vanishing props, and non-advancing dialogue before any pixel is paid for.
3. **Story Bible** — persists every character's locked descriptor + seed + reference image and every location's locked spec. Later episodes load it unchanged; this is the consistency mechanism.
4. **Cinematographer** (Qwen) — one camera direction per shot.
5. **Generator** (Wan) — renders each shot's still (locked character + locked place + action), then animates it; dialogue rides into the video model so characters perform their lines.
6. **QC Critic** (Qwen-VL) — checks every frame against the Bible and re-rolls drift (capped).
7. **Editor** (Qwen + ffmpeg) — titles the episode, opens it on a generated title card, burns each line as a caption, stitches the cut.

The UI shows honest progress while an episode renders (the engine reports every stage live), and a series survives page reloads via its `?series=` URL.

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

- **Model Studio (DashScope, International/Singapore endpoint)** — verified callable models: `qwen-plus` (writing, review, framing, titles), `qwen3-vl-plus` (visual consistency check), `wan2.5-t2i-preview` (stills), `wan2.6-i2v-flash` (image-to-video with generated audio). All ids overridable via `CANON_*` env vars.
- **Simple Application Server** — hosts the deployed API. See [canon/deploy/ecs-setup.md](canon/deploy/ecs-setup.md).
- Episode assets live on a per-series filesystem workspace (`canon/data/series/<id>/`); no database.

## Layout

```
canon/        engine: schemas, bible, providers, agents, pipeline, edit, api
canon/tests/  the test suite (TDD throughout)
web/          Vite + React + Tailwind studio UI (lucide-react)
```

## License

MIT — see [LICENSE](LICENSE).
