# garmin-marathon-ai-TODO.md

# 🏃‍♂️ 프로젝트 마스터 작업지시서: garmin-marathon-ai (초정밀 개정판)

## 1. 프로젝트 개요 및 핵심 아키텍처

본 프로젝트는 가민 스마트워치 및 스트라바(Strava) API를 하이브리드로 연동하여 사용자의 러닝/하프마라톤 훈련 데이터를 자율 수집하고, Gemini 2.0 Flash를 통해 페이스 분석 및 기술적 피드백을 제공하는 풀스택 AI 비서 시스템 구축을 목표로 한다.

사용자는 **Streamlit 무료 웹 대시보드**를 통해 URL로 시각화 리포트를 조회하고, **텔레그램 양방향 챗봇(Long Polling)**을 통해 실시간 대화 및 맞춤형 코칭을 받는다.

---

## 🛡️ 기존 인프라 상속 및 무료 티어 방어 제약 사항 (Fact)

### 1. Gemini 2.0 Flash 무료 쿼터 사수 (20 RPD 제한)

* 단순 누적 거리 조회, 오늘 운동 여부 확인, 대시보드 URL 요청 등 데이터 조회성 질문은 **파이썬 내부 함수가 DB를 조회하여 즉각 자체 응답(Gemini 호출 0회)** 한다.
* 고차원 심박수 구간 분석, 하프마라톤 1시간 50분 완주를 위한 페이스 전략 제안 등 전문 코칭 질의에 한해서만 Gemini API를 1-Turn 호출하여 토큰과 일일 한도를 철저히 수호한다.

### 2. Streamlit Cloud 무료 호스팅

* 분석 리포트 및 구간별 페이스 차트 시각화를 위한 웹 대시보드를 구축하고,
* Streamlit Community Cloud를 통해 100% 무료 퍼블릭 URL을 생성하여 텔레그램으로 자동 전달한다.

### 3. OAuth 2.0 토큰 리프레시 가드

* 스트라바 API의 억세스 토큰 만료(6시간)에 완벽 대응하기 위해,
* 데이터 수집 및 질의 체인이 가동될 때마다 `refresh_token`을 활용해 새 토큰을 자동 갱신하는 래퍼 모듈을 필수 상속한다.

### 4. 중복 브리핑 방어 및 싱크 블랙박스

* 이미 분석 완료된 액티비티 ID는 `data/processed_activities.json`에 영구 기록하여 동일 액티비티에 대한 알림 도배를 차단한다.
* 작업 완료 시마다 본 파일(`TODO.md`)의 진척도를 갱신하여 AI 간 컨텍스트 단절을 방어한다.

---

# 2. 🗂️ Phase 1: 기반 인프라 이식 및 환경 셋팅

## [x] 2.1 독립 프로젝트 디렉토리 환경 구축

* `garmin-marathon-ai` 독립 폴더 생성 및 파이썬 가상환경(`.venv`) 셋팅
* `requirements.txt` 핵심 패키지 정의 및 설치

```text
google-genai
python-dotenv
requests
pandas
python-telegram-bot==20.*
streamlit
```

### `.env` 파일 변수 정의

```env
STRAVA_CLIENT_ID="내 스트라바 클라이언트 ID"
STRAVA_CLIENT_SECRET="내 스트라바 시크릿 키"
STRAVA_REFRESH_TOKEN="내 스트라바 리프레시 토큰"

GEMINI_API_KEY="내 제미나이 API 키"

TELEGRAM_BOT_TOKEN="내 텔레그램 봇 토큰"
TELEGRAM_CHAT_ID="내 텔레그램 개인 챗 ID"
```

---

## [x] 2.2 인프라 공통 모듈 상속 (기존 코인 봇 유산 활용)

### `app/config.py`

* `pydantic` 또는 기본 `os.environ` 기반 환경변수 유효성 체크 로더 이식
* 변수 누락 시 `ValueError` 발생 및 가동 차단

### `app/notifiers/telegram_notifier.py`

* 4,096자 초과 메시지 발생 시
* 줄바꿈(`\n`) 기준으로 안전하게 청킹하여 분할 발송하는 모듈 이식

### `app/storage/history_manager.py`

* `data/processed_activities.json` 파일이 없을 시 빈 배열(`[]`)로 자동 초기화
* 발송 완료된 스트라바 `activity_id`를 읽고 쓰는 로직 무결성 완공

---

# 3. 🚀 Phase 2: 세부 모듈 및 파이프라인 빌드업

## 📌 Milestone 1: 스트라바 API 클라이언트 패키지 구축

### [x] `app/client/strava_client.py` - 토큰 리프레시 구현

```http
POST https://www.strava.com/oauth/token
```

* 새로운 `access_token`을 동적 발급받는 `refresh_access_token()` 함수 구현

---

### [x] `app/client/strava_client.py` - 최신 액티비티 덤프 구현

```http
GET https://www.strava.com/api/v3/athlete/activities
```

### 파싱 대상 스키마

* `id`
* `name`
* `distance`
* `moving_time`
* `total_elevation_gain`
* `type`
* `start_date_local`
* `average_heartrate`
* `max_heartrate`

### 요구사항

* 딕셔너리 리스트 형태 반환
* `type == "Run"` 데이터만 필터링하는 방어 코드 장착

---

## 📌 Milestone 2: 텔레그램 양방향 실시간 챗봇 비서 엔진 완공

### [x] `app/bot/chatbot_handler.py` - Polling 리스너 가동

* `python-telegram-bot 20` 버전의 `ApplicationBuilder` 클래스를 활용
* 비동기(`async/await`) 챗봇 엔진 가동

---

