import os
import subprocess

from canon.agents import parse_script
from canon.local_media import LocalMediaProviders


def test_local_media_generates_real_playable_media(tmp_path):
    p = LocalMediaProviders()
    img = p.gen_image("a girl in red", 1, None, str(tmp_path / "a.png"))
    clip = p.img2video(img, "pan", str(tmp_path / "a.mp4"))
    wav = p.tts("hello", str(tmp_path / "a.wav"))
    dur = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", clip],
        capture_output=True, text=True,
    ).stdout.strip()
    assert float(dur) > 1.0  # a real, probeable video
    assert os.path.exists(img) and os.path.exists(wav)


def test_local_media_chat_returns_parseable_script():
    script, chars = parse_script(LocalMediaProviders().chat("s", "u"), "p")
    assert chars and script.shots  # the offline stub script parses through the real pipeline
