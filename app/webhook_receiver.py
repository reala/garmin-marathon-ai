from flask import Flask, request, jsonify
from app.config import get
from app.webhook_handler import handle_strava_webhook

app = Flask(__name__)

_VERIFY_TOKEN = "garmin-marathon-ai-webhook"


@app.route("/webhook", methods=["GET"])
def webhook_verify():
    """Strava 웹훅 등록 시 검증 요청."""
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == _VERIFY_TOKEN:
        return jsonify({"hub.challenge": challenge}), 200
    return jsonify({"error": "Forbidden"}), 403


@app.route("/webhook", methods=["POST"])
def webhook_activity():
    """Strava 활동 완료 알림 수신."""
    data = request.get_json()

    # 비동기 처리 (병렬 실행)
    try:
        handle_strava_webhook(data)
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
