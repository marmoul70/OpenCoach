"""Proposition d'un test physiologique par OpenCoach.

Un test n'est jamais imposé à l'athlète.

Le coach peut recommander un protocole lorsqu'une mesure mérite
d'être recalibrée, mais l'athlète conserve la décision finale.

En cas de refus, le test est remplacé par une séance qualitative
cohérente avec le stimulus d'entraînement qui devait être travaillé.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date
from enum import StrEnum
from uuid import UUID

from opencoach.physiology.testing.models import (
    PhysiologicalMetric,
    PhysiologicalTestType,
)


class PhysiologicalTestDecision(StrEnum):
    """Décision de l'athlète concernant le test."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class PhysiologicalTestReplacementStimulus(StrEnum):
    """Stimulus utilisé si l'athlète refuse le test.

    Le remplacement conserve une séance de qualité sans
    obliger l'athlète à effectuer une évaluation maximale.
    """

    AEROBIC_POWER = "aerobic_power"
    THRESHOLD = "threshold"
    UPHILL_INTENSITY = "uphill_intensity"
    LONG_TRAIL_QUALITY = "long_trail_quality"


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestProposal:
    """Proposition de test soumise à l'athlète."""

    athlete_profile_id: UUID

    protocol: PhysiologicalTestType

    target_metrics: tuple[
        PhysiologicalMetric,
        ...,
    ]

    proposed_date: date

    reason: str
    recommendation: str

    replacement_stimulus: (
        PhysiologicalTestReplacementStimulus
    )

    id: UUID | None = None

    target_session_id: UUID | None = None

    decision: PhysiologicalTestDecision = (
        PhysiologicalTestDecision.PENDING
    )

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(
                "La raison du test "
                "ne peut pas être vide."
            )

        if not self.recommendation.strip():
            raise ValueError(
                "La recommandation du coach "
                "ne peut pas être vide."
            )

        if not self.target_metrics:
            raise ValueError(
                "Une proposition doit cibler "
                "au moins une métrique."
            )

    @property
    def awaiting_athlete_decision(
        self,
    ) -> bool:
        """Indique si l'athlète doit encore répondre."""

        return (
            self.decision
            is PhysiologicalTestDecision.PENDING
        )

    @property
    def test_authorized(
        self,
    ) -> bool:
        """Indique si le test peut être programmé."""

        return (
            self.decision
            is PhysiologicalTestDecision.ACCEPTED
        )

    @property
    def replacement_required(
        self,
    ) -> bool:
        """Indique qu'une séance de remplacement est nécessaire."""

        return (
            self.decision
            is PhysiologicalTestDecision.DECLINED
        )

    def assign_to_session(
        self,
        session_id: UUID,
    ) -> "PhysiologicalTestProposal":
        """Rattache la proposition à une séance planifiée.

        Cette opération ne remplace pas encore la séance.
        Elle mémorise uniquement la séance qualitative
        susceptible d'être remplacée si l'athlète accepte.
        """

        return replace(
            self,
            target_session_id=session_id,
        )

    def accept(
        self,
    ) -> "PhysiologicalTestProposal":
        """Accepte explicitement le test."""

        return replace(
            self,
            decision=(
                PhysiologicalTestDecision.ACCEPTED
            ),
        )

    def decline(
        self,
    ) -> "PhysiologicalTestProposal":
        """Refuse le test sans supprimer le stimulus de qualité."""

        return replace(
            self,
            decision=(
                PhysiologicalTestDecision.DECLINED
            ),
        )
