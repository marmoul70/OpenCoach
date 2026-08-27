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

        planned_sessions = (
            self._get_reference_sessions(
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

        has_prescription = bool(
            planned_sessions
        )

        has_planned_rest = any(
            session.type == "rest"
            for session in planned_sessions
        )

        planned_duration_minutes = sum(
            session.duration_minutes
            for session in planned_sessions
            if session.type != "rest"
        )

        planned_load = sum(
            estimate_prescribed_load(
                session,
            )
            for session in planned_sessions
            if session.type != "rest"
        )

        planned_sessions_count = sum(
            1
            for session in planned_sessions
            if session.type != "rest"
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
                has_prescription=(
                    has_prescription
                ),
                has_planned_rest=(
                    has_planned_rest
                ),
            ),
        )

    @staticmethod
    def _get_reference_sessions(
        sessions: list[TrainingSession],
    ) -> tuple[
        TrainingSession,
        ...,
    ]:
        """Retourne les séances OpenCoach de référence de la journée.

        Plusieurs séances peuvent légitimement partager une même date,
        par exemple une sortie facile suivie d'un renforcement.

        Les séances supplementary restent exclues de la référence.
        """

        return tuple(
            session
            for session in sessions
            if session.type != "supplementary"
        )
