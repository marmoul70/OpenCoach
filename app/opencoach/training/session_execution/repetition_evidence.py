"""Preuves multi-signal d'une répétition réalisée."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from math import isfinite
from numbers import Real

from opencoach.models import (
    ActivityDetail,
    ActivityStream,
)

from .interval_prescription import (
    IntervalSetPrescription,
)
from .stream_repetition_detection import (
    StreamRepetitionCandidate,
)


@dataclass(frozen=True, slots=True)
class RepetitionEvidence:
    """Preuves indépendantes confirmant une répétition."""

    duration_score: float | None
    speed_contrast_score: float | None
    cadence_score: float | None
    watts_score: float | None
    heart_rate_score: float | None

    confidence: float

    @property
    def available_signals(self) -> tuple[str, ...]:
        result = []

        for name, value in (
            (
                "duration",
                self.duration_score,
            ),
            (
                "speed_contrast",
                self.speed_contrast_score,
            ),
            (
                "cadence",
                self.cadence_score,
            ),
            (
                "watts",
                self.watts_score,
            ),
            (
                "heart_rate",
                self.heart_rate_score,
            ),
        ):
            if value is not None:
                result.append(name)

        return tuple(result)


@dataclass(frozen=True, slots=True)
class _MetricSeries:
    """Stream numérique préparé pour des requêtes temporelles."""

    times: tuple[float, ...]
    values: tuple[float, ...]

    prefix_sum: tuple[float, ...]

    def mean(
        self,
        start_time: float,
        end_time: float,
    ) -> float | None:
        left, right = self._bounds(
            start_time,
            end_time,
        )

        if right <= left:
            return None

        total = (
            self.prefix_sum[right]
            - self.prefix_sum[left]
        )

        return (
            total
            / (right - left)
        )

    def maximum(
        self,
        start_time: float,
        end_time: float,
    ) -> float | None:
        left, right = self._bounds(
            start_time,
            end_time,
        )

        if right <= left:
            return None

        # Le maximum est uniquement utilisé pour la FC,
        # sur une petite fenêtre autour de la fraction.
        return max(
            self.values[left:right]
        )

    def _bounds(
        self,
        start_time: float,
        end_time: float,
    ) -> tuple[int, int]:
        return (
            bisect_left(
                self.times,
                start_time,
            ),
            bisect_left(
                self.times,
                end_time,
            ),
        )


class RepetitionEvidenceScorer:
    """Scorer réutilisable préparant les streams une seule fois."""

    __slots__ = (
        "prescription",
        "speed",
        "cadence",
        "watts",
        "heart_rate",
    )

    def __init__(
        self,
        activity_detail: ActivityDetail,
        prescription: IntervalSetPrescription,
    ) -> None:
        self.prescription = prescription

        time_stream = (
            activity_detail.streams.time
        )

        self.speed = _prepare_series(
            time_stream,
            activity_detail.streams.velocity_smooth,
        )

        self.cadence = _prepare_series(
            time_stream,
            activity_detail.streams.cadence,
        )

        self.watts = _prepare_series(
            time_stream,
            activity_detail.streams.watts,
        )

        self.heart_rate = _prepare_series(
            time_stream,
            activity_detail.streams.heartrate,
        )

    def score(
        self,
        candidate: StreamRepetitionCandidate,
    ) -> RepetitionEvidence:
        duration_score = _duration_score(
            candidate,
            self.prescription,
        )

        recovery_window = (
            _recovery_window_seconds(
                self.prescription,
                candidate,
            )
        )

        speed_contrast_score = _contrast_score(
            series=self.speed,
            start_time=(
                candidate.start_time_seconds
            ),
            end_time=(
                candidate.end_time_seconds
            ),
            window_seconds=recovery_window,
            expected_gain_ratio=1.20,
        )

        cadence_score = _contrast_score(
            series=self.cadence,
            start_time=(
                candidate.start_time_seconds
            ),
            end_time=(
                candidate.end_time_seconds
            ),
            window_seconds=recovery_window,
            expected_gain_ratio=1.08,
        )

        watts_score = _contrast_score(
            series=self.watts,
            start_time=(
                candidate.start_time_seconds
            ),
            end_time=(
                candidate.end_time_seconds
            ),
            window_seconds=recovery_window,
            expected_gain_ratio=1.20,
        )

        heart_rate_score = (
            _heart_rate_response_score(
                series=self.heart_rate,
                start_time=(
                    candidate.start_time_seconds
                ),
                end_time=(
                    candidate.end_time_seconds
                ),
                window_seconds=recovery_window,
            )
        )

        confidence = _weighted_confidence(
            candidate.duration_seconds,
            duration_score=duration_score,
            speed_contrast_score=(
                speed_contrast_score
            ),
            cadence_score=cadence_score,
            watts_score=watts_score,
            heart_rate_score=(
                heart_rate_score
            ),
        )

        return RepetitionEvidence(
            duration_score=duration_score,
            speed_contrast_score=(
                speed_contrast_score
            ),
            cadence_score=cadence_score,
            watts_score=watts_score,
            heart_rate_score=(
                heart_rate_score
            ),
            confidence=confidence,
        )


def score_repetition_candidate(
    activity_detail: ActivityDetail,
    candidate: StreamRepetitionCandidate,
    prescription: IntervalSetPrescription,
) -> RepetitionEvidence:
    """Évalue un candidat isolé.

    Pour plusieurs candidats d'une même activité, utiliser
    ``RepetitionEvidenceScorer`` afin de préparer les streams
    une seule fois.
    """

    scorer = RepetitionEvidenceScorer(
        activity_detail,
        prescription,
    )

    return scorer.score(
        candidate
    )


def _prepare_series(
    time_stream: ActivityStream | None,
    metric_stream: ActivityStream | None,
) -> _MetricSeries | None:
    if (
        time_stream is None
        or metric_stream is None
    ):
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

    prefix_sum = [
        0.0
    ]

    running_sum = 0.0

    for value in values:
        running_sum += value

        prefix_sum.append(
            running_sum
        )

    return _MetricSeries(
        times=tuple(times),
        values=tuple(values),
        prefix_sum=tuple(
            prefix_sum
        ),
    )


def _duration_score(
    candidate: StreamRepetitionCandidate,
    prescription: IntervalSetPrescription,
) -> float | None:
    target = prescription.repetition_target

    if (
        target is not None
        and target.target_duration_min_seconds
        is not None
        and target.target_duration_max_seconds
        is not None
    ):
        minimum = (
            target.target_duration_min_seconds
        )

        maximum = (
            target.target_duration_max_seconds
        )

        actual = candidate.duration_seconds

        if minimum <= actual <= maximum:
            return 1.0

        boundary = (
            minimum
            if actual < minimum
            else maximum
        )

        error = (
            abs(actual - boundary)
            / boundary
        )

        return max(
            0.0,
            1.0 - error,
        )

    if (
        prescription.work_duration_seconds
        is not None
    ):
        expected = (
            prescription.work_duration_seconds
        )

        error = (
            abs(
                candidate.duration_seconds
                - expected
            )
            / expected
        )

        return max(
            0.0,
            1.0 - error,
        )

    return None


def _contrast_score(
    *,
    series: _MetricSeries | None,
    start_time: float,
    end_time: float,
    window_seconds: float,
    expected_gain_ratio: float,
) -> float | None:
    if series is None:
        return None

    work_mean = series.mean(
        start_time,
        end_time,
    )

    before_mean = series.mean(
        max(
            0.0,
            start_time - window_seconds,
        ),
        start_time,
    )

    after_mean = series.mean(
        end_time,
        end_time + window_seconds,
    )

    recovery_values = [
        value
        for value in (
            before_mean,
            after_mean,
        )
        if (
            value is not None
            and value > 0
        )
    ]

    if (
        work_mean is None
        or work_mean <= 0
        or not recovery_values
    ):
        return None

    recovery_mean = (
        sum(recovery_values)
        / len(recovery_values)
    )

    if recovery_mean <= 0:
        return None

    ratio = (
        work_mean
        / recovery_mean
    )

    if ratio <= 1.0:
        return 0.0

    if ratio >= expected_gain_ratio:
        return 1.0

    return _clamp01(
        (
            ratio - 1.0
        )
        / (
            expected_gain_ratio - 1.0
        )
    )


def _heart_rate_response_score(
    *,
    series: _MetricSeries | None,
    start_time: float,
    end_time: float,
    window_seconds: float,
) -> float | None:
    if series is None:
        return None

    baseline = series.mean(
        max(
            0.0,
            start_time - window_seconds,
        ),
        start_time,
    )

    response_end = (
        end_time
        + min(
            30.0,
            window_seconds,
        )
    )

    peak = series.maximum(
        start_time,
        response_end,
    )

    if (
        baseline is None
        or peak is None
        or baseline <= 0
    ):
        return None

    increase = (
        peak - baseline
    )

    if increase <= 0:
        return 0.0

    return _clamp01(
        increase / 15.0
    )


def _weighted_confidence(
    duration_seconds: float,
    *,
    duration_score: float | None,
    speed_contrast_score: float | None,
    cadence_score: float | None,
    watts_score: float | None,
    heart_rate_score: float | None,
) -> float:
    if duration_seconds <= 120.0:
        weights = {
            "duration": 0.30,
            "speed_contrast": 0.30,
            "cadence": 0.12,
            "watts": 0.18,
            "heart_rate": 0.10,
        }
    else:
        weights = {
            "duration": 0.25,
            "speed_contrast": 0.25,
            "cadence": 0.08,
            "watts": 0.17,
            "heart_rate": 0.25,
        }

    values = {
        "duration": duration_score,
        "speed_contrast": speed_contrast_score,
        "cadence": cadence_score,
        "watts": watts_score,
        "heart_rate": heart_rate_score,
    }

    numerator = 0.0
    denominator = 0.0

    for name, value in values.items():
        if value is None:
            continue

        weight = weights[name]

        numerator += (
            value * weight
        )

        denominator += weight

    if denominator <= 0:
        return 0.0

    return round(
        _clamp01(
            numerator
            / denominator
        ),
        4,
    )


def _recovery_window_seconds(
    prescription: IntervalSetPrescription,
    candidate: StreamRepetitionCandidate,
) -> float:
    recovery = (
        prescription.recovery_duration_seconds
    )

    if recovery is None:
        recovery = (
            candidate.duration_seconds
            * 0.75
        )

    return min(
        90.0,
        max(
            10.0,
            recovery,
        ),
    )


def _number(
    value: object,
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

    if not isfinite(
        result
    ):
        return None

    return result


def _clamp01(
    value: float,
) -> float:
    return min(
        1.0,
        max(
            0.0,
            value,
        ),
    )
