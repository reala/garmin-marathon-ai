import json
from google import genai
from app.config import get

_TARGET_PACE_SEC = 5 * 60 + 12  # 5분 12초/km
_TARGET_FINISH_MIN = 110         # 1시간 50분

_HR_ZONES = [
    (0, 114, "Zone 1 (회복)"),
    (115, 133, "Zone 2 (유산소)"),
    (134, 152, "Zone 3 (템포)"),
    (153, 171, "Zone 4 (역치)"),
    (172, 999, "Zone 5 (최대)"),
]


def _zone_label(hr: float | None) -> str:
    if hr is None:
        return "측정 없음"
    for lo, hi, label in _HR_ZONES:
        if lo <= hr <= hi:
            return label
    return "알 수 없음"


def _pace_str(seconds_per_km: float) -> str:
    m, s = divmod(int(seconds_per_km), 60)
    return f"{m}분 {s:02d}초/km"


def _parse_structured_report(response_text: str) -> dict:
    """Gemini 응답에서 구조화된 데이터 추출."""
    lines = response_text.split("\n")
    report = {
        "종합_판정": "",
        "페이스_적정성": "",
        "심박수_구간_피드백": "",
        "다음_훈련_제안": "",
        "목표_달성률": ""
    }

    current_section = None
    for line in lines:
        line = line.strip()
        if not line:
            continue

        if "종합" in line or "판정" in line:
            current_section = "종합_판정"
        elif "페이스" in line or "속도" in line:
            current_section = "페이스_적정성"
        elif "심박" in line or "심장" in line:
            current_section = "심박수_구간_피드백"
        elif "훈련" in line or "다음" in line:
            current_section = "다음_훈련_제안"
        elif "목표" in line or "달성" in line:
            current_section = "목표_달성률"
        elif current_section:
            report[current_section] += line + " "

    for key in report:
        report[key] = report[key].strip()[:200]

    return report


def _build_prompt(activity: dict) -> str:
    distance_km = (activity.get("distance") or 0) / 1000
    moving_time_sec = activity.get("moving_time") or 0
    pace_sec = (moving_time_sec / distance_km) if distance_km > 0 else 0
    pace_diff = pace_sec - _TARGET_PACE_SEC
    diff_sign = "느림" if pace_diff > 0 else "빠름"

    avg_hr = activity.get("average_heartrate")
    max_hr = activity.get("max_heartrate")

    pace_judgment = "오버페이스 ⚡" if pace_diff < -30 else "처짐 🐌" if pace_diff > 30 else "적정 ✅"

    return f"""당신은 10년 경력의 전문 러닝 코치입니다.
아래 러닝 데이터를 분석하고, 하프마라톤 1시간 50분 완주를 위한 맞춤 피드백을 제공하세요.

## 🎯 목표
- 완주 목표: 하프마라톤 1시간 50분 ({_TARGET_FINISH_MIN}분) 이내
- 목표 평균 페이스: {_pace_str(_TARGET_PACE_SEC)}

## 📊 이번 러닝 데이터
- 이름: {activity.get('name', '러닝')}
- 날짜: {activity.get('start_date_local', '알 수 없음')}
- 거리: {distance_km:.2f} km
- 러닝 시간: {moving_time_sec // 60}분 {moving_time_sec % 60}초
- 실제 평균 페이스: {_pace_str(pace_sec)} (목표 대비 {abs(pace_diff):.0f}초 {diff_sign})
- 고도 상승: {activity.get('total_elevation_gain', 0)} m
- 평균 심박수: {avg_hr if avg_hr else '측정 없음'} bpm → {_zone_label(avg_hr)}
- 최대 심박수: {max_hr if max_hr else '측정 없음'} bpm

## 🔍 페이스 판정
현재 페이스가 목표 대비 "{pace_judgment}"인 상황입니다. 기술적으로 냉정하게 평가하고 피드백하세요.

## 📝 분석 요청 (한글, 이모지, 400자 이내)
1. 종합 판정: 이 러닝의 전체 평가
2. 페이스 적정성: 오버페이스/처짐/적정 판정 및 이유
3. 심박수 피드백: 구간 분석 및 훈련 효율성
4. 다음 훈련 제안: 개선할 구체적 포인트 2가지
5. 목표 달성률: 1시간 50분 완주까지 현재 위치 평가"""


def generate_coaching_report(activity: dict) -> tuple[str, dict]:
    """Gemini로 코칭 리포트 생성 및 구조화된 데이터 동시 리턴.

    Returns:
        (텔레그램용_텍스트, 구조화된_JSON_딕셔너리)
    """
    client = genai.Client(api_key=get("GEMINI_API_KEY"))
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=_build_prompt(activity),
    )

    text_report = response.text
    structured_data = _parse_structured_report(text_report)
    structured_data["activity_id"] = activity.get("id")
    structured_data["activity_name"] = activity.get("name", "러닝")
    structured_data["거리_km"] = round((activity.get("distance") or 0) / 1000, 2)
    structured_data["평균_페이스"] = _pace_str((activity.get("moving_time") or 0) / ((activity.get("distance") or 1) / 1000) if (activity.get("distance") or 0) > 0 else 0)
    structured_data["평균_심박수"] = activity.get("average_heartrate")

    return text_report, structured_data
