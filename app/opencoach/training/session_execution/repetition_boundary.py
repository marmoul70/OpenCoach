"""Raffinement des frontières réelles d'une répétition."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from numbers import Real

from opencoach.models import ActivityDetail

from .interval_prescription import (
    IntervalSetPrescription,
)
from .stream_repetition_detection import (
    StreamRepetitionCandidate,
)


@dataclass(frozen=True, slots=True)
class RefinedRepetitionBoundary:
    """Frontières de travail déterminées par les signaux."""

    start_time_seconds: float
    end_time_seconds: float

    duration_seconds: float

    original_start_time_seconds: float
    original_end_time_seconds: float

    start_shift_seconds: float
    end_shift_seconds: float

    confidence: float


def refine_repetition_boundary(
    activity_detail: ActivityDetail,
    candidate: StreamRepetitionCandidate,
    prescription: IntervalSetPrescription,
) -> RefinedRepetitionBoundary:
    """Recale le début et la fin du travail sur les streams.

    Le candidat initial localise approximativement la fraction.
    Les frontières finales utilisent uniquement les variations
    de vitesse, watts et cadence.

    La récupération prescrite détermine uniquement la largeur
    de la zone inspectée ; elle ne fixe jamais la frontière.
    """

    time_stream = activity_detail.streams.time

    if time_stream is None:
        return _unchanged(
            candidate
        )

    metric_streams = (
        (
            activity_detail.streams.velocity_smooth,
            0.45,
        ),
        (
            activity_detail.streams.watts,
            0.35,
        ),
        (
            activity_detail.streams.cadence,
            0.20,
        ),
    )

    available = [
        (
            stream,
            weight,
        )
        for stream, weight in metric_streams
        if stream is not None
    ]

    if not available:
        return _unchanged(
            candidate
        )

    margin = _search_margin(
        prescription,
        candidate,
    )

    search_start = max(
        0.0,
        candidate.start_time_seconds
        - margin,
    )

    search_end = (
        candidate.end_time_seconds
        + margin
    )

    points = _build_signal_points(
        time_stream.data,
        available,
        search_start=search_start,
        search_end=search_end,
    )

    if len(points) < 5:
        return _unchanged(
            candidate
        )

    references = _build_references(
        points,
        candidate,
        available,
    )

    if not references:
        return _unchanged(
            candidate
        )

    scored = []

    for time_value, values in points:
        score = _combined_work_score(
            values,
            references,
        )

        scored.append(
            (
                time_value,
                score,
            )
        )

    refined = _find_work_region(
        scored,
        candidate,
    )

    if refined is None:
        return _unchanged(
            candidate
        )

    start, end, confidence = refined

    if end <= start:
        return _unchanged(
            candidate
        )

    return RefinedRepetitionBoundary(
        start_time_seconds=round(
            start,
            3,
        ),
        end_time_seconds=round(
            end,
            3,
        ),
        duration_seconds=round(
            end - start,
            3,
        ),
        original_start_time_seconds=(
            candidate.start_time_seconds
        ),
        original_end_time_seconds=(
            candidate.end_time_seconds
        ),
        start_shift_seconds=round(
            start
            - candidate.start_time_seconds,
            3,
        ),
        end_shift_seconds=round(
            end
            - candidate.end_time_seconds,
            3,
        ),
        confidence=round(
            confidence,
            4,
        ),
    )


def _search_margin(
    prescription: IntervalSetPrescription,
    candidate: StreamRepetitionCandidate,
) -> float:
    recovery = (
        prescription.recovery_duration_seconds
    )

    if recovery is None:
        recovery = (
            candidate.duration_seconds
            * 0.5
        )

    return min(
        30.0,
        max(
            10.0,
            recovery * 0.35,
        ),
    )


def _build_signal_points(
    time_values,
    available,
    *,
    search_start: float,
    search_end: float,
):
    metric_data = [
        stream.data
        for stream, _ in available
    ]

    result = []

    for index, raw_time in enumerate(
        time_values
    ):
        time_value = _number(
            raw_time
        )

        if time_value is None:
            continue

        if not (
            search_start
            <= time_value
            <= search_end
        ):
            continue

        values = []

        for data in metric_data:
            if index >= len(data):
                values.append(None)
                continue

            values.append(
                _number(
                    data[index]
                )
            )

        result.append(
            (
                time_value,
                tuple(values),
            )
        )

    return tuple(result)


def _build_references(
    points,
    candidate,
    available,
):
    duration = (
        candidate.end_time_seconds
        - candidate.start_time_seconds
    )

    core_start = (
        candidate.start_time_seconds
        + duration * 0.25
    )

    core_end = (
        candidate.end_time_seconds
        - duration * 0.25
    )

    before_start = max(
        points[0][0],
        candidate.start_time_seconds
        - 20.0,
    )

    before_end = (
        candidate.start_time_seconds
        - 2.0
    )

    after_start = (
        candidate.end_time_seconds
        + 2.0
    )

    after_end = min(
        points[-1][0],
        candidate.end_time_seconds
        + 20.0,
    )

    references = []

    total_weight = sum(
        weight
        for _, weight in available
    )

    for metric_index, (
        _,
        weight,
    ) in enumerate(available):
        work_values = _metric_values(
            points,
            metric_index,
            core_start,
            core_end,
        )

        recovery_values = (
            _metric_values(
                points,
                metric_index,
                before_start,
                before_end,
            )
            + _metric_values(
                points,
                metric_index,
                after_start,
                after_end,
            )
        )

        if (
            not work_values
            or not recovery_values
        ):
            continue

        work_reference = (
            sum(work_values)
            / len(work_values)
        )

        recovery_reference = (
            sum(recovery_values)
            / len(recovery_values)
        )

        contrast = (
            work_reference
            - recovery_reference
        )

        if contrast <= 0:
            continue

        references.append(
            (
                metric_index,
                recovery_reference,
                work_reference,
                weight / total_weight,
            )
        )

    if not references:
        return ()

    normalization = sum(
        reference[3]
        for reference in references
    )

    return tuple(
        (
            metric_index,
            recovery,
            work,
            weight / normalization,
        )
        for (
            metric_index,
            recovery,
            work,
            weight,
        ) in references
    )


def _metric_values(
    points,
    metric_index,
    start,
    end,
):
    return [
        values[metric_index]
        for time_value, values in points
        if (
            start
            <= time_value
            < end
            and values[metric_index]
            is not None
        )
    ]


def _combined_work_score(
    values,
    references,
) -> float:
    numerator = 0.0
    denominator = 0.0

    for (
        metric_index,
        recovery_reference,
        work_reference,
        weight,
    ) in references:
        value = values[
            metric_index
        ]

        if value is None:
            continue

        contrast = (
            work_reference
            - recovery_reference
        )

        if contrast <= 0:
            continue

        normalized = (
            value
            - recovery_reference
        ) / contrast

        normalized = min(
            1.0,
            max(
                0.0,
                normalized,
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


def _find_work_region(
    scored,
    candidate,
):
    # On recherche la région de travail contenant le milieu
    # du candidat initial. Une courte chute de 1–2 secondes
    # n'interrompt pas immédiatement la fraction.
    threshold = 0.55
    max_gap_seconds = 2.5

    center = (
        candidate.start_time_seconds
        + candidate.end_time_seconds
    ) / 2.0

    center_index = min(
        range(len(scored)),
        key=lambda index: abs(
            scored[index][0]
            - center
        ),
    )

    # Si le milieu lui-même est faible, chercher le point fort
    # le plus proche dans le corps du candidat.
    if (
        scored[center_index][1]
        < threshold
    ):
        candidates = [
            index
            for index, (
                time_value,
                score,
            ) in enumerate(scored)
            if (
                candidate.start_time_seconds
                <= time_value
                <= candidate.end_time_seconds
                and score >= threshold
            )
        ]

        if not candidates:
            return None

        center_index = min(
            candidates,
            key=lambda index: abs(
                scored[index][0]
                - center
            ),
        )

    left = center_index
    last_good_time = scored[
        center_index
    ][0]

    for index in range(
        center_index - 1,
        -1,
        -1,
    ):
        time_value, score = scored[
            index
        ]

        if score >= threshold:
            left = index
            last_good_time = time_value
            continue

        if (
            last_good_time
            - time_value
            <= max_gap_seconds
        ):
            left = index
            continue

        break

    right = center_index
    last_good_time = scored[
        center_index
    ][0]

    for index in range(
        center_index + 1,
        len(scored),
    ):
        time_value, score = scored[
            index
        ]

        if score >= threshold:
            right = index
            last_good_time = time_value
            continue

        if (
            time_value
            - last_good_time
            <= max_gap_seconds
        ):
            right = index
            continue

        break

    selected = scored[
        left:right + 1
    ]

    positive_scores = [
        score
        for _, score in selected
        if score >= threshold
    ]

    if not positive_scores:
        return None

    start = scored[left][0]
    end = scored[right][0]

    confidence = (
        sum(positive_scores)
        / len(positive_scores)
    )

    return (
        start,
        end,
        confidence,
    )


def _unchanged(
    candidate: StreamRepetitionCandidate,
) -> RefinedRepetitionBoundary:
    return RefinedRepetitionBoundary(
        start_time_seconds=(
            candidate.start_time_seconds
        ),
        end_time_seconds=(
            candidate.end_time_seconds
        ),
        duration_seconds=(
            candidate.duration_seconds
        ),
        original_start_time_seconds=(
            candidate.start_time_seconds
        ),
        original_end_time_seconds=(
            candidate.end_time_seconds
        ),
        start_shift_seconds=0.0,
        end_shift_seconds=0.0,
        confidence=0.0,
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
