import pandas as pd
import streamlit as st

from app.client.strava_client import get_recent_activities, get_activity_detail
from app.storage.history_manager import get_latest_coaching_report

_TARGET_PACE_SEC = 5 * 60 + 12


def _pace_str(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m}'{s:02d}\""


def _build_df(activities: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(activities)
    df["start_date_local"] = pd.to_datetime(df["start_date_local"]).dt.tz_localize(None)
    df["distance_km"] = df["distance"] / 1000
    df["pace_sec"] = df.apply(
        lambda r: r["moving_time"] / r["distance_km"] if r["distance_km"] > 0 else None,
        axis=1,
    )
    df["pace_label"] = df["pace_sec"].apply(lambda s: _pace_str(s) if s else "N/A")
    df = df.sort_values("start_date_local")
    return df


def _get_today_activity(df: pd.DataFrame) -> dict | None:
    """오늘의 액티비티 조회."""
    today = pd.Timestamp.now(tz=None).date()
    today_activities = df[df["start_date_local"].dt.date == today]
    if len(today_activities) > 0:
        return today_activities.iloc[-1].to_dict()
    return None


def _build_splits_chart(splits_metric: list) -> pd.DataFrame | None:
    """splits_metric을 DataFrame으로 변환."""
    if not splits_metric or len(splits_metric) == 0:
        return None

    data = []
    for idx, split in enumerate(splits_metric, 1):
        pace_sec = split.get("moving_time", 0) / split.get("distance", 1) if split.get("distance", 0) > 0 else 0
        data.append({
            "분할": f"{idx}km",
            "페이스_초": pace_sec,
            "거리_m": split.get("distance", 0),
            "심박": split.get("average_heartrate"),
        })

    return pd.DataFrame(data)


def main():
    st.set_page_config(page_title="마라톤 AI 대시보드", page_icon="🏃", layout="wide")
    st.title("🏃 마라톤 AI 코치 대시보드")
    st.caption("목표: 하프마라톤 1시간 50분 완주 | 목표 페이스 5'12\"/km")

    with st.spinner("Strava 데이터 불러오는 중..."):
        try:
            activities = get_recent_activities(per_page=50)
        except Exception as e:
            st.error(f"Strava API 오류: {e}")
            return

    if not activities:
        st.warning("러닝 기록이 없습니다.")
        return

    df = _build_df(activities)

    # ── 섹션 1: 오늘 액티비티 메트릭 ──────────────────────────────────
    st.subheader("📊 오늘의 러닝 기록")
    today_activity = _get_today_activity(df)

    if today_activity:
        distance_km = today_activity.get("distance_km", 0)
        moving_time_sec = today_activity.get("moving_time", 0)
        avg_hr = today_activity.get("average_heartrate")
        max_hr = today_activity.get("max_heartrate")

        pace_sec = (moving_time_sec / distance_km) if distance_km > 0 else 0
        pace_diff = pace_sec - _TARGET_PACE_SEC
        pace_label = _pace_str(pace_sec)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("거리", f"{distance_km:.2f} km")
        col2.metric(
            "평균 페이스",
            pace_label,
            delta=f"{abs(pace_diff):.0f}초 {'느림' if pace_diff > 0 else '빠름'}",
            delta_color="inverse",
        )
        col3.metric("평균 심박수", f"{avg_hr:.0f} bpm" if avg_hr else "N/A")

        running_time_min = int(moving_time_sec // 60)
        running_time_sec = int(moving_time_sec % 60)
        col4.metric("운동 시간", f"{running_time_min}'{running_time_sec:02d}\"")

        st.divider()

        # ── 섹션 2: 🤖 AI 러닝 코치 기술 판단 ────────────────────────────
        st.subheader("🤖 AI 러닝 코치 기술 판단")

        coaching_result = get_latest_coaching_report()
        if coaching_result:
            _, report_data = coaching_result
            col_a, col_b = st.columns([1, 1])

            with col_a:
                if report_data.get("종합_판정"):
                    st.success(f"**종합 판정**\n\n{report_data['종합_판정']}")

                if report_data.get("페이스_적정성"):
                    st.info(f"**페이스 적정성**\n\n{report_data['페이스_적정성']}")

            with col_b:
                if report_data.get("심박수_구간_피드백"):
                    st.info(f"**심박수 피드백**\n\n{report_data['심박수_구간_피드백']}")

                if report_data.get("다음_훈련_제안"):
                    st.warning(f"**다음 훈련 제안**\n\n{report_data['다음_훈련_제안']}")

            if report_data.get("목표_달성률"):
                st.info(f"**목표 달성률**\n\n{report_data['목표_달성률']}")

        else:
            st.info("🔄 AI 분석 대기 중... (Railway Cron 실행 후 최대 5분 소요)")

        st.divider()

        # ── 섹션 3: 분할 페이스 및 심박수 추이 ──────────────────────────
        st.subheader("⏱️ 구간별 페이스 변화 및 심박수 추이")

        today_activity_id = today_activity.get("id")
        if today_activity_id:
            detail = get_activity_detail(today_activity_id)
            if detail and detail.get("splits_metric"):
                splits_df = _build_splits_chart(detail["splits_metric"])
                if splits_df is not None and len(splits_df) > 0:
                    col_chart1, col_chart2 = st.columns(2)

                    with col_chart1:
                        st.line_chart(
                            splits_df.set_index("분할")["페이스_초"],
                            use_container_width=True,
                        )
                        st.caption("낮을수록 빠른 페이스 (단위: 초/km)")

                    with col_chart2:
                        st.line_chart(
                            splits_df.set_index("분할")["심박"],
                            use_container_width=True,
                        )
                        st.caption("심박수 추이 (bpm)")
                else:
                    st.info("구간별 데이터가 아직 준비 중입니다.")
            else:
                st.info("구간별 데이터가 아직 준비 중입니다.")

    else:
        st.info("📅 오늘 러닝 기록이 없습니다.")

    st.divider()

    # ── 섹션 4: 주간 누적 거리 및 통계 ──────────────────────────────────
    st.subheader("📈 주간 통계")
    week_start = pd.Timestamp.now().normalize().to_period("W").start_time
    weekly = df[df["start_date_local"].dt.date >= week_start.date()]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("이번 주 누적 거리", f"{weekly['distance_km'].sum():.1f} km")
    col2.metric("이번 주 러닝 횟수", f"{len(weekly)} 회")

    avg_pace = df["pace_sec"].mean()
    target_diff = avg_pace - _TARGET_PACE_SEC
    col3.metric(
        "전체 평균 페이스",
        _pace_str(avg_pace),
        delta=f"목표 대비 {abs(target_diff):.0f}초 {'느림' if target_diff > 0 else '빠름'}",
        delta_color="inverse",
    )
    avg_hr = df["average_heartrate"].dropna().mean()
    col4.metric("전체 평균 심박수", f"{avg_hr:.0f} bpm" if not pd.isna(avg_hr) else "N/A")

    st.divider()

    # ── 섹션 5: 최근 러닝 목록 ──────────────────────────────────────────
    st.subheader("📋 최근 러닝 기록")
    display = df[["start_date_local", "name", "distance_km", "pace_label", "average_heartrate", "total_elevation_gain"]].copy()
    display.columns = ["날짜", "이름", "거리(km)", "페이스", "평균 심박(bpm)", "고도(m)"]
    display["날짜"] = display["날짜"].dt.strftime("%Y-%m-%d")
    display["거리(km)"] = display["거리(km)"].round(2)
    st.dataframe(display.sort_values("날짜", ascending=False), use_container_width=True)


if __name__ == "__main__":
    main()
