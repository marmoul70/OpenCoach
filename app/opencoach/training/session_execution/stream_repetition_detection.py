"""Reconstruction des répétitions depuis les streams réalisés."""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import dataclass
from functools import lru_cache
from math import isfinite
from numbers import Real

from opencoach.models import ActivityDetail

from .interval_prescription import (
    IntervalSetPrescription,
)


@dataclass(frozen=True, slots=True)
class StreamRepetitionCandidate:
    """Segment de stream correspondant à une répétition possible."""

    start_index: int
    end_index: int

    start_time_seconds: float
    end_time_seconds: float

    distance_m: float
    duration_seconds: float

    average_speed_mps: float

    match_score: float


def detect_distance_repetitions_from_streams(
    activity_detail: ActivityDetail,
    prescription: IntervalSetPrescription,
) -> tuple[StreamRepetitionCandidate, ...]:
    """Reconstruit les fractions prescrites par distance.

    La prescription pilote entièrement la recherche.
    Aucun lap fournisseur n'est nécessaire.
    """

    target_distance = (
        prescription.work_distance_m
    )

    if target_distance is None:
        return ()

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
        return ()

    points = _build_monotonic_points(
        time_stream.data,
        distance_stream.data,
    )

    if len(points) < 2:
        return ()

    candidates = _build_candidates(
        points,
        prescription,
    )

    if not candidates:
        return ()

    minimum_gap = _minimum_recovery_gap(
        prescription
    )

    selected = _select_candidates(
        candidates,
        maximum_count=(
            prescription.repetitions
        ),
        minimum_gap_seconds=minimum_gap,
    )

    return tuple(
        candidates[index]
        for index in selected
    )


def _build_monotonic_points(
    time_values,
    distance_values,
) -> tuple[
    tuple[int, float, float],
    ...,
]:
    result = []

    previous_time = None
    previous_distance = None

    for original_index, (
        raw_time,
        raw_distance,
    ) in enumerate(
        zip(
            time_values,
            distance_values,
            strict=False,
        )
    ):
        time_value = _number(
            raw_time
        )

        distance_value = _number(
            raw_distance
        )

        if (
            time_value is None
            or distance_value is None
        ):
            continue

        if (
            previous_time is not None
            and time_value <= previous_time
        ):
            continue

        if (
            previous_distance is not None
            and distance_value < previous_distance
        ):
            continue

        result.append(
            (
                original_index,
                time_value,
                distance_value,
            )
        )

        previous_time = time_value
        previous_distance = distance_value

    return tuple(result)


def _build_candidates(
    points: tuple[
        tuple[int, float, float],
        ...,
    ],
    prescription: IntervalSetPrescription,
) -> tuple[
    StreamRepetitionCandidate,
    ...,
]:
    target_distance = (
        prescription.work_distance_m
    )

    if target_distance is None:
        return ()

    distances = [
        point[2]
        for point in points
    ]

    result = []

    for start_position in range(
        len(points) - 1
    ):
        (
            start_index,
            start_time,
            start_distance,
        ) = points[
            start_position
        ]

        target_end_distance = (
            start_distance
            + target_distance
        )

        end_position = bisect_left(
            distances,
            target_end_distance,
            lo=start_position + 1,
        )

        if end_position >= len(points):
            continue

        (
            end_index,
            end_time,
            end_distance,
        ) = points[
            end_position
        ]

        previous_position = (
            end_position - 1
        )

        (
            _,
            previous_time,
            previous_distance,
        ) = points[
            previous_position
        ]

        if (
            end_distance
            <= previous_distance
        ):
            continue

        ratio = (
            target_end_distance
            - previous_distance
        ) / (
            end_distance
            - previous_distance
        )

        interpolated_end_time = (
            previous_time
            + ratio
            * (
                end_time
                - previous_time
            )
        )

        duration = (
            interpolated_end_time
            - start_time
        )

        if duration <= 0:
            continue

        score = _duration_score(
            duration,
            prescription,
        )

        if score is None:
            continue

        result.append(
            StreamRepetitionCandidate(
                start_index=start_index,
                end_index=end_index,
                start_time_seconds=(
                    start_time
                ),
                end_time_seconds=(
                    interpolated_end_time
                ),
                distance_m=(
                    target_distance
                ),
                duration_seconds=duration,
                average_speed_mps=(
                    target_distance
                    / duration
                ),
                match_score=score,
            )
        )

    return tuple(result)


