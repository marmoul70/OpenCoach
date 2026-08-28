"""Localisation d'un effort continu dans les streams."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from math import isfinite
from numbers import Real

from opencoach.models import (
    ActivityDetail,
    ActivityStream,
)


@dataclass(frozen=True, slots=True)
class ContinuousEffortWindow:
    """Fenêtre d'effort continu reconstruite."""

    start_time_seconds: float
    end_time_seconds: float
    duration_seconds: float

    distance_m: float | None

    average_speed_mps: float | None
    average_watts: float | None
    average_cadence: float | None

    average_heart_rate: float | None
    max_heart_rate: float | None

    continuity_ratio: float | None
    confidence: float


@dataclass(frozen=True, slots=True)
class _Series:
    times: tuple[float, ...]
    values: tuple[float, ...]
    prefix_sum: tuple[float, ...]

    def mean(
        self,
        start: float,
        end: float,
    ) -> float | None:
        left, right = self.bounds(
            start,
            end,
        )

        if right <= left:
            return None

        return (
            self.prefix_sum[right]
            - self.prefix_sum[left]
        ) / (
            right - left
        )

    def maximum(
        self,
        start: float,
        end: float,
    ) -> float | None:
        left, right = self.bounds(
            start,
            end,
        )

        if right <= left:
            return None

        return max(
            self.values[left:right]
        )

    def bounds(
        self,
        start: float,
        end: float,
    ) -> tuple[int, int]:
        return (
            bisect_left(
                self.times,
                start,
            ),
            bisect_left(
                self.times,
                end,
            ),
        )


@dataclass(frozen=True, slots=True)
class _ContinuitySeries:
    times: tuple[float, ...]
    prefix_active: tuple[int, ...]

    def ratio(
        self,
        start: float,
        end: float,
    ) -> float | None:
        left = bisect_left(
            self.times,
            start,
        )

        right = bisect_left(
            self.times,
            end,
        )

        count = right - left

        if count <= 0:
            return None

        active = (
            self.prefix_active[right]
            - self.prefix_active[left]
        )

        return active / count


def locate_continuous_effort_window(
    activity_detail: ActivityDetail,
    *,
    target_duration_seconds: float,
    minimum_active_speed_mps: float = 1.0,
) -> ContinuousEffortWindow | None:
    """Localise l'effort continu le plus probable.

    Le moteur ne dépend d'aucun lap fournisseur.

    La durée recherchée vient de la prescription.
    La localisation vient ensuite des streams réalisés.

    Pour un effort maximal continu, la vitesse constitue
    le signal principal. Watts et cadence renforcent
    la confiance lorsqu'ils sont disponibles.

    La FC est mesurée mais n'est pas utilisée pour placer
    directement la fenêtre à cause de son inertie.
    """

    if target_duration_seconds <= 0:
        raise ValueError(
            "target_duration_seconds doit être positif."
        )

    time_stream = (
        activity_detail.streams.time
    )

    if time_stream is None:
        return None

    raw_times = _valid_times(
        time_stream
    )

    if len(raw_times) < 2:
        return None

    activity_start = raw_times[0]
    activity_end = raw_times[-1]

    if (
        activity_end
        - activity_start
        < target_duration_seconds
    ):
        return None

    speed = _prepare_series(
        time_stream,
        activity_detail.streams.velocity_smooth,
    )

    watts = _prepare_series(
        time_stream,
        activity_detail.streams.watts,
    )

    cadence = _prepare_series(
        time_stream,
        activity_detail.streams.cadence,
    )

    heart_rate = _prepare_series(
        time_stream,
        activity_detail.streams.heartrate,
    )

    distance = _prepare_series(
        time_stream,
        activity_detail.streams.distance,
    )

    continuity = _prepare_continuity(
        time_stream,
        activity_detail.streams.velocity_smooth,
        minimum_active_speed_mps,
    )

    candidates = []

    for start in raw_times:
        end = (
            start
            + target_duration_seconds
        )

        if end > activity_end:
            break

        measured_distance = (
            _distance_between(
                distance,
                start,
                end,
            )
        )

        average_speed = (
            measured_distance
            / target_duration_seconds
            if measured_distance is not None
            else (
                speed.mean(
                    start,
                    end,
                )
                if speed is not None
                else None
            )
        )

        average_watts = (
            watts.mean(
                start,
                end,
            )
            if watts is not None
            else None
        )

        average_cadence = (
            cadence.mean(
                start,
                end,
            )
            if cadence is not None
            else None
        )

        continuity_ratio = (
            continuity.ratio(
                start,
                end,
            )
            if continuity is not None
            else None
        )

        if (
            average_speed is None
            and average_watts is None
            and average_cadence is None
        ):
            continue

        candidates.append(
            (
                start,
                end,
                measured_distance,
                average_speed,
                average_watts,
                average_cadence,
                continuity_ratio,
            )
        )

    if not candidates:
        return None

    maxima = {
        "speed": _maximum_available(
            candidate[3]
            for candidate in candidates
        ),
        "watts": _maximum_available(
            candidate[4]
            for candidate in candidates
        ),
        "cadence": _maximum_available(
            candidate[5]
            for candidate in candidates
        ),
    }

    scored = []

    for candidate in candidates:
        score = _candidate_score(
            average_speed=candidate[3],
            average_watts=candidate[4],
            average_cadence=candidate[5],
            continuity_ratio=candidate[6],
            maxima=maxima,
        )

        scored.append(
            (
                score,
                candidate,
            )
        )

    score, best = max(
        scored,
        key=lambda item: (
            item[0],
            item[1][3]
            if item[1][3] is not None
            else -1.0,
            -item[1][0],
        ),
    )

    (
        start,
        end,
        measured_distance,
        average_speed,
        average_watts,
        average_cadence,
        continuity_ratio,
    ) = best

    average_hr = (
        heart_rate.mean(
            start,
            end,
        )
        if heart_rate is not None
        else None
    )

    max_hr = (
        heart_rate.maximum(
            start,
            end,
        )
        if heart_rate is not None
        else None
    )

    return ContinuousEffortWindow(
        start_time_seconds=round(
            start,
            3,
        ),
        end_time_seconds=round(
            end,
            3,
        ),
        duration_seconds=round(
            target_duration_seconds,
            3,
        ),
        distance_m=_rounded(
            measured_distance,
            3,
        ),
        average_speed_mps=_rounded(
            average_speed,
            6,
        ),
        average_watts=_rounded(
            average_watts,
            3,
        ),
        average_cadence=_rounded(
            average_cadence,
            3,
        ),
        average_heart_rate=_rounded(
            average_hr,
            3,
        ),
        max_heart_rate=_rounded(
            max_hr,
            3,
        ),
        continuity_ratio=_rounded(
            continuity_ratio,
            4,
        ),
        confidence=round(
            score,
            4,
        ),
    )


