"""Mesure d'une répétition à partir de ses frontières réelles."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from math import isfinite
from numbers import Real

from opencoach.models import (
    ActivityDetail,
    ActivityStream,
)

from .repetition_boundary import (
    RefinedRepetitionBoundary,
)


@dataclass(frozen=True, slots=True)
class MeasuredRepetition:
    """Mesures réellement observées sur une fraction."""

    start_time_seconds: float
    end_time_seconds: float

    duration_seconds: float

    distance_m: float | None

    average_speed_mps: float | None

    average_heart_rate: float | None
    max_heart_rate: float | None

    average_cadence: float | None
    average_watts: float | None


def measure_refined_repetition(
    activity_detail: ActivityDetail,
    boundary: RefinedRepetitionBoundary,
) -> MeasuredRepetition:
    """Mesure les données réelles entre deux frontières."""

    start = boundary.start_time_seconds
    end = boundary.end_time_seconds

    if end <= start:
        raise ValueError(
            "La fin de répétition doit être "
            "postérieure au début."
        )

    distance = _distance_between(
        activity_detail,
        start,
        end,
    )

    duration = (
        end - start
    )

    average_speed = (
        distance / duration
        if (
            distance is not None
            and duration > 0
        )
        else _mean_metric(
            activity_detail.streams.time,
            activity_detail.streams.velocity_smooth,
            start,
            end,
        )
    )

    average_hr = _mean_metric(
        activity_detail.streams.time,
        activity_detail.streams.heartrate,
        start,
        end,
    )

    max_hr = _max_metric(
        activity_detail.streams.time,
        activity_detail.streams.heartrate,
        start,
        end,
    )

    average_cadence = _mean_metric(
        activity_detail.streams.time,
        activity_detail.streams.cadence,
        start,
        end,
    )

    average_watts = _mean_metric(
        activity_detail.streams.time,
        activity_detail.streams.watts,
        start,
        end,
    )

    return MeasuredRepetition(
        start_time_seconds=round(
            start,
            3,
        ),
        end_time_seconds=round(
            end,
            3,
        ),
        duration_seconds=round(
            duration,
            3,
        ),
        distance_m=(
            round(
                distance,
                3,
            )
            if distance is not None
            else None
        ),
        average_speed_mps=(
            round(
                average_speed,
                6,
            )
            if average_speed is not None
            else None
        ),
        average_heart_rate=(
            round(
                average_hr,
                3,
            )
            if average_hr is not None
            else None
        ),
        max_heart_rate=(
            round(
                max_hr,
                3,
            )
            if max_hr is not None
            else None
        ),
        average_cadence=(
            round(
                average_cadence,
                3,
            )
            if average_cadence is not None
            else None
        ),
        average_watts=(
            round(
                average_watts,
                3,
            )
            if average_watts is not None
            else None
        ),
    )


def _distance_between(
    activity_detail: ActivityDetail,
    start: float,
    end: float,
) -> float | None:
    time_stream = (
        activity_detail.streams.time
    )

    distance_stream = (
        activity_detail.streams.distance
    )

    if (
        time_stream is None
        or distance_stream is None
    ):
        return None

    series = _prepare_series(
        time_stream,
        distance_stream,
    )

    if series is None:
        return None

    start_distance = _interpolate(
        series,
        start,
    )

    end_distance = _interpolate(
        series,
        end,
    )

    if (
        start_distance is None
        or end_distance is None
    ):
        return None

    distance = (
        end_distance
        - start_distance
    )

    if distance < 0:
        return None

    return distance


def _mean_metric(
    time_stream: ActivityStream | None,
    metric_stream: ActivityStream | None,
    start: float,
    end: float,
) -> float | None:
    values = _metric_values(
        time_stream,
        metric_stream,
        start,
        end,
    )

    if not values:
        return None

    return (
        sum(values)
        / len(values)
    )


def _max_metric(
    time_stream: ActivityStream | None,
    metric_stream: ActivityStream | None,
    start: float,
    end: float,
) -> float | None:
    values = _metric_values(
        time_stream,
        metric_stream,
        start,
        end,
    )

    if not values:
        return None

    return max(values)


def _metric_values(
    time_stream: ActivityStream | None,
    metric_stream: ActivityStream | None,
    start: float,
    end: float,
) -> list[float]:
    if (
        time_stream is None
        or metric_stream is None
    ):
        return []

    result = []

    for raw_time, raw_value in zip(
        time_stream.data,
        metric_stream.data,
        strict=False,
    ):
        time_value = _number(
            raw_time
        )

        value = _number(
            raw_value
        )

        if (
            time_value is None
            or value is None
        ):
            continue

        if (
            start
            <= time_value
            < end
        ):
            result.append(
                value
            )

    return result


def _prepare_series(
    time_stream: ActivityStream,
    value_stream: ActivityStream,
) -> tuple[
    tuple[float, ...],
    tuple[float, ...],
] | None:
    times = []
    values = []

    previous_time = None
    previous_value = None

    for raw_time, raw_value in zip(
        time_stream.data,
        value_stream.data,
        strict=False,
    ):
        time_value = _number(
            raw_time
        )

        value = _number(
            raw_value
        )

        if (
            time_value is None
            or value is None
        ):
            continue

        if (
            previous_time is not None
            and time_value <= previous_time
        ):
            continue

        if (
            previous_value is not None
            and value < previous_value
        ):
            continue

        times.append(
            time_value
        )

        values.append(
            value
        )

        previous_time = time_value
        previous_value = value

    if len(times) < 2:
        return None

    return (
        tuple(times),
        tuple(values),
    )


def _interpolate(
    series: tuple[
        tuple[float, ...],
        tuple[float, ...],
    ],
    target_time: float,
) -> float | None:
    times, values = series

    if (
        target_time < times[0]
        or target_time > times[-1]
    ):
        return None

    index = bisect_left(
        times,
        target_time,
    )

    if index < len(times):
        if times[index] == target_time:
            return values[index]

    if index == 0:
        return values[0]

    if index >= len(times):
        return values[-1]

    before = (
        index - 1
    )

    t0 = times[before]
    t1 = times[index]

    v0 = values[before]
    v1 = values[index]

    if t1 <= t0:
        return None

    ratio = (
        target_time - t0
    ) / (
        t1 - t0
    )

    return (
        v0
        + ratio
        * (
            v1 - v0
        )
    )


def _number(
    value,
) -> float | None:
    if (
        not isinstance(
            value,
            Real,
        )
        or isinstance(value, bool)
    ):
        return None

    result = float(value)

    if not isfinite(result):
        return None

    return result
