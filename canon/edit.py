"""ffmpeg primitives for assembling an episode. Every call goes through _run, which passes an
argument LIST (never shell=True), so untrusted dialogue/subtitle text cannot inject a command.
Subtitle text is written into an .srt data file and rendered by libass, never placed on the
command line. render_episode composes these with real clip durations + TTS later."""
import os
import subprocess


def _run(cmd, cwd=None):
    """Run an ffmpeg/ffprobe argument list (no shell). Raise a clear RuntimeError on failure."""
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed (exit {proc.returncode}): {proc.stderr.strip()[-500:]}")
    return proc


def _concat_line(path):
    # concat-demuxer syntax is `file '<path>'`; escape single quotes to keep the list well-formed.
    safe = os.path.abspath(path).replace("'", "'\\''")
    return f"file '{safe}'\n"


def concat(clip_paths, out_path):
    """Stitch clips into one file (stream copy, no re-encode)."""
    if not clip_paths:
        raise ValueError("no clips to concat")
    work = os.path.dirname(os.path.abspath(out_path))
    listfile = os.path.join(work, "_concat.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        f.writelines(_concat_line(c) for c in clip_paths)
    try:
        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile, "-c", "copy", out_path])
    finally:
        os.remove(listfile)
    return out_path


def _fmt_ts(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(entries, srt_path):
    """entries: list of (start_seconds, end_seconds, text). Text is data, never shell input."""
    blocks = [
        f"{i}\n{_fmt_ts(a)} --> {_fmt_ts(b)}\n{text}\n" for i, (a, b, text) in enumerate(entries, 1)
    ]
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocks))
    return srt_path


def add_subtitles(video, srt_path, out_path):
    """Embed subtitles as a soft mov_text track. Works without libass (this ffmpeg lacks it).
    The text lives in the .srt data file, never on the command line.
    ponytail: burned-in (always-visible) subtitles need a libass-enabled ffmpeg; do that on the
    deploy/render box by swapping to -vf subtitles=, not on this dev machine."""
    _run(
        ["ffmpeg", "-y", "-i", os.path.abspath(video), "-i", os.path.abspath(srt_path),
         "-map", "0", "-map", "1", "-c", "copy", "-c:s", "mov_text", os.path.abspath(out_path)]
    )
    return out_path


def mux_audio(video, audio_path, out_path):
    """Overlay an audio track on the video, trimming to the shorter stream."""
    _run(
        ["ffmpeg", "-y", "-i", os.path.abspath(video), "-i", os.path.abspath(audio_path),
         "-c:v", "copy", "-c:a", "aac", "-shortest", os.path.abspath(out_path)]
    )
    return out_path
