"""
設定檔與環境變數管理 (Flight Clearance & Bug Fare Radar Bot)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"
SUBSCRIBERS_FILE = BASE_DIR / "subscribers_radar.json"

LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_LIFF_ID = os.getenv("LINE_LIFF_ID", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "") or os.getenv("GOOGLE_API_KEY", "")
CRON_SECRET = os.getenv("CRON_SECRET", "")
PORT = int(os.getenv("PORT", "8000"))

IS_MOCK_MODE = not (LINE_CHANNEL_SECRET and LINE_CHANNEL_ACCESS_TOKEN)
