from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.ai.activity_tools import (
    ActivityDetailArguments,
    build_activity_detail_tool,
)
from opencoach.database.base import Base
from opencoach.database.models import Activity as ActivityModel
from opencoach.database.repositories import SqlActivityDetailRepository
from opencoach.models import ActivityDetail, ActivityInterval, ActivityStream, ActivityStreams


def _database():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    return engine


def _activity(session, profile_id, *, name="Sortie trail", day=9):
    activity = ActivityModel(
        athlete_profile_id=profile_id,
        provider="intervals",
        provider_activity_id=f"provider-{uuid4()}",
        name=name,
        sport_type="TrailRun",
        start_at=datetime(2026, 11, day, 8),
        start_at_local=datetime(2026, 11, day, 9),
        distance_m=12000,
        elevation_gain_m=650,
        average_heart_rate=145,
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return activity


def test_activity_detail_returns_curated_activity_and_interval_data():
    engine = _database()
    profile_id = uuid4()
    with Session(engine) as session:
        activity = _activity(session, profile_id)
        repository = SqlActivityDetailRepository(session)
        repository.save_activity_detail(
            profile_id,
            ActivityDetail(
                provider_activity_id=activity.provider_activity_id,
                intervals=(
                    ActivityInterval(
                        provider_interval_id="lap-1",
                        interval_type="WORK",
                        label="Montée",
                        start_index=0,
                        end_index=10,
                        start_time_seconds=0,
                        end_time_seconds=600,
                        distance_m=1800,
                        average_heart_rate=152,
                        max_heart_rate=169,
                    ),
                ),
                streams=ActivityStreams(
                    heartrate=ActivityStream(
                        stream_type="heartrate",
                        data=(120, 140, None, 160),
                    ),
                ),
                interval_summary=("1 montée de 10 min",),
                provider_lap_count=1,
            ),
        )
        tool = build_activity_detail_tool(session, profile_id)
        result = tool.handler(
            ActivityDetailArguments(activity_date=date(2026, 11, 9))
        )

    assert result["status"] == "ok"
    assert result["activity"]["activity_id"] == str(activity.id)
    assert result["activity"]["distance_m"] == 12000
    assert result["detail"]["intervals"][0]["label"] == "Montée"
    assert result["detail"]["streams"]["heartrate"] == {
        "samples": 4,
        "valid_samples": 3,
        "minimum": 120,
        "maximum": 160,
        "average": 140.0,
    }
    assert "raw_data" not in result
    engine.dispose()


def test_activity_detail_requests_clarification_when_date_matches_multiple_activities():
    engine = _database()
    profile_id = uuid4()
    with Session(engine) as session:
        _activity(session, profile_id, name="Sortie matin")
        _activity(session, profile_id, name="Sortie soir")
        tool = build_activity_detail_tool(session, profile_id)
        result = tool.handler(
            ActivityDetailArguments(activity_date=date(2026, 11, 9))
        )

    assert result["status"] == "ambiguous"
    assert len(result["choices"]) == 2
    assert all("activity_id" in choice for choice in result["choices"])
    engine.dispose()


def test_activity_detail_does_not_expose_another_athletes_activity():
    engine = _database()
    owner_id = uuid4()
    other_profile_id = uuid4()
    with Session(engine) as session:
        activity = _activity(session, owner_id)
        tool = build_activity_detail_tool(session, other_profile_id)
        result = tool.handler(
            ActivityDetailArguments(activity_id=activity.id)
        )

    assert result["status"] == "not_found"
    engine.dispose()


def test_activity_detail_reports_missing_detail_without_inventing_streams():
    engine = _database()
    profile_id = uuid4()
    with Session(engine) as session:
        _activity(session, profile_id)
        tool = build_activity_detail_tool(session, profile_id)
        result = tool.handler(
            ActivityDetailArguments(activity_date=date(2026, 11, 9))
        )

    assert result["status"] == "ok"
    assert result["detail_available"] is False
    assert "Aucun détail" in result["detail_message"]
    engine.dispose()


def test_activity_detail_requires_a_selector_and_rejects_extra_fields():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ActivityDetailArguments()
    with pytest.raises(ValidationError):
        ActivityDetailArguments(activity_date=date(2026, 11, 9), extra="nope")
