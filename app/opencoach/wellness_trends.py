"""Calcul des tendances Wellness sur une fenêtre courte."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from statistics import fmean

from opencoach.models import WellnessDay


@dataclass(frozen=True, slots=True)
class WellnessTrendPoint:
    """Valeur Wellness datée."""

    date: date
    value: float


@dataclass(frozen=True, slots=True)
class WellnessMetricTrend:
    """Résumé statistique d'une métrique Wellness."""

    current: float | None
    average: float | None
    change_percent: float | None
    direction: str
    sample_count: int

    points: tuple[
        WellnessTrendPoint,
        ...
    ]


@dataclass(frozen=True, slots=True)
class WellnessTrends:
    """Tendances consolidées des métriques de forme."""

    start_date: date
    end_date: date
    days: int

    hrv: WellnessMetricTrend
    hrv_baseline: WellnessMetricTrend
    resting_hr: WellnessMetricTrend
    stress_avg: WellnessMetricTrend
    sleep_score: WellnessMetricTrend
    sleep_seconds: WellnessMetricTrend
    sleep_deep_seconds: WellnessMetricTrend
    sleep_light_seconds: WellnessMetricTrend
    sleep_rem_seconds: WellnessMetricTrend
    sleep_awake_seconds: WellnessMetricTrend
    fitness_ctl: WellnessMetricTrend
    fatigue_atl: WellnessMetricTrend


def build_wellness_trends(
    *,
    wellness_days: list[WellnessDay],
    start_date: date,
    end_date: date,
    days: int,
) -> WellnessTrends:
    """Construit les tendances depuis les journées disponibles."""

    return WellnessTrends(
        start_date=start_date,
        end_date=end_date,
        days=days,
        hrv=_metric_trend(wellness_days, "hrv"),
        hrv_baseline=_metric_trend(wellness_days, "hrv_baseline"),
        resting_hr=_metric_trend(wellness_days, "resting_hr"),
        stress_avg=_metric_trend(wellness_days, "stress_avg"),
        sleep_score=_metric_trend(
            wellness_days,
            "sleep_score",
        ),
        sleep_seconds=_metric_trend(wellness_days, "sleep_seconds"),
        sleep_deep_seconds=_metric_trend(wellness_days, "sleep_deep_seconds"),
        sleep_light_seconds=_metric_trend(wellness_days, "sleep_light_seconds"),
        sleep_rem_seconds=_metric_trend(wellness_days, "sleep_rem_seconds"),
        sleep_awake_seconds=_metric_trend(wellness_days, "sleep_awake_seconds"),
        fitness_ctl=_metric_trend(
            wellness_days,
            "fitness_ctl",
        ),
        fatigue_atl=_metric_trend(
            wellness_days,
            "fatigue_atl",
        ),
    )


def _metric_trend(
    wellness_days: list[WellnessDay],
    attribute: str,
) -> WellnessMetricTrend:
    points: list[
        WellnessTrendPoint
    ] = []

    for wellness in wellness_days:
        raw_value = getattr(
            wellness,
            attribute,
        )

        if raw_value is None:
            continue

        points.append(
            WellnessTrendPoint(
                date=wellness.date,
                value=float(
                    raw_value
                ),
            )
        )

    if not points:
        return WellnessMetricTrend(
            current=None,
            average=None,
            change_percent=None,
            direction="unknown",
            sample_count=0,
            points=(),
        )

    current = points[-1].value

    average = fmean(
        point.value
        for point in points
    )

    if average == 0:
        change_percent = None
        direction = "stable"
    else:
        change_percent = (
            (
                current
                - average
            )
            / abs(
                average
            )
            * 100.0
        )

        if change_percent > 2.0:
            direction = "up"
        elif change_percent < -2.0:
            direction = "down"
        else:
            direction = "stable"

    return WellnessMetricTrend(
        current=current,
        average=average,
        change_percent=(
            change_percent
        ),
        direction=direction,
        sample_count=len(
            points
        ),
        points=tuple(
            points
        ),
    )
