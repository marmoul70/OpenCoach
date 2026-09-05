from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from opencoach.coaching.weekly_debrief_closure import (
    WeeklyDebriefClosureService,
    serialize_weekly_adaptation_decision,
)


WEEK_START = date(2026, 8, 31)
WEEK_END = date(2026, 9, 6)


@dataclass(frozen=True)
class FakeSession:
    id: UUID
    status: str
    duration_minutes: int
    activity_id: UUID | None = None


@dataclass(frozen=True)
class FakeActivity:
    id: UUID
    moving_time_seconds: int | None = None
    elapsed_time_seconds: int | None = None
    training_load: float | None = None


@dataclass(frozen=True)
class FakePlan:
    target_load: float | None


@dataclass(frozen=True)
class FakeAnalysis:
    training_session_id: UUID
    overall_status: str
    technical_status: str | None = None


class FakeSessionReader:
    def __init__(self, sessions):
        self.sessions = list(sessions)
        self.calls = []

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )
        return list(self.sessions)


class FakeActivityReader:
    def __init__(self, activities):
        self.activities = list(activities)
        self.calls = []

    def list_activities_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                start_date,
                end_date,
            )
        )
        return list(self.activities)


class FakePlanReader:
    def __init__(self, plan):
        self.plan = plan
        self.calls = []

    def get_plan_for_week(
        self,
        athlete_profile_id,
        week_start,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                week_start,
            )
        )
        return self.plan


class FakeAnalysisReader:
    def __init__(self, analyses):
        self.analyses = dict(analyses)
        self.calls = []

    def get_for_session(
        self,
        *,
        athlete_profile_id,
        training_session_id,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                training_session_id,
            )
        )
        return self.analyses.get(
            training_session_id
        )


class FakeDebriefRepository:
    def __init__(self, existing=None):
        self.existing = existing
        self.get_calls = []
        self.saved = []

    def get_for_week(
        self,
        athlete_profile_id,
        week_start,
    ):
        self.get_calls.append(
            (
                athlete_profile_id,
                week_start,
            )
        )
        return self.existing

    def save_closed(
        self,
        athlete_profile_id,
        facts,
        debrief,
        *,
        adaptation_payload=None,
        allow_recalculation=False,
    ):
        del allow_recalculation

        stored = object()

        self.saved.append(
            {
                "athlete_profile_id": (
                    athlete_profile_id
                ),
                "facts": facts,
                "debrief": debrief,
                "adaptation_payload": (
                    adaptation_payload
                ),
                "result": stored,
            }
        )

        return stored


def _service(
    *,
    sessions=(),
    activities=(),
    plan=None,
    analyses=None,
    existing=None,
):
    session_reader = FakeSessionReader(
        sessions
    )
    activity_reader = FakeActivityReader(
        activities
    )
    plan_reader = FakePlanReader(
        plan
    )
    analysis_reader = FakeAnalysisReader(
        analyses or {}
    )
    repository = FakeDebriefRepository(
        existing=existing
    )

    service = WeeklyDebriefClosureService(
        session_reader=session_reader,
        activity_reader=activity_reader,
        weekly_plan_reader=plan_reader,
        execution_analysis_reader=(
            analysis_reader
        ),
        debrief_repository=repository,
    )

    return (
        service,
        session_reader,
        activity_reader,
        plan_reader,
        analysis_reader,
        repository,
    )


def test_existing_debrief_is_strictly_idempotent() -> None:
    existing = object()

    (
        service,
        session_reader,
        activity_reader,
        plan_reader,
        analysis_reader,
        repository,
    ) = _service(
        existing=existing
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        week_start=WEEK_START,
        week_end=WEEK_END,
    )

    assert result is existing

    assert repository.saved == []
    assert session_reader.calls == []
    assert activity_reader.calls == []
    assert plan_reader.calls == []
    assert analysis_reader.calls == []


