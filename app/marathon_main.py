import asyncio
import logging

from app.client.strava_client import get_recent_activities
from app.agents.coach_agent import generate_coaching_report
from app.notifiers.telegram_notifier import send_message
from app.storage.history_manager import is_processed, mark_processed, save_coaching_report
from app.bot.chatbot_handler import build_application

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def run_pipeline() -> None:
    """새 러닝 발견 → 분석 → 텔레그램 발송 → 히스토리 갱신."""
    log.info("Strava 액티비티 수집 시작")
    activities = get_recent_activities(per_page=10)

    new_count = 0
    for activity in activities:
        aid = activity["id"]
        if is_processed(aid):
            continue

        log.info(f"새 액티비티 발견: {activity['name']} (id={aid})")
        text_report, structured_data = generate_coaching_report(activity)

        # 코칭 데이터 저장
        save_coaching_report(aid, structured_data)
        log.info(f"코칭 데이터 저장: id={aid}")

        # 텔레그램 발송
        send_message(text_report)
        mark_processed(aid)
        new_count += 1
        log.info(f"분석 완료 및 히스토리 갱신: id={aid}")

    if new_count == 0:
        log.info("새 액티비티 없음 — 파이프라인 종료")
    else:
        log.info(f"파이프라인 완료: {new_count}개 액티비티 처리")


async def _main_async() -> None:
    # 시작 시 파이프라인 1회 실행
    run_pipeline()

    # 텔레그램 챗봇 Long Polling 상시 구동
    log.info("텔레그램 챗봇 리스너 시작")
    app = build_application()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    log.info("챗봇 대기 중... (종료: Ctrl+C)")
    try:
        await asyncio.Event().wait()
    finally:
        await app.updater.stop()
        await app.stop()
        await app.shutdown()


def main() -> None:
    asyncio.run(_main_async())


if __name__ == "__main__":
    main()
