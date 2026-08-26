from datetime import date
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.coaching.daily_checkin import (
    AthleteDailyCheckIn,
    BodySide,
    PainArea,
    PainLocation,
)
from opencoach.database.base import Base
from opencoach.database.models.athlete_profile import (
    AthleteProfile as AthleteProfileModel,
)
from opencoach.database.repositories.sql_daily_checkin import (
    SqlDailyCheckInRepository,
)


def create_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:"
    )

    Base.metadata.create_all(engine)

    return Session(engine)


def create_athlete(
    session: Session,
):
    athlete = AthleteProfileModel(
        user_id=uuid4(),
    )

    session.add(athlete)
    session.commit()
    session.refresh(athlete)

    return athlete


def test_checkin_can_be_saved_and_loaded() -> None:
    with create_session() as session:
        athlete = create_athlete(
            session
        )

        repository = (
            SqlDailyCheckInRepository(
                session
            )
        )

        checkin = AthleteDailyCheckIn(
            date=date(
                2026,
                8,
                26,
            ),
            energy_rating=3,
            pain_wellness_rating=3,
            pain_locations=(
                PainLocation(
                    area=PainArea.LOWER_BACK,
                    side=BodySide.CENTER,
                ),
            ),
            note="Dos sensible.",
        )

        saved = repository.save(
            athlete.id,
            checkin,
        )

        assert saved.id is not None

        loaded = repository.get_for_date(
            athlete.id,
            checkin.date,
        )

        assert loaded is not None
        assert loaded.id == saved.id
        assert loaded.energy_rating == 3

        assert (
            loaded.pain_locations[0].area
            is PainArea.LOWER_BACK
        )


def test_second_checkin_same_day_updates_existing_record() -> None:
    with create_session() as session:
        athlete = create_athlete(
            session
        )

        repository = (
            SqlDailyCheckInRepository(
                session
            )
        )

        first = repository.save(
            athlete.id,
            AthleteDailyCheckIn(
                date=date(
                    2026,
                    8,
                    26,
                ),
                energy_rating=3,
                pain_wellness_rating=4,
            ),
        )

        second = repository.save(
            athlete.id,
            AthleteDailyCheckIn(
                date=date(
                    2026,
                    8,
                    26,
                ),
                energy_rating=4,
                pain_wellness_rating=5,
                note="Ça va mieux.",
            ),
        )

        assert second.id == first.id
        assert second.energy_rating == 4
        assert second.pain_wellness_rating == 5
        assert second.note == "Ça va mieux."


def test_checkins_are_isolated_by_athlete() -> None:
    with create_session() as session:
        first_athlete = create_athlete(
            session
        )
        second_athlete = create_athlete(
            session
        )

        repository = (
            SqlDailyCheckInRepository(
                session
            )
        )

        repository.save(
            first_athlete.id,
            AthleteDailyCheckIn(
                date=date(
                    2026,
                    8,
                    26,
                ),
                energy_rating=2,
                pain_wellness_rating=3,
            ),
        )

        assert (
            repository.get_for_date(
                second_athlete.id,
                date(
                    2026,
                    8,
                    26,
                ),
            )
            is None
        )
