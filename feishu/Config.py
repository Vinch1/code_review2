import os

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET") or None
#POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "0"))
TIMEOUT_SEC = int(os.getenv("TIMEOUT_SEC", "6"))

