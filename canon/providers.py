"""Every external model call (Qwen chat, Wan image/video, Qwen-VL check, TTS) lives behind this
one interface. FakeProviders lets the whole pipeline run and be tested with zero API credits.
DashScopeProviders (the real calls) is filled in from the Task 0.2 spike."""
import os
from abc import ABC, abstractmethod
from typing import Optional


class Providers(ABC):
    @abstractmethod
    def chat(self, system: str, user: str) -> str: ...

    @abstractmethod
    def gen_image(self, prompt: str, seed: int, ref_image: Optional[str], out_path: str) -> str: ...

    @abstractmethod
    def img2video(self, image_path: str, motion: str, out_path: str) -> str: ...

    @abstractmethod
    def vl_check(self, image_path: str, expectation: str) -> dict: ...

    @abstractmethod
    def tts(self, text: str, out_path: str) -> str: ...


def _write_placeholder(out_path: str, data: bytes) -> str:
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path


class FakeProviders(Providers):
    """Deterministic test double. `vl_results` scripts vl_check outcomes (a list of verdicts
    returned in order, then a passing default). `calls` counts invocations for assertions."""

    def __init__(self, chat_reply: str = '{"ok": true}', vl_results=None):
        self.chat_reply = chat_reply
        self.vl_results = list(vl_results or [])
        self.calls = {"chat": 0, "gen_image": 0, "img2video": 0, "vl_check": 0, "tts": 0}

    def chat(self, system: str, user: str) -> str:
        self.calls["chat"] += 1
        return self.chat_reply

    def gen_image(self, prompt: str, seed: int, ref_image: Optional[str], out_path: str) -> str:
        self.calls["gen_image"] += 1
        return _write_placeholder(out_path, b"\x89PNG\r\n")

    def img2video(self, image_path: str, motion: str, out_path: str) -> str:
        self.calls["img2video"] += 1
        self.last_motion = motion  # tests assert dialogue reaches the video model
        return _write_placeholder(out_path, b"fake-mp4")

    def vl_check(self, image_path: str, expectation: str) -> dict:
        self.calls["vl_check"] += 1
        return self.vl_results.pop(0) if self.vl_results else {"ok": True, "reason": "ok"}

    def tts(self, text: str, out_path: str) -> str:
        self.calls["tts"] += 1
        return _write_placeholder(out_path, b"fake-wav")


def _as_uri(path: str) -> str:
    if path.startswith(("http://", "https://", "file://")):
        return path
    return "file://" + os.path.abspath(path)


def _download(url: str, out_path: str) -> str:
    """Fetch a model-generated asset to out_path, https-only and size-capped (a model response must
    not be able to make us fetch arbitrary schemes or unbounded data)."""
    import urllib.request

    from canon.config import MAX_DOWNLOAD_BYTES

    if not url.startswith("https://"):
        raise ValueError(f"refusing non-https asset url: {url[:48]}")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with urllib.request.urlopen(url, timeout=180) as resp:  # noqa: S310 (scheme checked above)
        data = resp.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise ValueError(f"asset exceeds {MAX_DOWNLOAD_BYTES} bytes")
    with open(out_path, "wb") as f:
        f.write(data)
    return out_path


class DashScopeProviders(Providers):
    """Real calls against Alibaba Model Studio (DashScope). Written from the docs; each call is marked
    SPIKE where the exact id or response shape must be confirmed once a key exists. Not exercised by
    tests (no key) — validate with canon/spikes/spike_providers.py, then correct any model id via env."""

    def __init__(self, api_key=None):
        import dashscope

        from canon import config

        self._ds = dashscope
        dashscope.api_key = api_key or config.DASHSCOPE_API_KEY
        if not dashscope.api_key:
            raise RuntimeError("DASHSCOPE_API_KEY is not set")
        dashscope.base_http_api_url = config.DASHSCOPE_BASE_URL  # International, not the China default
        dashscope.base_websocket_api_url = config.DASHSCOPE_WS_URL

    def chat(self, system: str, user: str) -> str:
        from canon import config

        r = self._ds.Generation.call(
            model=config.CHAT_MODEL,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            result_format="message",
        )
        return r["output"]["choices"][0]["message"]["content"]

    def gen_image(self, prompt, seed, ref_image, out_path):
        from canon import config

        # SPIKE: confirm the text-to-image model id and whether ref_image conditioning is supported.
        rsp = self._ds.ImageSynthesis.call(model=config.IMAGE_MODEL, prompt=prompt, n=1, seed=seed)
        return _download(rsp.output.results[0].url, out_path)

    def img2video(self, image_path, motion, out_path):
        from canon import config

        # SPIKE: assumes an image-to-video model. If only text-to-video (HappyHorse T2V) is available,
        # switch to a t2v call using the shot prompt (thread the prompt into this method).
        rsp = self._ds.VideoSynthesis.call(
            model=config.VIDEO_MODEL, img_url=_as_uri(image_path), prompt=motion
        )
        return _download(rsp.output.video_url, out_path)

    def vl_check(self, image_path, expectation):
        from canon import config

        r = self._ds.MultiModalConversation.call(
            model=config.VL_MODEL,
            messages=[{"role": "user", "content": [
                {"image": _as_uri(image_path)},
                {"text": f"Does this frame match: '{expectation}'? Reply 'yes' or 'no' and one short reason."},
            ]}],
        )
        content = r["output"]["choices"][0]["message"]["content"]
        text = content if isinstance(content, str) else " ".join(str(p.get("text", "")) for p in content)
        return {"ok": text.strip().lower().startswith("yes"), "reason": text.strip()}

    def tts(self, text, out_path):
        from canon import config
        from dashscope.audio.tts_v2 import SpeechSynthesizer

        audio = SpeechSynthesizer(model=config.TTS_MODEL, voice="loongstella").call(text)
        with open(out_path, "wb") as f:
            f.write(audio)
        return out_path


def get_providers():
    """DashScopeProviders when DASHSCOPE_API_KEY is set (real), else LocalMediaProviders (offline)."""
    from canon import config

    if config.DASHSCOPE_API_KEY:
        return DashScopeProviders()
    from canon.local_media import LocalMediaProviders

    return LocalMediaProviders()
