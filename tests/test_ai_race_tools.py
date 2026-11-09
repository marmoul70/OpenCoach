from datetime import date, datetime
from types import SimpleNamespace
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.ai.race_tools import (
    RacePreparationArguments,
    build_race_preparation_tool,
)
from opencoach.database.base import Base
from opencoach.database.models import AthleteProfile, Race, User
from opencoach.models import Activity
from opencoach.training.stats import TrainingStats


class FakeRepository:
    def __init__(self, items):
        self.items = items

    def list_activities_between(self, athlete_profile_id, start_date, end_date):
        return self.items

    def list_sessions_between(self, athlete_profile_id, start_date, end_date):
        return self.items


class FakeTrainingStatsService:
    def __init__(self, activities, sessions, stats):
        self.activity_repository = FakeRepository(activities)
        self.training_session_repository = FakeRepository(sessions)
        self.stats = stats
        self.request = None

    def calculate(self, athlete_profile_id, start_date, end_date):
        self.request = (athlete_profile_id, start_date, end_date)
        return self.stats


def _database():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine


def _profile(session: Session, suffix: str):
    user = User(email=f"{suffix}-{uuid4()}@example.test")
    session.add(user)
    session.flush()
    profile = AthleteProfile(
        user_id=user.id,
        weekly_sessions=4,
        weekly_duration_minutes=300,
        weekly_distance_km=40,
        experience="advanced",
        sport_disciplines=["trail_running"],
    )
    session.add(profile)
    session.flush()
    return profile


def _stats():
    return TrainingStats(
        start_date=date(2026, 10, 13),
        end_date=date(2026, 11, 9),
        activities_count=1,
        manual_sessions_count=2,
        total_duration_minutes=360,
        total_distance_km=42.0,
        total_elevation_gain_m=1800.0,
        measured_load=120.0,
        estimated_load=90.0,
    )


def _race(session: Session, profile_id, *, race_date=date(2026, 12, 1)):
    race = Race(
        athlete_profile_id=profile_id,
        date=race_date,
        name="Trail objectif",
        location="Vosges",
        race_type="trail",
        priority="primary",
        distance_km=65,
        elevation_gain_m=3100,
        target_time_minutes=600,
        status="planned",
    )
    session.add(race)
    session.flush()
    return race


def test_race_preparation_analysis_returns_course_and_complete_training_metrics():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, "race-prep")
        race = _race(session, profile.id)
        activity = Activity(
            provider="coros",
            provider_activity_id="activity-1",
            name="Sortie trail",
            sport_type="trail_running",
            start_at=datetime(2026, 11, 8, 8, 0),
            moving_time_seconds=7200,
            distance_m=15000,
            elevation_gain_m=700,
            training_load=60,
        )
        manual = [
            SimpleNamespace(
                status="completed",
                activity_id=None,
                type="trail",
                duration_minutes=90,
                distance_km=12,
                elevation_gain_m=500,
            ),
            SimpleNamespace(
                status="completed",
                activity_id=None,
                type="endurance",
                duration_minutes=90,
                distance_km=15,
                elevation_gain_m=600,
            ),
        ]
        stats = _stats()
        service = FakeTrainingStatsService([activity], manual, stats)
        result = build_race_preparation_tool(
            session,
            service,
            profile.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        ).handler(
            RacePreparationArguments(race_id=race.id, history_days=28)
        )

    assert result["status"] == "ok"
    assert result["days_to_race"] == 22
    assert result["race"]["course_profile"]["distance_km"] == 65
    assert result["race"]["course_profile"]["elevation_density_m_per_km"] == 47.7
    assert result["athlete_capacity"]["weekly_distance_target_km"] == 40
    assert result["recent_training"]["distance"]["total"] == 42
    assert result["recent_training"]["distance"]["weekly_equivalent"] == 10.5
    assert result["recent_training"]["elevation_gain"]["weekly_equivalent"] == 450
    assert result["recent_training"]["load"]["total"] == 210
    assert service.request == (
        profile.id,
        date(2026, 10, 13),
        date(2026, 11, 9),
    )
    engine.dispose()


def test_race_preparation_masks_partial_metrics_instead_of_extrapolating():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, "race-partial")
        race = _race(session, profile.id)
        activity = Activity(
            provider="coros",
            provider_activity_id="activity-1",
            name="Sortie incomplète",
            sport_type="trail_running",
            start_at=datetime(2026, 11, 8, 8, 0),
            moving_time_seconds=3600,
            distance_m=None,
            elevation_gain_m=300,
            training_load=None,
        )
        manual = [
            SimpleNamespace(
                status="completed",
                activity_id=None,
                type="trail",
                duration_minutes=60,
                distance_km=10,
                elevation_gain_m=200,
            )
        ]
        service = FakeTrainingStatsService([activity], manual, _stats())
        result = build_race_preparation_tool(
            session,
            service,
            profile.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        ).handler(
            RacePreparationArguments(race_id=race.id, history_days=28)
        )

    assert result["status"] == "ok"
    assert result["recent_training"]["distance"]["total"] is None
    assert result["recent_training"]["distance"]["coverage"]["status"] == "partial"
    assert result["recent_training"]["elevation_gain"]["total"] == 500
    assert result["recent_training"]["load"]["total"] is None
    assert result["recent_training"]["load"]["coverage"] == "partial_or_unavailable"
    engine.dispose()


def test_race_preparation_does_not_expose_another_athletes_race():
    engine = _database()
    with Session(engine) as session:
        owner = _profile(session, "race-owner")
        other = _profile(session, "race-other")
        race = _race(session, owner.id)
        service = FakeTrainingStatsService([], [], _stats())
        result = build_race_preparation_tool(
            session,
            service,
            other.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        ).handler(
            RacePreparationArguments(race_id=race.id, history_days=28)
        )

    assert result["status"] == "not_found"
    assert service.request is None
    engine.dispose()


def test_race_preparation_refuses_to_analyse_past_race_as_future_goal():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, "race-past")
        race = _race(session, profile.id, race_date=date(2026, 11, 8))
        service = FakeTrainingStatsService([], [], _stats())
        result = build_race_preparation_tool(
            session,
            service,
            profile.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        ).handler(
            RacePreparationArguments(race_id=race.id, history_days=28)
        )

    assert result["status"] == "past_event"
    assert service.request is None
    engine.dispose()
