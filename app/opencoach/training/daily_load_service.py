from datetime import date
from uuid import UUID

from opencoach.database.repositories import (
    ActivityRepository,
    TrainingSessionRepository,
)
from .load_estimation import (
    estimate_session_load,
)
from opencoach.models import Activity, TrainingSession

from .daily_load import DailyTrainingLoad


class DailyTrainingLoadService:
    """Calcule la charge sportive réellement effectuée."""

    def __init__(
        self,
        activity_repository: ActivityRepository,
        training_session_repository: TrainingSessionRepository,
    ) -> None:
        self.activity_repository = activity_repository
        self.training_session_repository = (
            training_session_repository
        )

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> DailyTrainingLoad:
        """Calcule la charge réelle d'une journée."""

        activities = (
            self.activity_repository.list_activities_between(
                athlete_profile_id,
                target_date,
                target_date,
            )
        )

        sessions = (
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                target_date,
                target_date,
            )
        )

        manual_sessions = [
            session
            for session in sessions
            if self._is_manual_completed_session(
                session,
            )
        ]

        total_duration_minutes = (
            sum(
                self._activity_duration_minutes(
                    activity,
                )
                for activity in activities
            )
            + sum(
                session.duration_minutes
                for session in manual_sessions
            )
        )

        total_distance_km = (
            sum(
                (activity.distance_m or 0.0)
                / 1000.0
                for activity in activities
            )
            + sum(
                session.distance_km or 0.0
                for session in manual_sessions
            )
        )

        total_elevation_gain_m = (
            sum(
                activity.elevation_gain_m or 0.0
                for activity in activities
            )
            + sum(
                session.elevation_gain_m or 0.0
                for session in manual_sessions
            )
        )

        measured_load = sum(
            activity.training_load or 0.0
            for activity in activities
        )

        estimated_load = sum(
            estimate_session_load(
                session,
            )
            for session in manual_sessions
        )

        sport_types = tuple(
            sorted(
                {
                    *(
                        activity.sport_type
                        for activity in activities
                    ),
                    *(
                        session.sport_type
                        for session in manual_sessions
                    ),
                }
            )
        )

        return DailyTrainingLoad(
            date=target_date,
            activities_count=len(
                activities,
            ),
            manual_sessions_count=len(
                manual_sessions,
            ),
            total_duration_minutes=(
                total_duration_minutes
            ),
            total_distance_km=round(
                total_distance_km,
                3,
            ),
            total_elevation_gain_m=round(
                total_elevation_gain_m,
                1,
            ),
            measured_load=round(
                measured_load,
                2,
            ),
            estimated_load=round(
                estimated_load,
                2,
            ),
            sport_types=sport_types,
        )

    @staticmethod
    def _is_manual_completed_session(
        session: TrainingSession,
    ) -> bool:
        """Détermine si une séance doit être comptée manuellement."""

        return (
            session.status == "completed"
            and session.activity_id is None
            and session.type != "rest"
        )

    @staticmethod
    def _activity_duration_minutes(
        activity: Activity,
    ) -> int:
        """Retourne la meilleure durée disponible pour une activité."""

        seconds = (
            activity.moving_time_seconds
            if activity.moving_time_seconds is not None
            else activity.elapsed_time_seconds
        )

        if seconds is None:
            return 0

        return round(
            seconds / 60,
        )
