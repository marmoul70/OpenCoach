"""Mapping conservateur des rapports santé COROS vers WellnessDay.

Le MCP COROS renvoie certaines métriques sous forme de rapports texte.
Les données brutes restent conservées séparément dans CorosDailyData.
"""

from __future__ import annotations

import math
import re
from datetime import date, datetime
from typing import Any

from opencoach.models import WellnessDay


def _key(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _flatten(value: Any) -> dict[str, Any]:
    """Aplati les objets imbriqués sans écraser les premières valeurs."""
    flattened: dict[str, Any] = {}
    if isinstance(value, dict):
        for raw_key, child in value.items():
            flattened.setdefault(_key(str(raw_key)), child)
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
    """Convertit un payload JSON structuré COROS en WellnessDay."""
    data = _flatten(payload)
    resting_hr = _integer(data, (
        "restingHeartRate", "restingHr", "restHr", "resting_heart_rate",
        "restingHeartRateBpm", "rhr",
    ))
    hrv = _number(data, (
        "hrv", "hrvValue", "hrvMs", "rmssd", "hrvRmssd", "nightHrv",
        "averageHrv", "avgHrv",
    ))
    avg_hr = _number(data, ("averageHeartRate", "avgHeartRate", "avgHr", "averageHr"))
    min_hr = _number(data, ("minHeartRate", "minimumHeartRate", "minHr"))
    max_hr = _number(data, ("maxHeartRate", "maximumHeartRate", "maxHr"))
    avg_sleeping_hr = _number(data, (
        "averageSleepingHeartRate", "avgSleepingHr", "sleepingHeartRate",
        "averageSleepHeartRate", "sleepAvgHr",
    ))
    sleep_seconds = _integer(data, (
        "sleepSeconds", "sleepDurationSeconds", "totalSleepSeconds",
        "totalSleepTimeSeconds", "sleepDuration",
    ))
    if sleep_seconds is None:
        sleep_minutes = _number(data, (
            "sleepMinutes", "sleepDurationMinutes", "totalSleepMinutes",
        ))
        if sleep_minutes is not None and sleep_minutes >= 0:
            sleep_seconds = round(sleep_minutes * 60)

    return WellnessDay(
        provider="coros",
        date=wellness_date,
        fitness_ctl=_number(data, ("fitnessCtl", "ctl", "chronicTrainingLoad")),
        fatigue_atl=_number(data, ("fatigueAtl", "atl", "acuteTrainingLoad")),
        ramp_rate=_number(data, ("rampRate", "trainingLoadRampRate")),
        resting_hr=resting_hr,
        avg_hr=avg_hr,
        min_hr=min_hr,
        max_hr=max_hr,
        hrv=hrv,
        hrv_baseline=_number(data, ("hrvBaseline", "baselineHrv", "hrvBase")),
        stress_avg=_number(data, ("stressAvg", "averageStress", "avgStress")),
        sleep_seconds=sleep_seconds,
        sleep_score=_number(data, ("sleepScore", "sleep_score", "sleepQualityScore")),
        sleep_quality=_integer(data, ("sleepQuality", "sleep_quality")),
        sleep_deep_seconds=_integer(data, ("sleepDeepSeconds", "deepSleepSeconds")),
        sleep_light_seconds=_integer(data, ("sleepLightSeconds", "lightSleepSeconds")),
        sleep_rem_seconds=_integer(data, ("sleepRemSeconds", "remSleepSeconds")),
        sleep_awake_seconds=_integer(data, ("sleepAwakeSeconds", "awakeSleepSeconds")),
        avg_sleeping_hr=avg_sleeping_hr,
        min_sleeping_hr=_number(data, ("minSleepingHr", "minSleepHr")),
        max_sleeping_hr=_number(data, ("maxSleepingHr", "maxSleepHr")),
        spo2=_number(data, ("spo2", "bloodOxygen", "bloodOxygenLevel", "oxygenSaturation", "averageSpo2")),
        steps=_integer(data, ("steps", "stepCount", "dailySteps")),
        provider_updated_at=_datetime(data),
    )


def _report_text(payload: Any) -> str | None:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "text"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                nested = _report_text(value)
                if nested:
                    return nested
    return None


def _duration_seconds(value: str) -> int | None:
    match = re.search(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*min)?", value, re.IGNORECASE)
    if not match or not any(match.groups()):
        return None
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    if minutes >= 60:
        return None
    return hours * 3600 + minutes * 60


def _report_dates(text: str) -> list[tuple[date, str]]:
    matches = list(re.finditer(r"(?m)^\s*(?:---\s*)?(\d{4}-\d{2}-\d{2}|\d{8})(?:\s*:)?(?:\s*---)?\s*$", text))
    entries: list[tuple[date, str]] = []
    for index, match in enumerate(matches):
        raw_date = match.group(1)
        try:
            day = datetime.strptime(raw_date, "%Y%m%d").date() if len(raw_date) == 8 else date.fromisoformat(raw_date)
        except ValueError:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        entries.append((day, text[match.end():end]))
    return entries


def map_coros_wellness_report(
    category: str,
    payload: Any,
    fallback_date: date,
) -> list[WellnessDay]:
    """Extrait une journée Wellness par date contenue dans un rapport COROS.

    Seules les métriques dont la signification est explicite sont mappées.
    Les valeurs absentes restent None ; les rapports non reconnus ne créent
    pas artificiellement de journée.
    """
    text = _report_text(payload)
    if category == "heart_rate" and text:
        parsed_days: list[WellnessDay] = []
        pattern = re.compile(
            r"(?m)^\\s*(\\d{4}-\\d{2}-\\d{2}):\\s*"
            r"(\\d+(?:\\.\\d+)?)\\s*bpm\\s*"
            r"\\(\\s*Min:\\s*(\\d+(?:\\.\\d+)?),\\s*"
            r"Max:\\s*(\\d+(?:\\.\\d+)?)\\s*\\)"
        )
        for match in pattern.finditer(text):
            try:
                metric_date = date.fromisoformat(match.group(1))
            except ValueError:
                continue
            parsed_days.append(map_coros_wellness(
                category,
                {
                    "avgHr": float(match.group(2)),
                    "minHr": float(match.group(3)),
                    "maxHr": float(match.group(4)),
                },
                metric_date,
            ))
        if parsed_days:
            return parsed_days

    if not text:
        if isinstance(payload, dict):
            return [map_coros_wellness(category, payload, fallback_date)]
        return []

    # Les rapports quotidiens peuvent contenir plusieurs jours sous forme
    # de sous-sections --- YYYYMMDD ---.
    entries = _report_dates(text)
    if not entries and re.search(r"\b(?:Sleep Score|HRV Avg|Short-Term Load):", text):
        entries = [(fallback_date, text)]

    result: list[WellnessDay] = []
    header_resting_hr = re.search(r"Resting HR:\s*(\d+)\s*bpm", text, re.IGNORECASE)
    header_hrv_baseline = re.search(r"HRV Baseline:\s*(\d+(?:\.\d+)?)\s*ms", text, re.IGNORECASE)

    for day, block in entries:
        values: dict[str, Any] = {}
        if category == "daily_health":
            steps = re.search(r"Steps:\s*([\d,]+)", block, re.IGNORECASE)
            if steps:
                values["steps"] = int(steps.group(1).replace(",", ""))
            total_sleep = re.search(r"Total:\s*([^|\n]+)", block, re.IGNORECASE)
            if total_sleep:
                seconds = _duration_seconds(total_sleep.group(1))
                if seconds is not None:
                    values["sleepSeconds"] = seconds
            stress = re.search(r"Stress:\s*Avg\s*(\d+(?:\.\d+)?)", block, re.IGNORECASE)
            if stress:
                values["stressAvg"] = float(stress.group(1))
            for label, field in (
                ("Deep", "sleepDeepSeconds"),
                ("Light", "sleepLightSeconds"),
                ("REM", "sleepRemSeconds"),
                ("Awake", "sleepAwakeSeconds"),
            ):
                stage = re.search(rf"\b{label}:\s*([^|\n]+)", block, re.IGNORECASE)
                if stage:
                    seconds = _duration_seconds(stage.group(1))
                    if seconds is not None:
                        values[field] = seconds
            sleep_hr = re.search(r"Sleep HR:\s*Avg\s*(\d+(?:\.\d+)?)\s*bpm", block, re.IGNORECASE)
            if sleep_hr:
                values["avgSleepingHr"] = float(sleep_hr.group(1))
            sleep_hr_min = re.search(r"Sleep HR:.*?\bMin\s*(\d+(?:\.\d+)?)\s*bpm", block, re.IGNORECASE)
            if sleep_hr_min:
                values["minSleepingHr"] = float(sleep_hr_min.group(1))
            sleep_hr_max = re.search(r"Sleep HR:.*?\bMax\s*(\d+(?:\.\d+)?)\s*bpm", block, re.IGNORECASE)
            if sleep_hr_max:
                values["maxSleepingHr"] = float(sleep_hr_max.group(1))
            if day == fallback_date:
                if header_resting_hr:
                    values["restingHeartRate"] = int(header_resting_hr.group(1))
                if header_hrv_baseline:
                    values["hrvBaseline"] = float(header_hrv_baseline.group(1))

        elif category == "sleep":
            score = re.search(r"Sleep Score:\s*(\d+(?:\.\d+)?)", block, re.IGNORECASE)
            if score:
                values["sleepScore"] = float(score.group(1))
            main_sleep = re.search(r"Main Sleep \(asleep\):\s*([^\n]+)", block, re.IGNORECASE)
            daily_sleep = re.search(r"Daily Sleep:\s*([^\n]+)", block, re.IGNORECASE)
            duration = _duration_seconds((main_sleep or daily_sleep).group(1)) if (main_sleep or daily_sleep) else None
            if duration is not None:
                values["sleepSeconds"] = duration

        elif category == "hrv":
            average = re.search(r"HRV Avg:\s*(\d+(?:\.\d+)?)\s*ms", block, re.IGNORECASE)
            baseline = re.search(r"Baseline:\s*(\d+(?:\.\d+)?)\s*ms", block, re.IGNORECASE)
            if average:
                values["hrv"] = float(average.group(1))
            if baseline:
                values["hrvBaseline"] = float(baseline.group(1))

        elif category == "stress":
            average_stress = re.search(
                r"Average Stress:\s*(\d+(?:\.\d+)?)",
                block,
                re.IGNORECASE,
            )
            if average_stress:
                values["stressAvg"] = float(average_stress.group(1))

        elif category == "training_load":
            short = re.search(r"Short-Term Load:\s*(\d+(?:\.\d+)?)", block, re.IGNORECASE)
            long = re.search(r"Long-Term Load:\s*(\d+(?:\.\d+)?)", block, re.IGNORECASE)
            if short:
                values["fatigueAtl"] = float(short.group(1))
            if long:
                values["fitnessCtl"] = float(long.group(1))

        if values:
            result.append(map_coros_wellness(category, values, day))

    return result
