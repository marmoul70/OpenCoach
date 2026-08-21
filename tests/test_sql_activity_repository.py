from datetime import date, datetime, timezone

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

def test_sql_activity_repository_lists_activities_between_dates() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlActivityRepository(db)

        before = create_activity()
        before.provider_activity_id = "before"
        before.start_at = datetime(
            2026,
            8,
            9,
            8,
            0,
            tzinfo=timezone.utc,
        )

        first = create_activity()
        first.provider_activity_id = "first"
        first.start_at = datetime(
            2026,
            8,
            10,
            8,
            0,
            tzinfo=timezone.utc,
        )

        second = create_activity()
        second.provider_activity_id = "second"
        second.start_at = datetime(
            2026,
            8,
            12,
            8,
            0,
            tzinfo=timezone.utc,
        )

        after = create_activity()
        after.provider_activity_id = "after"
        after.start_at = datetime(
            2026,
            8,
            13,
            8,
            0,
            tzinfo=timezone.utc,
        )

        for activity in (
            before,
            first,
            second,
            after,
        ):
            repository.save_activity(
                profile.id,
                activity,
            )

        activities = (
            repository.list_activities_between(
                profile.id,
                date(2026, 8, 10),
                date(2026, 8, 12),
            )
        )

        assert len(activities) == 2

        assert {
            activity.provider_activity_id
            for activity in activities
        } == {
            "first",
            "second",
        }

    finally:
        db.close()


def test_sql_activity_repository_uses_local_date_first() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlActivityRepository(db)

        activity = create_activity()

        activity.provider_activity_id = (
            "local-date"
        )

        activity.start_at = datetime(
            2026,
            8,
            19,
            22,
            30,
            tzinfo=timezone.utc,
        )

        activity.start_at_local = datetime(
            2026,
            8,
            20,
            0,
            30,
        )

        repository.save_activity(
            profile.id,
            activity,
        )

        august_19 = (
            repository.list_activities_between(
                profile.id,
                date(2026, 8, 19),
                date(2026, 8, 19),
            )
        )

        august_20 = (
            repository.list_activities_between(
                profile.id,
                date(2026, 8, 20),
                date(2026, 8, 20),
            )
        )

        assert august_19 == []

        assert len(august_20) == 1

        assert (
            august_20[0]
            .provider_activity_id
            == "local-date"
        )

    finally:
        db.close()


def test_sql_activity_repository_falls_back_to_start_at() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlActivityRepository(db)

        activity = create_activity()

        activity.provider_activity_id = (
            "fallback-start-at"
        )

        activity.start_at = datetime(
            2026,
            8,
            20,
            8,
            0,
            tzinfo=timezone.utc,
        )

        activity.start_at_local = None

        repository.save_activity(
            profile.id,
            activity,
        )

        activities = (
            repository.list_activities_between(
                profile.id,
                date(2026, 8, 20),
                date(2026, 8, 20),
            )
        )

        assert len(activities) == 1

        assert (
            activities[0]
            .provider_activity_id
            == "fallback-start-at"
        )

    finally:
        db.close()

def test_sql_activity_repository_gets_activity_by_id() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        activity = create_activity()

        repository = SqlActivityRepository(
            db
        )

        repository.save_activity(
            profile.id,
            activity,
        )

        saved_activities = (
            repository.list_activities(
                profile.id
            )
        )

        assert len(saved_activities) == 1

        saved_activity = saved_activities[0]

        assert saved_activity.id is not None

        result = repository.get_activity(
            profile.id,
            saved_activity.id,
        )

        assert result is not None
        assert result.id == saved_activity.id
        assert (
            result.provider_activity_id
            == activity.provider_activity_id
        )

    finally:
        db.close()