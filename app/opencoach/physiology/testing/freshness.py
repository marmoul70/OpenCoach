"""Fraîcheur des mesures physiologiques OpenCoach.

Les seuils définis ici sont une politique de coaching OpenCoach.

Ils ne représentent pas une durée de validité physiologique
universelle. Ils permettent au moteur de décider quand une
recalibration peut redevenir pertinente.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from opencoach.physiology.testing.models import (
    PhysiologicalMetric,
    PhysiologicalTestType,
    PhysiologicalTestAcquisitionMode,
)


class MeasurementConfidence(StrEnum):
    """Confiance accordée à une mesure."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MeasurementFreshness(StrEnum):
    """État temporel d'une mesure."""

    FRESH = "fresh"
    AGING = "aging"
    STALE = "stale"
    MISSING = "missing"


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalMeasurementEvidence:
    """Mesure disponible pour la décision de calibration."""

    metric: PhysiologicalMetric

    measured_at: date

    confidence: MeasurementConfidence

    acquisition_mode: PhysiologicalTestAcquisitionMode

    protocol: PhysiologicalTestType | None = None


@dataclass(
    frozen=True,
    slots=True,
)
class MeasurementFreshnessPolicy:
    """Durées de fraîcheur utilisées par OpenCoach."""

    fresh_days: int
    stale_after_days: int

    def __post_init__(self) -> None:
        if self.fresh_days < 0:
            raise ValueError(
                "fresh_days doit être positif."
            )

        if (
            self.stale_after_days
            < self.fresh_days
        ):
            raise ValueError(
                "stale_after_days doit être "
                "supérieur ou égal à fresh_days."
            )


# ============================================================
# Politique OpenCoach V1
# ============================================================
#
# Ces valeurs seront centralisées/configurables plus tard.
#
# FCmax :
#     évolution généralement lente -> fenêtre longue.
#
# VMA / seuil / CS :
#     sensibles à l'état d'entraînement -> plus fréquents.
#
# Trail :
#     mesures spécifiques utilisées surtout pendant
#     les blocs correspondants.
# ============================================================

_FRESHNESS_POLICIES: dict[
    PhysiologicalMetric,
    MeasurementFreshnessPolicy,
] = {
    PhysiologicalMetric.VMA: (
        MeasurementFreshnessPolicy(
            fresh_days=56,
            stale_after_days=84,
        )
    ),

    PhysiologicalMetric.MAX_HEART_RATE: (
        MeasurementFreshnessPolicy(
            fresh_days=180,
            stale_after_days=365,
        )
    ),

    PhysiologicalMetric.THRESHOLD_PACE: (
        MeasurementFreshnessPolicy(
            fresh_days=42,
            stale_after_days=70,
        )
    ),

    PhysiologicalMetric.THRESHOLD_HEART_RATE: (
        MeasurementFreshnessPolicy(
            fresh_days=42,
            stale_after_days=70,
        )
    ),

    PhysiologicalMetric.CRITICAL_SPEED: (
        MeasurementFreshnessPolicy(
            fresh_days=42,
            stale_after_days=70,
        )
    ),

    PhysiologicalMetric.D_PRIME: (
        MeasurementFreshnessPolicy(
            fresh_days=42,
            stale_after_days=70,
        )
    ),

    PhysiologicalMetric.UPHILL_VAM: (
        MeasurementFreshnessPolicy(
            fresh_days=42,
            stale_after_days=70,
        )
    ),

    PhysiologicalMetric.UPHILL_SUSTAINED_VAM: (
        MeasurementFreshnessPolicy(
            fresh_days=42,
            stale_after_days=70,
        )
    ),

    PhysiologicalMetric.TRAIL_DURABILITY: (
        MeasurementFreshnessPolicy(
            fresh_days=28,
            stale_after_days=56,
        )
    ),
}


def get_measurement_freshness_policy(
    metric: PhysiologicalMetric,
) -> MeasurementFreshnessPolicy:
    """Retourne la politique associée à une métrique."""

    try:
        return _FRESHNESS_POLICIES[
            metric
        ]

    except KeyError as exc:
        raise KeyError(
            "Aucune politique de fraîcheur "
            f"pour {metric}."
        ) from exc


def evaluate_measurement_freshness(
    *,
    metric: PhysiologicalMetric,
    reference_date: date,
    measurement: (
        PhysiologicalMeasurementEvidence
        | None
    ),
) -> MeasurementFreshness:
    """Évalue l'ancienneté d'une mesure."""

    if measurement is None:
        return MeasurementFreshness.MISSING

    if measurement.metric is not metric:
        raise ValueError(
            "La mesure ne correspond pas "
            "à la métrique évaluée."
        )

    age_days = (
        reference_date
        - measurement.measured_at
    ).days

    if age_days < 0:
        raise ValueError(
            "Une mesure physiologique "
            "ne peut pas dater du futur."
        )

    policy = (
        get_measurement_freshness_policy(
            metric
        )
    )

    if age_days <= policy.fresh_days:
        return MeasurementFreshness.FRESH

    if (
        age_days
        <= policy.stale_after_days
    ):
        return MeasurementFreshness.AGING

    return MeasurementFreshness.STALE
