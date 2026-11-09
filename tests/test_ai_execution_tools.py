from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.ai.execution_tools import (
    SessionExecutionReviewArguments,
    build_session_execution_review_tool,
)
from opencoach.database.base import Base
from opencoach.database.models import (
    Activity as ActivityModel,
    AthleteProfile as AthleteProfileModel,
    TrainingSession as TrainingSessionModel,
    User,
)


def _database():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine


def _profile(session: Session, suffix: str):
    user = User(email=f"{suffix}-{uuid4()}@example.test")
    session.add(user)
    session.flush()
    profile = AthleteProfileModel(user_id=user.id)
    session.add(profile)
    session.flush()
    return profile


def _planned_session(session: Session, profile_id, *, activity_id=None):
    planned = TrainingSessionModel(
        athlete_profile_id=profile_id,
        date=date(2026, 11, 9),
        type="aerobic_easy",
        sport_type="Run",
        title="Endurance fondamentale",
        description="Description non transmise au modèle",
        duration_minutes=60,
        distance_km=10,
        elevation_gain_m=150,
        intensity="easy",
        heart_rate_zone="Z2",
        prescription={
            "intensity": {
                "targets": [
                    {
                        "reference": "heart_rate",
                        "label": "Fréquence cardiaque",
                        "minimum": 130,
                        "maximum": 150,
                        "unit": "bpm",
                    }
                ]
            }
        },
        status="completed",
        activity_id=activity_id,
    )
    session.add(planned)
    session.flush()
    return planned


def test_session_execution_review_uses_deterministic_engine_and_scoped_repositories():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, "review")
        activity = ActivityModel(
            athlete_profile_id=profile.id,
            provider="intervals",
            provider_activity_id=f"activity-{uuid4()}",
            name="Sortie réelle",
            sport_type="Run",
            start_at=datetime(2026, 11, 9, 8),
            start_at_local=datetime(2026, 11, 9, 9),
            moving_time_seconds=3600,
            distance_m=10000,
            elevation_gain_m=150,
            average_heart_rate=140,
            average_speed_mps=2.78,
            training_load=45,
        )
        session.add(activity)
        session.flush()
        planned = _planned_session(
            session,
            profile.id,
            activity_id=activity.id,
        )
        result = build_session_execution_review_tool(
            session, profile.id
        ).handler(SessionExecutionReviewArguments(session_id=planned.id))

    assert result["status"] == "ok"
    assert result["planned_session"]["session_id"] == str(planned.id)
    assert result["activity"]["activity_id"] == str(activity.id)
    assert result["detail_available"] is False
    assert result["assessment"]["goal_type"] == "endurance"
    assert result["assessment"]["overall_status"] in {
        "compliant",
        "partial",
        "non_compliant",
        "insufficient_data",
        "not_applicable",
    }
    assert result["assessment"]["metrics"]
    assert "description" not in result["planned_session"]
    assert "Description non transmise" not in str(result)
    engine.dispose()


def test_session_execution_review_asks_for_activity_link_instead_of_guessing():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, "unlinked")
        planned = _planned_session(session, profile.id)
        result = build_session_execution_review_tool(
            session, profile.id
        ).handler(SessionExecutionReviewArguments(session_id=planned.id))

    assert result["status"] == "activity_not_linked"
    assert result["planned_session"]["title"] == "Endurance fondamentale"
    assert "confirmer" in result["message"]
    engine.dispose()


def test_session_execution_review_does_not_expose_another_athletes_session():
    engine = _database()
    with Session(engine) as session:
        owner = _profile(session, "review-owner")
        other = _profile(session, "review-other")
        planned = _planned_session(session, owner.id)
        result = build_session_execution_review_tool(
            session, other.id
        ).handler(SessionExecutionReviewArguments(session_id=planned.id))

    assert result["status"] == "not_found"
    engine.dispose()
