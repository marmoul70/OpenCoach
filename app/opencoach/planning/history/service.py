from datetime import date, timedelta
from uuid import UUID

from opencoach.database.repositories import (
    ActivityRepository,
)
from opencoach.training import (
    TrainingStats,
    TrainingStatsService,
)

from opencoach.planning.history.training import (
    TrainingHistorySnapshot,
)


class TrainingHistorySnapshotService:
    """Construit l'historique multi-fenêtres utilisé par le planificateur."""

    def __init__(
        self,
        training_stats_service: TrainingStatsService,
        activity_repository: ActivityRepository,
    ) -> None:
        self.training_stats_service = (
            training_stats_service
        )
        self.activity_repository = (
            activity_repository
        )

    def build(
        self,
        athlete_profile_id: UUID,
        reference_date: date,
    ) -> TrainingHistorySnapshot:
        """Construit les fenêtres précédant la date de référence."""

        last_7_days = self._calculate_window(
            athlete_profile_id=athlete_profile_id,
            reference_date=reference_date,
            days=7,
        )

        last_28_days = self._calculate_window(
            athlete_profile_id=athlete_profile_id,
            reference_date=reference_date,
            days=28,
        )

        last_42_days = self._calculate_window(
            athlete_profile_id=athlete_profile_id,
            reference_date=reference_date,
            days=42,
        )

        last_84_days = self._calculate_window(
            athlete_profile_id=athlete_profile_id,
            reference_date=reference_date,
            days=84,
        )

        activities_start_date = (
            reference_date
            - timedelta(days=84)
        )

        activities_end_date = (
            reference_date
            - timedelta(days=1)
        )

        activities = (
            self.activity_repository.list_activities_between(
                athlete_profile_id,
                activities_start_date,
                activities_end_date,
            )
        )

        return TrainingHistorySnapshot(
            reference_date=reference_date,
            last_7_days=last_7_days,
            last_28_days=last_28_days,
            last_42_days=last_42_days,
            last_84_days=last_84_days,
            activities_84_days=tuple(activities),
        )

    def _calculate_window(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
        days: int,
    ) -> TrainingStats:
        """Calcule exactement les N jours précédant la référence."""

        start_date = (
            reference_date
            - timedelta(days=days)
        )

        end_date = (
            reference_date
            - timedelta(days=1)
        )

        return self.training_stats_service.calculate(
            athlete_profile_id,
            start_date,
            end_date,
        )
