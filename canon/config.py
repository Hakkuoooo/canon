import os

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# Confirm/replace these ids in Task 0.2 against the models the hackathon grants.
CHAT_MODEL = "qwen-plus"
VL_MODEL = "qwen-vl-plus"
IMAGE_MODEL = "wan2.1-t2i"
VIDEO_MODEL = "wan2.1-i2v"
TTS_MODEL = "cosyvoice-v1"

MAX_REGEN = 1
MAX_SHOTS = 6          # locked: ~60-70s episodes
DEFAULT_STYLE = "flat 2D anime, soft cel shading, muted palette"
