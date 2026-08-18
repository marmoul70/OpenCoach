from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    DailyContext as DailyContextModel,
    User,
)
from opencoach.database.repositories import (
    SqlDailyContextRepository,
)
from opencoach.models import DailyContext


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


def create_context() -> DailyContext:
    return DailyContext(
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
        notes="Fatigue importante.",
    )


def test_sql_daily_context_repository_inserts_context() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlDailyContextRepository(
            db
        )

        result = repository.save(
            profile.id,
            create_context(),
        )

        saved = db.query(
            DailyContextModel
        ).one()

        assert saved.athlete_profile_id == profile.id
        assert saved.date == date(
            2026,
            8,
            18,
        )
        assert saved.fatigue_subjective == 4
        assert saved.pain_level == 2
        assert saved.treatment_impact == "significant"

        assert result.fatigue_subjective == 4
        assert result.treatment_impact == "significant"

    finally:
        db.close()


def test_sql_daily_context_repository_updates_existing_context() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlDailyContextRepository(
            db
        )

        context = create_context()

        repository.save(
            profile.id,
            context,
        )

        context.fatigue_subjective = 2
        context.pain_level = 0
        context.treatment_impact = "mild"
        context.motivation = 4

        repository.save(
            profile.id,
            context,
        )

        rows = db.query(
            DailyContextModel
        ).all()

        assert len(rows) == 1

        saved = rows[0]

        assert saved.fatigue_subjective == 2
        assert saved.pain_level == 0
        assert saved.treatment_impact == "mild"
        assert saved.motivation == 4

    finally:
        db.close()


def test_sql_daily_context_repository_gets_context_by_date() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlDailyContextRepository(
            db
        )

        repository.save(
            profile.id,
            create_context(),
        )

        result = repository.get_by_date(
            profile.id,
            date(
                2026,
                8,
                18,
            ),
        )

        assert result is not None
        assert result.date == date(
            2026,
            8,
            18,
        )
        assert result.fatigue_subjective == 4
        assert result.treatment_impact == "significant"

    finally:
        db.close()


def test_sql_daily_context_repository_returns_none_when_missing() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = SqlDailyContextRepository(
            db
        )

        result = repository.get_by_date(
            profile.id,
            date(
                2026,
                8,
                18,
            ),
        )

        assert result is None

    finally:
        db.close()
