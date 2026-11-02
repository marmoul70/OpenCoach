from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import Activity

SPORT_NAMES = {
    100: "Course extérieure",
    101: "Course sur tapis",
    102: "Trail",
    103: "Piste",
    104: "Randonnée",
    200: "Vélo",
    203: "Gravel",
    204: "VTT",
    300: "Natation piscine",
    301: "Eau libre",
    402: "Renforcement musculaire",
    1005: "Tennis",
}


def upsert_coros_activity(db: Session, profile_id: UUID, record: dict[str, Any]) -> bool:
    label_id = record.get("labelId") or record.get("label_id")
    if label_id is None:
        return False
    timestamp = record.get("startTimestamp") or record.get("start_at")
    try:
        if isinstance(timestamp, (int, float)):
            start_at = datetime.fromtimestamp(timestamp / (1000 if timestamp > 10_000_000_000 else 1), timezone.utc).replace(tzinfo=None)
        elif isinstance(timestamp, str):
            start_at = datetime.fromisoformat(timestamp.replace("Z", "+00:00")).replace(tzinfo=None)
        else:
            return False
    except (OverflowError, OSError, ValueError):
        return False

    sport_code = record.get("sportType")
    sport_type = SPORT_NAMES.get(sport_code, str(sport_code or "COROS"))
    duration = record.get("workoutTime") or record.get("durationSeconds") or record.get("elapsed_time_seconds")
    try:
        duration_seconds = int(duration) if duration is not None else None
    except (TypeError, ValueError):
        duration_seconds = None

    activity = db.scalar(select(Activity).where(
        Activity.provider == "coros",
        Activity.provider_activity_id == str(label_id),
    ))
    if activity is None:
        activity = Activity(
            athlete_profile_id=profile_id,
            provider="coros",
            provider_activity_id=str(label_id),
            name=str(record.get("name") or sport_type),
            sport_type=sport_type,
            start_at=start_at,
        )
        db.add(activity)
    activity.name = str(record.get("name") or sport_type)
    activity.sport_type = sport_type
    activity.start_at = start_at
    activity.elapsed_time_seconds = duration_seconds
    return True
