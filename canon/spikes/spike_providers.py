"""Day-1 spike: confirm each real DashScope call works, then correct any model id via env.

    DASHSCOPE_API_KEY=...  python -m canon.spikes.spike_providers

Prints PASS/FAIL per capability. The reference-image question on gen_image is the make-or-break one
for the consistency wedge. Fix model ids without editing code via CANON_CHAT_MODEL / CANON_IMAGE_MODEL /
CANON_VIDEO_MODEL / CANON_VL_MODEL / CANON_TTS_MODEL."""
import os
import tempfile


def main():
    if not os.environ.get("DASHSCOPE_API_KEY"):
        raise SystemExit("set DASHSCOPE_API_KEY first (and `pip install dashscope`)")

    from canon.providers import DashScopeProviders

    p = DashScopeProviders()
    d = tempfile.mkdtemp()
    img = os.path.join(d, "ref.png")

    def check(name, fn):
        try:
            print(f"PASS  {name}: {fn()}")
        except Exception as e:  # noqa: BLE001 - spike wants every failure surfaced, not raised
            print(f"FAIL  {name}: {type(e).__name__}: {e}")

    check("chat (Qwen)", lambda: p.chat("Reply with one word.", "Say ok")[:40])
    check("gen_image (text->image + seed)", lambda: p.gen_image("flat 2D anime, a girl in a red jacket", 42, None, img))
    check("vl_check (Qwen-VL)", lambda: p.vl_check(img, "a girl in a red jacket"))
    check("img2video", lambda: p.img2video(img, "slow pan", os.path.join(d, "clip.mp4")))
    check("tts", lambda: p.tts("It still opens.", os.path.join(d, "line.wav")))

    print("\nKEY QUESTION: does gen_image accept a reference image + seed for character consistency?")
    print("If not, the wedge leans on locked-prompt + seed + the QC loop instead of reference conditioning.")


if __name__ == "__main__":
    main()
