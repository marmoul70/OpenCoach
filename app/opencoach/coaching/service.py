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
from opencoach.training import (
    RecentLoadAssessment,
    RecentTrainingLoad,
    RecentTrainingLoadService,
    assess_recent_training_load,
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
class CoachSessionDecision:
    """Décision du coach associée à une séance."""

    session: TrainingSession | None
    decision: CoachDecision


@dataclass(frozen=True)
class CoachDecisionAssessment:
    """Décision complète du coach pour une journée."""

    date: date

    session_decisions: tuple[
        CoachSessionDecision,
        ...
    ]

    readiness: ReadinessAssessment

    recent_load: RecentTrainingLoad | None = None

    recent_load_assessment: (
        RecentLoadAssessment
        | None
    ) = None

    @property
    def session(
        self,
    ) -> TrainingSession | None:
        """Compatibilité historique pour une seule séance."""

        if len(
            self.session_decisions
        ) != 1:
            return None

        return (
            self.session_decisions[0]
            .session
        )

    @property
    def decision(
        self,
    ) -> CoachDecision:
        """Compatibilité historique pour une seule décision."""

        if len(
            self.session_decisions
        ) != 1:
            raise CoachDecisionServiceError(
                "La journée contient plusieurs décisions de séance."
            )

        return (
            self.session_decisions[0]
            .decision
        )


class CoachDecisionService:
    """Orchestre la décision du coach pour une séance planifiée."""

    def __init__(
        self,
        training_repository: TrainingSessionRepository,
        readiness_service: ReadinessService,
        *,
        recent_load_service: RecentTrainingLoadService | None = None,
        thresholds: ThresholdSettings | None = None,
    ) -> None:
        self.training_repository = training_repository
        self.readiness_service = readiness_service
        self.recent_load_service = recent_load_service

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

        skipped_sessions = [
            session
            for session in sessions
            if session.status == "skipped"
            and session.type != "rest"
        ]

        completed_sessions = [
            session
            for session in sessions
            if session.status == "completed"
            and session.type != "rest"
        ]

        readiness = self.readiness_service.calculate(
            athlete_profile_id,
            target_date,
        )

        recent_load = None
        recent_load_assessment = None

        if self.recent_load_service is not None:
            recent_load = (
                self.recent_load_service.calculate(
                    athlete_profile_id,
                    target_date,
                )
            )

            recent_load_assessment = (
                assess_recent_training_load(
                    recent_load,
                )
            )

        if not planned_sessions:
            historical_session = None

            if skipped_sessions:
                historical_session = skipped_sessions[0]

                reason = (
                    f"La séance « {historical_session.title} » "
                    "prévue aujourd'hui a été déclarée "
                    "non réalisée. Aucune autre séance "
                    "n'est planifiée aujourd'hui."
                )

            elif completed_sessions:
                historical_session = completed_sessions[0]

                reason = (
                    f"La séance « {historical_session.title} » "
                    "prévue aujourd'hui a déjà été réalisée. "
                    "Aucune autre séance n'est planifiée."
                )

            else:
                reason = (
                    "Aucune séance n'est planifiée aujourd'hui. "
                    "Journée de repos maintenue."
                )

            decision = CoachDecision(
                action="rest",
                reason=reason,
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
                session_decisions=(
                    CoachSessionDecision(
                        session=historical_session,
                        decision=decision,
                    ),
                ),
                readiness=readiness,
                recent_load=recent_load,
                recent_load_assessment=(
                    recent_load_assessment
                ),
            )

        session_decisions = tuple(
            CoachSessionDecision(
                session=session,
                decision=decide_training_session(
                    session=session,
                    readiness=(
                        readiness.readiness
                    ),
                    thresholds=(
                        self.thresholds
                        .coach_decision
                    ),
                    recent_load=(
                        recent_load_assessment
                    ),
                ),
            )
            for session
            in planned_sessions
        )

        return CoachDecisionAssessment(
            date=target_date,
            session_decisions=(
                session_decisions
            ),
            readiness=readiness,
            recent_load=recent_load,
            recent_load_assessment=(
                recent_load_assessment
            ),
        )
