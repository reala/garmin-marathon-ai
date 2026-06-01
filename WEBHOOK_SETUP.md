# Strava Webhook 설정 가이드

## 1단계: Railway 배포

```bash
1. https://railway.app 접속 (GitHub 로그인)
2. New Project → GitHub Repo 선택 (garmin-marathon-ai)
3. Add SERVICE → Environment Variables 설정:
   - STRAVA_CLIENT_ID
   - STRAVA_CLIENT_SECRET
   - STRAVA_REFRESH_TOKEN
   - GEMINI_API_KEY
   - TELEGRAM_BOT_TOKEN
   - TELEGRAM_CHAT_ID
4. Deploy → Domain 확인 (예: https://garmin-marathon-ai.railway.app)
```

## 2단계: Strava 웹훅 등록

```bash
curl -X POST https://api.strava.com/v3/push_subscriptions \
  -d client_id=254226 \
  -d client_secret=YOUR_CLIENT_SECRET \
  -d callback_url=https://YOUR_RAILWAY_DOMAIN.railway.app/webhook \
  -d verify_token=garmin-marathon-ai-webhook
```

### 또는 Postman/브라우저로:

```
POST https://api.strava.com/v3/push_subscriptions

Body (form-data):
- client_id: 254226
- client_secret: (발급받은 값)
- callback_url: https://your-domain.railway.app/webhook
- verify_token: garmin-marathon-ai-webhook
```

## 3단계: 검증

```bash
# 웹훅 상태 확인
curl -X GET https://api.strava.com/v3/push_subscriptions \
  -H "Authorization: Bearer YOUR_STRAVA_TOKEN" \
  -d client_id=254226 \
  -d client_secret=YOUR_CLIENT_SECRET
```

## 동작 확인

러닝 완료 후 → Strava 업로드 완료 → 2초 이내 텔레그램 알림 수신

---

## 문제해결

**"Invalid callback_url"**
- Railway 도메인이 맞는지 확인
- `/webhook` 경로가 정확한지 확인

**웹훅이 안 오는 경우**
- Railway 로그에서 에러 확인: `railway logs`
- Strava 개발자 문서: https://developers.strava.com/docs/webhooks/
