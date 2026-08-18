from datetime import date, timedelta
from statistics import median
from typing import Callable

from opencoach.models import WellnessDay

from .models import (
    MetricBaseline,
    ReadinessBaseline,
)


def calculate_readiness_baseline(
    wellness_days: list[WellnessDay],
    *,
    current_date: date,
    window_days: int,
    minimum_samples: int,
) -> ReadinessBaseline:
    """Calcule les baselines personnelles précédant la journée courante.

    La journée courante est volontairement exclue afin que la mesure
    évaluée ne modifie pas sa propre référence.
    """

    if window_days <= 0:
        raise ValueError(
            "window_days doit être supérieur à zéro."
        )

    if minimum_samples <= 0:
        raise ValueError(
            "minimum_samples doit être supérieur à zéro."
        )

    end_date = current_date - timedelta(
        days=1,
    )

    start_date = current_date - timedelta(
        days=window_days,
    )

    historical_days = [
        wellness
        for wellness in wellness_days
        if (
            start_date
            <= wellness.date
            <= end_date
        )
    ]

    return ReadinessBaseline(
        start_date=start_date,
        end_date=end_date,
        hrv=_build_metric_baseline(
            historical_days,
            lambda day: day.hrv,
            minimum_samples,
        ),
        resting_hr=_build_metric_baseline(
            historical_days,
            lambda day: (
                float(day.resting_hr)
                if day.resting_hr is not None
                else None
            ),
            minimum_samples,
        ),
        sleep_seconds=_build_metric_baseline(
            historical_days,
            lambda day: (
                float(day.sleep_seconds)
                if day.sleep_seconds is not None
                else None
            ),
            minimum_samples,
        ),
        sleep_score=_build_metric_baseline(
            historical_days,
            lambda day: day.sleep_score,
            minimum_samples,
        ),
    )


def _build_metric_baseline(
    wellness_days: list[WellnessDay],
    extractor: Callable[
        [WellnessDay],
        float | None,
    ],
    minimum_samples: int,
) -> MetricBaseline:
    values = [
        value
        for wellness in wellness_days
        if (
            value := extractor(
                wellness
            )
        )
        is not None
    ]

    if not values:
        return MetricBaseline(
            median=None,
            sample_count=0,
            reliable=False,
        )

    return MetricBaseline(
        median=float(
            median(values)
        ),
        sample_count=len(values),
        reliable=(
            len(values)
            >= minimum_samples
        ),
    )
