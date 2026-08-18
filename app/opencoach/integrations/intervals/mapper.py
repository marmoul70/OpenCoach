from datetime import datetime

from opencoach.integrations.intervals.errors import (
    IntervalsDataError,
)
from opencoach.models import Activity


def map_intervals_activity(
    data: dict,
) -> Activity:
    """Convertit une activité Intervals.icu en activité OpenCoach."""

    provider_activity_id = _required_string(
        data,
        "id",
    )
    name = _required_string(
        data,
        "name",
    )
    sport_type = _required_string(
        data,
        "type",
    )
    start_at = _required_datetime(
        data,
        "start_date",
    )

    start_at_local = _optional_datetime(
        data.get("start_date_local"),
    )

    return Activity(
        provider="intervals",
        provider_activity_id=provider_activity_id,
        source=data.get("source"),
        source_file_name=data.get("external_id"),
        name=name,
        sport_type=sport_type,
        start_at=start_at,
        start_at_local=start_at_local,
        device_name=data.get("device_name"),
        elapsed_time_seconds=data.get("elapsed_time"),
        moving_time_seconds=data.get("moving_time"),
        distance_m=data.get("distance"),
        elevation_gain_m=data.get("total_elevation_gain"),
        elevation_loss_m=data.get("total_elevation_loss"),
        average_speed_mps=data.get("average_speed"),
        max_speed_mps=data.get("max_speed"),
        average_heart_rate=data.get("average_heartrate"),
        max_heart_rate=data.get("max_heartrate"),
        lactate_threshold_heart_rate=data.get("lthr"),
        athlete_max_heart_rate=data.get("athlete_max_hr"),
        average_cadence=data.get("average_cadence"),
        average_stride_m=data.get("average_stride"),
        average_stance_time_ms=data.get(
            "average_stance_time"
        ),
        average_vertical_oscillation_mm=data.get(
            "average_vertical_oscillation"
        ),
        average_power_w=data.get("icu_average_watts"),
        average_altitude_m=data.get("average_altitude"),
        min_altitude_m=data.get("min_altitude"),
        max_altitude_m=data.get("max_altitude"),
        average_temperature_c=data.get("average_temp"),
        min_temperature_c=data.get("min_temp"),
        max_temperature_c=data.get("max_temp"),
        calories=data.get("calories"),
        training_load=data.get("icu_training_load"),
        fitness_ctl=data.get("icu_ctl"),
        fatigue_atl=data.get("icu_atl"),
        hr_load=data.get("hr_load"),
        intensity=data.get("icu_intensity"),
        feel=data.get("feel"),
    )


def _required_string(
    data: dict,
    field: str,
) -> str:
    value = data.get(field)

    if not isinstance(value, str) or not value.strip():
        raise IntervalsDataError(
            f"Champ Intervals.icu obligatoire absent : {field}."
        )

    return value.strip()


def _required_datetime(
    data: dict,
    field: str,
) -> datetime:
    value = data.get(field)

    if not isinstance(value, str) or not value:
        raise IntervalsDataError(
            f"Champ Intervals.icu obligatoire absent : {field}."
        )

    try:
        return _parse_datetime(value)
    except ValueError as exc:
        raise IntervalsDataError(
            f"Date Intervals.icu invalide : {field}."
        ) from exc


def _optional_datetime(
    value: object,
) -> datetime | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise IntervalsDataError(
            "Date Intervals.icu locale invalide."
        )

    try:
        return _parse_datetime(value)
    except ValueError as exc:
        raise IntervalsDataError(
            "Date Intervals.icu locale invalide."
        ) from exc


def _parse_datetime(
    value: str,
) -> datetime:
    if value.endswith("Z"):
        value = f"{value[:-1]}+00:00"

    return datetime.fromisoformat(value)