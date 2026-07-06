import os

DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_API_KEY", "")

# International (Singapore) endpoints. The dashscope SDK defaults to the China endpoint, which
# rejects an International key with 401 InvalidApiKey, so we must set these. Override via env if
# your workspace uses a dedicated domain (https://{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com).
DASHSCOPE_BASE_URL = os.environ.get("CANON_DASHSCOPE_BASE_URL", "https://dashscope-intl.aliyuncs.com/api/v1")
DASHSCOPE_WS_URL = os.environ.get("CANON_DASHSCOPE_WS_URL", "wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference")

# Model IDs observed in Model Studio (US Virginia). Overridable by env so the spike can correct any
# of them without a code change. SPIKE = confirm the exact callable id when the key exists.
CHAT_MODEL = os.environ.get("CANON_CHAT_MODEL", "qwen-plus")      # works; qwen3.7-plus needs the compat endpoint (todo)
VL_MODEL = os.environ.get("CANON_VL_MODEL", "qwen3-vl-plus")      # current vision model
IMAGE_MODEL = os.environ.get("CANON_IMAGE_MODEL", "wan2.6-t2i")   # current, ~$0.03/image
VIDEO_MODEL = os.environ.get("CANON_VIDEO_MODEL", "wan2.6-i2v-flash")  # current image-to-video, ~$0.05/sec (was pricier happyhorse)
TTS_MODEL = os.environ.get("CANON_TTS_MODEL", "cosyvoice-v3-plus")     # current TTS

MAX_REGEN = 1
MAX_SHOTS = int(os.environ.get("CANON_MAX_SHOTS", "6"))  # cap; lower it to limit cost while testing
DEFAULT_STYLE = "flat 2D anime, soft cel shading, muted palette"

# Safety cap on any asset downloaded from a model response.
MAX_DOWNLOAD_BYTES = 64 * 1024 * 1024
