"""Détection déterministe des répétitions réalisées."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from opencoach.models import (
    ActivityDetail,
    ActivityInterval,
)

from .stream_repetition_detection import (
    detect_distance_repetitions_from_streams,
)
from .interval_prescription import (
    IntervalSetPrescription,
)


DEFAULT_DISTANCE_TOLERANCE_PERCENT = 20.0
DEFAULT_DURATION_TOLERANCE_PERCENT = 25.0


@dataclass(frozen=True, slots=True)
class ObservedRepetition:
    """Répétition réellement reconstruite."""

    start_index: int
    end_index: int

    start_time_seconds: float
    end_time_seconds: float

    distance_m: float | None
    duration_seconds: float

    average_speed_mps: float | None
    average_heart_rate: float | None
    max_heart_rate: float | None

    match_score: float


@dataclass(frozen=True, slots=True)
class RepetitionDetectionResult:
    """Résultat de détection d'un groupe de répétitions."""

    expected_repetitions: int
    repetitions: tuple[
        ObservedRepetition,
        ...,
    ]

    @property
    def detected_repetitions(self) -> int:
        return len(
            self.repetitions
        )

    @property
    def is_complete(self) -> bool:
        return (
            self.detected_repetitions
            == self.expected_repetitions
        )


@dataclass(frozen=True, slots=True)
class _Candidate:
    interval: ActivityInterval
    duration_seconds: float
    score: float


def detect_repetitions(
    activity_detail: ActivityDetail,
    prescription: IntervalSetPrescription,
    *,
    distance_tolerance_percent: float = (
        DEFAULT_DISTANCE_TOLERANCE_PERCENT
    ),
    duration_tolerance_percent: float = (
        DEFAULT_DURATION_TOLERANCE_PERCENT
    ),
) -> RepetitionDetectionResult:
    """Détecte les répétitions correspondant à la prescription.

    Les intervalles fournisseur sont uniquement des candidats.
    La sélection finale impose une chronologie sans chevauchement.
    """

    if distance_tolerance_percent < 0:
        raise ValueError(
            "La tolérance de distance "
            "ne peut pas être négative."
        )

    if prescription.work_distance_m is not None:
        stream_repetitions = (
            detect_distance_repetitions_from_streams(
                activity_detail,
                prescription,
            )
        )

        if stream_repetitions:
            return RepetitionDetectionResult(
                expected_repetitions=(
                    prescription.repetitions
                ),
                repetitions=tuple(
                    ObservedRepetition(
                        start_index=rep.start_index,
                        end_index=rep.end_index,
                        start_time_seconds=(
                            rep.start_time_seconds
                        ),
                        end_time_seconds=(
                            rep.end_time_seconds
                        ),
                        distance_m=rep.distance_m,
                        duration_seconds=(
                            rep.duration_seconds
                        ),
                        average_speed_mps=(
                            rep.average_speed_mps
                        ),
                        average_heart_rate=None,
                        max_heart_rate=None,
                        match_score=rep.match_score,
                    )
                    for rep in stream_repetitions
                ),
            )

    if duration_tolerance_percent < 0:
        raise ValueError(
            "La tolérance de durée "
            "ne peut pas être négative."
        )

    candidates = tuple(
        _build_candidate(
            interval,
            prescription,
            distance_tolerance_percent=(
                distance_tolerance_percent
            ),
            duration_tolerance_percent=(
                duration_tolerance_percent
            ),
        )
        for interval in activity_detail.intervals
    )

    candidates = tuple(
        candidate
        for candidate in candidates
        if candidate is not None
    )

    if not candidates:
        return RepetitionDetectionResult(
            expected_repetitions=(
                prescription.repetitions
            ),
            repetitions=(),
        )

    ordered = tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                candidate.interval.start_index,
                candidate.interval.end_index,
                -candidate.score,
            ),
        )
    )

    selected_indexes = _select_best_non_overlapping(
        ordered,
        maximum_count=prescription.repetitions,
    )

    repetitions = tuple(
        _to_observed_repetition(
            ordered[index]
        )
        for index in selected_indexes
    )

    return RepetitionDetectionResult(
        expected_repetitions=(
            prescription.repetitions
        ),
        repetitions=repetitions,
    )


