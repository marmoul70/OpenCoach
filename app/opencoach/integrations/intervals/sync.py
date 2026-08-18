from datetime import date
from opencoach.database.repositories import (
    ActivityRepository,
    WellnessRepository,
)
from opencoach.integrations.intervals.wellness_mapper import (
    map_intervals_wellness,
)
from opencoach.integrations.intervals.client import IntervalsClient
from opencoach.integrations.intervals.mapper import (
    map_intervals_activity,
)

class IntervalsSyncService:
    """Synchronise les activités Intervals.icu vers OpenCoach."""

    def __init__(
        self,
        client: IntervalsClient,
        repository: ActivityRepository,
        wellness_repository: WellnessRepository | None = None,
    ) -> None:
        self.client = client
        self.repository = repository
        self.wellness_repository = wellness_repository

    def sync_activities(
        self,
        athlete_profile_id,
        oldest: date,
        newest: date,
    ) -> int:
        raw_activities = self.client.get_activities(
            oldest,
            newest,
        )

        synced = 0

        for raw_activity in raw_activities:
            activity = map_intervals_activity(
                raw_activity,
            )

            self.repository.save_activity(
                athlete_profile_id,
                activity,
            )

            synced += 1

        return synced

    def sync_wellness(
        self,
        athlete_profile_id,
        oldest: date,
        newest: date,
    ) -> int:
        if self.wellness_repository is None:
            raise RuntimeError(
                "Le repository Wellness n'est pas configuré."
            )

        raw_wellness = self.client.get_wellness(
            oldest,
            newest,
        )

        synced = 0

        for raw_day in raw_wellness:
            wellness = map_intervals_wellness(
                raw_day,
            )

            self.wellness_repository.save_wellness_day(
                athlete_profile_id,
                wellness,
            )

            synced += 1

        return synced