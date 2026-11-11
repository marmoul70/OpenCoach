from __future__ import annotations

import math
import re
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



def _report_number(text: str, pattern: str) -> float | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    if not match:
        return None
    try:
        value = float(match.group(1).replace(",", "."))
    except (TypeError, ValueError, OverflowError):
        return None
    return value if math.isfinite(value) and value >= 0 else None


def _report_duration(text: str, label: str) -> int | None:
    match = re.search(
        rf"^\\s*{re.escape(label)}\\s*:\\s*(?:(\\d+)\\s*h\\s*)?(?:(\\d+)\\s*:\\s*)?(\\d+)\\s*(?:min)?\\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    if minutes >= 60 or seconds >= 60:
        return None
    return hours * 3600 + minutes * 60 + seconds


def _pace_to_speed(text: str, label: str) -> float | None:
    match = re.search(
        rf"^\\s*{re.escape(label)}\\s*:\\s*(\\d{{1,2}}):(\\d{{2}})\\s*/km\\s*$",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not match:
        return None
    minutes, seconds = int(match.group(1)), int(match.group(2))
    total_seconds = minutes * 60 + seconds
    if total_seconds <= 0 or seconds >= 60:
        return None
    return 1000 / total_seconds


def _parse_activity_report(value: Any) -> dict[str, float | int]:
    """Parse uniquement les métriques explicitement présentes dans le rapport COROS."""
    if not isinstance(value, str) or not value.strip():
        return {}
    parsed: dict[str, float | int] = {}
    workout = _report_duration(value, "Workout Time")
    total = _report_duration(value, "Total Time")
    if workout is not None:
        parsed["moving_time_seconds"] = workout
    if total is not None:
        parsed["elapsed_time_seconds"] = total
    mappings = {
        "distance_m": (r"^\\s*Distance\\s*:\\s*([\\d.,]+)\\s*km", 1000),
        "average_heart_rate": (r"^\\s*Average Heart Rate\\s*:\\s*([\\d.,]+)\\s*bpm", 1),
        "average_cadence": (r"^\\s*Average Cadence\\s*:\\s*([\\d.,]+)\\s*spm", 1),
        "average_stride_m": (r"^\\s*Average Stride Length\\s*:\\s*([\\d.,]+)\\s*m", 1),
        "average_power_w": (r"^\\s*Average Power\\s*:\\s*([\\d.,]+)\\s*W", 1),
        "calories": (r"^\\s*Calories\\s*:\\s*([\\d.,]+)\\s*kcal", 1),
        "training_load": (r"^\\s*Training Load\\s*:\\s*([\\d.,]+)", 1),
    }
    for field, (pattern, multiplier) in mappings.items():
        value_number = _report_number(value, pattern)
        if value_number is not None:
            parsed[field] = round(value_number * multiplier, 3)
    elevation = re.search(
        r"^\\s*Elevation Gain\\s*/\\s*Loss\\s*:\\s*([\\d.,]+)\\s*m\\s*/\\s*([\\d.,]+)\\s*m",
        value,
        re.IGNORECASE | re.MULTILINE,
    )
    if elevation:
        parsed["elevation_gain_m"] = float(elevation.group(1).replace(",", "."))
        parsed["elevation_loss_m"] = float(elevation.group(2).replace(",", "."))
    average_speed = _pace_to_speed(value, "Average Pace")
    if average_speed is not None:
        parsed["average_speed_mps"] = average_speed
    moving_speed = _pace_to_speed(value, "Moving Average Pace")
    if moving_speed is not None:
        parsed["moving_average_speed_mps"] = moving_speed
    return parsed


def upsert_coros_activity(db: Session, profile_id: UUID, record: dict[str, Any]) -> bool:
    # Le résumé COROS et le détail d'activité sont conservés séparément dans
    # le snapshot brut. Fusionner les champs du détail pour normaliser aussi
    # les métriques qu'il expose, sans écraser les valeurs du résumé.
    detail = record.get("activity_detail")
    detail_values = detail if isinstance(detail, dict) else {}
    detail_data = detail_values.get("data")
    if isinstance(detail_data, dict):
        detail_values = {**detail_data, **detail_values}
    report_values = _parse_activity_report(detail)
    record = {**report_values, **detail_values, **record}
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

    # Le rapport détaillé COROS fournit les durées moving/elapsed explicitement.
    # Elles priment sur workoutTime du résumé, dont la sémantique peut varier.
    for attribute in ("moving_time_seconds", "elapsed_time_seconds"):
        value = report_values.get(attribute)
        if value is not None:
            setattr(activity, attribute, value)

    # Les autres métriques du rapport complètent uniquement les champs absents
    # du résumé structuré ; aucune valeur déjà importée n'est écrasée.
    for attribute, value in report_values.items():
        if attribute in {"moving_time_seconds", "elapsed_time_seconds", "moving_average_speed_mps"}:
            continue
        if value is not None and getattr(activity, attribute, None) is None:
            setattr(activity, attribute, value)
    return True
