from datetime import date

from opencoach.database.repositories import ActivityRepository
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
    ) -> None:
        self.client = client
        self.repository = repository

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