"""Construction des propositions d'adaptation quotidiennes.

Le service transforme l'analyse d'un DailyCheckIn en proposition
destinée à l'athlète.

Il ne modifie jamais directement une séance.
"""

from __future__ import annotations

from uuid import UUID

from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)
from opencoach.coaching.daily_checkin_policy import (
    CheckInCoachAction,
    DailyCheckInAssessment,
)


def build_daily_adaptation_proposal(
    *,
    checkin_id: UUID,
    assessment: DailyCheckInAssessment,
) -> CoachAdaptationProposal | None:
    """Construit une proposition lorsque l'accord est nécessaire."""

    if assessment.action in {
        CheckInCoachAction.NONE,
        CheckInCoachAction.MONITOR,
    }:
        return None

    reason = _build_reason(
        assessment
    )

    if (
        assessment.action
        is CheckInCoachAction.OFFER_ADAPTATION
    ):
        recommendation = (
            "Ton check-in indique qu'une adaptation peut être "
            "pertinente. Veux-tu adapter la séance prévue ?"
        )

    else:
        recommendation = (
            "Ton check-in indique qu'une adaptation de la séance "
            "est fortement recommandée. Veux-tu que le coach "
            "adapte la séance prévue ?"
        )

    return CoachAdaptationProposal(
        checkin_id=checkin_id,
        reason=reason,
        recommendation=recommendation,
    )


def _build_reason(
    assessment: DailyCheckInAssessment,
) -> str:
    """Construit une explication lisible depuis l'évaluation."""

    if assessment.reasons:
        return " ".join(
            assessment.reasons
        )

    return (
        "Le check-in nécessite une attention "
        "particulière du coach."
    )
