# Strava Webhook 로컬 테스트 가이드

## 🎯 목표
ngrok으로 로컬 서버를 터널링한 후, Strava 웹훅 핸드셰이크 검증 및 이벤트 수신 테스트

---

## 📋 사전 준비

```bash
# 1. Flask 설치 (이미 requirements.txt에 있음)
pip install flask

# 2. ngrok 설치
# macOS:
brew install ngrok
# 또는 https://ngrok.com/download 에서 다운로드
```

---

## 🚀 Step 1: 로컬 웹훅 서버 시작

```bash
cd garmin-marathon-ai
python webhook_test.py
```

**출력:**
```
============================================================
🚀 Strava Webhook 리스너 시작 (로컬 테스트 모드)
============================================================
📝 Verify Token: garmin-marathon-ai-webhook
📋 이벤트 로그: webhook_events.log
🌐 http://localhost:5000
⚡ ngrok 실행: ngrok http 5000
============================================================
```

---

## 🌐 Step 2: ngrok 터널링 (다른 터미널)

```bash
ngrok http 5000
```

**출력:**
```
ngrok                                       (Ctrl+C to quit)

Session Status                online
Session Expires               1h 59m 57s
Version                       3.0.0
Region                        us (United States)
Forwarding                    https://YOUR_NGROK_URL.ngrok.io -> http://localhost:5000
Forwarding                    http://YOUR_NGROK_URL.ngrok.io -> http://localhost:5000
```

**ngrok URL 복사: `https://YOUR_NGROK_URL.ngrok.io`**

---

## ✅ Step 3: 웹훅 검증 테스트

**로컬 테스트 (ngrok 없이):**
```bash
curl "http://localhost:5000/webhook?hub.mode=subscribe&hub.verify_token=garmin-marathon-ai-webhook&hub.challenge=TEST123"
```

**응답:**
```json
{"hub.challenge": "TEST123"}
```

---

## 📝 Step 4: Strava에 웹훅 등록

**ngrok URL로 Strava 등록:**
```bash
curl -X POST https://api.strava.com/v3/push_subscriptions \
  -d client_id=254226 \
  -d client_secret=3c557ec392f5e3e00952dbca260079200424f6f8 \
  -d callback_url=https://YOUR_NGROK_URL.ngrok.io/webhook \
  -d verify_token=garmin-marathon-ai-webhook
```

**성공 응답:**
```json
{
  "id": 123456,
  "created_at": "2026-06-01T...",
  "push_events": ["create"],
  "callback_url": "https://YOUR_NGROK_URL.ngrok.io/webhook"
}
```

---

## 🧪 Step 5: 테스트 이벤트 전송

```bash
# 테스트 웹훅 이벤트 시뮬레이션
curl -X POST http://localhost:5000/test

# 수신된 이벤트 확인
curl http://localhost:5000/events
```

---

## 📊 모니터링

**웹훅 리스너 상태:**
```bash
curl http://localhost:5000/status
```

**수신된 모든 이벤트:**
```bash
curl http://localhost:5000/events
```

**로그 파일:**
```bash
tail -f webhook_events.log
```

---

## 🏃 실제 러닝으로 테스트

1. ✅ 웹훅 등록 완료
2. ✅ 로컬 서버 실행 중
3. ✅ ngrok 터널 활성화
4. **이제 실제 러닝 기록해보세요!**
   - Strava 앱에서 러닝 시작
   - 러닝 완료 후 업로드
   - 1-2초 내에 터미널에서 확인:
   ```
   📍 웹훅 이벤트 수신: activity/create (activity_id=12345678)
   🏃 새 러닝 활동 감지! (id=12345678, athlete=190062067)
   ```

---

## 🔍 디버깅

**웹훅이 안 오는 경우:**

1. ngrok 상태 확인
   ```bash
   # ngrok 대시보드: http://localhost:4040
   ```

2. Strava 로그 확인
   ```bash
   # https://www.strava.com/settings/api → Webhooks 섹션에서 최근 전송 보기
   ```

3. 로컬 로그 확인
   ```bash
   tail -f webhook_events.log
   ```

---

## 🎯 다음 단계

테스트 성공 후:
1. Railway에 배포 (Procfile 이용)
2. Railway 도메인으로 Strava 웹훅 업데이트
3. webhook_handler.py 통합 (파이프라인 자동 실행)
