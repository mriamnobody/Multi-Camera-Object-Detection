# multicam_app/config.py

RTSP_STREAMS = [
    {"id": "cam1", "url": "rtsp://url"},
    {"id": "cam2", "url": "rtsp://url"},
    {"id": "cam3", "url": "rtsp://url"},
    {"id": "cam4", "url": "rtsp://url"},
]

# CONF_THRESHOLD = 0.75

LOG_FILE = "app.log"
MODEL_PATH = ""
MAX_QUEUE_SIZE = 5
RECONNECT_DELAY = 2   # seconds
RETRY_CONNECTION_DELAY = 5  # seconds
MAX_DROPS_BEFORE_RECONNECT = 10

TELEGRAM_CHAT_ID = ""
TELEGRAM_BOT_TOKEN = ""

# Directory where detection frames will be saved
DETECTIONS_DIR = "detections"
