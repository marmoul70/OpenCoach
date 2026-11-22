from datetime import date, timedelta
from uuid import UUID

from opencoach.database.repositories import (
    ActivityRepository,
    TrainingSessionRepository,
)
from opencoach.models import (
    Activity,
    TrainingSession,
)

from .load_estimation import (
    estimate_session_load,
)
from .stats import TrainingStats


class TrainingStatsService:
    """Calcule les statistiques réellement effectuées
    sur une période.
    """

    def __init__(
        self,
        activity_repository: ActivityRepository,
        training_session_repository: TrainingSessionRepository,
        *,
        reference_date_provider=date.today,
    ) -> None:
        self.activity_repository = activity_repository
        self.training_session_repository = (
            training_session_repository
        )
        self.reference_date_provider = reference_date_provider

    def calculate(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
    ) -> TrainingStats:
        """Calcule les statistiques réelles d'une période."""

        if end_date < start_date:
            raise ValueError(
                "La date de fin doit être "
                "postérieure ou égale à la date de début."
            )

        activities = (
            self.activity_repository
            .list_activities_between(
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        sessions = (
            self.training_session_repository
            .list_sessions_between(
                athlete_profile_id,
                start_date,
                end_date,
            )
        )

        manual_sessions = [
            session
            for session in sessions
            if self._is_manual_completed_session(
                session
            )
        ]

        total_duration_minutes = (
            sum(
                self._activity_duration_minutes(
                    activity
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

        duration_data_count = sum(
            activity.moving_time_seconds is not None
            or activity.elapsed_time_seconds is not None
            for activity in activities
        ) + sum(
            session.duration_minutes is not None
            for session in manual_sessions
        )
        distance_data_count = sum(
            activity.distance_m is not None for activity in activities
        ) + sum(
            session.distance_km is not None for session in manual_sessions
        )
        elevation_data_count = sum(
            activity.elevation_gain_m is not None for activity in activities
        ) + sum(
            session.elevation_gain_m is not None for session in manual_sessions
        )
        measured_load_data_count = sum(
            activity.training_load is not None for activity in activities
        )
        estimated_load_data_count = sum(
            session.duration_minutes is not None and session.duration_minutes > 0
            for session in manual_sessions
        )

        measured_load = sum(
            activity.training_load or 0.0
            for activity in activities
        )

        estimated_load = sum(
            estimate_session_load(
                session
            )
            for session in manual_sessions
        )

        return TrainingStats(
            start_date=start_date,
            end_date=end_date,
            activities_count=len(
                activities
            ),
            manual_sessions_count=len(
                manual_sessions
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
            duration_data_count=duration_data_count,
            distance_data_count=distance_data_count,
            elevation_data_count=elevation_data_count,
            measured_load_data_count=measured_load_data_count,
            estimated_load_data_count=estimated_load_data_count,
        )

    def compare_adjacent_periods(
        self,
        athlete_profile_id: UUID,
        *,
        reference_date: date | None = None,
        current_days: int,
        comparison_days: int,
    ) -> dict:
        """Compare deux périodes successives de statistiques d'entraînement.

        Les fenêtres sont ancrées sur la veille de reference_date afin de ne
        comparer que des journées entièrement écoulées. La couverture et les
        écarts restent ceux du modèle TrainingStats.
        """
        reference_date = reference_date or self.reference_date_provider()
        if not 1 <= current_days <= 180:
            raise ValueError("La période récente doit être comprise entre 1 et 180 jours.")
        if not 1 <= comparison_days <= 180:
            raise ValueError("La période de comparaison doit être comprise entre 1 et 180 jours.")

        current_end = reference_date - timedelta(days=1)
        current_start = current_end - timedelta(days=current_days - 1)
        comparison_end = current_start - timedelta(days=1)
        comparison_start = comparison_end - timedelta(days=comparison_days - 1)

        current = self.calculate(athlete_profile_id, current_start, current_end)
        comparison = self.calculate(athlete_profile_id, comparison_start, comparison_end)
        comparison_result = current.compare_to(comparison)

        return {
            "current_period": {
                "start_date": current.start_date.isoformat(),
                "end_date": current.end_date.isoformat(),
                "nb_days": current_days,
                "sessions": current.sessions_count,
            },
            "comparison_period": {
                "start_date": comparison.start_date.isoformat(),
                "end_date": comparison.end_date.isoformat(),
                "nb_days": comparison_days,
                "sessions": comparison.sessions_count,
            },
            "metrics": comparison_result["metrics"],
            "warnings": comparison_result["warnings"],
        }

    def calculate_days(
        self,
        athlete_profile_id: UUID,
        reference_date: date | None = None,
        *,
        days: int = 7,
        include_reference_day: bool = True,
    ) -> TrainingStats:
        """Calcule une fenêtre calendaire inclusive à partir d'une date d'ancrage."""
        reference_date = reference_date or self.reference_date_provider()
        if not 1 <= days <= 365:
            raise ValueError("La période doit être comprise entre 1 et 365 jours (au moins un jour).")
        end_date = reference_date if include_reference_day else reference_date - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)
        return self.calculate(athlete_profile_id, start_date, end_date)

    @staticmethod
    def _is_manual_completed_session(
        session: TrainingSession,
    ) -> bool:
        """Détermine si une séance terminée doit servir
        de fallback en l'absence d'activité réelle.
        """

        return (
            session.status == "completed"
            and session.activity_id is None
            and session.type != "rest"
        )

    @staticmethod
    def _activity_duration_minutes(
        activity: Activity,
    ) -> int:
        """Retourne la meilleure durée réelle disponible."""

        seconds = (
            activity.moving_time_seconds
            if activity.moving_time_seconds is not None
            else activity.elapsed_time_seconds
        )

        if seconds is None:
            return 0

        return round(
            seconds / 60
        )
