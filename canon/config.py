import os

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# Model IDs observed in Model Studio (US Virginia). Overridable by env so the spike can correct any
# of them without a code change. SPIKE = confirm the exact callable id when the key exists.
CHAT_MODEL = os.environ.get("CANON_CHAT_MODEL", "qwen3.7-plus")   # multimodal: handles chat and vision
VL_MODEL = os.environ.get("CANON_VL_MODEL", "qwen3.7-plus")       # same family runs the QC vision check
IMAGE_MODEL = os.environ.get("CANON_IMAGE_MODEL", "wan2.2-t2i-flash")   # SPIKE: text-to-image id
VIDEO_MODEL = os.environ.get("CANON_VIDEO_MODEL", "happyhorse-1.0-t2v")  # SPIKE: t2v vs i2v affects the pipeline
TTS_MODEL = os.environ.get("CANON_TTS_MODEL", "cosyvoice-v2")     # SPIKE: speech-synthesis id

MAX_REGEN = 1
MAX_SHOTS = 6          # locked: ~60-70s episodes
DEFAULT_STYLE = "flat 2D anime, soft cel shading, muted palette"

# Safety cap on any asset downloaded from a model response.
MAX_DOWNLOAD_BYTES = 64 * 1024 * 1024
