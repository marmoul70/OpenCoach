from datetime import date, timedelta
from uuid import UUID

from opencoach.integrations.intervals import IntervalsSyncService


DEFAULT_SYNC_DAYS = 30


class IntervalsApplicationService:
    """Service applicatif de synchronisation Intervals.icu."""

    def __init__(
        self,
        sync_service: IntervalsSyncService,
    ) -> None:
        self.sync_service = sync_service

    def sync_activities(
        self,
        athlete_profile_id: UUID,
        *,
        newest: date | None = None,
        days: int = DEFAULT_SYNC_DAYS,
    ) -> int:
        """Synchronise les activités récentes d'un athlète."""

        if days < 1:
            raise ValueError(
                "La période de synchronisation doit être positive."
            )

        if newest is None:
            newest = date.today()

        oldest = newest - timedelta(days=days)

        return self.sync_service.sync_activities(
            athlete_profile_id=athlete_profile_id,
            oldest=oldest,
            newest=newest,
        )