"""
Streamlit Cloud 진입점.
로컬: .env에서 os.environ 로드 (app/config.py가 처리)
Cloud: st.secrets → os.environ 브리지 후 대시보드 실행
"""
import os
import streamlit as st

_SECRET_KEYS = [
    "STRAVA_CLIENT_ID",
    "STRAVA_CLIENT_SECRET",
    "STRAVA_REFRESH_TOKEN",
    "GEMINI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
]

# Streamlit Cloud 환경에서 st.secrets → os.environ 주입
for _key in _SECRET_KEYS:
    if _key not in os.environ and _key in st.secrets:
        os.environ[_key] = st.secrets[_key]

from app.dashboard import main

main()
