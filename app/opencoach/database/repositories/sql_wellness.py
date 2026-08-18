from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import WellnessDaily
from opencoach.database.repositories.errors import (
    WellnessRepositoryError,
)
from opencoach.database.repositories.wellness import (
    WellnessRepository,
)
from opencoach.models import WellnessDay


class SqlWellnessRepository(WellnessRepository):
    """Persiste les données Wellness quotidiennes."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save_wellness_day(
        self,
        athlete_profile_id: UUID,
        wellness: WellnessDay,
    ) -> None:
        try:
            database_wellness = self._get_database_wellness(
                athlete_profile_id=athlete_profile_id,
                provider=wellness.provider,
                wellness_date=wellness.date,
            )

            if database_wellness is None:
                database_wellness = WellnessDaily(
                    athlete_profile_id=athlete_profile_id,
                    provider=wellness.provider,
                    date=wellness.date,
                )

                self.session.add(database_wellness)

            database_wellness.athlete_profile_id = (
                athlete_profile_id
            )
            database_wellness.provider = wellness.provider
            database_wellness.date = wellness.date

            database_wellness.fitness_ctl = wellness.fitness_ctl
            database_wellness.fatigue_atl = wellness.fatigue_atl
            database_wellness.ramp_rate = wellness.ramp_rate
            database_wellness.steps = wellness.steps
            database_wellness.provider_updated_at = (
                wellness.provider_updated_at
            )

            self.session.commit()
            self.session.refresh(database_wellness)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WellnessRepositoryError(
                "Impossible d'enregistrer les données Wellness."
            ) from exc

    def _get_database_wellness(
        self,
        *,
        athlete_profile_id: UUID,
        provider: str,
        wellness_date,
    ) -> WellnessDaily | None:
        statement = (
            select(WellnessDaily)
            .where(
                WellnessDaily.athlete_profile_id
                == athlete_profile_id,
                WellnessDaily.provider == provider,
                WellnessDaily.date == wellness_date,
            )
        )

        return self.session.scalar(statement)
