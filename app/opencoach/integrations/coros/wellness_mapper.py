"""Mapping conservateur des snapshots santé COROS vers le modèle Wellness."""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any

from opencoach.models import WellnessDay


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _flatten(value: Any, *, prefix: str = "") -> dict[str, Any]:
    """Aplati les objets imbriqués sans écraser les premières valeurs rencontrées."""
    flattened: dict[str, Any] = {}
    if isinstance(value, dict):
        for raw_key, child in value.items():
            key = str(raw_key)
            flattened.setdefault(_key(key), child)
            if isinstance(child, dict):
                for nested_key, nested_value in _flatten(child).items():
                    flattened.setdefault(nested_key, nested_value)
    return flattened


def _number(data: dict[str, Any], aliases: tuple[str, ...]) -> float | None:
    for alias in aliases:
        value = data.get(_key(alias))
        if value is None or isinstance(value, bool):
            continue
        if isinstance(value, str):
            value = value.strip().replace(",", ".")
            if not value:
                continue
        try:
            result = float(value)
        except (TypeError, ValueError, OverflowError):
            continue
        if math.isfinite(result):
            return result
    return None


def _integer(data: dict[str, Any], aliases: tuple[str, ...]) -> int | None:
    value = _number(data, aliases)
    if value is None or not value.is_integer() or value < 0:
        return None
    return int(value)


def _datetime(data: dict[str, Any]) -> datetime | None:
    for alias in ("updatedAt", "updated", "lastUpdated", "updateTime"):
        value = data.get(_key(alias))
        if not isinstance(value, str) or not value.strip():
            continue
        try:
            return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError:
            continue
    return None


def map_coros_wellness(
    category: str,
    payload: dict[str, Any],
    wellness_date: date,
) -> WellnessDay:
    """Convertit un snapshot COROS en WellnessDay.

    Le mapping est volontairement permissif sur les noms de champs, mais
    conservateur sur les valeurs : une métrique non présente reste None.
    Les alias devront être enrichis à partir de payloads COROS réels validés.
    """
    data = _flatten(payload)

    resting_hr = _integer(data, (
        "restingHeartRate", "restingHr", "restHr", "resting_heart_rate",
        "restingHeartRateBpm", "rhr",
    ))
    hrv = _number(data, (
        "hrv", "hrvValue", "hrvMs", "rmssd", "hrvRmssd", "nightHrv",
        "averageHrv", "avgHrv",
    ))
    avg_sleeping_hr = _number(data, (
        "averageSleepingHeartRate", "avgSleepingHr", "sleepingHeartRate",
        "averageSleepHeartRate", "sleepAvgHr",
    ))
    sleep_seconds = _integer(data, (
        "sleepSeconds", "sleepDurationSeconds", "totalSleepSeconds",
        "totalSleepTimeSeconds", "sleepDuration",
    ))
    # Les durées exprimées en minutes ne sont converties que si le nom du
    # champ l'indique explicitement.
    if sleep_seconds is None:
        sleep_minutes = _number(data, (
            "sleepMinutes", "sleepDurationMinutes", "totalSleepMinutes",
        ))
        if sleep_minutes is not None and sleep_minutes >= 0:
            sleep_seconds = round(sleep_minutes * 60)

    sleep_score = _number(data, (
        "sleepScore", "sleep_score", "sleepQualityScore",
    ))
    sleep_quality = _integer(data, (
        "sleepQuality", "sleep_quality",
    ))
    spo2 = _number(data, (
        "spo2", "bloodOxygen", "bloodOxygenLevel", "oxygenSaturation",
        "averageSpo2",
    ))
    steps = _integer(data, (
        "steps", "stepCount", "dailySteps",
    ))
    fitness_ctl = _number(data, (
        "fitnessCtl", "ctl", "chronicTrainingLoad",
    ))
    fatigue_atl = _number(data, (
        "fatigueAtl", "atl", "acuteTrainingLoad",
    ))
    ramp_rate = _number(data, (
        "rampRate", "trainingLoadRampRate",
    ))

    return WellnessDay(
        provider="coros",
        date=wellness_date,
        fitness_ctl=fitness_ctl,
        fatigue_atl=fatigue_atl,
        ramp_rate=ramp_rate,
        resting_hr=resting_hr,
        hrv=hrv,
        sleep_seconds=sleep_seconds,
        sleep_score=sleep_score,
        sleep_quality=sleep_quality,
        avg_sleeping_hr=avg_sleeping_hr,
        spo2=spo2,
        steps=steps,
        provider_updated_at=_datetime(data),
    )
