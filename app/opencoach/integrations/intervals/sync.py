from datetime import date

from opencoach.database.repositories import (
    ActivityDetailRepository,
    ActivityRepository,
    WellnessRepository,
)
from opencoach.integrations.intervals.activity_detail_mapper import (
    map_intervals_activity_detail,
)
from opencoach.integrations.intervals.client import IntervalsClient
from opencoach.integrations.intervals.mapper import (
    map_intervals_activity,
)
from opencoach.integrations.intervals.wellness_mapper import (
    map_intervals_wellness,
)


COACH_STREAM_TYPES = (
    "time",
    "distance",
    "heartrate",
    "velocity_smooth",
    "cadence",
    "watts",
)


class IntervalsSyncService:
    """Synchronise les données Intervals.icu vers OpenCoach."""

    def __init__(
        self,
        client: IntervalsClient,
        repository: ActivityRepository,
        activity_detail_repository: ActivityDetailRepository,
        wellness_repository: WellnessRepository | None = None,
    ) -> None:
        self.client = client
        self.repository = repository
        self.activity_detail_repository = (
            activity_detail_repository
        )
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

            provider_activity_id = (
                activity.provider_activity_id
            )

            raw_detail = (
                self.client.get_activity_details(
                    provider_activity_id,
                    include_intervals=True,
                )
            )

            stream_types = _select_coach_stream_types(
                raw_detail,
            )

            raw_streams = (
                self.client.get_activity_streams(
                    provider_activity_id,
                    types=stream_types,
                )
                if stream_types
                else []
            )

            detail = map_intervals_activity_detail(
                raw_detail,
                raw_streams,
            )

            self.activity_detail_repository.save_activity_detail(
                athlete_profile_id,
                detail,
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

def _select_coach_stream_types(
    raw_detail: dict,
) -> tuple[str, ...]:
    """Sélectionne uniquement les streams utiles et disponibles.

    Intervals.icu peut refuser une requête lorsqu'un type demandé
    n'existe pas pour l'activité. Le détail d'activité expose la liste
    ``stream_types`` permettant de construire une requête exacte.
    """

    available = raw_detail.get(
        "stream_types"
    )

    if not isinstance(
        available,
        list,
    ):
        return ()

    available_types = {
        value
        for value in available
        if isinstance(value, str)
    }

    return tuple(
        stream_type
        for stream_type in COACH_STREAM_TYPES
        if stream_type in available_types
    )
