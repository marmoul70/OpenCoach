from dataclasses import dataclass
from typing import Literal

from opencoach.planning.physiology.snapshot import (
    PhysiologicalCalibrationMetric,
    PhysiologicalCalibrationSnapshot,
)


AssessmentType = Literal[
    "vma_calibration",
    "threshold_calibration",
    "max_heart_rate_calibration",
]

AssessmentPriority = Literal[
    "low",
    "medium",
    "high",
]


@dataclass(frozen=True)
class AssessmentNeed:
    """Besoin de calibration physiologique identifié par OpenCoach."""

    assessment_type: AssessmentType
    priority: AssessmentPriority

    metrics: tuple[str, ...]

    reason: str


def identify_assessment_needs(
    snapshot: PhysiologicalCalibrationSnapshot,
) -> tuple[AssessmentNeed, ...]:
    """Transforme un snapshot physiologique en besoins de calibration."""

    needs: list[AssessmentNeed] = []

    threshold_need = _build_threshold_need(
        snapshot
    )

    if threshold_need is not None:
        needs.append(
            threshold_need
        )

    vma_need = _build_single_metric_need(
        metric=snapshot.vma,
        assessment_type="vma_calibration",
    )

    if vma_need is not None:
        needs.append(
            vma_need
        )

    max_hr_need = _build_single_metric_need(
        metric=snapshot.max_heart_rate,
        assessment_type="max_heart_rate_calibration",
    )

    if max_hr_need is not None:
        needs.append(
            max_hr_need
        )

    return tuple(
        sorted(
            needs,
            key=_priority_sort_key,
        )
    )


def _build_threshold_need(
    snapshot: PhysiologicalCalibrationSnapshot,
) -> AssessmentNeed | None:
    metrics = (
        snapshot.threshold_heart_rate_1,
        snapshot.threshold_heart_rate_2,
    )

    requiring_calibration = tuple(
        metric
        for metric in metrics
        if metric.recalibration_recommended
    )

    if not requiring_calibration:
        return None

    priority = _highest_priority(
        requiring_calibration
    )

    names = tuple(
        metric.metric
        for metric in requiring_calibration
    )

    return AssessmentNeed(
        assessment_type="threshold_calibration",
        priority=priority,
        metrics=names,
        reason=(
            "La calibration des seuils physiologiques "
            "est absente, ancienne ou insuffisamment fiable."
        ),
    )


def _build_single_metric_need(
    *,
    metric: PhysiologicalCalibrationMetric,
    assessment_type: AssessmentType,
) -> AssessmentNeed | None:
    if not metric.recalibration_recommended:
        return None

    return AssessmentNeed(
        assessment_type=assessment_type,
        priority=_metric_priority(
            metric
        ),
        metrics=(
            metric.metric,
        ),
        reason=metric.reason,
    )


def _highest_priority(
    metrics: tuple[
        PhysiologicalCalibrationMetric,
        ...,
    ],
) -> AssessmentPriority:
    priorities = {
        _metric_priority(metric)
        for metric in metrics
    }

    if "high" in priorities:
        return "high"

    if "medium" in priorities:
        return "medium"

    return "low"


def _metric_priority(
    metric: PhysiologicalCalibrationMetric,
) -> AssessmentPriority:
    if metric.source == "missing":
        return "high"

    if metric.source == "legacy_profile":
        return "medium"

    if (
        metric.freshness is not None
        and metric.freshness.freshness == "stale"
    ):
        return "high"

    if (
        metric.measurement is not None
        and metric.measurement.confidence == "low"
    ):
        return "medium"

    return "low"


def _priority_sort_key(
    need: AssessmentNeed,
) -> int:
    priorities = {
        "high": 0,
        "medium": 1,
        "low": 2,
    }

    return priorities[
        need.priority
    ]
