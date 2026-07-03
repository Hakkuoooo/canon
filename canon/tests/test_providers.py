import os

import pytest

from canon.providers import Providers, FakeProviders


def test_providers_interface_is_abstract():
    with pytest.raises(TypeError):
        Providers()


def test_incomplete_provider_cannot_instantiate():
    class Partial(Providers):
        def chat(self, system, user):
            return ""

    with pytest.raises(TypeError):
        Partial()  # missing gen_image/img2video/vl_check/tts -> contract enforced


def test_fake_providers_write_assets_and_count(tmp_path):
    p = FakeProviders()
    img = p.gen_image("a girl in red", 42, None, str(tmp_path / "shot0.png"))
    clip = p.img2video(img, "pan", str(tmp_path / "shot0.mp4"))
    wav = p.tts("hello", str(tmp_path / "line0.wav"))
    assert os.path.exists(img) and os.path.exists(clip) and os.path.exists(wav)
    assert p.calls["gen_image"] == 1 and p.calls["img2video"] == 1 and p.calls["tts"] == 1


def test_fake_chat_returns_injected_reply():
    p = FakeProviders(chat_reply='{"scenes": []}')
    assert p.chat("system", "user") == '{"scenes": []}'
    assert p.calls["chat"] == 1


def test_fake_vl_check_scripts_then_defaults_pass():
    p = FakeProviders(vl_results=[{"ok": False, "reason": "drift"}])
    assert p.vl_check("img", "expect")["ok"] is False  # scripted verdict
    assert p.vl_check("img", "expect")["ok"] is True  # default after the list exhausts
    assert p.calls["vl_check"] == 2


def test_fake_gen_image_creates_missing_parent_dir(tmp_path):
    p = FakeProviders()
    nested = str(tmp_path / "deep" / "nested" / "shot.png")
    p.gen_image("x", 1, None, nested)
    assert os.path.exists(nested)
