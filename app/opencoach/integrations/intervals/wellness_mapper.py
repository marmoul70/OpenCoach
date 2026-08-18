from datetime import date, datetime

from opencoach.integrations.intervals.errors import (
    IntervalsDataError,
)
from opencoach.models import WellnessDay


def map_intervals_wellness(
    data: dict,
) -> WellnessDay:
    """Convertit une journée Wellness Intervals.icu en modèle OpenCoach."""

    wellness_date = _required_date(
        data,
        "id",
    )

    provider_updated_at = _optional_datetime(
        data.get("updated"),
    )

    return WellnessDay(
        provider="intervals",
        date=wellness_date,
        fitness_ctl=data.get("ctl"),
        fatigue_atl=data.get("atl"),
        ramp_rate=data.get("rampRate"),
        resting_hr=data.get("restingHR"),
        hrv=data.get("hrv"),
        sleep_seconds=data.get("sleepSecs"),
        sleep_score=data.get("sleepScore"),
        sleep_quality=data.get("sleepQuality"),
        avg_sleeping_hr=data.get("avgSleepingHR"),
        spo2=data.get("spO2"),
        steps=data.get("steps"),
        provider_updated_at=provider_updated_at,
    )


def _required_date(
    data: dict,
    field: str,
) -> date:
    value = data.get(field)

    if not isinstance(value, str) or not value:
        raise IntervalsDataError(
            f"Champ Wellness obligatoire absent : {field}."
        )

    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise IntervalsDataError(
            f"Date Wellness invalide : {field}."
        ) from exc


def _optional_datetime(
    value: object,
) -> datetime | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise IntervalsDataError(
            "Date de mise à jour Wellness invalide."
        )

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )
    except ValueError as exc:
        raise IntervalsDataError(
            "Date de mise à jour Wellness invalide."
        ) from exc
