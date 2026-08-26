from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.coaching.daily_adaptation import (
    AdaptationDecision,
    CoachAdaptationProposal,
)
from opencoach.database.base import Base
from opencoach.database.models.athlete_profile import (
    AthleteProfile as AthleteProfileModel,
)
from opencoach.database.models.daily_checkin import (
    DailyCheckIn as DailyCheckInModel,
)
from opencoach.database.repositories.sql_daily_adaptation import (
    SqlDailyAdaptationRepository,
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


def create_checkin(
    session: Session,
    athlete_id,
):
    checkin = DailyCheckInModel(
        athlete_profile_id=athlete_id,
        date=__import__(
            "datetime"
        ).date(
            2026,
            8,
            26,
        ),
        energy_rating=3,
        pain_wellness_rating=3,
        illness=False,
        unavailable=False,
        pain_locations=[],
    )

    session.add(checkin)
    session.commit()
    session.refresh(checkin)

    return checkin


def test_proposal_can_be_saved_and_loaded() -> None:
    with create_session() as session:
        athlete = create_athlete(
            session
        )

        checkin = create_checkin(
            session,
            athlete.id,
        )

        repository = (
            SqlDailyAdaptationRepository(
                session
            )
        )

        proposal = (
            CoachAdaptationProposal(
                checkin_id=checkin.id,
                reason="Douleur modérée.",
                recommendation=(
                    "Veux-tu adapter la séance ?"
                ),
            )
        )

        saved = repository.save(
            athlete.id,
            proposal,
        )

        assert saved.id is not None

        loaded = repository.get_for_checkin(
            athlete.id,
            checkin.id,
        )

        assert loaded is not None
        assert loaded.id == saved.id

        assert (
            loaded.decision
            is AdaptationDecision.PENDING
        )


def test_proposal_decision_can_be_updated() -> None:
    with create_session() as session:
        athlete = create_athlete(
            session
        )

        checkin = create_checkin(
            session,
            athlete.id,
        )

        repository = (
            SqlDailyAdaptationRepository(
                session
            )
        )

        saved = repository.save(
            athlete.id,
            CoachAdaptationProposal(
                checkin_id=checkin.id,
                reason="Fatigue modérée.",
                recommendation=(
                    "Veux-tu adapter la séance ?"
                ),
            ),
        )

        accepted = saved.accept()

        updated = repository.save(
            athlete.id,
            accepted,
        )

        assert updated.id == saved.id

        assert (
            updated.decision
            is AdaptationDecision.ACCEPTED
        )


def test_proposal_is_isolated_by_athlete() -> None:
    with create_session() as session:
        first_athlete = create_athlete(
            session
        )
        second_athlete = create_athlete(
            session
        )

        checkin = create_checkin(
            session,
            first_athlete.id,
        )

        repository = (
            SqlDailyAdaptationRepository(
                session
            )
        )

        repository.save(
            first_athlete.id,
            CoachAdaptationProposal(
                checkin_id=checkin.id,
                reason="Douleur.",
                recommendation=(
                    "Adapter la séance ?"
                ),
            ),
        )

        assert (
            repository.get_for_checkin(
                second_athlete.id,
                checkin.id,
            )
            is None
        )
