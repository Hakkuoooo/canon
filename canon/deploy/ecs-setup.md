# Deploy Canon backend on Alibaba Cloud (Simple Application Server)

Proof of deployment = a screenshot of your Alibaba Cloud console showing the SAS instance running and
the app responding. Only the **backend** (FastAPI) needs deploying; the React frontend can stay local.
SAS is simpler/cheaper than ECS and is explicitly accepted by the hackathon. ECS works too if you prefer.

## 1. Create the server
- Alibaba Cloud console → **Simple Application Server** → Create.
- **Region: same as your API key** = International (Singapore).
- Image: **Ubuntu 22.04**, smallest plan.
- After it boots, note the **public IP**, and open the firewall for **TCP 8000** (SAS console → Firewall → add rule, port 8000).

## 2. SSH in and install
```bash
ssh root@<public-ip>
apt update && apt install -y python3.11 python3.11-venv ffmpeg git
```

## 3. Get the code + key
```bash
git clone https://github.com/Hakkuoooo/<REPO>.git canon && cd canon   # <REPO> = the repo name we push
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
export DASHSCOPE_API_KEY=<your key>          # do NOT commit this
```

## 4. Run it
```bash
.venv/bin/uvicorn canon.api:app --host 0.0.0.0 --port 8000
```
Open `http://<public-ip>:8000/api/health` — it should return `{"ok":true,"provider":"DashScopeProviders"}`.
That is your live backend on Alibaba Cloud.

## 5. Keep it alive after logout (optional)
```bash
apt install -y tmux && tmux new -s canon
# run the uvicorn command inside, then detach: Ctrl-b then d
```

## 6. Screenshot for the submission
Capture: the **SAS console showing the instance "Running"**, plus a browser hitting
`http://<public-ip>:8000/api/health`. That image is your "Alibaba Cloud Deployment Verification".
