"""FastAPI tier so the React frontend can drive the engine. Single-user / demo scope, no auth.
series_id is validated as a strict slug before it ever touches the filesystem — this is the
path-traversal boundary the Bible module deferred to the API. Generation is synchronous here
(fine offline and for a pre-generated demo); a job queue is the scale answer, out of scope."""
import json
import logging
import os
import re
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from canon.bible import Bible
from canon.pipeline import _report, render_episode
from canon.providers import get_providers

DATA_ROOT = os.path.join(os.path.dirname(__file__), "data", "series")
_SLUG = re.compile(r"^[a-z0-9-]{1,40}$")

app = FastAPI(title="Canon")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)  # dev/demo: single-user, open CORS


def _series_dir(series_id: str) -> str:
    if not _SLUG.match(series_id):  # blocks ../, absolute paths, anything non-slug
        raise HTTPException(status_code=400, detail="invalid series id")
    return os.path.join(DATA_ROOT, series_id)


def _characters(bible):
    return [{"name": c.name, "descriptor": c.descriptor, "seed": c.seed} for c in bible.characters.values()]


class EpisodeReq(BaseModel):
    premise: str
    style: str | None = None
    shots: int | None = None


@app.get("/api/health")
def health():
    return {"ok": True, "provider": type(get_providers()).__name__}


@app.post("/api/series")
def create_series():
    sid = uuid.uuid4().hex[:12]
    os.makedirs(_series_dir(sid), exist_ok=True)
    return {"series_id": sid}


@app.post("/api/series/{series_id}/episodes")
def create_episode(series_id: str, req: EpisodeReq):
    d = _series_dir(series_id)
    os.makedirs(d, exist_ok=True)
    bible = Bible(d).load()
    premise = req.premise if not req.style else f"{req.premise}\n\nVisual style: {req.style}."
    max_shots = max(1, min(12, req.shots)) if req.shots is not None else None  # clamp: bound cost
    try:
        out = render_episode(premise, get_providers(), d, bible, max_shots)
    except Exception:
        logging.exception("episode generation failed for series %s", series_id)
        _report(d, stage="error")  # so the progress poller stops narrating a dead run
        raise HTTPException(status_code=500, detail="generation failed on the engine; check the server logs")
    n = int(re.search(r"episode(\d+)\.mp4$", out).group(1))
    meta = {}
    meta_path = os.path.join(d, f"episode{n}.json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding="utf-8") as f:
            meta = json.load(f)
    return {
        "episode": n,
        "title": meta.get("title"),
        "logline": meta.get("logline"),
        "video_url": f"/api/series/{series_id}/episodes/{n}/video",
        "style": bible.style,
        "characters": _characters(bible),
    }


@app.get("/api/series/{series_id}/episodes/{n}/video")
def get_video(series_id: str, n: int):
    path = os.path.join(_series_dir(series_id), f"episode{int(n)}.mp4")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="episode not found")
    return FileResponse(path, media_type="video/mp4")


@app.get("/api/series/{series_id}/progress")
def get_progress(series_id: str):
    """Live pipeline stage, polled by the UI during a render. Idle when nothing has run yet."""
    path = os.path.join(_series_dir(series_id), "progress.json")
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"stage": "idle"}


@app.get("/api/series/{series_id}/bible")
def get_bible(series_id: str):
    bible = Bible(_series_dir(series_id)).load()
    return {"style": bible.style, "characters": _characters(bible)}
