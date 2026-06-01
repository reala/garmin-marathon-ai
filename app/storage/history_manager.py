import json
import os
from pathlib import Path

_DATA_FILE = Path(__file__).resolve().parents[2] / "data" / "processed_activities.json"


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


def is_processed(activity_id: int) -> bool:
    return activity_id in _load()


def mark_processed(activity_id: int) -> None:
    ids = _load()
    if activity_id not in ids:
        ids.append(activity_id)
        _save(ids)


def get_all_processed() -> list[int]:
    return _load()
