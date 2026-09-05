from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from opencoach.coaching.weekly_debrief_closure import (
    WeeklyDebriefClosureService,
)
from opencoach.coaching.weekly_debrief_sql_runtime import (
    SqlWeeklyDebriefRuntime,
    load_active_athlete_profile_ids,
)
from opencoach.database.repositories.sql_activity import (
    SqlActivityRepository,
)
from opencoach.database.repositories.sql_session_execution_analysis import (
    SqlSessionExecutionAnalysisRepository,
)
from opencoach.database.repositories.sql_training_session import (
    SqlTrainingSessionRepository,
)
from opencoach.database.repositories.sql_weekly_debrief import (
    SqlWeeklyDebriefRepository,
)
from opencoach.database.repositories.sql_weekly_training_plan import (
    SqlWeeklyTrainingPlanRepository,
)


class FakeScalarResult:
    def __init__(self, values):
        self.values = values

    def all(self):
        return list(
            self.values
        )


class FakeDatabase:
    def __init__(self, profile_ids=()):
        self.profile_ids = tuple(
            profile_ids
        )
        self.statement = None

    def scalars(self, statement):
        self.statement = statement

        return FakeScalarResult(
            self.profile_ids
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
            item
            for item in self.sessions
            if (
                start_date
                <= item.date
                <= end_date
            )
        ]


class FakeActivityReader:
    def __init__(self, activities):
        self.activities = {
            item.id: item
            for item in activities
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


def test_active_profile_loader_returns_scalar_ids() -> None:
    first = uuid4()
    second = uuid4()

    database = FakeDatabase(
        (
            first,
            second,
        )
    )

    result = load_active_athlete_profile_ids(
        database
    )

    assert result == (
        first,
        second,
    )

    assert database.statement is not None


def test_active_profile_query_filters_active_users() -> None:
    database = FakeDatabase()

    load_active_athlete_profile_ids(
        database
    )

    sql = str(
        database.statement
    ).lower()

    assert "users" in sql
    assert "active" in sql
    assert "order by" in sql


def test_sql_runtime_builds_all_expected_repositories() -> None:
    runtime = SqlWeeklyDebriefRuntime(
        FakeDatabase()
    )

    assert isinstance(
        runtime.training_sessions,
        SqlTrainingSessionRepository,
    )

    assert isinstance(
        runtime.activities,
        SqlActivityRepository,
    )

    assert isinstance(
        runtime.weekly_plans,
        SqlWeeklyTrainingPlanRepository,
    )

    assert isinstance(
        runtime.execution_analyses,
        SqlSessionExecutionAnalysisRepository,
    )

    assert isinstance(
        runtime.weekly_debriefs,
        SqlWeeklyDebriefRepository,
    )


def test_sql_runtime_builds_real_closure_service() -> None:
    runtime = SqlWeeklyDebriefRuntime(
        FakeDatabase()
    )

    service = runtime.build_closure_service()

    assert isinstance(
        service,
        WeeklyDebriefClosureService,
    )

    assert (
        service._session_reader
        is runtime.training_sessions
    )

    assert (
        service._activity_reader
        is runtime.activities
    )


def test_runtime_facts_use_injected_repository_state() -> None:
    runtime = SqlWeeklyDebriefRuntime(
        FakeDatabase()
    )

    key_id = uuid4()

    runtime.training_sessions = (
        FakeSessionReader(
            [
                FakeSession(
                    id=key_id,
                    date=date(
                        2026,
                        9,
                        6,
                    ),
                    status="planned",
                    planning_importance="key",
                )
            ]
        )
    )

    runtime.activities = (
        FakeActivityReader(
            []
        )
    )

    facts = runtime.build_runtime_facts(
        athlete_profile_id=uuid4(),
        reference_date=date(
            2026,
            9,
            6,
        ),
    )

    assert (
        facts.has_remaining_planned_session
        is True
    )

    assert facts.key_session_ids == frozenset(
        {key_id}
    )


def test_runtime_facts_resolve_real_completion_time() -> None:
    runtime = SqlWeeklyDebriefRuntime(
        FakeDatabase()
    )

    activity_id = uuid4()

    runtime.training_sessions = (
        FakeSessionReader(
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
        )
    )

    runtime.activities = (
        FakeActivityReader(
            [
                FakeActivity(
                    id=activity_id,
                    start_at=datetime(
                        2026,
                        9,
                        6,
                        20,
                        0,
                        tzinfo=timezone.utc,
                    ),
                    moving_time_seconds=3600,
                )
            ]
        )
    )

    facts = runtime.build_runtime_facts(
        athlete_profile_id=uuid4(),
        reference_date=date(
            2026,
            9,
            6,
        ),
    )

    assert facts.last_completed_at == datetime(
        2026,
        9,
        6,
        21,
        0,
        tzinfo=timezone.utc,
    )
