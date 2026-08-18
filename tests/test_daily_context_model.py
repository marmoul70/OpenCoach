from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    DailyContext,
    User,
)


def create_session():
    engine = create_engine(
        "sqlite:///:memory:",
    )

    Base.metadata.create_all(
        engine
    )

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return SessionLocal()


def create_profile(
    db,
) -> AthleteProfile:
    user = User(
        email="local@opencoach.local",
    )

    profile = AthleteProfile(
        user=user,
        first_name="Test",
        last_name="Athlete",
    )

    db.add(
        profile
    )

    db.commit()

    return profile


def test_daily_context_can_be_persisted() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        context = DailyContext(
            athlete_profile_id=profile.id,
            date=date(
                2026,
                8,
                18,
            ),
            fatigue_subjective=4,
            pain_level=2,
            illness_status="none",
            treatment_impact="significant",
            motivation=2,
            notes=(
                "Fatigue importante après traitement."
            ),
        )

        db.add(
            context
        )

        db.commit()

        saved = db.query(
            DailyContext
        ).one()

        assert (
            saved.athlete_profile_id
            == profile.id
        )

        assert saved.date == date(
            2026,
            8,
            18,
        )

        assert saved.fatigue_subjective == 4
        assert saved.pain_level == 2
        assert saved.illness_status == "none"

        assert (
            saved.treatment_impact
            == "significant"
        )

        assert saved.motivation == 2

        assert saved.notes == (
            "Fatigue importante après traitement."
        )

    finally:
        db.close()


def test_daily_context_relationship_is_available() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        context = DailyContext(
            athlete_profile=profile,
            date=date(
                2026,
                8,
                18,
            ),
            fatigue_subjective=2,
            pain_level=0,
        )

        db.add(
            context
        )

        db.commit()

        assert len(
            profile.daily_contexts
        ) == 1

        assert (
            profile.daily_contexts[0].id
            == context.id
        )

    finally:
        db.close()
