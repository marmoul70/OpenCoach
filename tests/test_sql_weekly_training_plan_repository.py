from datetime import date
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    User,
)
from opencoach.database.repositories import (
    SqlWeeklyTrainingPlanRepository,
)
from opencoach.models import (
    WeeklyTrainingPlan,
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
        email=f"{uuid4()}@example.com",
        password_hash="test",
    )

    db.add(user)
    db.flush()

    profile = AthleteProfile(
        user_id=user.id,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile


def create_plan(
    athlete_profile_id,
    **overrides,
) -> WeeklyTrainingPlan:
    values = {
        "id": None,
        "athlete_profile_id": athlete_profile_id,
        "week_start": date(
            2026,
            8,
            24,
        ),
        "week_end": date(
            2026,
            8,
            30,
        ),
        "phase": "base",
        "phase_week_index": 2,
        "target_load": 200.0,
        "load_min": 190.0,
        "load_max": 210.0,
        "reference_duration_minutes": 240.0,
        "target_duration_minutes": 250.0,
        "long_endurance_reference_minutes": 90.0,
        "schedule_pressure": "moderate",
        "athlete_schedule_constrained": False,
        "generated_at": None,
        "updated_at": None,
    }

    values.update(
        overrides
    )

    return WeeklyTrainingPlan(
        **values,
    )


def test_sql_weekly_training_plan_repository_saves_plan() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlWeeklyTrainingPlanRepository(
                db
            )
        )

        saved = repository.save_plan(
            create_plan(
                profile.id
            )
        )

        assert saved.id is not None
        assert saved.athlete_profile_id == profile.id
        assert saved.week_start == date(
            2026,
            8,
            24,
        )
        assert saved.target_load == 200.0
        assert saved.load_min == 190.0
        assert saved.load_max == 210.0
        assert saved.generated_at is not None
        assert saved.updated_at is not None

    finally:
        db.close()


def test_sql_weekly_training_plan_repository_reads_plan() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlWeeklyTrainingPlanRepository(
                db
            )
        )

        repository.save_plan(
            create_plan(
                profile.id
            )
        )

        loaded = (
            repository.get_plan_for_week(
                profile.id,
                date(
                    2026,
                    8,
                    24,
                ),
            )
        )

        assert loaded is not None
        assert loaded.target_load == 200.0
        assert loaded.phase == "base"
        assert loaded.phase_week_index == 2

    finally:
        db.close()


def test_sql_weekly_training_plan_repository_updates_same_week() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlWeeklyTrainingPlanRepository(
                db
            )
        )

        first = repository.save_plan(
            create_plan(
                profile.id
            )
        )

        updated = repository.save_plan(
            create_plan(
                profile.id,
                target_load=220.0,
                load_min=209.0,
                load_max=231.0,
                target_duration_minutes=270.0,
                schedule_pressure="high",
                athlete_schedule_constrained=True,
            )
        )

        assert updated.id == first.id
        assert updated.target_load == 220.0
        assert updated.load_min == 209.0
        assert updated.load_max == 231.0
        assert (
            updated.target_duration_minutes
            == 270.0
        )
        assert updated.schedule_pressure == "high"
        assert (
            updated.athlete_schedule_constrained
            is True
        )

    finally:
        db.close()



def test_sql_weekly_training_plan_repository_refresh_keeps_same_plan_id() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        repository = (
            SqlWeeklyTrainingPlanRepository(
                db
            )
        )

        first = repository.save_plan(
            create_plan(
                profile.id,
                target_load=200.0,
                load_min=190.0,
                load_max=210.0,
            )
        )

        refreshed = repository.save_plan(
            create_plan(
                profile.id,
                target_load=205.0,
                load_min=194.75,
                load_max=215.25,
                target_duration_minutes=260.0,
            )
        )

        assert refreshed.id == first.id

        loaded = (
            repository.get_plan_for_week(
                profile.id,
                date(
                    2026,
                    8,
                    24,
                ),
            )
        )

        assert loaded is not None
        assert loaded.id == first.id
        assert loaded.target_load == 205.0
        assert loaded.load_min == 194.75
        assert loaded.load_max == 215.25
        assert (
            loaded.target_duration_minutes
            == 260.0
        )

    finally:
        db.close()
