import pandas as pd
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.config import get
from app.client.strava_client import get_recent_activities
from app.agents.coach_agent import generate_coaching_report
from app.notifiers.telegram_notifier import send_message_async
from app.storage.history_manager import is_processed

_DASHBOARD_URL = "https://your-app.streamlit.app"  # Streamlit 배포 후 교체

_HELP_TEXT = """
🏃 *마라톤 AI 코치 명령어*

/start — 봇 시작
/help — 명령어 안내

💬 *자연어 질문 예시*
• `이번 주 총 거리` — 주간 누적 거리 조회
• `분석` / `코칭 요청` — AI 페이스 & 심박 분석
• `대시보드` — 시각화 리포트 URL
""".strip()


async def _cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("안녕하세요! 🏃 마라톤 AI 코치입니다.\n/help 로 사용법을 확인하세요.")


async def _cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_markdown(_HELP_TEXT)


def _weekly_distance_text(activities: list[dict]) -> str:
    if not activities:
        return "이번 주 러닝 기록이 없습니다."

    df = pd.DataFrame(activities)
    df["start_date_local"] = pd.to_datetime(df["start_date_local"])
    week_start = pd.Timestamp.now(tz="UTC").tz_localize(None).to_period("W").start_time
    weekly = df[df["start_date_local"] >= week_start]

    if weekly.empty:
        return "이번 주 러닝 기록이 없습니다."

    total_km = weekly["distance"].sum() / 1000
    count = len(weekly)
    return f"🗓️ *이번 주 러닝 현황*\n\n거리: `{total_km:.2f} km` ({count}회)"


async def _handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.message.text or "").strip()
    lower = text.lower()

    # ── 거리 조회: Gemini 호출 없음 ──────────────────────────────────
    if any(kw in lower for kw in ["총 거리", "이번 주", "주간"]):
        try:
            activities = get_recent_activities()
            reply = _weekly_distance_text(activities)
        except Exception as e:
            reply = f"⚠️ 데이터 조회 오류: {e}"
        await update.message.reply_markdown(reply)
        return

    # ── 대시보드 URL: Gemini 호출 없음 ───────────────────────────────
    if "대시보드" in lower:
        await update.message.reply_markdown(
            f"📊 *대시보드 바로가기*\n\n[{_DASHBOARD_URL}]({_DASHBOARD_URL})"
        )
        return

    # ── 코칭 요청: Gemini 1-Turn 호출 ────────────────────────────────
    if any(kw in lower for kw in ["분석", "코칭", "피드백", "페이스"]):
        await update.message.reply_text("🔍 최근 러닝 데이터를 분석 중입니다...")
        try:
            activities = get_recent_activities(per_page=5)
            unprocessed = [a for a in activities if not is_processed(a["id"])]
            target = unprocessed[0] if unprocessed else (activities[0] if activities else None)
            if target is None:
                await update.message.reply_text("분석할 러닝 기록이 없습니다.")
                return
            report = generate_coaching_report(target)
            await send_message_async(report)
        except Exception as e:
            await update.message.reply_text(f"⚠️ 분석 오류: {e}")
        return

    # ── 기타 질문 ─────────────────────────────────────────────────────
    await update.message.reply_text(
        "❓ 인식하지 못한 명령입니다.\n`분석`, `이번 주 총 거리`, `대시보드` 중 하나를 입력해 주세요."
    )


def build_application():
    app = ApplicationBuilder().token(get("TELEGRAM_BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", _cmd_start))
    app.add_handler(CommandHandler("help", _cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, _handle_message))
    return app