### [x] `app/bot/chatbot_handler.py` - 스마트 라우터(Router) 구현

#### 무료 쿼터 방어 필수 정책

### `/start`, `/help`

* 기본 명령어 핸들러 장착

### 사용자가 "이번 주 총 거리" 입력 시

➡️ Gemini 호출 없이:

* pandas 기반 러닝 로그 합산
* 자체 텍스트 응답 반환

### 사용자가 "분석", "코칭 요청" 입력 시

➡️ 최근 미분석 러닝 로그 바인딩 후:

* `coach_agent.py` 전달
* Gemini 정밀 분석 결과 반환

### 사용자가 "대시보드" 입력 시

➡️ 배포된 Streamlit 퍼블릭 URL:

* 텔레그램 링크 카드로 즉시 반환

---

## 📌 Milestone 3: 주간 분석 코칭 에이전트 및 프롬프트 하드코딩

### [x] `app/agents/coach_agent.py`

## 전문 러닝 코치 페르소나 주입

### 목표 컨텍스트 강제 하드코딩

* 목표:

  * 하프마라톤 1시간 50분 이내 완주
* 목표 평균 페이스:

  * `5분 12초/km`

### 구현 요구사항

* 실제 수집 페이스와 목표 페이스 비교 분석
* 평균 심박수 구간(Zone 1 ~ Zone 5) 기반 피드백
* 한글 + 이모지 기반 초가독성 포맷

### 핵심 함수

```python
generate_coaching_report(activity_data)
```

---

## 📌 Milestone 4: Streamlit 무료 웹 대시보드 시각화 및 배포

### [x] `app/dashboard.py` - 로컬 대시보드 UI 구축 (Phase 1)

### UI 요구사항

* 상단:

  * 주간 누적 거리
  * 평균 페이스
  * Metric 타일 배치

### 시각화 요구사항

```python
st.line_chart
```

* 일자별 러닝 거리 추이
* 일자별 페이스 추이 선그래프

---

### [x] `app/dashboard.py` - 대시보드 고도화 (Phase 2: AI 코칭 동적 바인딩)

#### 레이아웃 개편: [요약 메트릭 → 🤖 AI 기술 판단 → 📈 기술 지표 시각화]

* **섹션 1: 오늘 액티비티 메트릭**
  * 오늘 러닝의 [거리(km), 평균 페이스, 평균 심박수, 운동 시간] st.columns(4) 타일 배치
  * 목표 페이스(5'12") 대비 delta 증감 수치 동적 표시 (초록/빨강)

* **섹션 2: 🤖 AI 러닝 코치 기술 판단**
  * `data/coaching_reports.json`에서 최신 액티비티 ID 매핑 데이터 로드
  * AI 종합 판정, 페이스 적정성, 심박수 피드백, 다음 훈련 제안을 st.success/info/warning으로 시각화

* **섹션 3: ⏱️ 구간별 페이스 및 심박수 추이**
  * strava_client.py의 get_activity_detail(activity_id) 함수로 splits_metric 조회
  * 1km당 페이스 변화 선그래프 표시
  * 심박수 추이 선그래프 표시 (병렬 차트)

---

### [x] Streamlit Community Cloud 무료 웹 배포

* GitHub 레포지토리 커밋
* Streamlit Cloud 연동
* 상시 접근 가능한 무료 퍼블릭 URL 확보 완료

---

## 📌 Milestone 5: 메인 조립 및 자율 예외 처리 통합

### [x] `app/marathon_main.py` 허브 구동 파일 구현

## 실행 플로우

```text
앱 실행
→ strava_client 가동
→ 새로운 러닝 세션 발견
→ processed_activities.json 중복 검사
→ coach_agent 호출
→ 분석서 생성
→ 텔레그램 자동 알림 발송
→ 히스토리 갱신 완료
```

---

## 실시간 챗봇 병렬 구동 요구사항

* 텔레그램 챗봇 리스너 비동기 루프를 백그라운드에서 상시 구동
* 사용자 실시간 질문에 실시간 대응 체제 구축

---

# 4. 🚀 Phase 3: Railway Cron Job 배포 (실시간 자동화)

## [x] 3.1 Cron Job 파이프라인 구축

### `app/cron_pipeline.py`

* 5분마다 자동 실행되는 Strava 폴링
* 새 러닝 감지 → Gemini 분석 → 텔레그램 알림
* Webhook 불필요 (안정적인 폴링 방식)

---

## [x] 3.2 Railway Cron Job 배포

* Schedule: `*/5 * * * *` (5분마다)
* 환경변수 설정 (Strava, Gemini, Telegram)
* 무료 티어 내에서 24/7 운영

---

## ✅ 최종 완성

### 아키텍처

```
📊 Streamlit Cloud (대시보드)
   ↑
   └─ 주간 거리, 페이스 추이, 최근 기록

⚙️ Railway Cron Job (파이프라인)
   ├─ 5분마다 자동 실행
   ├─ Strava API (최근 러닝 조회)
   ├─ Gemini 2.0 Flash (AI 분석)
   └─ Telegram (실시간 알림)

💾 GitHub (데이터)
   └─ processed_activities.json
```

### 비용

* Streamlit Cloud: 무료
* Railway: $0 (월 $5 크레딧 충분)
* Gemini: 무료 쿼터 (20 RPD)
* Telegram: 무료

**총 월 비용: $0 ✅**

### 작동 흐름

```
러닝 완료
  ↓
Strava 업로드
  ↓
Railway Cron (5분마다 확인)
  ↓
새 러닝 감지
  ↓
Gemini 페이스/심박 분석
  ↓
🔔 텔레그램 즉시 알림
  ↓
히스토리 갱신
```

