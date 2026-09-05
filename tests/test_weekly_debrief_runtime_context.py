from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import UUID, uuid4

from opencoach.coaching.weekly_debrief_runtime_context import (
    build_weekly_debrief_runtime_facts,
    resolve_week_bounds,
)


TZ = timezone(
    timedelta(hours=2)
)


@dataclass(frozen=True)
class FakeSession:
    id: UUID
    date: date
    status: str
    planning_importance: str | None = None
    activity_id: UUID | None = None


@dataclass(frozen=True)
class FakeActivity:
    id: UUID
    start_at: datetime
    moving_time_seconds: int | None = None
    elapsed_time_seconds: int | None = None


class FakeSessionReader:
    def __init__(self, sessions):
        self.sessions = list(sessions)

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        del athlete_profile_id

        return [
            session
            for session in self.sessions
            if (
                start_date
                <= session.date
                <= end_date
            )
        ]


class FakeActivityReader:
    def __init__(self, activities):
        self.activities = {
            activity.id: activity
            for activity in activities
        }

    def get_activity(
        self,
        athlete_profile_id,
        activity_id,
    ):
        del athlete_profile_id

        return self.activities.get(
            activity_id
        )


def test_resolves_monday_to_sunday() -> None:
    assert resolve_week_bounds(
        date(2026, 9, 6)
    ) == (
        date(2026, 8, 31),
        date(2026, 9, 6),
    )


def test_detects_remaining_sunday_session() -> None:
    profile_id = uuid4()

    facts = (
        build_weekly_debrief_runtime_facts(
            athlete_profile_id=profile_id,
            reference_date=date(
                2026,
                9,
                6,
            ),
            session_reader=FakeSessionReader(
                [
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            6,
                        ),
                        status="planned",
                    )
                ]
            ),
            activity_reader=FakeActivityReader(
                []
            ),
        )
    )

    assert (
        facts.has_remaining_planned_session
        is True
    )


def test_planned_session_before_sunday_does_not_block() -> None:
    facts = (
        build_weekly_debrief_runtime_facts(
            athlete_profile_id=uuid4(),
            reference_date=date(
                2026,
                9,
                6,
            ),
            session_reader=FakeSessionReader(
                [
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            5,
                        ),
                        status="planned",
                    )
                ]
            ),
            activity_reader=FakeActivityReader(
                []
            ),
        )
    )

    assert (
        facts.has_remaining_planned_session
        is False
    )


def test_resolves_key_sessions_from_persisted_importance() -> None:
    key_id = uuid4()

    facts = (
        build_weekly_debrief_runtime_facts(
            athlete_profile_id=uuid4(),
            reference_date=date(
                2026,
                9,
                6,
            ),
            session_reader=FakeSessionReader(
                [
                    FakeSession(
                        id=key_id,
                        date=date(
                            2026,
                            9,
                            2,
                        ),
                        status="completed",
                        planning_importance="key",
                    ),
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            3,
                        ),
                        status="completed",
                        planning_importance=(
                            "important"
                        ),
                    ),
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            4,
                        ),
                        status="completed",
                        planning_importance=(
                            "support"
                        ),
                    ),
                ]
            ),
            activity_reader=FakeActivityReader(
                []
            ),
        )
    )

    assert facts.key_session_ids == frozenset(
        {key_id}
    )


def test_completed_activity_uses_moving_time_for_end() -> None:
    activity_id = uuid4()

    activity = FakeActivity(
        id=activity_id,
        start_at=datetime(
            2026,
            9,
            6,
            20,
            0,
            tzinfo=TZ,
        ),
        moving_time_seconds=3600,
        elapsed_time_seconds=7200,
    )

    facts = (
        build_weekly_debrief_runtime_facts(
            athlete_profile_id=uuid4(),
            reference_date=date(
                2026,
                9,
                6,
            ),
            session_reader=FakeSessionReader(
                [
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            6,
                        ),
                        status="completed",
                        activity_id=activity_id,
                    )
                ]
            ),
            activity_reader=FakeActivityReader(
                [activity]
            ),
        )
    )

    assert facts.last_completed_at == datetime(
        2026,
        9,
        6,
        21,
        0,
        tzinfo=TZ,
    )


