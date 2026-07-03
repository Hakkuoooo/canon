# Canon — Architecture

## System

```mermaid
flowchart TD
  U[User] --> UI[React Studio UI - web/]
  UI -->|POST premise| API[FastAPI - canon/api.py]
  API --> ORCH[Orchestrator - render_episode]
  ORCH --> W[Writer - Qwen]
  ORCH --> QC[QC Critic - Qwen-VL]
  ORCH <--> BIB[(Story Bible - bible.json)]
  W --> PROV[Providers factory]
  QC --> PROV
  ORCH --> ED[Editor - ffmpeg]
  PROV -->|key set| DS[[Alibaba Model Studio: Qwen / Wan / HappyHorse / CosyVoice]]
  PROV -->|no key| LOC[LocalMediaProviders - offline]
  ED --> OSS[(OSS / local files - episode mp4)]
  API --> OSS
```

Every external model call sits behind the `Providers` interface. `get_providers()` returns `DashScopeProviders` when `DASHSCOPE_API_KEY` is set, otherwise `LocalMediaProviders`, so the whole system runs and is fully tested offline with zero credits.

## Data flow (one episode)

```mermaid
sequenceDiagram
  actor U as User
  participant UI as React
  participant API as FastAPI
  participant O as Orchestrator
  participant W as Writer
  participant B as Bible
  participant G as Generator
  participant Q as QC (Qwen-VL)
  participant E as Editor
  U->>UI: premise + style
  UI->>API: POST /api/series/{id}/episodes
  API->>O: render_episode
  O->>W: write_script (ep2+: reuse existing cast)
  W-->>O: script + characters
  O->>B: ep1 seeds the bible / ep2 loads it
  O->>B: establish one reference image per character
  loop each shot
    O->>G: gen_image(prompt from bible, seed, ref)
    O->>Q: vl_check
    alt drift
      O->>G: regenerate (<= MAX_REGEN)
    end
    O->>G: img2video
  end
  O->>E: stitch (+ voice, subtitles)
  E-->>API: episodeN.mp4
  API-->>UI: video_url + cast
```

## Data model

No relational DB. The datastore is a per-series directory:

```
canon/data/series/<id>/
  bible.json          {style, characters:{name:{descriptor, seed, ref_image}}}
  refs/<slug>_<seed>.png    canonical character reference (locks the look)
  work_ep<n>/         intermediate shot pngs + mp4s
  episode<n>.mp4      the finished episode
```

`bible.json` is the single source of truth. Episode 2's consistency = it loads this file instead of rewriting it.

## The critical trade-off: consistency

| | **A: descriptor + reference + fixed seed + QC loop** (chosen) | **B: per-character LoRA / fine-tune** |
|---|---|---|
| Consistency | good, occasional drift | excellent |
| Build time | hours | days |
| Infra | none beyond API | GPU training pipeline |
| Iteration | edit a string | retrain |
| Fits the timeline | yes | no |

**A.** It reaches most of B's consistency for a fraction of the effort, keeps a live knob, and turns residual drift into an on-camera feature: the QC critic catching and fixing itself.

## Security boundaries

- **Path traversal:** model-supplied character names are slugged before becoming filenames; shot files key off the integer shot index; the API validates `series_id` against `^[a-z0-9-]{1,40}$` before any filesystem use.
- **Subprocess:** every ffmpeg call is an argument list (never `shell=True`); subtitle/dialogue text lives in an `.srt` data file, never on the command line.
- **Downloads:** model-returned asset URLs are fetched https-only and size-capped.
- **Secrets:** the API key is read from the environment, never committed (`.env` is gitignored).

## Top failure modes

1. **Model API / credits** — backoff, cache shots by `hash(prompt, seed)`, cap regen, pre-generate demo assets, fallback model id via env.
2. **Consistency miss** — the QC loop, a human review gate before recording, stylized aesthetic, seed + reference locking.
3. **Demo-day environment** — the demo is pre-recorded, assets on OSS, the app is stateless and redeployable.
