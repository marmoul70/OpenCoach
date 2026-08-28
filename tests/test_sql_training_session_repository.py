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
    SqlTrainingSessionRepository,
)
from opencoach.models import TrainingSession


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


def create_training_session() -> TrainingSession:
    return TrainingSession(
        id=None,
        date=date(2026, 8, 9),
        type="easy",
        title="Endurance fondamentale",
        sport_type="Run",
        description="Course facile en endurance.",
        duration_minutes=60,
        distance_km=9.0,
        elevation_gain_m=100.0,
        intensity="Facile",
        heart_rate_zone="Z2",
        status="planned",
        activity_id=None,
    )


def create_activity(
    db,
    profile: AthleteProfile,
    *,
    provider_activity_id: str,
    hour: int,
    name: str,
    feel: int | None = None,
) -> ActivityModel:
    activity = ActivityModel(
        athlete_profile_id=profile.id,
        provider="intervals",
        provider_activity_id=provider_activity_id,
        name=name,
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            9,
            hour - 2,
            0,
            tzinfo=timezone.utc,
        ),
        start_at_local=datetime(
            2026,
            8,
            9,
            hour,
            0,
        ),
        distance_m=8000.0,
        moving_time_seconds=3000,
        elevation_gain_m=120.0,
        feel=feel,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity


def test_sql_training_session_repository_inserts_session() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlTrainingSessionRepository(db)

        saved = repository.save_session(
            profile.id,
            create_training_session(),
        )

        assert saved.id is not None
        assert saved.date == date(2026, 8, 9)
        assert saved.type == "easy"
        assert saved.title == "Endurance fondamentale"
        assert saved.sport_type == "Run"
        assert saved.duration_minutes == 60
        assert saved.distance_km == 9.0
        assert saved.status == "planned"
        assert saved.activity_id is None

    finally:
        db.close()


def test_sql_training_session_repository_gets_session() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlTrainingSessionRepository(db)

        saved = repository.save_session(
            profile.id,
            create_training_session(),
        )

        result = repository.get_session(
            profile.id,
            saved.id,
        )

        assert result is not None
        assert result.id == saved.id
        assert result.title == "Endurance fondamentale"
        assert result.status == "planned"

    finally:
        db.close()


def test_sql_training_session_repository_lists_period() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlTrainingSessionRepository(db)

        first = create_training_session()
        first.date = date(2026, 8, 8)

        second = create_training_session()
        second.date = date(2026, 8, 9)
        second.title = "Sortie longue"

        third = create_training_session()
        third.date = date(2026, 8, 15)

        repository.save_session(
            profile.id,
            first,
        )

        repository.save_session(
            profile.id,
            second,
        )

        repository.save_session(
            profile.id,
            third,
        )

        sessions = repository.list_sessions_between(
            profile.id,
            date(2026, 8, 8),
            date(2026, 8, 10),
        )

        assert len(sessions) == 2
        assert sessions[0].date == date(2026, 8, 8)
        assert sessions[1].date == date(2026, 8, 9)
        assert sessions[1].title == "Sortie longue"

    finally:
        db.close()


def test_sql_training_session_repository_updates_status() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlTrainingSessionRepository(db)

        saved = repository.save_session(
            profile.id,
            create_training_session(),
        )

        updated = repository.update_status(
            profile.id,
            saved.id,
            "completed",
        )

        assert updated.status == "completed"

        reloaded = repository.get_session(
            profile.id,
            saved.id,
        )

        assert reloaded is not None
        assert reloaded.status == "completed"

    finally:
        db.close()


def test_sql_training_session_repository_links_activity() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlTrainingSessionRepository(db)

        session = repository.save_session(
            profile.id,
            create_training_session(),
        )

        activity = create_activity(
            db,
            profile,
            provider_activity_id="i-run",
            hour=7,
            name="Morning Course à pied",
            feel=2,
        )

        updated = repository.link_activity(
            profile.id,
            session.id,
            activity.id,
        )

        assert updated.activity_id == activity.id

        detached = repository.link_activity(
            profile.id,
            session.id,
            None,
        )

        assert detached.activity_id is None

    finally:
        db.close()


def test_sql_training_session_repository_lists_same_day_activities() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlTrainingSessionRepository(db)

        first = create_activity(
            db,
            profile,
            provider_activity_id="i-run",
            hour=7,
            name="Morning Course à pied",
            feel=None,
        )

        second = create_activity(
            db,
            profile,
            provider_activity_id="i-walk",
            hour=8,
            name="Morning Marche",
            feel=1,
        )

        activities = (
            repository.list_candidate_activities_for_date(
                profile.id,
                date(2026, 8, 9),
            )
        )

        assert len(activities) == 2

        assert activities[0].id == first.id
        assert activities[0].name == "Morning Course à pied"

        assert activities[1].id == second.id
        assert activities[1].name == "Morning Marche"
        assert activities[1].feel == 1

    finally:
        db.close()


def test_sql_training_session_repository_ignores_other_days() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlTrainingSessionRepository(db)

        activity = ActivityModel(
            athlete_profile_id=profile.id,
            provider="intervals",
            provider_activity_id="i-other-day",
            name="Other Course",
            sport_type="Run",
            start_at=datetime(
                2026,
                8,
                10,
                6,
                0,
                tzinfo=timezone.utc,
            ),
            start_at_local=datetime(
                2026,
                8,
                10,
                8,
                0,
            ),
        )

        db.add(activity)
        db.commit()

        activities = (
            repository.list_candidate_activities_for_date(
                profile.id,
                date(2026, 8, 9),
            )
        )

        assert activities == []

    finally:
        db.close()


def test_training_session_repository_persists_prescription() -> None:
    db = create_session()

    try:
        profile = create_profile(
            db
        )

        prescription = {
            "version": 1,
            "structure": {
                "kind": "intervals",
                "intervals": [
                    {
                        "repetitions": 6,
                        "work": {
                            "duration_seconds": 180,
                        },
                        "recovery": {
                            "duration_seconds": 120,
                        },
                        "target": {
                            "vma_percent_min": 95.0,
                            "vma_percent_max": 100.0,
                        },
                    },
                ],
            },
        }

        training_session = (
            create_training_session()
        )

        training_session.prescription = (
            prescription
        )

        repository = (
            SqlTrainingSessionRepository(
                db
            )
        )

        saved = repository.save_session(
            profile.id,
            training_session,
        )

        assert saved.id is not None

        loaded = repository.get_session(
            profile.id,
            saved.id,
        )

        assert loaded is not None

        assert (
            loaded.prescription
            == prescription
        )

    finally:
        db.close()
