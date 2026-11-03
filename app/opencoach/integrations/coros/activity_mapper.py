from __future__ import annotations

import math
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
    activity = db.scalar(select(Activity).where(
        Activity.provider == "coros",
        Activity.provider_activity_id == str(label_id),
    ))
    # The current database uniqueness constraint is global per provider/id.
    # Never let an import for one profile mutate another profile's activity.
    if activity is not None and activity.athlete_profile_id != profile_id:
        return False
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
    duration = next((
        record[key]
        for key in ("workoutTime", "durationSeconds", "elapsed_time_seconds")
        if record.get(key) is not None
    ), None)
    if duration is not None:
        try:
            parsed_duration = int(duration)
            if not isinstance(duration, bool) and parsed_duration >= 0 and float(duration) == parsed_duration:
                activity.elapsed_time_seconds = parsed_duration
        except (TypeError, ValueError, OverflowError):
            pass

    metric_fields = {
        "distance_m": ("distanceMeters", "distance_m"),
        "elevation_gain_m": ("totalAscent", "elevationGain", "elevation_gain_m"),
        "average_heart_rate": ("avgHr", "averageHeartRate", "average_heart_rate"),
        "max_heart_rate": ("maxHr", "maxHeartRate", "max_heart_rate"),
        "average_speed_mps": ("average_speed_mps", "averageSpeedMps"),
        "calories": ("calories",),
    }
    for attribute, keys in metric_fields.items():
        value = next((record[key] for key in keys if record.get(key) is not None), None)
        if value is None or isinstance(value, bool):
            continue
        try:
            parsed_value = float(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(parsed_value) and parsed_value >= 0:
            setattr(activity, attribute, parsed_value)
    return True
