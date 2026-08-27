"""Orchestration d'une proposition de report quotidien.

Ce service construit le contexte nécessaire au moteur pur de
proposition de report après l'annulation d'une séance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from opencoach.coaching.daily_session_rescheduling import (
    DailySessionReschedulingProposal,
    propose_daily_session_rescheduling,
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
class DailySessionReschedulingService:
    """Construit et évalue un éventuel report de séance."""

    training_session_repository: TrainingSessionRepository
    athlete_constraint_repository: AthleteConstraintRepository

    def propose(
        self,
        *,
        athlete_profile_id: UUID,
        athlete: AthleteProfile,
        session: TrainingSession,
    ) -> DailySessionReschedulingProposal | None:
        """Propose le meilleur report restant dans la semaine."""

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

        week = build_weekly_availability(
            athlete=athlete,
            week_start=week_start,
            constraints=tuple(
                constraints
            ),
        )

        existing_sessions = tuple(
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                week_start,
                week_end,
            )
        )

        return propose_daily_session_rescheduling(
            session=session,
            week=week,
            existing_sessions=existing_sessions,
            reference_date=session.date,
        )
