import requests
from app.config import get

_TOKEN_URL = "https://www.strava.com/oauth/token"
_ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"

_ACTIVITY_FIELDS = [
    "id",
    "name",
    "distance",
    "moving_time",
    "total_elevation_gain",
    "type",
    "start_date_local",
    "average_heartrate",
    "max_heartrate",
]


def refresh_access_token() -> str:
    """Strava refresh_token으로 새 access_token 발급."""
    resp = requests.post(
        _TOKEN_URL,
        data={
            "client_id": get("STRAVA_CLIENT_ID"),
            "client_secret": get("STRAVA_CLIENT_SECRET"),
            "refresh_token": get("STRAVA_REFRESH_TOKEN"),
            "grant_type": "refresh_token",
        },
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def get_recent_activities(per_page: int = 30) -> list[dict]:
    """최신 러닝 액티비티 목록 반환 (type==Run 필터 적용)."""
    token = refresh_access_token()
    resp = requests.get(
        _ACTIVITIES_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": per_page},
        timeout=10,
    )
    resp.raise_for_status()

    activities = []
    for item in resp.json():
        if item.get("type") != "Run":
            continue
        activities.append({k: item.get(k) for k in _ACTIVITY_FIELDS})

    return activities
