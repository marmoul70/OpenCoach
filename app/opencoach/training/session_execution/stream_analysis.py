"""Primitives d'analyse temporelle des streams d'activité."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Real
from typing import Sequence


StreamSample = int | float | None


@dataclass(frozen=True, slots=True)
class StreamRangeAnalysis:
    """Temps exploitable passé dans une plage numérique."""

    valid_duration_seconds: float
    in_range_duration_seconds: float
    in_range_percent: float | None

    @property
    def has_data(self) -> bool:
        return (
            self.valid_duration_seconds
            > 0
            and self.in_range_percent is not None
        )


def calculate_time_in_range(
    time_values: Sequence[StreamSample],
    metric_values: Sequence[StreamSample],
    *,
    minimum: float,
    maximum: float,
) -> StreamRangeAnalysis:
    """Calcule le temps réellement passé dans une cible.

    La valeur de l'échantillon ``i`` est considérée comme
    représentative de l'intervalle temporel allant de
    ``time[i]`` à ``time[i + 1]``.

    Les intervalles ne disposant pas d'une valeur exploitable
    sont exclus du dénominateur au lieu d'être considérés
    hors cible.
    """

    if maximum < minimum:
        raise ValueError(
            "La borne maximale ne peut pas être "
            "inférieure à la borne minimale."
        )

    common_length = min(
        len(time_values),
        len(metric_values),
    )

    if common_length < 2:
        return StreamRangeAnalysis(
            valid_duration_seconds=0.0,
            in_range_duration_seconds=0.0,
            in_range_percent=None,
        )

    valid_duration = 0.0
    in_range_duration = 0.0

    for index in range(
        common_length - 1
    ):
        current_time = _number(
            time_values[index]
        )

        next_time = _number(
            time_values[index + 1]
        )

        metric = _number(
            metric_values[index]
        )

        if (
            current_time is None
            or next_time is None
            or metric is None
        ):
            continue

        duration = (
            next_time
            - current_time
        )

        if duration <= 0:
            continue

        valid_duration += duration

        if minimum <= metric <= maximum:
            in_range_duration += duration

    if valid_duration <= 0:
        percent = None
    else:
        percent = (
            in_range_duration
            / valid_duration
            * 100.0
        )

    return StreamRangeAnalysis(
        valid_duration_seconds=round(
            valid_duration,
            3,
        ),
        in_range_duration_seconds=round(
            in_range_duration,
            3,
        ),
        in_range_percent=(
            round(percent, 2)
            if percent is not None
            else None
        ),
    )


def _number(
    value: object,
) -> float | None:
    if (
        not isinstance(value, Real)
        or isinstance(value, bool)
    ):
        return None

    result = float(value)

    if not isfinite(result):
        return None

    return result
