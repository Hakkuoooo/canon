import os
import subprocess

import pytest

from canon.edit import concat, write_srt, add_subtitles, mux_audio, _run


def _clip(path, dur=1):
    subprocess.run(
        ["ffmpeg", "-f", "lavfi", "-i", f"color=c=black:s=64x64:d={dur}", "-y", path],
        check=True, capture_output=True,
    )


def _wav(path, dur=1):
    subprocess.run(
        ["ffmpeg", "-f", "lavfi", "-i", f"sine=frequency=440:duration={dur}", "-y", path],
        check=True, capture_output=True,
    )


def _duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True,
    ).stdout
    return float(out)


def _has_stream(path, kind):  # kind: "video" or "audio"
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", kind[0], "-show_entries", "stream=codec_type",
         "-of", "csv=p=0", path],
        capture_output=True, text=True,
    ).stdout
    return kind in out


def test_concat_joins_clips(tmp_path):
    clips = [str(tmp_path / f"{i}.mp4") for i in range(2)]
    for c in clips:
        _clip(c, 1)
    out = str(tmp_path / "ep.mp4")
    concat(clips, out)
    assert os.path.exists(out) and _duration(out) > 1.5  # ~2s of joined clips


def test_concat_empty_raises(tmp_path):
    with pytest.raises(ValueError):
        concat([], str(tmp_path / "x.mp4"))


def test_write_srt_format(tmp_path):
    srt = write_srt([(0.0, 1.5, "hello"), (1.5, 3.0, "world")], str(tmp_path / "s.srt"))
    content = open(srt, encoding="utf-8").read()
    assert content.startswith("1\n")
    assert "00:00:00,000 --> 00:00:01,500" in content
    assert "hello" in content and "world" in content


def test_add_subtitles_embeds_subtitle_stream(tmp_path):
    clip = str(tmp_path / "c.mp4")
    _clip(clip, 1)
    srt = write_srt([(0.0, 1.0, "line one")], str(tmp_path / "subs.srt"))
    out = str(tmp_path / "subbed.mp4")
    add_subtitles(clip, srt, out)
    assert os.path.exists(out) and _has_stream(out, "subtitle")


def test_mux_audio_adds_audio_stream(tmp_path):
    clip = str(tmp_path / "c.mp4")
    _clip(clip, 1)
    wav = str(tmp_path / "a.wav")
    _wav(wav, 1)
    out = str(tmp_path / "withaudio.mp4")
    mux_audio(clip, wav, out)
    assert os.path.exists(out) and _has_stream(out, "audio")


def test_run_raises_clear_error_on_bad_command(tmp_path):
    with pytest.raises(RuntimeError):
        _run(["ffmpeg", "-i", str(tmp_path / "nonexistent.mp4"), str(tmp_path / "o.mp4")])


def test_malicious_subtitle_text_is_data_not_command(tmp_path):
    # A shell-metacharacter-laden subtitle must render as text, never execute a command.
    clip = str(tmp_path / "c.mp4")
    _clip(clip, 1)
    canary = tmp_path / "pwned"
    evil = f"'; touch {canary}; echo '"
    srt = write_srt([(0.0, 1.0, evil)], str(tmp_path / "subs.srt"))
    out = str(tmp_path / "o.mp4")
    add_subtitles(clip, srt, out)
    assert os.path.exists(out)
    assert not canary.exists()  # no shell execution: text stayed data
