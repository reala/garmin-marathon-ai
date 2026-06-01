import logging
from app.client.strava_client import get_recent_activities
from app.agents.coach_agent import generate_coaching_report
from app.notifiers.telegram_notifier import send_message
from app.storage.history_manager import is_processed, mark_processed

log = logging.getLogger(__name__)


def handle_strava_webhook(data: dict) -> None:
    """Strava 웹훅 요청 처리."""
    event_type = data.get("object_type")
    aspect_type = data.get("aspect_type")
    activity_id = data.get("object_id")

    # ── 러닝 완료 이벤트만 처리 ──────────────────────────────────────
    if event_type != "activity" or aspect_type != "create":
        log.info(f"무시됨: {event_type} / {aspect_type}")
        return

    log.info(f"새 액티비티 감지: id={activity_id}")

    # ── 중복 확인 ──────────────────────────────────────────────────────
    if is_processed(activity_id):
        log.info(f"이미 처리됨: id={activity_id}")
        return

    # ── Strava에서 전체 액티비티 데이터 조회 ─────────────────────────
    try:
        activities = get_recent_activities(per_page=5)
        target = next((a for a in activities if a["id"] == activity_id), None)

        if target is None:
            log.warning(f"액티비티 상세 조회 실패: id={activity_id}")
            return

        # ── 분석 & 알림 ────────────────────────────────────────────────
        log.info(f"분석 중: {target.get('name')}")
        report = generate_coaching_report(target)
        send_message(report)
        mark_processed(activity_id)
        log.info(f"완료: id={activity_id}")

    except Exception as e:
        log.error(f"처리 오류: {e}", exc_info=True)
        send_message(f"⚠️ 분석 중 오류 발생: {e}")
