import json
import os
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "processed_activities.json"
_COACHING_FILE = Path(__file__).resolve().parents[2] / "data" / "coaching_reports.json"


def _load() -> list[int]:
    if not _DATA_FILE.exists():
        _DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        _save([])
        return []
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(ids: list[int]) -> None:
    with open(_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ids, f, indent=2)


def _load_coaching() -> dict:
    if not _COACHING_FILE.exists():
        _COACHING_FILE.parent.mkdir(parents=True, exist_ok=True)
        _save_coaching({})
        return {}
    with open(_COACHING_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_coaching(data: dict) -> None:
    with open(_COACHING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_processed(activity_id: int) -> bool:
    return activity_id in _load()


def mark_processed(activity_id: int) -> None:
    ids = _load()
    if activity_id not in ids:
        ids.append(activity_id)
        _save(ids)


def get_all_processed() -> list[int]:
    return _load()


def save_coaching_report(activity_id: int, report_data: dict) -> None:
    """코칭 분석 결과를 coaching_reports.json에 저장."""
    data = _load_coaching()
    data[str(activity_id)] = report_data
    _save_coaching(data)


def get_coaching_report(activity_id: int) -> dict | None:
    """특정 액티비티의 코칭 리포트 조회."""
    data = _load_coaching()
    return data.get(str(activity_id))


def get_latest_coaching_report() -> tuple[int, dict] | None:
    """최신 코칭 리포트 조회 (activity_id, report_data)."""
    data = _load_coaching()
    if not data:
        return None
    latest_id = max(int(aid) for aid in data.keys())
    return latest_id, data[str(latest_id)]
