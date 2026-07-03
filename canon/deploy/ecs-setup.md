# Deploy Canon on Alibaba Cloud (ECS + OSS)

This is the "proof of Alibaba Cloud deployment" runbook. It hosts the API + built frontend on an
ECS instance and stores generated episodes in OSS. Fill in the bracketed values as you go.

## 1. Provision

- **ECS**: smallest general-purpose instance, Ubuntu 22.04, in the **same region as your Model
  Studio key** (International, e.g. Singapore or US Virginia). Open the security-group port you
  serve on (8000, or 80 behind nginx).
- **OSS**: create a bucket `canon-<yourname>` in the same region.

## 2. Install

```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv ffmpeg git nodejs npm
# ffmpeg from apt includes libass, so burned-in subtitles work here (unlike the dev Mac build)
```

## 3. Deploy the app

```bash
git clone <your public repo> canon && cd canon
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
export DASHSCOPE_API_KEY=<your key>          # keep this out of git

# build the frontend, point it at this host's API
VITE_API_BASE=http://<ECS-public-ip>:8000 npm --prefix web install
VITE_API_BASE=http://<ECS-public-ip>:8000 npm --prefix web run build
# serve web/dist with any static server, or nginx; API below

.venv/bin/uvicorn canon.api:app --host 0.0.0.0 --port 8000
```

Confirm the models first: `DASHSCOPE_API_KEY=... .venv/bin/python -m canon.spikes.spike_providers`.

## 4. OSS for assets

Store finished `episode*.mp4` in OSS so they survive redeploys and can be served over a CDN. Minimal
addition (uses the `oss2` SDK):

```python
# ponytail: 6 lines, called after render_episode returns
import oss2
auth = oss2.Auth(ACCESS_KEY_ID, ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, "https://oss-<region>.aliyuncs.com", "canon-<yourname>")
bucket.put_object_from_file(f"episodes/{series}/{name}", local_path)
```

## 5. Proof for the submission

Capture: the running URL, `ecs.console` screenshot of the instance, the OSS bucket with objects, and
this file in the repo. Services used: **Model Studio (DashScope) + ECS + OSS**.
