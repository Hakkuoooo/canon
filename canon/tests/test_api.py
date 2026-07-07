from fastapi.testclient import TestClient

import canon.api as api

client = TestClient(api.app)


def test_health_reports_provider():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["ok"] is True


def test_create_series_episode_and_fetch_video(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DATA_ROOT", str(tmp_path))  # keep the repo clean
    sid = client.post("/api/series").json()["series_id"]

    r = client.post(f"/api/series/{sid}/episodes", json={"premise": "two siblings, one vault"})
    assert r.status_code == 200
    data = r.json()
    assert data["episode"] == 1 and data["characters"]  # offline provider rendered a real episode

    v = client.get(data["video_url"])
    assert v.status_code == 200 and v.headers["content-type"].startswith("video/")

    bible = client.get(f"/api/series/{sid}/bible").json()
    assert bible["characters"]


def test_progress_endpoint_idle_then_done(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DATA_ROOT", str(tmp_path))
    sid = client.post("/api/series").json()["series_id"]
    assert client.get(f"/api/series/{sid}/progress").json()["stage"] == "idle"

    client.post(f"/api/series/{sid}/episodes", json={"premise": "p", "shots": 1})
    done = client.get(f"/api/series/{sid}/progress").json()
    assert done["stage"] == "done" and done["episode"] == 1


def test_invalid_series_id_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(api, "DATA_ROOT", str(tmp_path))
    r = client.get("/api/series/..%2F..%2Fetc/bible")  # attempted path traversal
    assert r.status_code in (400, 404)  # slug validation refuses it
