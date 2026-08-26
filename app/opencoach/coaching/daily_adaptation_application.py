"""Application d'une adaptation quotidienne acceptée.

Ce service constitue la frontière entre :

- la décision explicite de l'athlète ;
- la politique d'adaptation de séance ;
- la persistance de la séance modifiée.

Une seule séance planifiée doit être identifiable sans ambiguïté.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from opencoach.coaching.daily_adaptation import (
    CoachAdaptationProposal,
)
from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
)
from opencoach.coaching.daily_session_adaptation import (
    DailySessionAdaptationResult,
    adapt_daily_training_session,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    TrainingSession,
)


class DailyAdaptationApplicationError(
    RuntimeError
):
    """Erreur d'application d'une adaptation quotidienne."""


class DailyAdaptationSessionNotFoundError(
    DailyAdaptationApplicationError
):
    """Aucune séance planifiée ne peut être adaptée."""


class DailyAdaptationSessionAmbiguousError(
    DailyAdaptationApplicationError
):
    """Plusieurs séances sont candidates à l'adaptation."""


@dataclass(slots=True)
class ApplyAcceptedDailyAdaptationService:
    """Applique une proposition explicitement acceptée."""

    training_session_repository: (
        TrainingSessionRepository
    )

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        checkin: AthleteDailyCheckIn,
        proposal: CoachAdaptationProposal,
    ) -> DailySessionAdaptationResult:
        """Adapte l'unique séance planifiée du jour."""

        if checkin.id is None:
            raise DailyAdaptationApplicationError(
                "Le check-in doit être persisté."
            )

        if proposal.checkin_id != checkin.id:
            raise DailyAdaptationApplicationError(
                "La proposition ne correspond pas au check-in."
            )

        if not proposal.adaptation_authorized:
            raise DailyAdaptationApplicationError(
                "L'adaptation n'a pas été acceptée "
                "par l'athlète."
            )

        sessions = (
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                checkin.date,
                checkin.date,
            )
        )

        candidates = tuple(
            session
            for session in sessions
            if (
                session.status == "planned"
                and session.activity_id is None
            )
        )

        if not candidates:
            raise DailyAdaptationSessionNotFoundError(
                "Aucune séance planifiée aujourd'hui "
                "ne peut être adaptée."
            )

        if len(candidates) > 1:
            raise DailyAdaptationSessionAmbiguousError(
                "Plusieurs séances sont planifiées aujourd'hui. "
                "L'athlète doit choisir la séance à adapter."
            )

        original = candidates[0]

        result = adapt_daily_training_session(
            session=original,
            checkin=checkin,
            proposal=proposal,
        )

        if not result.changed:
            return result

        persisted = (
            self.training_session_repository
            .save_session(
                athlete_profile_id,
                result.adapted,
            )
        )

        return DailySessionAdaptationResult(
            original=result.original,
            adapted=persisted,
            changed=True,
            reasons=result.reasons,
        )
