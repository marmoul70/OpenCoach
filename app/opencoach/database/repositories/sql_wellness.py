from datetime import date
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

                self.session.add(
                    database_wellness
                )

            database_wellness.athlete_profile_id = (
                athlete_profile_id
            )
            database_wellness.provider = wellness.provider
            database_wellness.date = wellness.date

            database_wellness.fitness_ctl = (
                wellness.fitness_ctl
            )
            database_wellness.fatigue_atl = (
                wellness.fatigue_atl
            )
            database_wellness.ramp_rate = (
                wellness.ramp_rate
            )

            database_wellness.resting_hr = (
                wellness.resting_hr
            )
            database_wellness.hrv = (
                wellness.hrv
            )

            database_wellness.sleep_seconds = (
                wellness.sleep_seconds
            )
            database_wellness.sleep_score = (
                wellness.sleep_score
            )
            database_wellness.sleep_quality = (
                wellness.sleep_quality
            )
            database_wellness.avg_sleeping_hr = (
                wellness.avg_sleeping_hr
            )

            database_wellness.spo2 = (
                wellness.spo2
            )
            database_wellness.steps = (
                wellness.steps
            )

            database_wellness.provider_updated_at = (
                wellness.provider_updated_at
            )

            self.session.commit()

            self.session.refresh(
                database_wellness
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WellnessRepositoryError(
                (
                    "Impossible d'enregistrer "
                    "les données Wellness."
                )
            ) from exc

    def get_latest(
        self,
        athlete_profile_id: UUID,
    ) -> WellnessDay | None:
        """Retourne la dernière journée Wellness disponible."""

        try:
            statement = (
                select(WellnessDaily)
                .where(
                    WellnessDaily.athlete_profile_id
                    == athlete_profile_id,
                )
                .order_by(
                    WellnessDaily.date.desc(),
                )
                .limit(1)
            )

            database_wellness = (
                self.session.scalar(
                    statement
                )
            )

            if database_wellness is None:
                return None

            return self._to_domain(
                database_wellness
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WellnessRepositoryError(
                (
                    "Impossible de charger "
                    "les données Wellness."
                )
            ) from exc

    def get_by_date(
        self,
        athlete_profile_id: UUID,
        wellness_date: date,
        *,
        provider: str | None = None,
    ) -> WellnessDay | None:
        """Retourne une journée Wellness précise."""

        try:
            conditions = [
                WellnessDaily.athlete_profile_id
                == athlete_profile_id,
                WellnessDaily.date
                == wellness_date,
            ]

            if provider is not None:
                conditions.append(
                    WellnessDaily.provider
                    == provider
                )

            statement = (
                select(WellnessDaily)
                .where(
                    *conditions
                )
                .order_by(
                    WellnessDaily.provider.asc(),
                )
                .limit(1)
            )

            database_wellness = (
                self.session.scalar(
                    statement
                )
            )

            if database_wellness is None:
                return None

            return self._to_domain(
                database_wellness
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WellnessRepositoryError(
                (
                    "Impossible de charger "
                    "la journée Wellness."
                )
            ) from exc

    def list_range(
        self,
        athlete_profile_id: UUID,
        start_date: date,
        end_date: date,
        *,
        provider: str | None = None,
    ) -> list[WellnessDay]:
        """Retourne les journées Wellness d'une période."""

        try:
            conditions = [
                WellnessDaily.athlete_profile_id
                == athlete_profile_id,
                WellnessDaily.date
                >= start_date,
                WellnessDaily.date
                <= end_date,
            ]

            if provider is not None:
                conditions.append(
                    WellnessDaily.provider
                    == provider
                )

            statement = (
                select(WellnessDaily)
                .where(
                    *conditions
                )
                .order_by(
                    WellnessDaily.date.asc(),
                )
            )

            rows = self.session.scalars(
                statement
            ).all()

            return [
                self._to_domain(
                    row
                )
                for row in rows
            ]

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise WellnessRepositoryError(
                (
                    "Impossible de charger "
                    "l'historique Wellness."
                )
            ) from exc

    def _get_database_wellness(
        self,
        *,
        athlete_profile_id: UUID,
        provider: str,
        wellness_date: date,
    ) -> WellnessDaily | None:
        statement = (
            select(WellnessDaily)
            .where(
                WellnessDaily.athlete_profile_id
                == athlete_profile_id,
                WellnessDaily.provider
                == provider,
                WellnessDaily.date
                == wellness_date,
            )
        )

        return self.session.scalar(
            statement
        )

    @staticmethod
    def _to_domain(
        wellness: WellnessDaily,
    ) -> WellnessDay:
        return WellnessDay(
            provider=wellness.provider,
            date=wellness.date,
            fitness_ctl=wellness.fitness_ctl,
            fatigue_atl=wellness.fatigue_atl,
            ramp_rate=wellness.ramp_rate,
            resting_hr=wellness.resting_hr,
            hrv=wellness.hrv,
            sleep_seconds=wellness.sleep_seconds,
            sleep_score=wellness.sleep_score,
            sleep_quality=wellness.sleep_quality,
            avg_sleeping_hr=(
                wellness.avg_sleeping_hr
            ),
            spo2=wellness.spo2,
            steps=wellness.steps,
            provider_updated_at=(
                wellness.provider_updated_at
            ),
        )