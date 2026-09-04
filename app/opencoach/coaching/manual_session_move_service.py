"""Service applicatif de prévisualisation d'un déplacement manuel.

Ce service compose les données nécessaires au moteur pur de
déplacement sans modifier aucune séance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from opencoach.coaching.manual_session_move import (
    SessionMovePlan,
    evaluate_manual_session_move,
)
from opencoach.database.repositories.athlete_constraint import (
    AthleteConstraintRepository,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import (
    AthleteProfile,
)
from opencoach.planning.athlete.weekly_availability import (
    build_weekly_availability,
)


class ManualSessionMoveServiceError(
    RuntimeError
):
    """Erreur applicative du déplacement manuel."""


class ManualSessionMoveSessionNotFoundError(
    ManualSessionMoveServiceError
):
    """La séance demandée n'existe pas."""



class ManualSessionMoveTargetUnavailableError(
    ManualSessionMoveServiceError
):
    """La date demandée n'est pas autorisée."""


@dataclass(slots=True)
class ManualSessionMoveService:
    """Prépare les options de déplacement d'une séance."""

    training_session_repository: (
        TrainingSessionRepository
    )

    athlete_constraint_repository: (
        AthleteConstraintRepository
    )

    def preview(
        self,
        *,
        athlete_profile_id: UUID,
        athlete: AthleteProfile,
        session_id: UUID,
        reference_date: date,
    ) -> SessionMovePlan:
        """Retourne les recommandations pour les 7 jours."""

        session = (
            self.training_session_repository
            .get_session(
                athlete_profile_id,
                session_id,
            )
        )

        if session is None:
            raise (
                ManualSessionMoveSessionNotFoundError(
                    "Séance introuvable."
                )
            )

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

        week = (
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

        return evaluate_manual_session_move(
            session=session,
            week=week,
            existing_sessions=(
                existing_sessions
            ),
            reference_date=reference_date,
        )


    def move(
        self,
        *,
        athlete_profile_id: UUID,
        athlete: AthleteProfile,
        session_id: UUID,
        target_date: date,
        reference_date: date,
    ):
        """Déplace une séance après revalidation complète."""

        plan = self.preview(
            athlete_profile_id=(
                athlete_profile_id
            ),
            athlete=athlete,
            session_id=session_id,
            reference_date=reference_date,
        )

        target = next(
            (
                day
                for day in plan.days
                if day.date == target_date
            ),
            None,
        )

        if target is None:
            raise ManualSessionMoveTargetUnavailableError(
                "La date demandée est hors de la semaine."
            )

        if target.current:
            raise ManualSessionMoveTargetUnavailableError(
                "La séance est déjà prévue ce jour."
            )

        if not target.selectable:
            reason = (
                target.blocking_reasons[0]
                if target.blocking_reasons
                else "Ce jour n'est pas disponible."
            )

            raise ManualSessionMoveTargetUnavailableError(
                reason
            )

        session = (
            self.training_session_repository
            .get_session(
                athlete_profile_id,
                session_id,
            )
        )

        if session is None:
            raise (
                ManualSessionMoveSessionNotFoundError(
                    "Séance introuvable."
                )
            )

        session.date = target_date

        return (
            self.training_session_repository
            .save_session(
                athlete_profile_id,
                session,
            )
        )
