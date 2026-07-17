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
    """Stitch clips into one file. Re-encodes: clips arrive from different encoders (Wan
    downloads vs caption re-encodes), and stream-copy across mixed encoder params produces
    corrupt output. Episodes are short; the re-encode cost is irrelevant."""
    if not clip_paths:
        raise ValueError("no clips to concat")
    work = os.path.dirname(os.path.abspath(out_path))
    listfile = os.path.join(work, "_concat.txt")
    with open(listfile, "w", encoding="utf-8") as f:
        f.writelines(_concat_line(c) for c in clip_paths)
    try:
        _run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listfile,
              "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", out_path])
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


CAPTION_FONT = os.environ.get("CANON_CAPTION_FONT", "/System/Library/Fonts/Helvetica.ttc")


def _wrap(text, width=42):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    lines.append(cur)
    return "\n".join(lines[:3])


def _caption_png(text, path, design_width=1440):
    """Render the caption as a transparent PNG pill (Pillow). Text is drawn, never parsed,
    so hostile dialogue is just pixels. Sized for our 1440-wide episodes.
    ponytail: fixed design width; scale against the actual video if formats ever vary."""
    from PIL import Image, ImageDraw, ImageFont

    lines = _wrap(text).split("\n")
    size = design_width // 26
    font = ImageFont.truetype(CAPTION_FONT, size)
    pad, gap = int(size * 0.7), int(size * 0.3)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    boxes = [probe.textbbox((0, 0), ln, font=font) for ln in lines]
    line_h = max(b[3] - b[1] for b in boxes)
    box_w = max(b[2] - b[0] for b in boxes) + pad * 2
    box_h = line_h * len(lines) + gap * (len(lines) - 1) + pad * 2
    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, box_w - 1, box_h - 1], radius=size // 2, fill=(0, 0, 0, 150))
    y = pad
    for ln, b in zip(lines, boxes):
        d.text(((box_w - (b[2] - b[0])) // 2 - b[0], y - b[1]), ln, font=font, fill=(255, 255, 255, 255))
        y += line_h + gap
    img.save(path)
    return path


def burn_caption(video, text, out_path):
    """Overlay a dialogue caption onto the video (caption PNG + ffmpeg overlay; works on
    slim ffmpeg builds that lack drawtext). Blank text returns the source untouched."""
    text = (text or "").strip()
    if not text:
        return video
    png = os.path.abspath(out_path) + ".caption.png"
    _caption_png(text, png)
    try:
        _run(["ffmpeg", "-y", "-i", os.path.abspath(video), "-i", png,
              "-filter_complex", "overlay=(W-w)/2:H-h-H/14", "-c:a", "copy",
              os.path.abspath(out_path)])
    finally:
        os.remove(png)
    return out_path


def mux_audio(video, audio_path, out_path):
    """Overlay an audio track on the video, trimming to the shorter stream."""
    _run(
        ["ffmpeg", "-y", "-i", os.path.abspath(video), "-i", os.path.abspath(audio_path),
         "-c:v", "copy", "-c:a", "aac", "-shortest", os.path.abspath(out_path)]
    )
    return out_path
