"""Décision de proposer ou non un test physiologique.

Ce module ne modifie aucun planning.

Il répond uniquement à la question :

    OpenCoach devrait-il proposer un test maintenant ?

Les décisions sont déterministes et explicables.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from opencoach.physiology.testing.freshness import (
    MeasurementConfidence,
    MeasurementFreshness,
    PhysiologicalMeasurementEvidence,
    evaluate_measurement_freshness,
)
from opencoach.physiology.testing.models import (
    PhysiologicalMetric,
    PhysiologicalTestType,
    SportDiscipline,
)
from opencoach.physiology.testing.proposal import (
    PhysiologicalTestDecision,
)


class PhysiologicalTestingSeasonPhase(StrEnum):
    """Contexte simplifié utilisé par le moteur de test.

    Cette enum reste volontairement indépendante du moteur
    annuel pour le moment.

    PT0.4 la raccordera à la vraie trajectoire OpenCoach.
    """

    BASE = "base"
    BUILD = "build"
    SPECIFIC = "specific"
    TAPER = "taper"
    RECOVERY = "recovery"
    RETURN_TO_TRAINING = (
        "return_to_training"
    )


class PhysiologicalTestNeedStatus(StrEnum):
    """Décision issue du moteur."""

    NOT_NEEDED = "not_needed"
    DEFER = "defer"
    PROPOSE = "propose"


@dataclass(
    frozen=True,
    slots=True,
)
class PreviousTestDecision:
    """Dernière décision connue pour cette métrique."""

    protocol: PhysiologicalTestType

    decision: PhysiologicalTestDecision

    decided_at: date


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestNeedRequest:
    """Contexte nécessaire à la décision."""

    metric: PhysiologicalMetric

    reference_date: date

    disciplines: tuple[
        SportDiscipline,
        ...,
    ]

    season_phase: PhysiologicalTestingSeasonPhase

    measurement: (
        PhysiologicalMeasurementEvidence
        | None
    ) = None

    previous_test_decision: (
        PreviousTestDecision
        | None
    ) = None


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestNeedDecision:
    """Décision explicable prise par OpenCoach."""

    status: PhysiologicalTestNeedStatus

    metric: PhysiologicalMetric

    freshness: MeasurementFreshness

    preferred_protocol: (
        PhysiologicalTestType
        | None
    )

    reason: str

    @property
    def should_propose(
        self,
    ) -> bool:
        return (
            self.status
            is PhysiologicalTestNeedStatus.PROPOSE
        )


# L'athlète vient de dire qu'il ne souhaite pas se tester.
# OpenCoach respecte cette décision pendant plusieurs semaines.
DECLINED_TEST_COOLDOWN_DAYS = 28


def evaluate_physiological_test_need(
    request: PhysiologicalTestNeedRequest,
) -> PhysiologicalTestNeedDecision:
    """Décide si une calibration doit être proposée."""

    freshness = (
        evaluate_measurement_freshness(
            metric=request.metric,
            reference_date=(
                request.reference_date
            ),
            measurement=(
                request.measurement
            ),
        )
    )

    # --------------------------------------------------------
    # 1. Respect du refus récent
    # --------------------------------------------------------

    if _has_recent_decline(
        request
    ):
        return PhysiologicalTestNeedDecision(
            status=PhysiologicalTestNeedStatus.DEFER,
            metric=request.metric,
            freshness=freshness,
            preferred_protocol=None,
            reason=(
                "L'athlète a récemment refusé "
                "une proposition de test. "
                "OpenCoach respecte ce choix avant "
                "de proposer une nouvelle calibration."
            ),
        )

    # --------------------------------------------------------
    # 2. Une bonne mesure récente ne nécessite rien
    # --------------------------------------------------------

    if (
        freshness
        is MeasurementFreshness.FRESH
        and request.measurement is not None
        and request.measurement.confidence
        is not MeasurementConfidence.LOW
    ):
        return PhysiologicalTestNeedDecision(
            status=PhysiologicalTestNeedStatus.NOT_NEEDED,
            metric=request.metric,
            freshness=freshness,
            preferred_protocol=None,
            reason=(
                "La mesure disponible est récente "
                "et suffisamment fiable."
            ),
        )

    # --------------------------------------------------------
    # 3. Taper / récupération :
    #    pas de test maximal par défaut
    # --------------------------------------------------------

    if request.season_phase in {
        PhysiologicalTestingSeasonPhase.TAPER,
        PhysiologicalTestingSeasonPhase.RECOVERY,
    }:
        return PhysiologicalTestNeedDecision(
            status=PhysiologicalTestNeedStatus.DEFER,
            metric=request.metric,
            freshness=freshness,
            preferred_protocol=None,
            reason=(
                "La phase actuelle n'est pas adaptée "
                "à l'ajout d'un test physiologique "
                "exigeant."
            ),
        )

    # --------------------------------------------------------
    # 4. Reprise :
    #    éviter de tester immédiatement
    # --------------------------------------------------------

    if (
        request.season_phase
        is PhysiologicalTestingSeasonPhase.RETURN_TO_TRAINING
    ):
        return PhysiologicalTestNeedDecision(
            status=PhysiologicalTestNeedStatus.DEFER,
            metric=request.metric,
            freshness=freshness,
            preferred_protocol=None,
            reason=(
                "La priorité actuelle est la reprise "
                "progressive. La calibration sera "
                "réévaluée après restauration d'une "
                "charge d'entraînement normale."
            ),
        )

    # --------------------------------------------------------
    # 5. Mesure vieillissante
    #
    # En BASE, on peut attendre.
    # En BUILD/SPECIFIC, une calibration devient pertinente.
    # --------------------------------------------------------

    if (
        freshness
        is MeasurementFreshness.AGING
        and request.season_phase
        is PhysiologicalTestingSeasonPhase.BASE
    ):
        return PhysiologicalTestNeedDecision(
            status=PhysiologicalTestNeedStatus.NOT_NEEDED,
            metric=request.metric,
            freshness=freshness,
            preferred_protocol=None,
            reason=(
                "La mesure commence à vieillir, "
                "mais reste exploitable pendant "
                "la phase de base."
            ),
        )

    # --------------------------------------------------------
    # 6. Choix du protocole
    # --------------------------------------------------------

    protocol = (
        _select_preferred_protocol(
            metric=request.metric,
            disciplines=(
                request.disciplines
            ),
        )
    )

    if protocol is None:
        return PhysiologicalTestNeedDecision(
            status=PhysiologicalTestNeedStatus.DEFER,
            metric=request.metric,
            freshness=freshness,
            preferred_protocol=None,
            reason=(
                "Aucun protocole compatible "
                "avec les disciplines de l'athlète "
                "n'est disponible."
            ),
        )

    return PhysiologicalTestNeedDecision(
        status=PhysiologicalTestNeedStatus.PROPOSE,
        metric=request.metric,
        freshness=freshness,
        preferred_protocol=protocol,
        reason=_build_proposal_reason(
            freshness=freshness,
            metric=request.metric,
        ),
    )


def _has_recent_decline(
    request: PhysiologicalTestNeedRequest,
) -> bool:
    previous = (
        request.previous_test_decision
    )

    if previous is None:
        return False

    if (
        previous.decision
        is not PhysiologicalTestDecision.DECLINED
    ):
        return False

    age_days = (
        request.reference_date
        - previous.decided_at
    ).days

    if age_days < 0:
        return False

    return (
        age_days
        < DECLINED_TEST_COOLDOWN_DAYS
    )


def _select_preferred_protocol(
    *,
    metric: PhysiologicalMetric,
    disciplines: tuple[
        SportDiscipline,
        ...,
    ],
) -> PhysiologicalTestType | None:
    """Choisit le protocole V1 le moins contraignant pertinent."""

    discipline_set = set(
        disciplines
    )

    is_runner = bool(
        discipline_set.intersection(
            {
                SportDiscipline.ROAD_RUNNING,
                SportDiscipline.TRAIL_RUNNING,
                SportDiscipline.TRACK_RUNNING,
            }
        )
    )

    is_trail = (
        SportDiscipline.TRAIL_RUNNING
        in discipline_set
    )

    if not is_runner:
        return None

    if (
        metric
        is PhysiologicalMetric.VMA
    ):
        return (
            PhysiologicalTestType.HALF_COOPER
        )

    if (
        metric
        is PhysiologicalMetric.MAX_HEART_RATE
    ):
        return (
            PhysiologicalTestType.VAMEVAL
        )

    if metric in {
        PhysiologicalMetric.THRESHOLD_PACE,
        PhysiologicalMetric.THRESHOLD_HEART_RATE,
    }:
        # 20 minutes devient le protocole par défaut.
        # Le 30 min reste disponible mais n'est pas
        # notre premier choix en raison de son coût.
        return (
            PhysiologicalTestType.THRESHOLD_20_MIN
        )

    if metric in {
        PhysiologicalMetric.CRITICAL_SPEED,
        PhysiologicalMetric.D_PRIME,
    }:
        return (
            PhysiologicalTestType
            .CRITICAL_SPEED_MULTI_EFFORT
        )

    if (
        metric
        is PhysiologicalMetric.UPHILL_VAM
    ):
        if not is_trail:
            return None

        return (
            PhysiologicalTestType.UPHILL_6_MIN
        )

    if (
        metric
        is PhysiologicalMetric.UPHILL_SUSTAINED_VAM
    ):
        if not is_trail:
            return None

        return (
            PhysiologicalTestType.UPHILL_20_MIN
        )

    if (
        metric
        is PhysiologicalMetric.TRAIL_DURABILITY
    ):
        if not is_trail:
            return None

        return (
            PhysiologicalTestType.TRAIL_DURABILITY
        )

    return None


def _build_proposal_reason(
    *,
    freshness: MeasurementFreshness,
    metric: PhysiologicalMetric,
) -> str:
    if freshness is MeasurementFreshness.MISSING:
        return (
            f"Aucune mesure exploitable n'est disponible "
            f"pour {metric.value}. "
            "Une calibration améliorerait la précision "
            "des prochaines prescriptions."
        )

    if freshness is MeasurementFreshness.STALE:
        return (
            f"La mesure {metric.value} est devenue "
            "trop ancienne pour être considérée comme "
            "une référence optimale."
        )

    if freshness is MeasurementFreshness.AGING:
        return (
            f"La mesure {metric.value} commence à vieillir "
            "et la phase actuelle justifie une "
            "recalibration."
        )

    # Cas typique : mesure récente mais confiance faible.
    return (
        f"La mesure {metric.value} est récente mais "
        "sa confiance est insuffisante. "
        "Une mesure plus robuste est recommandée."
    )
