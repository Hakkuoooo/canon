# Canon — demo video script (target 2:45, hard cap 3:00)

Voiceover: Satendra. Screen: Chrome at desktop width, Dark Reader off, studio at localhost:5173.
Record in chunks, stitch in iMovie/CapCut. Speak plainly, no rush; ~2.5 words a second is right.

## What to capture, when
- **Chunk A (during ep1 generation):** QuickTime rolling before you click Generate. Keep the whole run; we only use ~35s of it (the click, the Writer stage, a couple of shot stages, and the "drift caught, re-rolling" moment if it fires).
- **Chunk B (during ep2 generation):** same, mainly the click and the first seconds.
- **Chunk C (after both exist):** calm browsing take: play episode 1, switch to Ep 02, play it, scroll the Character Bible cards.
- **Stills:** the two loose-descriptor probe images (the drifted jacket pair) for the cold open; one frame of the architecture PDF for the close.

## The cut

| Time | On screen | Voiceover (exact words) |
|---|---|---|
| 0:00–0:15 | The two probe stills side by side: same prompt, same seed, different jacket. | "AI video has one unsolved problem. It can generate a clip, but it can't keep a character. Same character, same seed, and the jacket still changes between scenes. For serialized drama, that kills the show." |
| 0:15–0:30 | Studio, still. Premise typed, style and length picked. The click. (Chunk A) | "This is Canon. You give it a premise, pick a style and a length, and it runs the whole showrunner job itself." |
| 0:30–1:05 | Agents panel narrating live: Writer, reference portraits, Shot 3 of 6 · animating motion. (Chunk A) | "Five agents work the episode. The Writer casts the characters and locks each one into a Story Bible: a fixed description, a fixed seed, a reference image. Wan renders every shot, and a Qwen vision critic checks each frame against that Bible. This panel is not an animation, it's the engine reporting each step as it happens." |
| — (only if captured) | The "drift caught, re-rolling" state. | "There. It caught a shot drifting, rewrote the prompt, and re-rolled it. Nobody touched anything." |
| 1:05–1:40 | Episode 1 plays in the screening room. (Chunk C) | "Episode one, end to end, from that one line." Then let it play clean. |
| 1:40–2:10 | The Ep 2 click (Chunk B), then Ep 02 playing; pause side by side on the lead if possible. | "Now the part that matters. Ask for episode two and Canon doesn't cast again. It loads the same Bible. Same face, same jacket, next chapter. That's the thing generative video keeps getting wrong." |
| 2:10–2:30 | Character Bible cards: descriptors and locked seeds. (Chunk C) | "The whole trick is small on purpose: a persistent record of the cast, plus a critic that checks every frame. No fine-tuning, no LoRA, nothing to train." |
| 2:30–2:45 | Architecture PDF frame, then the SAS health URL and the repo. | "Built on Qwen, Qwen-VL, and Wan, deployed on Alibaba Cloud, open source under MIT. Canon: the showrunner that keeps its cast." |

## One-take fallback (if editing is a pain)
With both episodes already generated: one continuous recording. Studio → speak the intro over the idle panel → play Ep 01 → switch to Ep 02 → Bible cards → done. You lose the live-generation beat; keep the voiceover lines the same minus the panel section. Under 2 minutes, still lands the reveal.

## Do / don't
- Do end on the ep2 reveal held for a few quiet seconds; it is the pitch.
- Do record voice in one quiet room pass; re-record a sentence rather than living with a stumble.
- Don't show the terminal, .env, or billing pages.
- Don't claim voice/audio in episodes; they are silent by design in this build.
