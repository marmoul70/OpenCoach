from datetime import date, datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.coaching.weekly_debrief import (
    WeeklyDebriefFacts,
    build_weekly_debrief,
)
from opencoach.database import models  # noqa: F401
from opencoach.database.base import Base
from opencoach.database.repositories.sql_weekly_debrief import (
    SqlWeeklyDebriefRepository,
)
from opencoach.database.repositories.weekly_debrief import (
    WeeklyDebriefAlreadyClosedError,
)


WEEK_START = date(2026, 8, 31)
WEEK_END = date(2026, 9, 6)


@pytest.fixture
def session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    with Session(engine) as db:
        yield db

    Base.metadata.drop_all(engine)
    engine.dispose()


def create_facts(
    *,
    completed_sessions: int = 5,
    skipped_sessions: int = 0,
    actual_load: float = 300.0,
) -> WeeklyDebriefFacts:
    return WeeklyDebriefFacts(
        week_start=WEEK_START,
        week_end=WEEK_END,
        planned_sessions=5,
        completed_sessions=completed_sessions,
        skipped_sessions=skipped_sessions,
        supplementary_sessions=0,
        planned_duration_minutes=300,
        actual_duration_minutes=285,
        planned_load=300.0,
        actual_load=actual_load,
        key_sessions_planned=2,
        key_sessions_completed=2,
        compliant_intensity_sessions=4,
        analyzed_intensity_sessions=4,
        history_confidence=1.0,
    )


def test_training_import_does_not_trigger_weekly_debrief_cycle(
) -> None:
    """Le package training doit pouvoir démarrer avant T6.2."""

    import subprocess
    import sys

    code = (
        "import opencoach.training; "
        "from "
        "opencoach.database.repositories."
        "sql_weekly_debrief "
        "import SqlWeeklyDebriefRepository; "
        "assert SqlWeeklyDebriefRepository is not None"
    )

    subprocess.run(
        [
            sys.executable,
            "-c",
            code,
        ],
        check=True,
    )


def test_repository_round_trip(
    session: Session,
) -> None:
    athlete_profile_id = uuid4()

    repository = (
        SqlWeeklyDebriefRepository(
            session
        )
    )

    facts = create_facts()
    debrief = build_weekly_debrief(
        facts
    )

    stored = repository.save_closed(
        athlete_profile_id,
        facts,
        debrief,
        adaptation_payload={
            "source": "t6.2-test",
        },
    )

    loaded = repository.get_for_week(
        athlete_profile_id,
        WEEK_START,
    )

    assert loaded is not None
    assert loaded.id == stored.id
    assert (
        loaded.athlete_profile_id
        == athlete_profile_id
    )

    assert loaded.facts == facts
    assert loaded.debrief == debrief

    assert loaded.adaptation_payload == {
        "source": "t6.2-test",
    }

    assert loaded.generated_at is not None
    assert loaded.recalculated_at is None
    assert loaded.planning_updated_at is None
    assert loaded.notification_sent_at is None


def test_week_is_scoped_by_athlete(
    session: Session,
) -> None:
    repository = (
        SqlWeeklyDebriefRepository(
            session
        )
    )

    athlete_a = uuid4()
    athlete_b = uuid4()

    facts = create_facts()
    debrief = build_weekly_debrief(
        facts
    )

    repository.save_closed(
        athlete_a,
        facts,
        debrief,
    )

    assert (
        repository.get_for_week(
            athlete_b,
            WEEK_START,
        )
        is None
    )

    assert (
        repository.get_for_week(
            athlete_a,
            WEEK_START,
        )
        is not None
    )


def test_closed_week_cannot_be_silently_overwritten(
    session: Session,
) -> None:
    repository = (
        SqlWeeklyDebriefRepository(
            session
        )
    )

    athlete_profile_id = uuid4()

    original_facts = create_facts()
    original = build_weekly_debrief(
        original_facts
    )

    repository.save_closed(
        athlete_profile_id,
        original_facts,
        original,
    )

    changed_facts = create_facts(
        completed_sessions=4,
        skipped_sessions=1,
        actual_load=250.0,
    )
    changed = build_weekly_debrief(
        changed_facts
    )

    with pytest.raises(
        WeeklyDebriefAlreadyClosedError
    ):
        repository.save_closed(
            athlete_profile_id,
            changed_facts,
            changed,
        )

    loaded = repository.get_for_week(
        athlete_profile_id,
        WEEK_START,
    )

    assert loaded is not None
    assert loaded.debrief == original
    assert loaded.recalculated_at is None


