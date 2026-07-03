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
        return _write_placeholder(out_path, b"fake-mp4")

    def vl_check(self, image_path: str, expectation: str) -> dict:
        self.calls["vl_check"] += 1
        return self.vl_results.pop(0) if self.vl_results else {"ok": True, "reason": "ok"}

    def tts(self, text: str, out_path: str) -> str:
        self.calls["tts"] += 1
        return _write_placeholder(out_path, b"fake-wav")
