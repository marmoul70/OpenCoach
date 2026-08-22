from dataclasses import dataclass
from datetime import date
from typing import Literal

from opencoach.models import (
    PhysiologicalMeasurement,
    PhysiologicalMetric,
)


MeasurementFreshness = Literal[
    "fresh",
    "aging",
    "stale",
]


@dataclass(frozen=True)
class PhysiologicalFreshnessPolicy:
    """Seuils d'ancienneté applicables à une métrique."""

    fresh_days: int
    stale_after_days: int


@dataclass(frozen=True)
class PhysiologicalFreshnessAssessment:
    """Évalue la fraîcheur d'une mesure physiologique."""

    measurement: PhysiologicalMeasurement

    age_days: int
    freshness: MeasurementFreshness

    usable: bool
    recalibration_recommended: bool

    reason: str


POLICIES: dict[
    PhysiologicalMetric,
    PhysiologicalFreshnessPolicy,
] = {
    "vma": PhysiologicalFreshnessPolicy(
        fresh_days=90,
        stale_after_days=180,
    ),
    "max_heart_rate": PhysiologicalFreshnessPolicy(
        fresh_days=180,
        stale_after_days=365,
    ),
    "resting_heart_rate": PhysiologicalFreshnessPolicy(
        fresh_days=30,
        stale_after_days=60,
    ),
    "threshold_heart_rate_1": PhysiologicalFreshnessPolicy(
        fresh_days=90,
        stale_after_days=180,
    ),
    "threshold_heart_rate_2": PhysiologicalFreshnessPolicy(
        fresh_days=90,
        stale_after_days=180,
    ),
}


def assess_measurement_freshness(
    *,
    measurement: PhysiologicalMeasurement,
    reference_date: date,
) -> PhysiologicalFreshnessAssessment:
    """Évalue l'ancienneté et l'utilisabilité d'une mesure."""

    if measurement.measured_at > reference_date:
        raise ValueError(
            "La date de mesure ne peut pas être postérieure "
            "à la date de référence."
        )

    policy = POLICIES[
        measurement.metric
    ]

    age_days = (
        reference_date
        - measurement.measured_at
    ).days

    freshness = _classify_freshness(
        age_days=age_days,
        policy=policy,
    )

    usable = _is_usable(
        freshness=freshness,
        confidence=measurement.confidence,
    )

    recalibration_recommended = (
        freshness == "stale"
        or measurement.confidence == "low"
    )

    reason = _build_reason(
        freshness=freshness,
        confidence=measurement.confidence,
    )

    return PhysiologicalFreshnessAssessment(
        measurement=measurement,
        age_days=age_days,
        freshness=freshness,
        usable=usable,
        recalibration_recommended=(
            recalibration_recommended
        ),
        reason=reason,
    )


def _classify_freshness(
    *,
    age_days: int,
    policy: PhysiologicalFreshnessPolicy,
) -> MeasurementFreshness:
    if age_days <= policy.fresh_days:
        return "fresh"

    if age_days <= policy.stale_after_days:
        return "aging"

    return "stale"


def _is_usable(
    *,
    freshness: MeasurementFreshness,
    confidence: str,
) -> bool:
    if freshness == "stale":
        return False

    if confidence == "low":
        return False

    return True


def _build_reason(
    *,
    freshness: MeasurementFreshness,
    confidence: str,
) -> str:
    if freshness == "stale":
        return (
            "La mesure est trop ancienne pour être utilisée "
            "comme référence physiologique principale."
        )

    if confidence == "low":
        return (
            "La mesure est récente mais sa confiance est trop faible."
        )

    if freshness == "aging":
        return (
            "La mesure reste utilisable mais approche de sa "
            "période de recalibration."
        )

    return (
        "La mesure est suffisamment récente et fiable."
    )
