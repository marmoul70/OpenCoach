from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    Activity,
    AthleteProfile,
    User,
)


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


def create_athlete_profile(
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


def create_activity(
    profile: AthleteProfile,
    *,
    provider: str = "intervals",
    provider_activity_id: str = "i123456",
) -> Activity:
    return Activity(
        athlete_profile=profile,
        provider=provider,
        provider_activity_id=provider_activity_id,
        source="SUUNTO",
        source_file_name="activity.fit",
        name="Morning Course à pied",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            17,
            8,
            0,
            tzinfo=timezone.utc,
        ),
        distance_m=10000,
        elapsed_time_seconds=3600,
        moving_time_seconds=3500,
        elevation_gain_m=250,
        average_heart_rate=150,
        max_heart_rate=181,
        training_load=75,
        device_name="SUUNTO Suunto Race 2",
    )


def test_activity_is_persisted_and_linked_to_profile() -> None:
    db = create_session()

    try:
        profile = create_athlete_profile(db)

        activity = create_activity(profile)

        db.add(activity)
        db.commit()

        saved = db.query(Activity).one()

        assert saved.provider == "intervals"
        assert saved.provider_activity_id == "i123456"
        assert saved.source == "SUUNTO"
        assert saved.name == "Morning Course à pied"
        assert saved.sport_type == "Run"
        assert saved.distance_m == 10000
        assert saved.elevation_gain_m == 250
        assert saved.average_heart_rate == 150
        assert saved.max_heart_rate == 181
        assert saved.training_load == 75

        assert saved.athlete_profile is profile
        assert activity in profile.activities
    finally:
        db.close()


def test_activity_provider_id_must_be_unique_per_provider() -> None:
    db = create_session()

    try:
        profile = create_athlete_profile(db)

        first = create_activity(
            profile,
            provider="intervals",
            provider_activity_id="i123456",
        )

        db.add(first)
        db.commit()

        duplicate = create_activity(
            profile,
            provider="intervals",
            provider_activity_id="i123456",
        )

        db.add(duplicate)

        with pytest.raises(IntegrityError):
            db.commit()

        db.rollback()
    finally:
        db.close()


def test_same_external_id_is_allowed_for_different_providers() -> None:
    db = create_session()

    try:
        profile = create_athlete_profile(db)

        intervals_activity = create_activity(
            profile,
            provider="intervals",
            provider_activity_id="123456",
        )

        suunto_activity = create_activity(
            profile,
            provider="suunto",
            provider_activity_id="123456",
        )

        db.add_all(
            [
                intervals_activity,
                suunto_activity,
            ]
        )

        db.commit()

        activities = db.query(Activity).all()

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


def test_deleting_profile_deletes_activities() -> None:
    db = create_session()

    try:
        profile = create_athlete_profile(db)

        activity = create_activity(profile)

        db.add(activity)
        db.commit()

        assert db.query(Activity).count() == 1

        db.delete(profile)
        db.commit()

        assert db.query(Activity).count() == 0
    finally:
        db.close()