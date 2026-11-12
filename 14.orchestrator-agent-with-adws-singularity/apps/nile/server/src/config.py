"""Configuration settings for Nile server."""
import os
import re
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/nile.db"

# Login tokens expire this many hours after they are issued (default 7 days)
SESSION_LIFETIME = timedelta(hours=float(os.getenv("SESSION_LIFETIME_HOURS", "168")))

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Server settings
API_PREFIX = "/api"

# Comma-separated browser origins allowed by CORS. A "*" stands for one hostname
# label of letters, digits and hyphens (e.g. the per-sandbox E2B preview hosts).
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,https://5173-*.e2b.app"
    ).split(",")
    if origin.strip()
]
CORS_ORIGIN_REGEX = "|".join(
    re.escape(origin).replace(r"\*", "[A-Za-z0-9-]+") for origin in CORS_ORIGINS if "*" in origin
) or None
