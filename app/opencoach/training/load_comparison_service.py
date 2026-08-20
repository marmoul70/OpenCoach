from datetime import date
from uuid import UUID

from opencoach.database.repositories import (
    TrainingSessionRepository,
)
from opencoach.models import TrainingSession

from .daily_load_service import (
    DailyTrainingLoadService,
)
from .load_comparison import (
    TrainingLoadComparison,
    classify_training_load,
)
from .load_estimation import (
    estimate_prescribed_load,
)


class TrainingLoadComparisonService:
    """Compare le programme OpenCoach au travail réellement effectué."""

    def __init__(
        self,
        training_session_repository: TrainingSessionRepository,
        daily_training_load_service: DailyTrainingLoadService,
    ) -> None:
        self.training_session_repository = (
            training_session_repository
        )

        self.daily_training_load_service = (
            daily_training_load_service
        )

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> TrainingLoadComparison:
        """Compare la charge prévue et la charge réelle d'une journée."""

        sessions = (
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                target_date,
                target_date,
            )
        )

        planned_session = (
            self._get_reference_session(
                sessions,
            )
        )

        actual = (
            self.daily_training_load_service
            .calculate(
                athlete_profile_id,
                target_date,
            )
        )

        if planned_session is None:
            planned_duration_minutes = 0
            planned_load = 0.0
            planned_sessions_count = 0

        else:
            planned_duration_minutes = (
                planned_session.duration_minutes
            )

            planned_load = (
                estimate_prescribed_load(
                    planned_session,
                )
            )

            planned_sessions_count = (
                0
                if planned_session.type == "rest"
                else 1
            )

        actual_load = (
            actual.total_load
        )

        return TrainingLoadComparison(
            date=target_date,

            planned_duration_minutes=(
                planned_duration_minutes
            ),

            actual_duration_minutes=(
                actual.total_duration_minutes
            ),

            planned_load=planned_load,
            actual_load=actual_load,

            measured_load=(
                actual.measured_load
            ),

            estimated_load=(
                actual.estimated_load
            ),

            planned_sessions_count=(
                planned_sessions_count
            ),

            actual_sessions_count=(
                actual.sessions_count
            ),

            status=classify_training_load(
                planned_load=planned_load,
                actual_load=actual_load,
            ),
        )

    @staticmethod
    def _get_reference_session(
        sessions: list[TrainingSession],
    ) -> TrainingSession | None:
        """Retourne la séance OpenCoach de référence de la journée."""

        coach_sessions = [
            session
            for session in sessions
            if session.type != "supplementary"
        ]

        if not coach_sessions:
            return None

        if len(coach_sessions) > 1:
            raise RuntimeError(
                "Plusieurs séances OpenCoach de référence "
                "sont disponibles pour la journée."
            )

        return coach_sessions[0]