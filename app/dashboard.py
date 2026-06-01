import pandas as pd
import streamlit as st

from app.client.strava_client import get_recent_activities

_TARGET_PACE_SEC = 5 * 60 + 12


def _pace_str(sec: float) -> str:
    m, s = divmod(int(sec), 60)
    return f"{m}'{s:02d}\""


def _build_df(activities: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(activities)
    df["start_date_local"] = pd.to_datetime(df["start_date_local"])
    df["distance_km"] = df["distance"] / 1000
    df["pace_sec"] = df.apply(
        lambda r: r["moving_time"] / r["distance_km"] if r["distance_km"] > 0 else None,
        axis=1,
    )
    df["pace_label"] = df["pace_sec"].apply(lambda s: _pace_str(s) if s else "N/A")
    df = df.sort_values("start_date_local")
    return df


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

    # ── 상단 메트릭 타일 ──────────────────────────────────────────────
    week_start = pd.Timestamp.now().to_period("W").start_time
    weekly = df[df["start_date_local"] >= week_start]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("이번 주 누적 거리", f"{weekly['distance_km'].sum():.1f} km")
    col2.metric("이번 주 러닝 횟수", f"{len(weekly)} 회")

    avg_pace = df["pace_sec"].mean()
    target_diff = avg_pace - _TARGET_PACE_SEC
    col3.metric(
        "평균 페이스",
        _pace_str(avg_pace),
        delta=f"목표 대비 {abs(target_diff):.0f}초 {'느림' if target_diff > 0 else '빠름'}",
        delta_color="inverse",
    )
    avg_hr = df["average_heartrate"].dropna().mean()
    col4.metric("평균 심박수", f"{avg_hr:.0f} bpm" if not pd.isna(avg_hr) else "N/A")

    st.divider()

    # ── 시각화 ────────────────────────────────────────────────────────
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("📈 일자별 러닝 거리 추이")
        chart_df = df.set_index("start_date_local")[["distance_km"]]
        st.line_chart(chart_df, y="distance_km", use_container_width=True)

    with col_b:
        st.subheader("⏱️ 일자별 페이스 추이")
        pace_df = df.set_index("start_date_local")[["pace_sec"]].dropna()
        st.line_chart(pace_df, y="pace_sec", use_container_width=True)
        st.caption("※ 낮을수록 빠른 페이스 (단위: 초/km)")

    st.divider()

    # ── 최근 러닝 목록 ────────────────────────────────────────────────
    st.subheader("📋 최근 러닝 기록")
    display = df[["start_date_local", "name", "distance_km", "pace_label", "average_heartrate", "total_elevation_gain"]].copy()
    display.columns = ["날짜", "이름", "거리(km)", "페이스", "평균 심박(bpm)", "고도(m)"]
    display["날짜"] = display["날짜"].dt.strftime("%Y-%m-%d")
    display["거리(km)"] = display["거리(km)"].round(2)
    st.dataframe(display.sort_values("날짜", ascending=False), use_container_width=True)


if __name__ == "__main__":
    main()