def _duration_score(
    duration: float,
    prescription: IntervalSetPrescription,
) -> float | None:
    target = (
        prescription.repetition_target
    )

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

        # Une marge raisonnable est autorisée pour détecter
        # une répétition mal exécutée : sinon le comparateur
        # ferait disparaître précisément les fractions ratées.
        lower_limit = (
            minimum * 0.70
        )

        upper_limit = (
            maximum * 1.30
        )

        if not (
            lower_limit
            <= duration
            <= upper_limit
        ):
            return None

        if (
            minimum
            <= duration
            <= maximum
        ):
            return 1.0

        boundary = (
            minimum
            if duration < minimum
            else maximum
        )

        error = abs(
            duration - boundary
        ) / boundary

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
            abs(duration - expected)
            / expected
        )

        if error > 0.30:
            return None

        return (
            1.0 - error
        )

    # Une prescription par distance sans chrono cible reste
    # détectable, mais avec un score neutre.
    return 0.5


def _minimum_recovery_gap(
    prescription: IntervalSetPrescription,
) -> float:
    recovery = (
        prescription.recovery_duration_seconds
    )

    if recovery is None:
        return 1.0

    # La récupération réellement effectuée peut différer de
    # la prescription. Cette valeur sert seulement à empêcher
    # plusieurs fenêtres glissantes d'une même répétition.
    return max(
        1.0,
        recovery * 0.30,
    )


def _select_candidates(
    candidates: tuple[
        StreamRepetitionCandidate,
        ...,
    ],
    *,
    maximum_count: int,
    minimum_gap_seconds: float,
) -> tuple[int, ...]:
    ordered_indexes = tuple(
        sorted(
            range(
                len(candidates)
            ),
            key=lambda index: (
                candidates[index]
                .start_time_seconds,
                candidates[index]
                .end_time_seconds,
            ),
        )
    )

    ordered = tuple(
        candidates[index]
        for index in ordered_indexes
    )

    @lru_cache(maxsize=None)
    def solve(
        index: int,
        previous_end_ms: int,
        remaining: int,
    ):
        if (
            index >= len(ordered)
            or remaining <= 0
        ):
            return (
                0,
                0.0,
                (),
            )

        skip = solve(
            index + 1,
            previous_end_ms,
            remaining,
        )

        candidate = (
            ordered[index]
        )

        previous_end = (
            previous_end_ms
            / 1000.0
        )

        take = (
            -1,
            -1.0,
            (),
        )

        if (
            candidate.start_time_seconds
            >= (
                previous_end
                + minimum_gap_seconds
            )
        ):
            (
                next_count,
                next_score,
                next_indexes,
            ) = solve(
                index + 1,
                int(
                    round(
                        candidate.end_time_seconds
                        * 1000
                    )
                ),
                remaining - 1,
            )

            take = (
                next_count + 1,
                next_score
                + candidate.match_score,
                (
                    index,
                    *next_indexes,
                ),
            )

        best = _better(
            take,
            skip,
        )

        return best

    selected_ordered = solve(
        0,
        -10_000_000,
        maximum_count,
    )[2]

    return tuple(
        ordered_indexes[index]
        for index in selected_ordered
    )


def _better(
    left,
    right,
):
    if left[0] != right[0]:
        return (
            left
            if left[0] > right[0]
            else right
        )

    if abs(
        left[1] - right[1]
    ) > 1e-9:
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


def _number(
    value,
) -> float | None:
    if (
        not isinstance(
            value,
            Real,
        )
        or isinstance(
            value,
            bool,
        )
    ):
        return None

    result = float(
        value
    )

    if not isfinite(
        result
    ):
        return None

    return result