def test_closes_week_and_persists_adaptation() -> None:
    profile_id = uuid4()
    session_id = uuid4()
    activity_id = uuid4()

    (
        service,
        _,
        _,
        _,
        analysis_reader,
        repository,
    ) = _service(
        sessions=[
            FakeSession(
                id=session_id,
                status="completed",
                duration_minutes=60,
                activity_id=activity_id,
            )
        ],
        activities=[
            FakeActivity(
                id=activity_id,
                moving_time_seconds=3600,
                training_load=80.0,
            )
        ],
        plan=FakePlan(
            target_load=80.0
        ),
        analyses={
            session_id: FakeAnalysis(
                training_session_id=session_id,
                overall_status="compliant",
            )
        },
    )

    result = service.execute(
        athlete_profile_id=profile_id,
        week_start=WEEK_START,
        week_end=WEEK_END,
        key_session_ids=frozenset(
            {session_id}
        ),
    )

    assert len(repository.saved) == 1

    saved = repository.saved[0]

    assert result is saved["result"]

    facts = saved["facts"]

    assert facts.planned_sessions == 1
    assert facts.completed_sessions == 1
    assert facts.planned_load == 80.0
    assert facts.actual_load == 80.0
    assert facts.key_sessions_planned == 1
    assert facts.key_sessions_completed == 1
    assert facts.analyzed_intensity_sessions == 1
    assert facts.compliant_intensity_sessions == 1

    assert analysis_reader.calls == [
        (
            profile_id,
            session_id,
        )
    ]

    payload = saved[
        "adaptation_payload"
    ]

    assert isinstance(payload, dict)
    assert "direction" in payload

    # Le payload doit être immédiatement compatible JSON.
    json.dumps(payload)


def test_reads_analysis_only_for_completed_sessions() -> None:
    completed = uuid4()
    skipped = uuid4()
    planned = uuid4()

    (
        service,
        _,
        _,
        _,
        analysis_reader,
        repository,
    ) = _service(
        sessions=[
            FakeSession(
                id=completed,
                status="completed",
                duration_minutes=45,
            ),
            FakeSession(
                id=skipped,
                status="skipped",
                duration_minutes=45,
            ),
            FakeSession(
                id=planned,
                status="planned",
                duration_minutes=45,
            ),
        ],
        plan=FakePlan(
            target_load=100.0
        ),
        analyses={
            completed: FakeAnalysis(
                training_session_id=completed,
                overall_status="compliant",
            )
        },
    )

    profile_id = uuid4()

    service.execute(
        athlete_profile_id=profile_id,
        week_start=WEEK_START,
        week_end=WEEK_END,
    )

    assert analysis_reader.calls == [
        (
            profile_id,
            completed,
        )
    ]

    assert len(repository.saved) == 1


def test_missing_analysis_remains_neutral() -> None:
    session_id = uuid4()

    (
        service,
        _,
        _,
        _,
        _,
        repository,
    ) = _service(
        sessions=[
            FakeSession(
                id=session_id,
                status="completed",
                duration_minutes=45,
            )
        ],
        plan=FakePlan(
            target_load=50.0
        ),
    )

    service.execute(
        athlete_profile_id=uuid4(),
        week_start=WEEK_START,
        week_end=WEEK_END,
    )

    facts = repository.saved[0][
        "facts"
    ]

    assert facts.analyzed_intensity_sessions == 0
    assert facts.compliant_intensity_sessions == 0


def test_invalid_week_is_rejected_before_repository_read() -> None:
    (
        service,
        _,
        _,
        _,
        _,
        repository,
    ) = _service()

    try:
        service.execute(
            athlete_profile_id=uuid4(),
            week_start=WEEK_END,
            week_end=WEEK_START,
        )
    except ValueError:
        pass
    else:
        raise AssertionError(
            "ValueError attendu."
        )

    assert repository.get_calls == []


def test_adaptation_payload_is_json_safe() -> None:
    from opencoach.coaching.weekly_adaptation import (
        build_weekly_adaptation_decision,
    )
    from opencoach.coaching.weekly_debrief import (
        WeeklyDebriefFacts,
        build_weekly_debrief,
    )

    facts = WeeklyDebriefFacts(
        week_start=WEEK_START,
        week_end=WEEK_END,
        planned_sessions=1,
        completed_sessions=1,
        skipped_sessions=0,
        supplementary_sessions=0,
        planned_duration_minutes=60,
        actual_duration_minutes=60,
        planned_load=50.0,
        actual_load=50.0,
        key_sessions_planned=0,
        key_sessions_completed=0,
        compliant_intensity_sessions=0,
        analyzed_intensity_sessions=0,
        history_confidence=1.0,
    )

    debrief = build_weekly_debrief(
        facts
    )

    decision = (
        build_weekly_adaptation_decision(
            debrief
        )
    )

    payload = (
        serialize_weekly_adaptation_decision(
            decision
        )
    )

    encoded = json.dumps(
        payload
    )

    assert isinstance(encoded, str)
    assert payload["direction"]
