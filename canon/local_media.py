"""Offline provider that makes real (tiny) placeholder media with ffmpeg, so the whole pipeline runs
end-to-end with no API key and no credits. Used for local dev, tests, and a fallback demo. There is
no LLM offline, so chat() returns a fixed minimal script; prefer DashScopeProviders when a key exists."""
import os
import subprocess

from canon.providers import Providers

_OFFLINE_SCRIPT = (
    '{"style": "flat 2D anime", '
    '"characters": [{"name": "Mara", "descriptor": "crimson field jacket, cropped black hair", "seed": 40719}], '
    '"shots": [{"character": "Mara", "setting": "a vault", "action": "forces the lock", "dialogue": "It still opens."}]}'
)


def _ff(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", *args], check=True, capture_output=True)


class LocalMediaProviders(Providers):
    def chat(self, system, user):
        return _OFFLINE_SCRIPT  # no LLM offline; returns a parseable minimal script

    def gen_image(self, prompt, seed, ref_image, out_path):
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        _ff(["-f", "lavfi", "-i", "color=c=gray:s=512x288", "-frames:v", "1", "-y", out_path])
        return out_path

    def img2video(self, image_path, motion, out_path):
        _ff(["-loop", "1", "-i", image_path, "-t", "2", "-r", "24", "-pix_fmt", "yuv420p", "-y", out_path])
        return out_path

    def vl_check(self, image_path, expectation):
        return {"ok": True, "reason": "offline stub: accepted"}

    def tts(self, text, out_path):
        _ff(["-f", "lavfi", "-i", "sine=frequency=220:duration=2", "-y", out_path])
        return out_path