def test_explicit_recalculation_preserves_identity(
    session: Session,
) -> None:
    repository = (
        SqlWeeklyDebriefRepository(
            session
        )
    )

    athlete_profile_id = uuid4()

    original_facts = create_facts()
    original = build_weekly_debrief(
        original_facts
    )

    stored = repository.save_closed(
        athlete_profile_id,
        original_facts,
        original,
    )

    changed_facts = create_facts(
        completed_sessions=4,
        skipped_sessions=1,
        actual_load=250.0,
    )
    changed = build_weekly_debrief(
        changed_facts
    )

    recalculated = repository.save_closed(
        athlete_profile_id,
        changed_facts,
        changed,
        allow_recalculation=True,
    )

    assert recalculated.id == stored.id
    assert (
        recalculated.generated_at
        == stored.generated_at
    )
    assert (
        recalculated.recalculated_at
        is not None
    )
    assert recalculated.facts == changed_facts
    assert recalculated.debrief == changed


def test_operational_timestamps_can_be_marked(
    session: Session,
) -> None:
    repository = (
        SqlWeeklyDebriefRepository(
            session
        )
    )

    athlete_profile_id = uuid4()
    facts = create_facts()

    repository.save_closed(
        athlete_profile_id,
        facts,
        build_weekly_debrief(facts),
    )

    planning_time = datetime(
        2026,
        9,
        6,
        20,
        15,
        tzinfo=timezone.utc,
    )

    notification_time = datetime(
        2026,
        9,
        6,
        20,
        16,
        tzinfo=timezone.utc,
    )

    planned = repository.mark_planning_updated(
        athlete_profile_id,
        WEEK_START,
        timestamp=planning_time,
    )

    notified = repository.mark_notification_sent(
        athlete_profile_id,
        WEEK_START,
        timestamp=notification_time,
    )

    assert planned is not None
    assert notified is not None

    assert (
        planned.planning_updated_at
        == planning_time
    )
    assert (
        notified.notification_sent_at
        == notification_time
    )

    assert (
        planned.planning_updated_at.tzinfo
        is timezone.utc
    )
    assert (
        notified.notification_sent_at.tzinfo
        is timezone.utc
    )


def test_timestamp_with_offset_is_normalized_to_utc(
    session: Session,
) -> None:
    repository = (
        SqlWeeklyDebriefRepository(
            session
        )
    )

    athlete_profile_id = uuid4()
    facts = create_facts()

    repository.save_closed(
        athlete_profile_id,
        facts,
        build_weekly_debrief(facts),
    )

    from datetime import timedelta

    source_timezone = timezone(
        timedelta(hours=2)
    )

    source_time = datetime(
        2026,
        9,
        6,
        22,
        15,
        tzinfo=source_timezone,
    )

    stored = repository.mark_planning_updated(
        athlete_profile_id,
        WEEK_START,
        timestamp=source_time,
    )

    assert stored is not None

    assert (
        stored.planning_updated_at
        == datetime(
            2026,
            9,
            6,
            20,
            15,
            tzinfo=timezone.utc,
        )
    )


def test_mark_unknown_week_returns_none(
    session: Session,
) -> None:
    repository = (
        SqlWeeklyDebriefRepository(
            session
        )
    )

    athlete_profile_id = uuid4()

    assert (
        repository.mark_planning_updated(
            athlete_profile_id,
            WEEK_START,
        )
        is None
    )

    assert (
        repository.mark_notification_sent(
            athlete_profile_id,
            WEEK_START,
        )
        is None
    )


def test_repository_rejects_inconsistent_dates(
    session: Session,
) -> None:
    repository = (
        SqlWeeklyDebriefRepository(
            session
        )
    )

    facts = create_facts()
    debrief = build_weekly_debrief(
        facts
    )

    inconsistent = type(debrief)(
        week_start=date(2026, 9, 7),
        week_end=debrief.week_end,
        verdict=debrief.verdict,
        adaptation_direction=(
            debrief.adaptation_direction
        ),
        overall_score=debrief.overall_score,
        adherence_score=(
            debrief.adherence_score
        ),
        duration_score=(
            debrief.duration_score
        ),
        load_score=debrief.load_score,
        key_sessions_score=(
            debrief.key_sessions_score
        ),
        intensity_score=(
            debrief.intensity_score
        ),
        completion_ratio=(
            debrief.completion_ratio
        ),
        duration_ratio=(
            debrief.duration_ratio
        ),
        load_ratio=debrief.load_ratio,
        headline=debrief.headline,
        analysis=debrief.analysis,
        strengths=debrief.strengths,
        warnings=debrief.warnings,
    )

    with pytest.raises(ValueError):
        repository.save_closed(
            uuid4(),
            facts,
            inconsistent,
        )
