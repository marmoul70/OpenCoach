"""Proposition d'adaptation quotidienne du coach.

Ce module représente le dialogue entre le coach et l'athlète
lorsqu'un check-in quotidien justifie d'envisager une adaptation.

Principe fondamental :

- le coach peut proposer ou recommander une adaptation ;
- aucune adaptation n'est appliquée automatiquement ;
- l'athlète conserve la décision finale ;
- la décision doit pouvoir être conservée pour le suivi et
  le futur débriefing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID


class AdaptationDecision(StrEnum):
    """Décision prise par l'athlète."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"


@dataclass(frozen=True, slots=True)
class CoachAdaptationProposal:
    """Proposition d'adaptation soumise à l'athlète."""

    checkin_id: UUID

    reason: str
    recommendation: str

    id: UUID | None = None

    decision: AdaptationDecision = (
        AdaptationDecision.PENDING
    )

    def __post_init__(self) -> None:
        if not self.reason.strip():
            raise ValueError(
                "La raison de la proposition "
                "ne peut pas être vide."
            )

        if not self.recommendation.strip():
            raise ValueError(
                "La recommandation du coach "
                "ne peut pas être vide."
            )

    @property
    def awaiting_athlete_decision(
        self,
    ) -> bool:
        """Indique si l'athlète doit encore répondre."""

        return (
            self.decision
            is AdaptationDecision.PENDING
        )

    @property
    def adaptation_authorized(
        self,
    ) -> bool:
        """Indique si le coach peut appliquer l'adaptation."""

        return (
            self.decision
            is AdaptationDecision.ACCEPTED
        )

    def accept(
        self,
    ) -> "CoachAdaptationProposal":
        """Accepte explicitement la proposition."""

        return CoachAdaptationProposal(
            checkin_id=self.checkin_id,
            reason=self.reason,
            id=self.id,
            recommendation=self.recommendation,
            decision=AdaptationDecision.ACCEPTED,
        )

    def decline(
        self,
    ) -> "CoachAdaptationProposal":
        """Refuse explicitement la proposition."""

        return CoachAdaptationProposal(
            checkin_id=self.checkin_id,
            reason=self.reason,
            id=self.id,
            recommendation=self.recommendation,
            decision=AdaptationDecision.DECLINED,
        )
