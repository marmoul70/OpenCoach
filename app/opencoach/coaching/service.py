from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.config import (
    ThresholdSettings,
    get_threshold_settings,
)
from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.models import TrainingSession
from opencoach.readiness.service import (
    ReadinessAssessment,
    ReadinessService,
)

from .decision import decide_training_session
from .models import CoachDecision


class CoachDecisionServiceError(RuntimeError):
    """Erreur métier du service de décision du coach."""


class PlannedSessionUnavailableError(
    CoachDecisionServiceError
):
    """Aucune séance planifiée disponible pour la date demandée."""


@dataclass(frozen=True)
class CoachDecisionAssessment:
    """Décision complète du coach pour une séance planifiée."""

    date: date
    session: TrainingSession | None
    readiness: ReadinessAssessment
    decision: CoachDecision


class CoachDecisionService:
    """Orchestre la décision du coach pour une séance planifiée."""

    def __init__(
        self,
        training_repository: TrainingSessionRepository,
        readiness_service: ReadinessService,
        *,
        thresholds: ThresholdSettings | None = None,
    ) -> None:
        self.training_repository = training_repository
        self.readiness_service = readiness_service

        self.thresholds = (
            thresholds
            if thresholds is not None
            else get_threshold_settings()
        )

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> CoachDecisionAssessment:
        """Calcule la décision du coach pour une date."""

        sessions = (
            self.training_repository
            .list_sessions_between(
                athlete_profile_id,
                target_date,
                target_date,
            )
        )

        planned_sessions = [
            session
            for session in sessions
            if session.status == "planned"
        ]

        if not planned_sessions:
            readiness = self.readiness_service.calculate(
                athlete_profile_id,
                target_date,
            )

            decision = CoachDecision(
                action="rest",
                reason=(
                    "Aucune séance n'est planifiée aujourd'hui. "
                    "Journée de repos maintenue."
                ),
                original_duration_minutes=None,
                recommended_duration_minutes=None,
                duration_factor=None,
                intensity_factor=None,
                constraints=(
                    readiness.readiness.training_constraints
                ),
                original_intensity=None,
                recommended_intensity=None,
            )

            return CoachDecisionAssessment(
                date=target_date,
                session=None,
                readiness=readiness,
                decision=decision,
            )

        if len(planned_sessions) > 1:
            raise CoachDecisionServiceError(
                (
                    "Plusieurs séances planifiées sont "
                    f"disponibles pour le {target_date.isoformat()}."
                )
            )

        session = planned_sessions[0]

        readiness = self.readiness_service.calculate(
            athlete_profile_id,
            target_date,
        )

        decision = decide_training_session(
            session=session,
            readiness=readiness.readiness,
            thresholds=self.thresholds.coach_decision,
        )

        return CoachDecisionAssessment(
            date=target_date,
            session=session,
            readiness=readiness,
            decision=decision,
        )