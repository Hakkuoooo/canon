# Canon — Devpost submission

**Track:** AI Showrunner
**Tagline:** An autonomous AI showrunner that turns one premise into a serialized micro-drama, and keeps the same characters consistent across episodes.
**Repo:** https://github.com/Hakkuoooo/canon

---

## Inspiration
AI short-drama is one of the fastest-moving markets in the world. China's micro-drama industry is worth well over ten billion dollars and is the first mass commercial use of AI-generated video, with hundreds of AI dramas produced per day. The models can now generate a watchable clip from a single prompt. The problem is the second clip, and the second episode: the characters change. The lead's jacket shifts colour, her face is not quite her face, the world drifts. For a format built on serialized storytelling, that inconsistency is fatal. We did not try to render prettier frames. We picked the unsolved problem, consistency, and built an agent that does the whole showrunner job around it.

## What it does
You give Canon a one-line premise and pick a length. A society of five agents produces a short episode end to end:
1. **Writer** (Qwen) drafts the script and casts the characters.
2. **Showrunner / Story Bible** locks each character's look and a fixed generation seed, and persists it.
3. **Cinematographer** (Qwen) sets the camera framing for each shot.
4. **Generator** renders each shot, and when the critic flags drift it revises the prompt and re-rolls.
5. **QC Critic** (Qwen-VL) checks every shot against the Bible and catches inconsistencies.
6. **Editor** (Qwen) names the episode and the pipeline stitches it with ffmpeg.

The point is the **Story Bible**: generate episode one, then episode two, and it reuses the same locked cast instead of inventing a new one. Same character, next episode. The QC critic turns generative video's one weakness, drift, into something the system visibly catches and fixes.

## How we built it
- **Qwen Cloud models:** Qwen for writing and orchestration, Qwen-VL for the visual consistency check, and Wan for image and image-to-video generation, all through the International endpoint.
- **One boundary for every model call.** A `Providers` interface with two implementations: the real DashScope client, and an offline ffmpeg-backed one. A factory picks the real one when a key is present. Because of this, the entire pipeline is testable without spending a credit, so we built it test-first: 57 tests, red to green, before the cloud key existed.
- **Consistency without fine-tuning:** a locked text descriptor plus a fixed seed plus a reference image per character, verified by the Qwen-VL critic with a capped regeneration loop. No LoRA, no training pipeline.
- **Stack:** Python, FastAPI backend, React + Tailwind frontend, ffmpeg for assembly, deployed on Alibaba Cloud Simple Application Server.
- **Security taken seriously:** model-supplied names are slugged before touching the filesystem, shot files key off integer indexes, the API validates the series id, every ffmpeg call is an argument list (never a shell string), and downloaded assets are https-only and size-capped.

## The problem value and where it goes
Canon is not a toy that makes cute clips, it is a production tool for an industry that ships AI dramas at industrial scale and is desperate for consistency and lower cost. The commercial path is direct: a per-seat studio for content shops producing serialized verticals, or a consistency API that existing short-drama pipelines call. The engine is model-agnostic behind the `Providers` interface, and the whole thing is open source (MIT), so community adoption is a viable route too. The wedge, a small persistent record that makes a series feel like a series, is the defensible part.

## Challenges we ran into
- Making characters consistent without fine-tuning, which is why the Bible plus QC-loop approach exists.
- Cloud setup: the SDK defaults to the China endpoint and rejects an International key with a 401, and the console display names are not the callable model ids. Both cost real debugging time.
- Cost discipline: the free tier covers the text and vision agents, but image and video generation are billed per image and per second, so we isolate generation behind the provider boundary and cap shot counts.

## Accomplishments we're proud of
A genuinely test-driven, five-agent system where the multi-agent architecture is legible in the UI, a self-correcting critic loop, and cross-episode consistency achieved with no training infrastructure.

## What we learned
Do not fight the models where they are weakest. AI video is worst at photoreal faces, exactly where consistency is hardest, so Canon uses a stylized aesthetic on purpose. Picking the look that hides the failure mode is not a compromise, it is the design.

## What's next
Reference-image conditioning for even tighter consistency, an async job queue so long episodes render at scale, and voice.

## Built with
Python, Qwen Cloud (Qwen, Qwen-VL, Wan), FastAPI, React, Tailwind CSS, lucide-react, ffmpeg, Alibaba Cloud Simple Application Server, pytest.
