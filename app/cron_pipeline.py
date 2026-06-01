"""
Railway Cron Job 파이프라인
매 5분마다 실행되는 자동 Strava 동기화 및 AI 분석

사용법:
  Railway Cron Job 서비스에서 다음 명령어로 설정:
  python -m app.cron_pipeline
"""
import logging
import sys
from app.client.strava_client import get_recent_activities
from app.agents.coach_agent import generate_coaching_report
from app.notifiers.telegram_notifier import send_message
from app.storage.history_manager import is_processed, mark_processed

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s",
    stream=sys.stdout
)
log = logging.getLogger(__name__)


def run():
    """Strava 폴링 및 분석 파이프라인."""
    log.info("=" * 60)
    log.info("🏃 Cron Pipeline 시작")
    log.info("=" * 60)

    try:
        # ── Strava에서 최근 러닝 조회 ────────────────────────────────
        log.info("📊 Strava에서 최근 러닝 조회 중...")
        activities = get_recent_activities(per_page=10)

        if not activities:
            log.info("✅ 새로운 러닝이 없습니다.")
            return

        log.info(f"✅ {len(activities)}개 활동 조회 완료")

        # ── 미분석 활동 필터링 및 분석 ──────────────────────────────
        processed_count = 0
        for activity in activities:
            aid = activity["id"]

            if is_processed(aid):
                continue

            log.info(f"🔍 새 활동 발견: {activity['name']} (id={aid})")

            try:
                # Gemini 분석
                log.info(f"🤖 분석 중: {activity['name']}")
                report = generate_coaching_report(activity)

                # 텔레그램 발송
                log.info(f"💬 텔레그램 발송 중...")
                send_message(report)

                # 히스토리 갱신
                mark_processed(aid)
                processed_count += 1
                log.info(f"✅ 완료: {activity['name']}")

            except Exception as e:
                log.error(f"❌ 분석 오류: {e}", exc_info=True)
                try:
                    send_message(f"⚠️ 분석 중 오류 발생: {activity['name']}\n{str(e)[:100]}")
                except Exception as send_err:
                    log.error(f"알림 전송 실패: {send_err}")

        log.info("=" * 60)
        log.info(f"✅ Pipeline 완료: {processed_count}개 활동 처리")
        log.info("=" * 60)

    except Exception as e:
        log.error(f"❌ Pipeline 오류: {e}", exc_info=True)
        try:
            send_message(f"❌ Cron Pipeline 오류:\n{str(e)[:200]}")
        except Exception as send_err:
            log.error(f"오류 알림 전송 실패: {send_err}")
        sys.exit(1)


if __name__ == "__main__":
    run()
