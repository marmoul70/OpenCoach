from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    Activity as ActivityModel,
    AthleteProfile,
    User,
)
from opencoach.database.repositories import (
    SqlActivityRepository,
)
from opencoach.models import Activity


def create_session():
    engine = create_engine(
        "sqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

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

    db.add(profile)
    db.commit()

    return profile


def create_activity() -> Activity:
    return Activity(
        provider="intervals",
        provider_activity_id="i176833761",
        source="SUUNTO",
        source_file_name="activity.fit",
        name="Morning Course à pied",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            14,
            6,
            1,
            34,
            tzinfo=timezone.utc,
        ),
        distance_m=4453.0,
        elevation_gain_m=45.47586,
        average_heart_rate=67,
        max_heart_rate=80,
        training_load=2,
        fitness_ctl=18.286057,
        fatigue_atl=10.629515,
        feel=2,
    )


def test_sql_activity_repository_inserts_activity() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlActivityRepository(db)

        repository.save_activity(
            profile.id,
            create_activity(),
        )

        saved = db.query(ActivityModel).one()

        assert saved.provider == "intervals"
        assert saved.provider_activity_id == "i176833761"
        assert saved.source == "SUUNTO"
        assert saved.name == "Morning Course à pied"
        assert saved.distance_m == 4453.0
        assert saved.training_load == 2
        assert saved.feel == 2
    finally:
        db.close()


def test_sql_activity_repository_updates_existing_activity() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlActivityRepository(db)

        activity = create_activity()

        repository.save_activity(
            profile.id,
            activity,
        )

        activity.name = "Course modifiée"
        activity.distance_m = 5000.0
        activity.training_load = 10

        repository.save_activity(
            profile.id,
            activity,
        )

        activities = db.query(ActivityModel).all()

        assert len(activities) == 1

        saved = activities[0]

        assert saved.name == "Course modifiée"
        assert saved.distance_m == 5000.0
        assert saved.training_load == 10
    finally:
        db.close()


def test_sql_activity_repository_keeps_provider_identity() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlActivityRepository(db)

        intervals_activity = create_activity()

        suunto_activity = create_activity()
        suunto_activity.provider = "suunto"

        repository.save_activity(
            profile.id,
            intervals_activity,
        )

        repository.save_activity(
            profile.id,
            suunto_activity,
        )

        activities = db.query(ActivityModel).all()

        assert len(activities) == 2

        assert {
            activity.provider
            for activity in activities
        } == {
            "intervals",
            "suunto",
        }
    finally:
        db.close()

def test_sql_activity_repository_lists_activities_by_date() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlActivityRepository(db)

        first = create_activity()
        first.provider_activity_id = "i1"
        first.start_at = datetime(
            2026,
            8,
            10,
            8,
            0,
            tzinfo=timezone.utc,
        )

        second = create_activity()
        second.provider_activity_id = "i2"
        second.start_at = datetime(
            2026,
            8,
            14,
            8,
            0,
            tzinfo=timezone.utc,
        )

        repository.save_activity(
            profile.id,
            first,
        )

        repository.save_activity(
            profile.id,
            second,
        )

        activities = repository.list_activities(
            profile.id,
        )

        assert len(activities) == 2
        assert activities[0].provider_activity_id == "i2"
        assert activities[1].provider_activity_id == "i1"
        assert activities[0].feel == 2
        assert activities[1].feel == 2

    finally:
        db.close()