from datetime import date, datetime
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from opencoach.api.intervals import (
    get_current_athlete_profile_id,
)
from opencoach.database.base import Base
from opencoach.database.models import (
    Activity as ActivityModel,
    ActivityDetail as ActivityDetailModel,
    AthleteProfile as AthleteProfileModel,
    TrainingSession as TrainingSessionModel,
    User as UserModel,
)
from opencoach.database.models.activity_detail import (
    ActivityStream as ActivityStreamModel,
)
from opencoach.database.session import get_db
from opencoach.api.app import app


def _test_context():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )

    db = TestingSessionLocal()

    user = UserModel(
        id=uuid4(),
        email="api-test@example.test",
        password_hash="test",
    )

    athlete = AthleteProfileModel(
        id=uuid4(),
        user_id=user.id,
        first_name="Test",
        last_name="Athlete",
    )

    db.add(user)
    db.add(athlete)
    db.commit()

    def override_get_db():
        session = TestingSessionLocal()

        try:
            yield session
        finally:
            session.close()

    def override_athlete_profile_id():
        return athlete.id

    app.dependency_overrides[
        get_db
    ] = override_get_db

    app.dependency_overrides[
        get_current_athlete_profile_id
    ] = override_athlete_profile_id

    return (
        engine,
        TestingSessionLocal,
        athlete.id,
    )


def _seed_session_and_activity(
    SessionLocal,
    *,
    athlete_profile_id,
):
    db = SessionLocal()

    try:
        session_id = uuid4()
        activity_id = uuid4()

        training_session = TrainingSessionModel(
            id=session_id,
            athlete_profile_id=(
                athlete_profile_id
            ),
            planning_key=(
                "2026-08-29:aerobic_easy"
            ),
            date=date(2026, 8, 29),
            type="aerobic_easy",
            sport_type="Run",
            title="Endurance facile",
            description="EF",
            duration_minutes=45,
            intensity="easy",
            heart_rate_zone=(
                "129-152 bpm"
            ),
            prescription={
                "version": 1,
                "blocks": [],
                "work_structure": {
                    "type": "continuous",
                    "stimulus": "aerobic_easy",
                    "available_minutes": 45,
                    "continuous_minutes": 45,
                    "description": (
                        "Endurance facile."
                    ),
                    "circuit": None,
                    "intervals": [],
                },
                "intensity": {
                    "targets": [
                        {
                            "reference": (
                                "heart_rate"
                            ),
                            "minimum": 129,
                            "maximum": 152,
                            "unit": "bpm",
                            "label": "Zone EF",
                        },
                    ],
                    "guidance": [],
                },
            },
            status="planned",
            activity_id=None,
        )

        activity = ActivityModel(
            id=activity_id,
            athlete_profile_id=(
                athlete_profile_id
            ),
            provider="intervals_icu",
            provider_activity_id="i-api-test",
            name="Course EF",
            sport_type="Run",
            start_at=datetime(
                2026,
                8,
                29,
                8,
                0,
            ),
            start_at_local=datetime(
                2026,
                8,
                29,
                10,
                0,
            ),
            moving_time_seconds=2700,
            elapsed_time_seconds=2700,
            distance_m=7000,
            average_heart_rate=145,
            max_heart_rate=155,
        )

        detail = ActivityDetailModel(
            activity_id=activity_id,
            provider_lap_count=0,
            interval_summary=[],
        )

        db.add(training_session)
        db.add(activity)
        db.add(detail)
        db.flush()

        db.add(
            ActivityStreamModel(
                activity_id=activity_id,
                stream_type="time",
                data=[
                    0,
                    1,
                    2,
                    3,
                ],
            )
        )

        db.add(
            ActivityStreamModel(
                activity_id=activity_id,
                stream_type="heartrate",
                data=[
                    140,
                    145,
                    150,
                    150,
                ],
            )
        )

        db.add(
            ActivityStreamModel(
                activity_id=activity_id,
                stream_type="velocity_smooth",
                data=[
                    2.5,
                    2.5,
                    2.5,
                    2.5,
                ],
            )
        )

        db.commit()

        return (
            session_id,
            activity_id,
        )

    finally:
        db.close()


def test_validate_returns_session_and_debrief() -> None:
    (
        engine,
        SessionLocal,
        athlete_profile_id,
    ) = _test_context()

    try:
        (
            session_id,
            activity_id,
        ) = _seed_session_and_activity(
            SessionLocal,
            athlete_profile_id=(
                athlete_profile_id
            ),
        )

        client = TestClient(app)

        response = client.post(
            (
                "/api/training-sessions/"
                f"{session_id}/validate"
            ),
            json={
                "activity_id": str(
                    activity_id
                ),
            },
        )

        assert response.status_code == 200

        payload = response.json()

        assert (
            payload["session"]["status"]
            == "completed"
        )

        assert (
            payload["session"]["activity_id"]
            == str(activity_id)
        )

        assert (
            payload["analysis"][
                "training_session_id"
            ]
            == str(session_id)
        )

        assert (
            payload["analysis"][
                "activity_id"
            ]
            == str(activity_id)
        )

        assert payload["analysis"]["debriefing"]

    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_validate_twice_returns_conflict() -> None:
    (
        engine,
        SessionLocal,
        athlete_profile_id,
    ) = _test_context()

    try:
        (
            session_id,
            activity_id,
        ) = _seed_session_and_activity(
            SessionLocal,
            athlete_profile_id=(
                athlete_profile_id
            ),
        )

        client = TestClient(app)

        first = client.post(
            (
                "/api/training-sessions/"
                f"{session_id}/validate"
            ),
            json={
                "activity_id": str(
                    activity_id
                ),
            },
        )

        assert first.status_code == 200

        second = client.post(
            (
                "/api/training-sessions/"
                f"{session_id}/validate"
            ),
            json={
                "activity_id": str(
                    activity_id
                ),
            },
        )

        assert second.status_code == 409

    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_get_debrief_after_validation() -> None:
    (
        engine,
        SessionLocal,
        athlete_profile_id,
    ) = _test_context()

    try:
        (
            session_id,
            activity_id,
        ) = _seed_session_and_activity(
            SessionLocal,
            athlete_profile_id=(
                athlete_profile_id
            ),
        )

        client = TestClient(app)

        validated = client.post(
            (
                "/api/training-sessions/"
                f"{session_id}/validate"
            ),
            json={
                "activity_id": str(
                    activity_id
                ),
            },
        )

        assert validated.status_code == 200

        response = client.get(
            (
                "/api/training-sessions/"
                f"{session_id}/debrief"
            )
        )

        assert response.status_code == 200

        payload = response.json()

        assert (
            payload["training_session_id"]
            == str(session_id)
        )

        assert payload["debriefing"]

        assert isinstance(
            payload["metrics"],
            list,
        )

    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_get_debrief_before_validation_returns_404() -> None:
    (
        engine,
        SessionLocal,
        athlete_profile_id,
    ) = _test_context()

    try:
        (
            session_id,
            _,
        ) = _seed_session_and_activity(
            SessionLocal,
            athlete_profile_id=(
                athlete_profile_id
            ),
        )

        client = TestClient(app)

        response = client.get(
            (
                "/api/training-sessions/"
                f"{session_id}/debrief"
            )
        )

        assert response.status_code == 404

    finally:
        app.dependency_overrides.clear()
        engine.dispose()