def test_elapsed_time_is_fallback_for_end() -> None:
    activity_id = uuid4()

    activity = FakeActivity(
        id=activity_id,
        start_at=datetime(
            2026,
            9,
            6,
            21,
            0,
            tzinfo=TZ,
        ),
        moving_time_seconds=None,
        elapsed_time_seconds=1800,
    )

    facts = (
        build_weekly_debrief_runtime_facts(
            athlete_profile_id=uuid4(),
            reference_date=date(
                2026,
                9,
                6,
            ),
            session_reader=FakeSessionReader(
                [
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            6,
                        ),
                        status="completed",
                        activity_id=activity_id,
                    )
                ]
            ),
            activity_reader=FakeActivityReader(
                [activity]
            ),
        )
    )

    assert facts.last_completed_at == datetime(
        2026,
        9,
        6,
        21,
        30,
        tzinfo=TZ,
    )


def test_latest_completed_activity_wins() -> None:
    first = uuid4()
    second = uuid4()

    facts = (
        build_weekly_debrief_runtime_facts(
            athlete_profile_id=uuid4(),
            reference_date=date(
                2026,
                9,
                6,
            ),
            session_reader=FakeSessionReader(
                [
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            4,
                        ),
                        status="completed",
                        activity_id=first,
                    ),
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            6,
                        ),
                        status="completed",
                        activity_id=second,
                    ),
                ]
            ),
            activity_reader=FakeActivityReader(
                [
                    FakeActivity(
                        id=first,
                        start_at=datetime(
                            2026,
                            9,
                            4,
                            18,
                            0,
                            tzinfo=TZ,
                        ),
                        moving_time_seconds=3600,
                    ),
                    FakeActivity(
                        id=second,
                        start_at=datetime(
                            2026,
                            9,
                            6,
                            20,
                            30,
                            tzinfo=TZ,
                        ),
                        moving_time_seconds=2700,
                    ),
                ]
            ),
        )
    )

    assert facts.last_completed_at == datetime(
        2026,
        9,
        6,
        21,
        15,
        tzinfo=TZ,
    )


def test_unlinked_completed_session_does_not_fake_completion_time() -> None:
    facts = (
        build_weekly_debrief_runtime_facts(
            athlete_profile_id=uuid4(),
            reference_date=date(
                2026,
                9,
                6,
            ),
            session_reader=FakeSessionReader(
                [
                    FakeSession(
                        id=uuid4(),
                        date=date(
                            2026,
                            9,
                            6,
                        ),
                        status="completed",
                        activity_id=None,
                    )
                ]
            ),
            activity_reader=FakeActivityReader(
                []
            ),
        )
    )

    assert facts.last_completed_at is None


def test_naive_activity_start_is_normalized_to_utc() -> None:
    """SQLite peut restituer start_at sans tzinfo.

    Le runtime hebdomadaire doit restaurer le contrat temporel :
    start_at représente un instant UTC, tandis que start_at_local
    porte séparément la représentation locale.
    """

    from types import SimpleNamespace

    athlete_profile_id = uuid4()
    session_id = uuid4()
    activity_id = uuid4()

    class SessionReader:
        def list_sessions_between(
            self,
            athlete_profile_id_arg,
            start_date,
            end_date,
        ):
            assert (
                athlete_profile_id_arg
                == athlete_profile_id
            )

            return [
                SimpleNamespace(
                    id=session_id,
                    date=date(2026, 9, 3),
                    status="completed",
                    planning_importance=None,
                    activity_id=activity_id,
                )
            ]

    class ActivityReader:
        def get_activity(
            self,
            athlete_profile_id_arg,
            activity_id_arg,
        ):
            assert (
                athlete_profile_id_arg
                == athlete_profile_id
            )
            assert activity_id_arg == activity_id

            return SimpleNamespace(
                id=activity_id,
                start_at=datetime(
                    2026,
                    9,
                    3,
                    12,
                    30,
                    0,
                ),
                moving_time_seconds=(
                    26 * 60 + 9
                ),
                elapsed_time_seconds=None,
            )

    facts = build_weekly_debrief_runtime_facts(
        athlete_profile_id=athlete_profile_id,
        reference_date=date(2026, 9, 5),
        session_reader=SessionReader(),
        activity_reader=ActivityReader(),
    )

    assert facts.last_completed_at == datetime(
        2026,
        9,
        3,
        12,
        56,
        9,
        tzinfo=timezone.utc,
    )

    assert (
        facts.last_completed_at is not None
    )

    assert (
        facts.last_completed_at.tzinfo
        is timezone.utc
    )