def _candidate_score(
    *,
    average_speed: float | None,
    average_watts: float | None,
    average_cadence: float | None,
    continuity_ratio: float | None,
    maxima: dict[str, float | None],
) -> float:
    """Combine les preuves disponibles sans exiger leur présence."""

    signals = (
        (
            average_speed,
            maxima["speed"],
            0.65,
        ),
        (
            average_watts,
            maxima["watts"],
            0.20,
        ),
        (
            average_cadence,
            maxima["cadence"],
            0.10,
        ),
        (
            continuity_ratio,
            1.0,
            0.05,
        ),
    )

    numerator = 0.0
    denominator = 0.0

    for value, maximum, weight in signals:
        if (
            value is None
            or maximum is None
            or maximum <= 0
        ):
            continue

        normalized = min(
            1.0,
            max(
                0.0,
                value / maximum,
            ),
        )

        numerator += (
            normalized
            * weight
        )

        denominator += weight

    if denominator <= 0:
        return 0.0

    return (
        numerator
        / denominator
    )


def _prepare_series(
    time_stream: ActivityStream,
    metric_stream: ActivityStream | None,
) -> _Series | None:
    if metric_stream is None:
        return None

    times = []
    values = []

    previous_time = None

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
            previous_time is not None
            and time_value <= previous_time
        ):
            continue

        times.append(
            time_value
        )

        values.append(
            value
        )

        previous_time = time_value

    if not times:
        return None

    prefix = [0.0]
    running = 0.0

    for value in values:
        running += value
        prefix.append(
            running
        )

    return _Series(
        times=tuple(times),
        values=tuple(values),
        prefix_sum=tuple(prefix),
    )


def _prepare_continuity(
    time_stream: ActivityStream,
    speed_stream: ActivityStream | None,
    minimum_speed: float,
) -> _ContinuitySeries | None:
    if speed_stream is None:
        return None

    times = []
    active = []

    previous_time = None

    for raw_time, raw_speed in zip(
        time_stream.data,
        speed_stream.data,
        strict=False,
    ):
        time_value = _number(
            raw_time
        )

        speed = _number(
            raw_speed
        )

        if (
            time_value is None
            or speed is None
        ):
            continue

        if (
            previous_time is not None
            and time_value <= previous_time
        ):
            continue

        times.append(
            time_value
        )

        active.append(
            1
            if speed >= minimum_speed
            else 0
        )

        previous_time = time_value

    if not times:
        return None

    prefix = [0]
    running = 0

    for value in active:
        running += value
        prefix.append(
            running
        )

    return _ContinuitySeries(
        times=tuple(times),
        prefix_active=tuple(prefix),
    )


def _distance_between(
    distance: _Series | None,
    start: float,
    end: float,
) -> float | None:
    if distance is None:
        return None

    start_value = _interpolate(
        distance,
        start,
    )

    end_value = _interpolate(
        distance,
        end,
    )

    if (
        start_value is None
        or end_value is None
    ):
        return None

    result = (
        end_value
        - start_value
    )

    if result < 0:
        return None

    return result


def _interpolate(
    series: _Series,
    target: float,
) -> float | None:
    times = series.times
    values = series.values

    if (
        target < times[0]
        or target > times[-1]
    ):
        return None

    index = bisect_left(
        times,
        target,
    )

    if (
        index < len(times)
        and times[index] == target
    ):
        return values[index]

    if index == 0:
        return values[0]

    if index >= len(times):
        return values[-1]

    before = index - 1

    t0 = times[before]
    t1 = times[index]

    v0 = values[before]
    v1 = values[index]

    if t1 <= t0:
        return None

    ratio = (
        target - t0
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


def _valid_times(
    stream: ActivityStream,
) -> tuple[float, ...]:
    result = []

    previous = None

    for raw_value in stream.data:
        value = _number(
            raw_value
        )

        if value is None:
            continue

        if (
            previous is not None
            and value <= previous
        ):
            continue

        result.append(
            value
        )

        previous = value

    return tuple(result)


def _maximum_available(
    values,
) -> float | None:
    valid = [
        value
        for value in values
        if value is not None
    ]

    if not valid:
        return None

    return max(valid)


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


def _rounded(
    value: float | None,
    digits: int,
) -> float | None:
    if value is None:
        return None

    return round(
        value,
        digits,
    )
