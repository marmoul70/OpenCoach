from uuid import UUID

from opencoach.database.repositories.activity import (
    ActivityRepository,
)
from opencoach.models import (
    Activity,
    Race,
)
from opencoach.races.result import (
    RaceActualResult,
)


class RaceResultService:
    """Détermine le résultat réel d'une course."""

    def __init__(
        self,
        activity_repository: ActivityRepository,
    ) -> None:
        self.activity_repository = (
            activity_repository
        )

    def calculate(
        self,
        athlete_profile_id: UUID,
        race: Race,
    ) -> RaceActualResult:
        """Retourne les données réellement retenues."""

        activity = self._get_linked_activity(
            athlete_profile_id,
            race,
        )

        if activity is not None:
            return self._from_activity(
                activity
            )

        if race.status == "not_participated":
            return RaceActualResult(
                source="none",
                activity_id=None,
                distance_km=0.0,
                elevation_gain_m=0.0,
                duration_minutes=0.0,
                training_load=0.0,
            )

        if race.status in {
            "completed",
            "abandoned",
        }:
            return self._from_manual_result(
                race
            )

        return RaceActualResult(
            source="none",
            activity_id=None,
            distance_km=None,
            elevation_gain_m=None,
            duration_minutes=None,
            training_load=None,
        )

    def _get_linked_activity(
        self,
        athlete_profile_id: UUID,
        race: Race,
    ) -> Activity | None:
        if race.activity_id is None:
            return None

        return self.activity_repository.get_activity(
            athlete_profile_id,
            race.activity_id,
        )

    @staticmethod
    def _from_activity(
        activity: Activity,
    ) -> RaceActualResult:
        duration_seconds = (
            activity.moving_time_seconds
            if activity.moving_time_seconds
            is not None
            else activity.elapsed_time_seconds
        )

        duration_minutes = (
            duration_seconds / 60
            if duration_seconds is not None
            else None
        )

        distance_km = (
            activity.distance_m / 1000
            if activity.distance_m is not None
            else None
        )

        return RaceActualResult(
            source="activity",
            activity_id=activity.id,
            distance_km=(
                round(
                    distance_km,
                    3,
                )
                if distance_km is not None
                else None
            ),
            elevation_gain_m=(
                activity.elevation_gain_m
            ),
            duration_minutes=(
                round(
                    duration_minutes,
                    1,
                )
                if duration_minutes is not None
                else None
            ),
            training_load=(
                activity.training_load
            ),
        )

    @staticmethod
    def _from_manual_result(
        race: Race,
    ) -> RaceActualResult:
        return RaceActualResult(
            source="manual",
            activity_id=None,
            distance_km=(
                race.actual_distance_km
            ),
            elevation_gain_m=(
                race.actual_elevation_gain_m
            ),
            duration_minutes=(
                float(
                    race.actual_time_minutes
                )
                if race.actual_time_minutes
                is not None
                else None
            ),
            training_load=None,
        )
