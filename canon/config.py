import os

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# International (Singapore) endpoints. The dashscope SDK defaults to the China endpoint, which
# rejects an International key with 401 InvalidApiKey, so we must set these. Override via env if
# your workspace uses a dedicated domain (https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com).
DASHSCOPE_BASE_URL = os.environ.get("CANON_DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1")
DASHSCOPE_WS_URL = os.environ.get("CANON_DASHSCOPE_WS_URL", "wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference")

# Model IDs observed in Model Studio (US Virginia). Overridable by env so the spike can correct any
# of them without a code change. SPIKE = confirm the exact callable id when the key exists.
CHAT_MODEL = os.environ.get("CANON_CHAT_MODEL", "qwen-plus")      # verified callable id (Generation.call)
VL_MODEL = os.environ.get("CANON_VL_MODEL", "qwen-vl-plus")       # canonical vision model for the QC check
IMAGE_MODEL = os.environ.get("CANON_IMAGE_MODEL", "wan2.2-t2i-flash")   # SPIKE: text-to-image id
VIDEO_MODEL = os.environ.get("CANON_VIDEO_MODEL", "happyhorse-1.0-t2v")  # SPIKE: t2v vs i2v affects the pipeline
TTS_MODEL = os.environ.get("CANON_TTS_MODEL", "cosyvoice-v2")     # SPIKE: speech-synthesis id

MAX_REGEN = 1
MAX_SHOTS = int(os.environ.get("CANON_MAX_SHOTS", "6"))  # cap; lower it to limit cost while testing
DEFAULT_STYLE = "flat 2D anime, soft cel shading, muted palette"

# Safety cap on any asset downloaded from a model response.
MAX_DOWNLOAD_BYTES = 64 * 1024 * 1024
