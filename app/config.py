import os
from dotenv import load_dotenv

load_dotenv()

_REQUIRED_KEYS = [
    "STRAVA_CLIENT_ID",
    "STRAVA_CLIENT_SECRET",
    "STRAVA_REFRESH_TOKEN",
    "GEMINI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
]


def _load() -> dict:
    missing = [k for k in _REQUIRED_KEYS if not os.environ.get(k)]
    if missing:
        raise ValueError(f"필수 환경변수 누락 — 가동 차단: {', '.join(missing)}")
    return {k: os.environ[k] for k in _REQUIRED_KEYS}


_cfg = None


def get_config() -> dict:
    global _cfg
    if _cfg is None:
        _cfg = _load()
    return _cfg


def get(key: str) -> str:
    return get_config()[key]
