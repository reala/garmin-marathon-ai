# Railway Cron Job 설정 가이드

## 🎯 목표
Railway에서 5분마다 자동으로 `app/cron_pipeline.py` 실행 → Strava 폴링 → Gemini 분석 → 텔레그램 알림

---

## 📋 현재 상태
- **Web Service**: https://web-production-0840d.up.railway.app (Webhook 서버)
- **Cron Job**: 미생성 (지금 추가할 것)

---

## 🚀 Step 1: Railway에 Cron Job 서비스 추가

### 방법 1: Railway 대시보드 (권장)

```
1. https://railway.app → 프로젝트 선택 (garmin-marathon-ai)
2. "New" → "Service"
3. Service Type: "Cron Job" 선택
4. (또는 "Add Service" → "Create New")
```

### 방법 2: railway.json 설정 (고급)

프로젝트 루트에 다음 파일 추가:

```json
{
  "services": {
    "web": {
      "builder": "dockerfile"
    },
    "cron": {
      "builder": "dockerfile",
      "entrypoint": "python -m app.cron_pipeline"
    }
  }
}
```

---

## ⚙️ Step 2: Cron Job 설정

### 환경변수 설정
Cron Job 서비스에서 다음 변수 추가:

```
STRAVA_CLIENT_ID = 254226
STRAVA_CLIENT_SECRET = 3c557ec392f5e3e00952dbca260079200424f6f8
STRAVA_REFRESH_TOKEN = ba13b7d3b3368c2212f4a8f1ac92e88719b000d4
GEMINI_API_KEY = (발급받은 키)
TELEGRAM_BOT_TOKEN = 8962607146:AAFbvZTcN4InffEXNJ9w9IdOHl170tn7pn8
TELEGRAM_CHAT_ID = 52316221
```

### Schedule 설정

**Cron Expression:** `*/5 * * * *`

의미:
- `*/5` = 5분마다
- `*` = 매시간
- `*` = 매일
- `*` = 매월
- `*` = 매요일

다른 옵션:
```
*/1 * * * *   → 1분마다
*/5 * * * *   → 5분마다 (권장)
*/10 * * * * → 10분마다
0 * * * *    → 매시간
```

---

## 📝 Step 3: 배포 및 테스트

### 배포
```bash
git push origin main
# Railway가 자동으로 감지하고 배포
```

### 로그 확인
```
Railway 대시보드 → Cron Job 서비스 → Logs
```

**정상 로그 예시:**
```
============================================================
🏃 Cron Pipeline 시작
============================================================
📊 Strava에서 최근 러닝 조회 중...
✅ 5개 활동 조회 완료
🔍 새 활동 발견: Morning Run (id=123456)
🤖 분석 중: Morning Run
💬 텔레그램 발송 중...
✅ 완료: Morning Run
============================================================
✅ Pipeline 완료: 1개 활동 처리
============================================================
```

---

## 🧪 수동 테스트 (로컬)

```bash
# 로컬에서 한 번 실행해보기
python -m app.cron_pipeline
```

---

## 📊 모니터링

### 실행 통계 확인
```
Railway 대시보드 → Cron Job → Executions
- 실행 시간
- 상태 (Success/Failed)
- 로그 내용
```

### 텔레그램으로 직접 확인
- 텔레그램 채팅에서 새 러닝 알림 수신 시 = 정상 작동 ✅

---

## 🔍 문제 해결

### Cron Job이 실행 안 됨
1. Schedule 설정 확인 (`*/5 * * * *`)
2. 환경변수 모두 입력되었는지 확인
3. Railway 로그에서 에러 메시지 확인

### "ModuleNotFoundError: No module named 'app'"
```
Railway Dockerfile가 requirements.txt를 인식하지 못함
→ Procfile이 올바르게 설정되어 있는지 확인
```

### Strava API 에러
```
API 호출 실패 (한국 ISP DNS 차단)
→ Railway 서버에서는 미국에서 호출하므로 문제없음
→ 로그에서 오류 메시지 확인
```

---

## 🎯 최종 아키텍처

```
┌─────────────────────┐
│  Railway Cron Job   │
│   (5분마다 실행)     │
└──────────┬──────────┘
           │
           ├─→ Strava API (최근 러닝 조회)
           │
           ├─→ Gemini 2.0 Flash (분석)
           │
           └─→ Telegram (알림)
```

**월 비용: $0 (무료 크레딧 내에서 해결) ✅**

---

## ✅ 완료 체크리스트

- [ ] Railway에 Cron Job 서비스 생성
- [ ] 환경변수 6개 입력
- [ ] Schedule 설정: `*/5 * * * *`
- [ ] 배포 (git push)
- [ ] 로그 확인
- [ ] 실제 러닝 후 텔레그램 알림 수신 확인