def _build_candidate(
    interval: ActivityInterval,
    prescription: IntervalSetPrescription,
    *,
    distance_tolerance_percent: float,
    duration_tolerance_percent: float,
) -> _Candidate | None:
    duration = _interval_duration(
        interval
    )

    if duration <= 0:
        return None

    scores: list[float] = []

    if (
        prescription.work_distance_m
        is not None
    ):
        if interval.distance_m is None:
            return None

        distance_score = _exact_target_score(
            actual=interval.distance_m,
            expected=prescription.work_distance_m,
            tolerance_percent=(
                distance_tolerance_percent
            ),
        )

        if distance_score is None:
            return None

        scores.append(
            distance_score
        )

    target = prescription.repetition_target

    if (
        target is not None
        and target.target_duration_min_seconds
        is not None
        and target.target_duration_max_seconds
        is not None
    ):
        duration_score = _range_target_score(
            actual=duration,
            minimum=(
                target.target_duration_min_seconds
            ),
            maximum=(
                target.target_duration_max_seconds
            ),
            tolerance_percent=(
                duration_tolerance_percent
            ),
        )

        if duration_score is None:
            return None

        scores.append(
            duration_score
        )

    elif (
        prescription.work_duration_seconds
        is not None
    ):
        duration_score = _exact_target_score(
            actual=duration,
            expected=(
                prescription.work_duration_seconds
            ),
            tolerance_percent=(
                duration_tolerance_percent
            ),
        )

        if duration_score is None:
            return None

        scores.append(
            duration_score
        )

    if not scores:
        return None

    score = (
        sum(scores)
        / len(scores)
    )

    return _Candidate(
        interval=interval,
        duration_seconds=duration,
        score=round(
            score,
            6,
        ),
    )


def _select_best_non_overlapping(
    candidates: tuple[_Candidate, ...],
    *,
    maximum_count: int,
) -> tuple[int, ...]:
    """Sélectionne la meilleure combinaison non chevauchante.

    Optimisation lexicographique :
    1. maximiser le nombre de répétitions ;
    2. maximiser la somme des scores de correspondance.
    """

    @lru_cache(maxsize=None)
    def solve(
        index: int,
        previous_end: int,
        remaining: int,
    ) -> tuple[
        int,
        float,
        tuple[int, ...],
    ]:
        if (
            index >= len(candidates)
            or remaining <= 0
        ):
            return (
                0,
                0.0,
                (),
            )

        skip = solve(
            index + 1,
            previous_end,
            remaining,
        )

        candidate = candidates[index]

        take = (
            -1,
            -1.0,
            (),
        )

        if (
            candidate.interval.start_index
            > previous_end
        ):
            (
                next_count,
                next_score,
                next_indexes,
            ) = solve(
                index + 1,
                candidate.interval.end_index,
                remaining - 1,
            )

            take = (
                next_count + 1,
                next_score + candidate.score,
                (
                    index,
                    *next_indexes,
                ),
            )

        return _better_solution(
            take,
            skip,
        )

    return solve(
        0,
        -1,
        maximum_count,
    )[2]


def _better_solution(
    left: tuple[
        int,
        float,
        tuple[int, ...],
    ],
    right: tuple[
        int,
        float,
        tuple[int, ...],
    ],
) -> tuple[
    int,
    float,
    tuple[int, ...],
]:
    if left[0] != right[0]:
        return (
            left
            if left[0] > right[0]
            else right
        )

    if left[1] != right[1]:
        return (
            left
            if left[1] > right[1]
            else right
        )

    return (
        left
        if left[2] < right[2]
        else right
    )


def _interval_duration(
    interval: ActivityInterval,
) -> float:
    if interval.moving_time_seconds is not None:
        return float(
            interval.moving_time_seconds
        )

    if interval.elapsed_time_seconds is not None:
        return float(
            interval.elapsed_time_seconds
        )

    return float(
        interval.end_time_seconds
        - interval.start_time_seconds
    )


def _exact_target_score(
    *,
    actual: float,
    expected: float,
    tolerance_percent: float,
) -> float | None:
    if expected <= 0:
        return None

    relative_error = (
        abs(actual - expected)
        / expected
        * 100.0
    )

    if relative_error > tolerance_percent:
        return None

    if tolerance_percent == 0:
        return (
            1.0
            if relative_error == 0
            else None
        )

    return max(
        0.0,
        1.0
        - (
            relative_error
            / tolerance_percent
        ),
    )


def _range_target_score(
    *,
    actual: float,
    minimum: float,
    maximum: float,
    tolerance_percent: float,
) -> float | None:
    if (
        minimum <= actual <= maximum
    ):
        return 1.0

    boundary = (
        minimum
        if actual < minimum
        else maximum
    )

    return _exact_target_score(
        actual=actual,
        expected=boundary,
        tolerance_percent=(
            tolerance_percent
        ),
    )


def _to_observed_repetition(
    candidate: _Candidate,
) -> ObservedRepetition:
    interval = candidate.interval

    return ObservedRepetition(
        start_index=interval.start_index,
        end_index=interval.end_index,
        start_time_seconds=float(
            interval.start_time_seconds
        ),
        end_time_seconds=float(
            interval.end_time_seconds
        ),
        distance_m=interval.distance_m,
        duration_seconds=(
            candidate.duration_seconds
        ),
        average_speed_mps=(
            interval.average_speed_mps
        ),
        average_heart_rate=(
            interval.average_heart_rate
        ),
        max_heart_rate=(
            interval.max_heart_rate
        ),
        match_score=candidate.score,
    )
