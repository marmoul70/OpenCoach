from datetime import date
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.ai.constraints_tools import (
    ActiveConstraintsArguments,
    build_active_constraints_tool,
)
from opencoach.database.base import Base
from opencoach.database.models import AthleteConstraint, AthleteProfile, User


def _database():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine


def _profile(session: Session, suffix: str):
    user = User(email=f"{suffix}-{uuid4()}@example.test")
    session.add(user)
    session.flush()
    profile = AthleteProfile(user_id=user.id)
    session.add(profile)
    session.flush()
    return profile


def test_active_constraints_returns_only_constraints_covering_target_date():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, "constraint-owner")
        session.add_all([
            AthleteConstraint(
                athlete_profile_id=profile.id,
                start_date=date(2026, 11, 8),
                end_date=date(2026, 11, 12),
                constraint_type="injury",
                availability="limited",
                running_allowed=False,
                cross_training_allowed=True,
                max_duration_minutes=45,
                notes="Douleur signalée au mollet",
            ),
            AthleteConstraint(
                athlete_profile_id=profile.id,
                start_date=date(2026, 11, 13),
                end_date=date(2026, 11, 15),
                constraint_type="availability",
                availability="reduced",
                running_allowed=True,
                cross_training_allowed=True,
            ),
        ])
        session.flush()
        tool = build_active_constraints_tool(
            session,
            profile.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        )
        result = tool.handler(ActiveConstraintsArguments())

    assert result["status"] == "ok"
    assert result["target_date"] == "2026-11-09"
    assert result["constraint_count"] == 1
    assert result["constraints"][0]["running_allowed"] is False
    assert result["constraints"][0]["cross_training_allowed"] is True
    assert result["constraints"][0]["max_duration_minutes"] == 45
    assert result["constraints"][0]["notes"] == "Douleur signalée au mollet"
    engine.dispose()


def test_active_constraints_is_scoped_to_athlete_and_empty_is_explicit():
    engine = _database()
    with Session(engine) as session:
        owner = _profile(session, "constraint-owner")
        other = _profile(session, "constraint-other")
        session.add(
            AthleteConstraint(
                athlete_profile_id=owner.id,
                start_date=date(2026, 11, 1),
                end_date=date(2026, 11, 30),
                constraint_type="illness",
                availability="unavailable",
                running_allowed=False,
                cross_training_allowed=False,
            )
        )
        session.flush()
        result = build_active_constraints_tool(
            session,
            other.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        ).handler(ActiveConstraintsArguments())

    assert result["status"] == "empty"
    assert result["constraint_count"] == 0
    assert result["constraints"] == []
    engine.dispose()


def test_active_constraints_accepts_an_explicit_target_date():
    engine = _database()
    with Session(engine) as session:
        profile = _profile(session, "constraint-date")
        session.add(
            AthleteConstraint(
                athlete_profile_id=profile.id,
                start_date=date(2026, 11, 10),
                end_date=date(2026, 11, 10),
                constraint_type="availability",
                availability="limited",
                running_allowed=True,
                cross_training_allowed=True,
            )
        )
        session.flush()
        result = build_active_constraints_tool(
            session,
            profile.id,
            reference_date_provider=lambda: date(2026, 11, 9),
        ).handler(ActiveConstraintsArguments(target_date=date(2026, 11, 10)))

    assert result["status"] == "ok"
    assert result["target_date"] == "2026-11-10"
    assert result["constraint_count"] == 1
    engine.dispose()
