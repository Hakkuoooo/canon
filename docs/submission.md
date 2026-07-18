# Canon — Devpost submission

**Track:** AI Showrunner
**Tagline:** An autonomous AI showrunner that turns one premise into a serialized micro-drama, and keeps the same characters consistent across episodes.
**Repo:** https://github.com/Hakkuoooo/canon

---

## Inspiration
China's micro-drama industry is worth over ten billion dollars and it's the first mass commercial use of AI-generated video, with hundreds of AI dramas shipping every day. The models are good enough now that anyone can get a watchable clip from one prompt. The problem is the second clip, and the second episode: the characters change. The lead's jacket shifts colour, her face isn't quite her face, the world drifts. For a format built on serialized stories, that kills it. So we didn't try to render prettier frames. We picked the problem nobody had solved, consistency, and built an agent that does the whole showrunner job around it.

## What it does
Give Canon a one-line premise and pick a length. The agents take it from there:

- The **Writer** (Qwen) drafts the script: locked locations, a cast with head-to-toe specs, shots that chain cause to effect.
- The **Showrunner** (Qwen) reviews the draft against your premise and fixes broken continuity before a single frame is paid for.
- The **Story Bible** locks each character's look and seed, and each location's spec, and saves it all.
- The **Cinematographer** (Qwen) picks the framing for every shot.
- The **Generator** (Wan) renders each shot and performs its dialogue; when the critic flags drift, it fixes the prompt and re-rolls.
- The **QC Critic** (Qwen-VL) checks every shot against the Bible and catches the drift.
- The **Editor** (Qwen) names the episode, opens it on a generated title card, burns each line as a caption, and stitches it with ffmpeg.

Then ask for episode two. Canon loads the same locked cast and the same locked rooms instead of inventing new ones. Same characters, same places, next chapter. The critic loop takes generative video's biggest weakness, drift, and makes it something the system catches and repairs on its own.

## How we built it
- **Qwen Cloud models:** qwen-plus for the writing agents, qwen3-vl-plus for the visual check, wan2.5 for stills and wan2.6 for image-to-video with generated audio, all through the International (Singapore) endpoint.
- **One boundary for every model call.** A `Providers` interface with two implementations: the real DashScope client and an offline ffmpeg one. A factory picks the real client when a key is present, so the whole pipeline runs and tests without spending a credit. The suite was written red to green before we even had a cloud key.
- **Consistency without fine-tuning:** a locked descriptor, a fixed seed, and a reference image per character, plus a locked visual spec per location, checked by the Qwen-VL critic with a capped regeneration loop. No LoRA, no training pipeline.
- **Security:** character names from the model are slugged before they touch the filesystem, shot files are named by index instead of model output, the API validates every series id, ffmpeg is always called with an argument list and never a shell string, dialogue becomes pixels (Pillow) rather than command input, and downloaded assets are https-only and size-capped.
- **Stack:** Python and FastAPI, React and Tailwind, ffmpeg for assembly, deployed on Alibaba Cloud Simple Application Server.

## The problem it solves
Short-drama studios already ship AI content at industrial volume, and consistency is the one thing they can't buy. Canon is built as a production tool for them: a per-seat studio for shops making serialized verticals, or a consistency API their existing pipelines call. The engine is model-agnostic behind the Providers interface and open source under MIT, so community adoption is a real route too. The defensible part is deliberately small: a persistent record that makes a series feel like a series.

## Challenges we ran into
- Keeping characters consistent without fine-tuning. That constraint is where the Bible and the critic loop came from.
- Making the episode tell the user's story, not just render pretty frames. That took locked locations, a Showrunner review pass, a continuity rule (every shot carries an object or state from the previous one), and dialogue burned into the frame.
- Cloud setup ate real time. The SDK quietly defaults to the China endpoint and rejects an International key with a 401, and the model names shown in the console aren't the ids you actually call.
- Cost. The free tier covers text and vision, but image and video generation bill per image and per second. So generation sits behind the provider boundary and shot counts are capped.

## Accomplishments that we're proud of
Test-driven from the first commit, a critic loop that corrects its own output, and cross-episode consistency of both cast and places with no training infrastructure. The agents aren't a diagram on a slide; you watch them hand off to each other live while an episode renders.

## What we learned
Don't fight the models where they're weakest. AI video struggles most with photoreal faces, which is exactly where consistency is hardest, so Canon leans into a stylized look on purpose. Choosing the aesthetic that hides the failure mode isn't a compromise. It is the design.

## What's next for Canon
Reference-image conditioning to tighten consistency further, a job queue so long episodes don't block a request, and real voice acting.

## Built with
Python, Qwen Cloud (qwen-plus, qwen3-vl-plus, Wan 2.5/2.6), FastAPI, React, Tailwind CSS, lucide-react, Pillow, ffmpeg, Alibaba Cloud Simple Application Server, pytest.
