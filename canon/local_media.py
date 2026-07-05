"""Offline provider that makes real (tiny) placeholder media with ffmpeg, so the whole pipeline runs
end-to-end with no API key and no credits. Used for local dev, tests, and a fallback demo. There is
no LLM offline, so chat() returns a fixed cast but honors the requested shot count so episode length
still matches the user's choice. Prefer DashScopeProviders when a key exists."""
import json
import os
import re
import subprocess

from canon.providers import Providers


def _ff(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", *args], check=True, capture_output=True)


class LocalMediaProviders(Providers):
    def chat(self, system, user):
        # No LLM offline: fixed cast, but honor "Write exactly N shots" so length matches the choice.
        m = re.search(r"exactly (\d+) shots", user)
        n = max(1, int(m.group(1))) if m else 1
        shots = [
            {"character": "Mara", "setting": f"scene {i + 1}", "action": f"beat {i + 1}", "dialogue": ""}
            for i in range(n)
        ]
        return json.dumps({
            "style": "flat 2D anime",
            "characters": [
                {"name": "Mara", "descriptor": "crimson field jacket, cropped black hair", "seed": 40719}
            ],
            "shots": shots,
        })

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
