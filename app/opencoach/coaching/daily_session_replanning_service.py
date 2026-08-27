"""Orchestration de la replanification quotidienne multi-options.

Ce service construit le contexte nécessaire au moteur métier pur :

- disponibilité effective de toute la semaine ;
- contraintes temporaires de l'athlète ;
- séances déjà présentes dans la semaine.

Il ne persiste aucune décision de replanification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from opencoach.coaching.daily_session_replanning import (
    DailySessionReplanningProposal,
    propose_daily_session_replanning,
)
from opencoach.database.repositories.athlete_constraint import (
    AthleteConstraintRepository,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    AthleteProfile,
    TrainingSession,
)
from opencoach.planning.athlete.weekly_availability import (
    build_weekly_availability,
)


@dataclass(slots=True)
class DailySessionReplanningService:
    """Construit une proposition multi-options pour une séance annulée."""

    training_session_repository: (
        TrainingSessionRepository
    )

    athlete_constraint_repository: (
        AthleteConstraintRepository
    )

    def propose(
        self,
        *,
        athlete_profile_id: UUID,
        athlete: AthleteProfile,
        session: TrainingSession,
    ) -> DailySessionReplanningProposal | None:
        """Construit les choix de replanification restants dans la semaine."""

        week_start = (
            session.date
            - timedelta(
                days=session.date.weekday(),
            )
        )

        week_end = (
            week_start
            + timedelta(
                days=6,
            )
        )

        constraints = (
            self.athlete_constraint_repository
            .list_overlapping(
                athlete_profile_id,
                week_start,
                week_end,
            )
        )

        weekly_availability = (
            build_weekly_availability(
                athlete=athlete,
                week_start=week_start,
                constraints=tuple(
                    constraints
                ),
            )
        )

        existing_sessions = tuple(
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                week_start,
                week_end,
            )
        )

        return (
            propose_daily_session_replanning(
                session=session,
                week=weekly_availability,
                existing_sessions=(
                    existing_sessions
                ),
                reference_date=session.date,
            )
        )
