from __future__ import annotations

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import Activity

ATHLETE_TIMEZONE = ZoneInfo("Europe/Paris")

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
    # Le résumé COROS et le détail d'activité sont conservés séparément dans
    # le snapshot brut. Fusionner les champs du détail pour normaliser aussi
    # les métriques qu'il expose, sans écraser les valeurs du résumé.
    detail = record.get("activity_detail")
    detail_values = detail if isinstance(detail, dict) else {}
    detail_data = detail_values.get("data")
    if isinstance(detail_data, dict):
        detail_values = {**detail_data, **detail_values}
    record = {**detail_values, **record}
    label_id = record.get("labelId") or record.get("label_id")
    if label_id is None:
        return False
    timestamp = record.get("startTimestamp") or record.get("start_at")
    try:
        if isinstance(timestamp, (int, float)):
            timestamp_seconds = timestamp / (
                1000 if timestamp > 10_000_000_000 else 1
            )
            start_at_aware = datetime.fromtimestamp(
                timestamp_seconds,
                timezone.utc,
            )
        elif isinstance(timestamp, str):
            parsed_timestamp = datetime.fromisoformat(
                timestamp.replace("Z", "+00:00")
            )
            start_at_aware = (
                parsed_timestamp.replace(tzinfo=timezone.utc)
                if parsed_timestamp.tzinfo is None
                else parsed_timestamp.astimezone(timezone.utc)
            )
        else:
            return False
        start_at = start_at_aware.replace(tzinfo=None)
        start_at_local = (
            start_at_aware.astimezone(ATHLETE_TIMEZONE)
            .replace(tzinfo=None)
        )
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
            start_at_local=start_at_local,
        )
        db.add(activity)
    activity.name = str(record.get("name") or sport_type)
    activity.sport_type = sport_type
    activity.start_at = start_at
    activity.start_at_local = start_at_local
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
                activity.moving_time_seconds = parsed_duration
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
