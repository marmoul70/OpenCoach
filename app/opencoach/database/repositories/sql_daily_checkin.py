"""Repository SQLAlchemy des check-ins quotidiens."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
    BodySide,
    PainArea,
    PainLocation,
)
from opencoach.database.models.daily_checkin import (
    DailyCheckIn as DailyCheckInModel,
)
from opencoach.database.repositories.daily_checkin import (
    DailyCheckInRepository,
    DailyCheckInRepositoryError,
)


class SqlDailyCheckInRepository(
    DailyCheckInRepository
):
    """Implémentation SQLAlchemy des check-ins."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def save(
        self,
        athlete_profile_id: UUID,
        checkin: AthleteDailyCheckIn,
    ) -> AthleteDailyCheckIn:
        try:
            database_checkin = None

            if checkin.id is not None:
                database_checkin = self.session.scalar(
                    select(DailyCheckInModel).where(
                        DailyCheckInModel.id == checkin.id,
                        DailyCheckInModel.athlete_profile_id
                        == athlete_profile_id,
                    )
                )

            if database_checkin is None:
                database_checkin = self.session.scalar(
                    select(DailyCheckInModel).where(
                        DailyCheckInModel.athlete_profile_id
                        == athlete_profile_id,
                        DailyCheckInModel.date == checkin.date,
                    )
                )

            payload = [
                {
                    "area": location.area.value,
                    "side": location.side.value,
                }
                for location in checkin.pain_locations
            ]

            if database_checkin is None:
                database_checkin = DailyCheckInModel(
                    athlete_profile_id=athlete_profile_id,
                    date=checkin.date,
                    energy_rating=checkin.energy_rating,
                    pain_wellness_rating=(
                        checkin.pain_wellness_rating
                    ),
                    illness=checkin.illness,
                    unavailable=checkin.unavailable,
                    pain_locations=payload,
                    note=checkin.note,
                )

                self.session.add(database_checkin)

            else:
                database_checkin.date = checkin.date
                database_checkin.energy_rating = (
                    checkin.energy_rating
                )
                database_checkin.pain_wellness_rating = (
                    checkin.pain_wellness_rating
                )
                database_checkin.illness = checkin.illness
                database_checkin.unavailable = (
                    checkin.unavailable
                )
                database_checkin.pain_locations = payload
                database_checkin.note = checkin.note

            self.session.commit()
            self.session.refresh(database_checkin)

            return self._to_domain(database_checkin)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise DailyCheckInRepositoryError(
                "Impossible d'enregistrer le check-in."
            ) from exc

    def get_for_date(
        self,
        athlete_profile_id: UUID,
        checkin_date: date,
    ) -> AthleteDailyCheckIn | None:
        try:
            database_checkin = self.session.scalar(
                select(DailyCheckInModel).where(
                    DailyCheckInModel.athlete_profile_id
                    == athlete_profile_id,
                    DailyCheckInModel.date == checkin_date,
                )
            )

            if database_checkin is None:
                return None

            return self._to_domain(database_checkin)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise DailyCheckInRepositoryError(
                "Impossible de charger le check-in."
            ) from exc

    @staticmethod
    def _to_domain(
        database_checkin: DailyCheckInModel,
    ) -> AthleteDailyCheckIn:
        return AthleteDailyCheckIn(
            id=database_checkin.id,
            date=database_checkin.date,
            energy_rating=database_checkin.energy_rating,
            pain_wellness_rating=(
                database_checkin.pain_wellness_rating
            ),
            illness=database_checkin.illness,
            unavailable=database_checkin.unavailable,
            pain_locations=tuple(
                PainLocation(
                    area=PainArea(item["area"]),
                    side=BodySide(item["side"]),
                )
                for item in (
                    database_checkin.pain_locations
                    or []
                )
            ),
            note=database_checkin.note,
        )
