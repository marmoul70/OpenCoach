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

    sport_code = record.get("sportType") or record.get("sport_type")
    if isinstance(sport_code, str):
        normalized_sport = sport_code.strip()
        sport_type = normalized_sport or "COROS"
    else:
        sport_type = SPORT_NAMES.get(
            sport_code,
            f"COROS ({sport_code})" if sport_code is not None else "COROS",
        )
    duration = next((
        record[key]
        for key in ("workoutTime", "durationSeconds", "elapsed_time_seconds")
        if record.get(key) is not None
    ), None)
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
    distance = next((
        record[key]
        for key in ("distanceMeters", "distance_m")
        if record.get(key) is not None
    ), None)
    try:
        activity.distance_m = float(distance) if distance is not None else None
    except (TypeError, ValueError):
        activity.distance_m = None
    elevation = next((
        record[key]
        for key in ("totalAscent", "elevationGain", "elevation_gain_m")
        if record.get(key) is not None
    ), None)
    try:
        activity.elevation_gain_m = float(elevation) if elevation is not None else None
    except (TypeError, ValueError):
        activity.elevation_gain_m = None
    average_hr = next((
        record[key]
        for key in ("avgHr", "averageHeartRate", "average_heart_rate")
        if record.get(key) is not None
    ), None)
    try:
        activity.average_heart_rate = float(average_hr) if average_hr is not None else None
    except (TypeError, ValueError):
        activity.average_heart_rate = None
    max_hr = next((
        record[key]
        for key in ("maxHr", "maxHeartRate", "max_heart_rate")
        if record.get(key) is not None
    ), None)
    try:
        activity.max_heart_rate = float(max_hr) if max_hr is not None else None
    except (TypeError, ValueError):
        activity.max_heart_rate = None
    return True
