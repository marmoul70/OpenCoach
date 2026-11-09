from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.ai.coaching_tools import (
    PlannedSessionsArguments,
    RaceCalendarArguments,
    build_planned_sessions_tool,
    build_race_calendar_tool,
    build_training_profile_tool,
)
from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile as AthleteProfileModel,
    Race as RaceModel,
    TrainingSession as TrainingSessionModel,
    User,
)


def _database():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine


def _profile(session: Session, *, suffix: str = "one"):
    user = User(email=f"{suffix}-{uuid4()}@example.test")
    session.add(user)
    session.flush()
    profile = AthleteProfileModel(
        user_id=user.id,
        vma=15.0,
        max_heart_rate=181,
        resting_heart_rate=52,
        threshold_heart_rate_1=145,
        threshold_heart_rate_2=170,
        heart_rate_zones={
            "z1": {"max_bpm": 125},
            "z2": {"max_bpm": 145},
            "z3": {"max_bpm": 160},
            "z4": {"max_bpm": 175},
            "z5": {"max_bpm": 190},
        },
        weekly_sessions=4,
        weekly_duration_minutes=300,
        weekly_distance_km=40.0,
        available_days=[0, 1, 2, 4, 5],
        fatigue_threshold=0.7,
        experience="advanced",
        sport_disciplines=["trail_running"],
        carbohydrates_per_hour=70,
        fluids_per_hour=600,
        sodium_per_hour=500,
    )
    session.add(profile)
    session.flush()
    return profile


def test_training_profile_returns_recorded_values_and_personal_hr_zones():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session)
        tool = build_training_profile_tool(session, profile.id)
        result = tool.handler(PlannedSessionsArguments.model_construct(
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 7),
        ))

    assert result["status"] == "ok"
    assert result["physiology"]["vma_kmh"] == 15.0
    assert result["physiology"]["heart_rate_zones"] == [
        {"zone": "Z1", "min_bpm": None, "max_bpm": 125},
        {"zone": "Z2", "min_bpm": 126, "max_bpm": 145},
        {"zone": "Z3", "min_bpm": 146, "max_bpm": 160},
        {"zone": "Z4", "min_bpm": 161, "max_bpm": 175},
        {"zone": "Z5", "min_bpm": 176, "max_bpm": 190},
    ]
    assert result["training_capacity"]["weekly_sessions_target"] == 4
    assert result["fueling_targets"]["carbohydrates_g_per_hour"] == 70
    assert result["missing_profile_fields"] == []
    engine.dispose()


def test_training_profile_reports_missing_fields_without_estimating_them():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session)
        profile.vma = None
        profile.max_heart_rate = None
        profile.heart_rate_zones = {}
        session.flush()
        result = build_training_profile_tool(
            session, profile.id
        ).handler(PlannedSessionsArguments.model_construct(
            start_date=date(2026, 11, 1),
            end_date=date(2026, 11, 7),
        ))

    assert result["physiology"]["vma_kmh"] is None
    assert result["physiology"]["max_heart_rate_bpm"] is None
    assert "vma" in result["missing_profile_fields"]
    assert "heart_rate_zones" in result["missing_profile_fields"]
    assert result["physiology"]["heart_rate_zones"] == []
    engine.dispose()


def test_race_calendar_returns_only_authenticated_athletes_races_inclusive():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, suffix="owner")
        other_profile = _profile(session, suffix="other")
        session.add_all([
            RaceModel(
                athlete_profile_id=profile.id,
                date=date(2026, 11, 9),
                name="Ultra des Vosges",
                location="Vosges",
                race_type="trail",
                priority="primary",
                distance_km=65,
                elevation_gain_m=3100,
                status="planned",
            ),
            RaceModel(
                athlete_profile_id=other_profile.id,
                date=date(2026, 11, 10),
                name="Other athlete race",
                location="Elsewhere",
                race_type="road",
                priority="training",
                distance_km=10,
                status="planned",
            ),
        ])
        session.flush()
        result = build_race_calendar_tool(
            session,
            profile.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        ).handler(RaceCalendarArguments(horizon_days=30))

    assert result["status"] == "ok"
    assert result["race_count"] == 1
    assert result["races"][0]["name"] == "Ultra des Vosges"
    assert result["races"][0]["days_until"] == 0
    assert result["races"][0]["elevation_gain_m"] == 3100
    engine.dispose()


def test_race_calendar_reports_empty_period_explicitly():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session)
        result = build_race_calendar_tool(
            session,
            profile.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        ).handler(RaceCalendarArguments(horizon_days=7))

    assert result["status"] == "empty"
    assert result["race_count"] == 0
    assert result["races"] == []
    engine.dispose()


def test_planned_sessions_returns_bounded_fields_and_partial_aggregates():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, suffix="sessions")
        other_profile = _profile(session, suffix="other-sessions")
        session.add_all([
            TrainingSessionModel(
                athlete_profile_id=profile.id,
                date=date(2026, 11, 9),
                type="endurance",
                sport_type="trail_running",
                title="Sortie longue",
                duration_minutes=120,
                distance_km=15,
                elevation_gain_m=700,
                intensity="easy",
                heart_rate_zone="Z2",
                status="planned",
                description="Do not expose this text",
                prescription={"raw": "do not expose"},
            ),
            TrainingSessionModel(
                athlete_profile_id=profile.id,
                date=date(2026, 11, 11),
                type="recovery",
                sport_type="road_running",
                title="Footing",
                duration_minutes=45,
                distance_km=None,
                elevation_gain_m=100,
                intensity="low",
                heart_rate_zone="Z1",
                status="planned",
            ),
            TrainingSessionModel(
                athlete_profile_id=other_profile.id,
                date=date(2026, 11, 10),
                type="intervals",
                sport_type="road_running",
                title="Other athlete session",
                duration_minutes=60,
                distance_km=10,
                elevation_gain_m=0,
                intensity="hard",
                status="planned",
            ),
        ])
        session.flush()
        result = build_planned_sessions_tool(
            session, profile.id
        ).handler(PlannedSessionsArguments(
            start_date=date(2026, 11, 9),
            end_date=date(2026, 11, 11),
        ))

    assert result["status"] == "ok"
    assert result["session_count"] == 2
    assert result["summary"]["duration_minutes"] == 165
    assert result["summary"]["distance_km"] is None
    assert result["summary"]["distance_coverage"] == "1/2"
    assert result["summary"]["elevation_gain_m"] == 800
    assert "description" not in result["sessions"][0]
    assert "prescription" not in result["sessions"][0]
    assert "Do not expose" not in str(result)
    engine.dispose()


def test_planned_sessions_requires_valid_period_of_at_most_31_days():
    with pytest.raises(ValidationError):
        PlannedSessionsArguments(
            start_date=date(2026, 11, 10),
            end_date=date(2026, 11, 9),
        )
    with pytest.raises(ValidationError):
        PlannedSessionsArguments(
            start_date=date(2026, 11, 1),
            end_date=date(2026, 12, 2),
        )
    with pytest.raises(ValidationError):
        RaceCalendarArguments(horizon_days=366)
