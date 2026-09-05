from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import (
    date,
    datetime,
    timedelta,
    timezone,
)
from uuid import uuid4

from opencoach.coaching.weekly_debrief_eligibility import (
    WeeklyClosureEligibility,
)
from opencoach.coaching.weekly_debrief_orchestrator import (
    WeeklyDebriefOrchestrationResult,
    WeeklyDebriefOrchestrationBatch,
    WeeklyDebriefOrchestrationStatus,
    WeeklyDebriefOrchestrator,
    WeeklyDebriefProfileContext,
)


TZ = timezone(
    timedelta(hours=2)
)

WEEK_START = date(
    2026,
    8,
    31,
)

WEEK_END = date(
    2026,
    9,
    6,
)


@dataclass(frozen=True)
class FakePlanningResult:
    already_applied: bool = False


class FakeClosureService:
    def __init__(
        self,
        *,
        error: Exception | None = None,
    ) -> None:
        self.error = error
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        return object()


class FakePlanningApplicationService:
    def __init__(
        self,
        *,
        already_applied: bool = False,
        error: Exception | None = None,
    ) -> None:
        self.already_applied = already_applied
        self.error = error
        self.calls = []

    def execute(self, **kwargs):
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        return FakePlanningResult(
            already_applied=self.already_applied
        )


def context(
    *,
    hour: int = 20,
    minute: int = 30,
    remaining: bool = False,
    planning_input=...,
    last_completed_at=None,
):
    if planning_input is ...:
        planning_input = object()

    return WeeklyDebriefProfileContext(
        athlete_profile_id=uuid4(),
        week_start=WEEK_START,
        week_end=WEEK_END,
        now=datetime(
            2026,
            9,
            6,
            hour,
            minute,
            tzinfo=TZ,
        ),
        has_remaining_planned_session=remaining,
        completed_sessions_count=1,
        last_completed_at=last_completed_at,
        planning_input=planning_input,
    )


def test_wait_does_not_touch_persistence() -> None:
    closure = FakeClosureService()
    planning = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    ctx = context(
        hour=19,
        minute=59,
    )

    result = orchestrator.process_profile(
        ctx
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.WAIT
    )

    assert (
        result.eligibility
        is WeeklyClosureEligibility.WAIT
    )

    assert closure.calls == []
    assert planning.calls == []


def test_remaining_session_waits() -> None:
    closure = FakeClosureService()
    planning = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    result = orchestrator.process_profile(
        context(
            remaining=True
        )
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.WAIT
    )

    assert closure.calls == []
    assert planning.calls == []


def test_normal_close_runs_closure_then_planning() -> None:
    closure = FakeClosureService()
    planning = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    ctx = context()

    result = orchestrator.process_profile(
        ctx
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.COMPLETED
    )

    assert (
        result.eligibility
        is WeeklyClosureEligibility.CLOSE
    )

    assert len(closure.calls) == 1
    assert len(planning.calls) == 1

    assert (
        closure.calls[0]["athlete_profile_id"]
        == ctx.athlete_profile_id
    )

    assert (
        planning.calls[0]["athlete_profile_id"]
        == ctx.athlete_profile_id
    )


def test_cutoff_forces_processing() -> None:
    closure = FakeClosureService()
    planning = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    result = orchestrator.process_profile(
        context(
            hour=23,
            minute=45,
            remaining=True,
        )
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.COMPLETED
    )

    assert (
        result.eligibility
        is WeeklyClosureEligibility.CUTOFF
    )

    assert len(closure.calls) == 1
    assert len(planning.calls) == 1


def test_sync_grace_waits() -> None:
    closure = FakeClosureService()
    planning = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    completed_at = datetime(
        2026,
        9,
        6,
        21,
        0,
        tzinfo=TZ,
    )

    result = orchestrator.process_profile(
        context(
            hour=21,
            minute=10,
            last_completed_at=completed_at,
        )
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.WAIT
    )

    assert closure.calls == []
    assert planning.calls == []


def test_missing_planning_input_fails_before_closure() -> None:
    closure = FakeClosureService()
    planning = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    result = orchestrator.process_profile(
        context(
            planning_input=None
        )
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.FAILED
    )

    assert (
        result.error
        == "missing_planning_input"
    )

    assert closure.calls == []
    assert planning.calls == []


def test_existing_planning_is_reported_as_already_completed() -> None:
    closure = FakeClosureService()

    planning = FakePlanningApplicationService(
        already_applied=True
    )

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    result = orchestrator.process_profile(
        context()
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.ALREADY_COMPLETED
    )

    assert len(closure.calls) == 1
    assert len(planning.calls) == 1


def test_closure_failure_does_not_run_planning() -> None:
    closure = FakeClosureService(
        error=RuntimeError(
            "closure failed"
        )
    )

    planning = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    result = orchestrator.process_profile(
        context()
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.FAILED
    )

    assert "RuntimeError" in result.error
    assert planning.calls == []


def test_planning_failure_is_reported() -> None:
    closure = FakeClosureService()

    planning = FakePlanningApplicationService(
        error=RuntimeError(
            "planning failed"
        )
    )

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    result = orchestrator.process_profile(
        context()
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.FAILED
    )

    assert "planning failed" in result.error

    assert len(closure.calls) == 1
    assert len(planning.calls) == 1


def test_multi_profile_failure_is_isolated() -> None:
    class SelectiveClosure:
        def __init__(self):
            self.calls = []

        def execute(
            self,
            *,
            athlete_profile_id,
            **kwargs,
        ):
            del kwargs

            self.calls.append(
                athlete_profile_id
            )

            if len(self.calls) == 2:
                raise RuntimeError(
                    "athlete failure"
                )

            return object()

    closure = SelectiveClosure()
    planning = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure,
        planning_application_service=planning,
    )

    contexts = (
        context(),
        context(),
        context(),
    )

    batch = orchestrator.process_many(
        contexts
    )

    assert len(batch.results) == 3
    assert batch.completed == 2
    assert batch.failed == 1
    assert batch.waiting == 0

    assert (
        batch.results[0].status
        is WeeklyDebriefOrchestrationStatus.COMPLETED
    )

    assert (
        batch.results[1].status
        is WeeklyDebriefOrchestrationStatus.FAILED
    )

    assert (
        batch.results[2].status
        is WeeklyDebriefOrchestrationStatus.COMPLETED
    )


def test_no_completed_session_returns_no_debrief() -> None:
    closure_service = FakeClosureService()
    planning_service = FakePlanningApplicationService()

    orchestrator = WeeklyDebriefOrchestrator(
        closure_service=closure_service,
        planning_application_service=planning_service,
    )

    empty_context = replace(
        context(),
        completed_sessions_count=0,
        planning_input=None,
    )

    result = orchestrator.process_profile(
        empty_context
    )

    assert (
        result.status
        is WeeklyDebriefOrchestrationStatus.NO_DEBRIEF
    )

    assert result.error is None
    assert closure_service.calls == []
    assert planning_service.calls == []


def test_no_debrief_is_counted_separately_from_failure() -> None:
    batch = WeeklyDebriefOrchestrationBatch(
        results=(
            WeeklyDebriefOrchestrationResult(
                athlete_profile_id=uuid4(),
                status=(
                    WeeklyDebriefOrchestrationStatus.NO_DEBRIEF
                ),
                eligibility=(
                    WeeklyClosureEligibility.CLOSE
                ),
                reason="Aucune séance réalisée.",
            ),
        )
    )

    assert batch.no_debrief == 1
    assert batch.completed == 0
    assert batch.already_completed == 0
    assert batch.waiting == 0
    assert batch.failed == 0
