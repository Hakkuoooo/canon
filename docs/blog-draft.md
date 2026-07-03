# Building a consistency-first AI showrunner on Qwen Cloud

*By Satendra Mani Tiwari*

AI short-drama is one of the fastest-moving markets in the world right now. China's micro-drama
industry is worth well over ten billion dollars and has become the first mass commercial use of
AI-generated video. The models got good enough that a single prompt returns a watchable clip. The
problem is what happens on the second clip, and the second episode: the characters change. The
lead's jacket shifts colour, her face is not quite her face, the world drifts. For a format that
lives on serialized storytelling, that is fatal.

So when I built for the Global AI Hackathon Series with Qwen Cloud, I did not try to make prettier
pixels. A two-person team is not going to out-render studios. I picked a different axis to win on:
**consistency**, and an agent that does the whole showrunner job end to end. The project is called
Canon.

## The idea

You give Canon a one-line premise. A society of agents turns it into a short episode: a Writer
drafts the script and cast, a Cinematographer breaks it into shots, a Generator renders them, and a
QC Critic checks every shot before it ships. The part that matters is the **Story Bible**: a small
persistent record that locks each character's description and generation seed the first time they
appear. Every later shot, and every later episode, is built from that same locked record. Generate
episode one, then episode two, and it is the same character, because episode two loads the Bible
instead of inventing a new cast.

The self-correction is the second half. A Qwen-VL critic looks at each generated shot and compares
it against the Bible. If the character has drifted, it regenerates that shot, capped so it cannot
loop forever. That turns the one weakness of generative video, drift, into something the system
visibly catches and fixes.

## How it is built

The whole engine sits behind one boundary: a `Providers` interface with five methods (chat, image,
image-to-video, vision-check, speech). There are two implementations. `DashScopeProviders` calls the
real Qwen Cloud models. `LocalMediaProviders` makes tiny real placeholder clips with ffmpeg. A
factory picks the real one when an API key is present and the offline one otherwise.

That single design decision paid for itself repeatedly. The entire pipeline is testable without
spending a credit, so I built it test-first: forty-plus tests, red to green, before the cloud key
ever existed. It also means the app runs end to end on a laptop with no account, which is a useful
fallback when you are one flaky login away from a deadline.

I was strict about the unglamorous parts. Model output is untrusted, so the script parser tolerates
prose and fenced JSON and caps runaway output. Character names come from the model and end up as
filenames, so they are slugged and shot files key off an integer index, which closes a path
traversal. Every ffmpeg call is an argument list, never a shell string, and subtitle text lives in a
data file, so a line of dialogue cannot become a command. None of this is exciting. All of it is the
difference between a demo and a thing you can deploy.

## On Qwen Cloud

Canon uses Qwen for the writing and orchestration, Qwen-VL for the consistency check, Wan and
HappyHorse for the video, and CosyVoice for narration, all through Alibaba Cloud Model Studio, and
deploys on ECS with OSS holding the finished episodes. Building the whole thing on one native stack
kept the moving parts down, which matters when the interesting risk is the model behaviour, not the
plumbing.

## What I would tell the next person

Two honest notes. First, the region and account setup on Alibaba Cloud is the real long pole, not
the code. Get the key early. Second, do not fight the models where they are weakest. AI video is
worst at photoreal faces, which is exactly where consistency is hardest, so Canon uses a stylized
look on purpose. Picking the aesthetic that hides the failure mode is not a compromise, it is the
design.

The wedge here was never the generator. It was the small persistent record that makes a series feel
like a series, and an agent honest enough to check its own work. That is the part I would build
again.

---

*Canon is open source (MIT). Built on Qwen Cloud for the AI Showrunner track.*
