from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

from opencoach.coaching.weekly_debrief_planning_context import (
    DefaultWeeklyDebriefPlanningContextResolver,
)
from opencoach.coaching.weekly_debrief_runtime_context import (
    WeeklyDebriefRuntimeFacts,
)


@dataclass(
    frozen=True,
    slots=True,
)
class FakePreparedContext:
    planning_input: object
    sport_disciplines: tuple


class FakeContextBuilder:
    def __init__(self) -> None:
        self.planning_input = object()
        self.sport_disciplines = (
            "running",
            "cycling",
        )
        self.calls: list[dict] = []

    def build(
        self,
        *,
        athlete_profile_id,
        planning_date,
        trajectory_start_date,
    ):
        self.calls.append(
            {
                "athlete_profile_id":
                    athlete_profile_id,
                "planning_date":
                    planning_date,
                "trajectory_start_date":
                    trajectory_start_date,
            }
        )

        return FakePreparedContext(
            planning_input=self.planning_input,
            sport_disciplines=(
                self.sport_disciplines
            ),
        )


def create_runtime_facts() -> WeeklyDebriefRuntimeFacts:
    return WeeklyDebriefRuntimeFacts(
        week_start=date(
            2026,
            8,
            24,
        ),
        week_end=date(
            2026,
            8,
            30,
        ),
        has_remaining_planned_session=False,
        completed_sessions_count=1,
        last_completed_at=datetime(
            2026,
            8,
            30,
            17,
            30,
            tzinfo=timezone.utc,
        ),
        key_session_ids=frozenset(),
    )


def test_resolver_builds_next_week_context() -> None:
    athlete_profile_id = uuid4()
    builder = FakeContextBuilder()

    resolver = (
        DefaultWeeklyDebriefPlanningContextResolver(
            context_builder=builder,
        )
    )

    result = resolver.resolve(
        athlete_profile_id=athlete_profile_id,
        reference_date=date(
            2026,
            8,
            30,
        ),
        runtime_facts=create_runtime_facts(),
    )

    expected_start = date(
        2026,
        8,
        31,
    )

    assert builder.calls == [
        {
            "athlete_profile_id":
                athlete_profile_id,
            "planning_date":
                expected_start,
            "trajectory_start_date":
                expected_start,
        }
    ]

    assert (
        result.planning_input
        is builder.planning_input
    )

    assert (
        result.sport_disciplines
        == builder.sport_disciplines
    )

    assert (
        result.physiological_reference_date
        == expected_start
    )

    assert (
        result.reconcile_from_date
        == expected_start
    )

    assert result.additional_context == ()


def test_resolver_uses_runtime_week_end_not_reference_date() -> None:
    builder = FakeContextBuilder()

    resolver = (
        DefaultWeeklyDebriefPlanningContextResolver(
            context_builder=builder,
        )
    )

    resolver.resolve(
        athlete_profile_id=uuid4(),
        reference_date=date(
            2030,
            1,
            1,
        ),
        runtime_facts=create_runtime_facts(),
    )

    assert (
        builder.calls[0]["planning_date"]
        == date(
            2026,
            8,
            31,
        )
    )


def test_resolver_crosses_year_boundary() -> None:
    builder = FakeContextBuilder()

    resolver = (
        DefaultWeeklyDebriefPlanningContextResolver(
            context_builder=builder,
        )
    )

    facts = WeeklyDebriefRuntimeFacts(
        week_start=date(
            2026,
            12,
            21,
        ),
        week_end=date(
            2026,
            12,
            27,
        ),
        has_remaining_planned_session=False,
        completed_sessions_count=1,
        last_completed_at=None,
        key_session_ids=frozenset(),
    )

    result = resolver.resolve(
        athlete_profile_id=uuid4(),
        reference_date=date(
            2026,
            12,
            27,
        ),
        runtime_facts=facts,
    )

    assert (
        builder.calls[0]["planning_date"]
        == date(
            2026,
            12,
            28,
        )
    )

    assert (
        result.reconcile_from_date
        == date(
            2026,
            12,
            28,
        )
    )
