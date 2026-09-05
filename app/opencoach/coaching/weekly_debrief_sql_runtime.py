"""Assemblage SQL du débrief hebdomadaire.

Cette couche fournit les repositories concrets nécessaires aux
briques métier T6.5 tout en restant indépendante du scheduler et
du transport HTTP.

Le contexte de planning de la semaine suivante sera raccordé dans
l'étape suivante.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.coaching.weekly_debrief_closure import (
    WeeklyDebriefClosureService,
)
from opencoach.coaching.weekly_debrief_runtime_context import (
    WeeklyDebriefRuntimeFacts,
    build_weekly_debrief_runtime_facts,
)
from opencoach.database.models import (
    AthleteProfile,
    User,
)
from opencoach.database.repositories.sql_activity import (
    SqlActivityRepository,
)
from opencoach.database.repositories.sql_session_execution_analysis import (
    SqlSessionExecutionAnalysisRepository,
)
from opencoach.database.repositories.sql_training_session import (
    SqlTrainingSessionRepository,
)
from opencoach.database.repositories.sql_weekly_debrief import (
    SqlWeeklyDebriefRepository,
)
from opencoach.database.repositories.sql_weekly_training_plan import (
    SqlWeeklyTrainingPlanRepository,
)


def load_active_athlete_profile_ids(
    database: Session,
) -> tuple[UUID, ...]:
    """Charge tous les profils appartenant à un utilisateur actif."""

    statement = (
        select(
            AthleteProfile.id
        )
        .join(
            AthleteProfile.user
        )
        .where(
            User.active.is_(True)
        )
        .order_by(
            AthleteProfile.id
        )
    )

    return tuple(
        database.scalars(
            statement
        ).all()
    )


class SqlWeeklyDebriefRuntime:
    """Façade SQL concrète des composants hebdomadaires."""

    def __init__(
        self,
        database: Session,
    ) -> None:
        self.database = database

        self.training_sessions = (
            SqlTrainingSessionRepository(
                database
            )
        )

        self.activities = (
            SqlActivityRepository(
                database
            )
        )

        self.weekly_plans = (
            SqlWeeklyTrainingPlanRepository(
                database
            )
        )

        self.execution_analyses = (
            SqlSessionExecutionAnalysisRepository(
                database
            )
        )

        self.weekly_debriefs = (
            SqlWeeklyDebriefRepository(
                database
            )
        )

    def active_profile_ids(
        self,
    ) -> tuple[UUID, ...]:
        """Retourne les profils actifs du système."""

        return load_active_athlete_profile_ids(
            self.database
        )

    def build_runtime_facts(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
    ) -> WeeklyDebriefRuntimeFacts:
        """Résout les faits runtime depuis les repositories SQL."""

        return build_weekly_debrief_runtime_facts(
            athlete_profile_id=athlete_profile_id,
            reference_date=reference_date,
            session_reader=self.training_sessions,
            activity_reader=self.activities,
        )

    def build_closure_service(
        self,
    ) -> WeeklyDebriefClosureService:
        """Construit T6.5.3 avec toutes ses sources SQL réelles."""

        return WeeklyDebriefClosureService(
            session_reader=(
                self.training_sessions
            ),
            activity_reader=(
                self.activities
            ),
            weekly_plan_reader=(
                self.weekly_plans
            ),
            execution_analysis_reader=(
                self.execution_analyses
            ),
            debrief_repository=(
                self.weekly_debriefs
            ),
        )
