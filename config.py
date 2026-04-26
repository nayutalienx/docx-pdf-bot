from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN is not set. Add it to .env or environment variables.")

MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
CONVERT_TIMEOUT_SECONDS = 120
QUEUE_MAXSIZE = 5
