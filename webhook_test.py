"""
Strava Webhook 리스너 (로컬 테스트 + ngrok 지원)

사용법:
1. python webhook_test.py 실행
2. ngrok http 5000 (다른 터미널)
3. ngrok URL을 Strava에 등록

Strava 웹훅 등록 시:
  callback_url: https://YOUR_NGROK_URL/webhook
  verify_token: garmin-marathon-ai-webhook
"""
import os
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)
log = logging.getLogger(__name__)

app = Flask(__name__)

_VERIFY_TOKEN = "garmin-marathon-ai-webhook"
_WEBHOOK_LOG = "webhook_events.log"


def _log_event(event_type: str, data: dict) -> None:
    """웹훅 이벤트를 파일에 기록."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event_type,
        "data": data
    }
    with open(_WEBHOOK_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    log.info(f"✅ 이벤트 기록: {event_type} (activity_id={data.get('object_id')})")


@app.route("/", methods=["GET"])
def root():
    """상태 페이지."""
    return """
    <html>
    <body style="font-family: monospace; margin: 20px;">
        <h1>🏃 Strava Webhook 리스너 (로컬 테스트)</h1>
        <h2>엔드포인트:</h2>
        <ul>
            <li><b>GET /webhook</b> - Strava 핸드셰이크 검증</li>
            <li><b>POST /webhook</b> - 활동 알림 수신</li>
            <li><b>GET /status</b> - 리스너 상태</li>
            <li><b>GET /events</b> - 수신된 이벤트 목록</li>
            <li><b>POST /test</b> - 테스트 웹훅 전송</li>
        </ul>
        <h2>ngrok 터널링:</h2>
        <pre>ngrok http 5000</pre>
        <p>그 후 ngrok URL을 Strava 웹훅 등록에 사용하세요.</p>
        <h2>Strava 등록:</h2>
        <pre>
curl -X POST https://api.strava.com/v3/push_subscriptions \\
  -d client_id=254226 \\
  -d client_secret=YOUR_SECRET \\
  -d callback_url=https://YOUR_NGROK_URL/webhook \\
  -d verify_token=garmin-marathon-ai-webhook
        </pre>
    </body>
    </html>
    """, 200, {"Content-Type": "text/html; charset=utf-8"}


@app.route("/webhook", methods=["GET"])
def webhook_verify():
    """
    Strava 웹훅 검증 (핸드셰이크).

    Strava가 웹훅 등록 시 이 엔드포인트를 GET으로 호출하여
    hub.challenge를 반환받음으로써 검증합니다.
    """
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    log.info(f"🔗 핸드셰이크 요청 수신")
    log.info(f"   mode={mode}, token={token[:10]}..., challenge={challenge[:20]}...")

    if mode == "subscribe" and token == _VERIFY_TOKEN:
        log.info(f"✅ 검증 성공! hub.challenge 반환")
        _log_event("verification_success", {
            "mode": mode,
            "challenge": challenge
        })
        return jsonify({"hub.challenge": challenge}), 200

    log.warning(f"❌ 검증 실패! (토큰 불일치 또는 mode 오류)")
    _log_event("verification_failed", {
        "mode": mode,
        "token_valid": token == _VERIFY_TOKEN
    })
    return jsonify({"error": "Forbidden"}), 403


@app.route("/webhook", methods=["POST"])
def webhook_activity():
    """Strava 활동 완료 알림 수신."""
    data = request.get_json()

    event_type = data.get("object_type")  # "activity"
    aspect = data.get("aspect_type")       # "create", "update", "delete"
    activity_id = data.get("object_id")
    athlete_id = data.get("athlete_id")

    log.info(f"📍 웹훅 이벤트 수신: {event_type}/{aspect} (activity_id={activity_id})")
    _log_event("activity_notification", data)

    # ── 여기서 파이프라인 트리거 ────────────────────────────────────
    if event_type == "activity" and aspect == "create":
        log.info(f"🏃 새 러닝 활동 감지! (id={activity_id}, athlete={athlete_id})")
        # TODO: app.webhook_handler.handle_strava_webhook(data) 호출

    return jsonify({"status": "received"}), 200


@app.route("/status", methods=["GET"])
def status():
    """리스너 상태."""
    return jsonify({
        "status": "running",
        "verify_token": _VERIFY_TOKEN,
        "webhook_log": _WEBHOOK_LOG,
        "timestamp": datetime.now().isoformat()
    }), 200


@app.route("/events", methods=["GET"])
def get_events():
    """수신된 웹훅 이벤트 목록 (최근 20개)."""
    if not os.path.exists(_WEBHOOK_LOG):
        return jsonify({"events": []}), 200

    with open(_WEBHOOK_LOG, "r") as f:
        events = [json.loads(line) for line in f.readlines()[-20:]]

    return jsonify({"events": events, "count": len(events)}), 200


@app.route("/test", methods=["POST"])
def test_webhook():
    """테스트 웹훅 이벤트 시뮬레이션."""
    test_data = {
        "object_type": "activity",
        "aspect_type": "create",
        "object_id": 9999999,
        "athlete_id": 190062067,
        "updates": {
            "title": "Test Run",
            "type": "Run"
        }
    }

    log.info(f"🧪 테스트 웹훅 시뮬레이션: {test_data}")
    _log_event("test_activity", test_data)

    return jsonify({
        "status": "test_received",
        "data": test_data
    }), 200


@app.route("/clear", methods=["POST"])
def clear_logs():
    """웹훅 로그 초기화."""
    if os.path.exists(_WEBHOOK_LOG):
        os.remove(_WEBHOOK_LOG)
        log.info(f"🗑️ 로그 초기화 완료")
        return jsonify({"status": "logs_cleared"}), 200
    return jsonify({"status": "no_logs"}), 200


if __name__ == "__main__":
    log.info("=" * 60)
    log.info("🚀 Strava Webhook 리스너 시작 (로컬 테스트 모드)")
    log.info("=" * 60)
    log.info(f"📝 Verify Token: {_VERIFY_TOKEN}")
    log.info(f"📋 이벤트 로그: {_WEBHOOK_LOG}")
    log.info(f"🌐 http://localhost:5000")
    log.info(f"⚡ ngrok 실행: ngrok http 5000")
    log.info("=" * 60)

    app.run(host="0.0.0.0", port=5000, debug=True)
