from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

import pytest

from opencoach.coaching.weekly_debrief_facts import (
    build_weekly_debrief_facts_from_history,
)


@dataclass(frozen=True)
class FakeSession:
    status: str
    duration_minutes: int
    activity_id: UUID | None = None


@dataclass(frozen=True)
class FakeActivity:
    id: UUID
    moving_time_seconds: int | None = None
    elapsed_time_seconds: int | None = None
    training_load: float | None = None


class FakeSessionReader:
    def __init__(
        self,
        sessions: list[FakeSession],
    ) -> None:
        self.sessions = sessions
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
    def __init__(
        self,
        activities: list[FakeActivity],
    ) -> None:
        self.activities = activities
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


def test_builds_observable_weekly_facts() -> None:
    profile_id = uuid4()
    linked_1 = uuid4()
    linked_2 = uuid4()
    supplementary = uuid4()

    sessions = [
        FakeSession(
            status="completed",
            duration_minutes=60,
            activity_id=linked_1,
        ),
        FakeSession(
            status="completed",
            duration_minutes=45,
            activity_id=linked_2,
        ),
        FakeSession(
            status="skipped",
            duration_minutes=30,
        ),
        FakeSession(
            status="planned",
            duration_minutes=90,
        ),
    ]

    activities = [
        FakeActivity(
            id=linked_1,
            moving_time_seconds=3600,
            elapsed_time_seconds=3700,
            training_load=80.0,
        ),
        FakeActivity(
            id=linked_2,
            moving_time_seconds=None,
            elapsed_time_seconds=2700,
            training_load=45.5,
        ),
        FakeActivity(
            id=supplementary,
            moving_time_seconds=1800,
            training_load=20.0,
        ),
    ]

    session_reader = FakeSessionReader(
        sessions
    )
    activity_reader = FakeActivityReader(
        activities
    )

    facts = (
        build_weekly_debrief_facts_from_history(
            athlete_profile_id=profile_id,
            week_start=date(2026, 8, 31),
            week_end=date(2026, 9, 6),
            session_reader=session_reader,
            activity_reader=activity_reader,
        )
    )

    assert facts.planned_sessions == 4
    assert facts.completed_sessions == 2
    assert facts.skipped_sessions == 1
    assert facts.supplementary_sessions == 1

    assert facts.planned_duration_minutes == 225
    assert facts.actual_duration_minutes == 135.0

    assert facts.planned_load == 0.0
    assert facts.actual_load == 145.5

    assert facts.key_sessions_planned == 0
    assert facts.key_sessions_completed == 0
    assert facts.compliant_intensity_sessions == 0
    assert facts.analyzed_intensity_sessions == 0

    assert facts.history_confidence == 1.0

    assert session_reader.calls == [
        (
            profile_id,
            date(2026, 8, 31),
            date(2026, 9, 6),
        )
    ]

    assert activity_reader.calls == [
        (
            profile_id,
            date(2026, 8, 31),
            date(2026, 9, 6),
        )
    ]


def test_unlinked_activity_is_supplementary() -> None:
    profile_id = uuid4()
    activity_id = uuid4()

    facts = (
        build_weekly_debrief_facts_from_history(
            athlete_profile_id=profile_id,
            week_start=date(2026, 8, 31),
            week_end=date(2026, 9, 6),
            session_reader=FakeSessionReader(
                []
            ),
            activity_reader=FakeActivityReader(
                [
                    FakeActivity(
                        id=activity_id,
                        moving_time_seconds=1800,
                        training_load=10.0,
                    )
                ]
            ),
        )
    )

    assert facts.planned_sessions == 0
    assert facts.supplementary_sessions == 1
    assert facts.actual_duration_minutes == 30.0
    assert facts.actual_load == 10.0
    assert facts.history_confidence == 1.0


def test_linked_activity_is_not_supplementary() -> None:
    profile_id = uuid4()
    activity_id = uuid4()

    facts = (
        build_weekly_debrief_facts_from_history(
            athlete_profile_id=profile_id,
            week_start=date(2026, 8, 31),
            week_end=date(2026, 9, 6),
            session_reader=FakeSessionReader(
                [
                    FakeSession(
                        status="completed",
                        duration_minutes=30,
                        activity_id=activity_id,
                    )
                ]
            ),
            activity_reader=FakeActivityReader(
                [
                    FakeActivity(
                        id=activity_id,
                        moving_time_seconds=1800,
                    )
                ]
            ),
        )
    )

    assert facts.supplementary_sessions == 0


def test_elapsed_time_is_used_when_moving_time_missing() -> None:
    facts = (
        build_weekly_debrief_facts_from_history(
            athlete_profile_id=uuid4(),
            week_start=date(2026, 8, 31),
            week_end=date(2026, 9, 6),
            session_reader=FakeSessionReader(
                []
            ),
            activity_reader=FakeActivityReader(
                [
                    FakeActivity(
                        id=uuid4(),
                        elapsed_time_seconds=900,
                    )
                ]
            ),
        )
    )

    assert facts.actual_duration_minutes == 15.0


def test_empty_week_has_zero_confidence() -> None:
    facts = (
        build_weekly_debrief_facts_from_history(
            athlete_profile_id=uuid4(),
            week_start=date(2026, 8, 31),
            week_end=date(2026, 9, 6),
            session_reader=FakeSessionReader(
                []
            ),
            activity_reader=FakeActivityReader(
                []
            ),
        )
    )

    assert facts.planned_sessions == 0
    assert facts.completed_sessions == 0
    assert facts.supplementary_sessions == 0
    assert facts.history_confidence == 0.0


def test_invalid_week_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="week_end",
    ):
        build_weekly_debrief_facts_from_history(
            athlete_profile_id=uuid4(),
            week_start=date(2026, 9, 6),
            week_end=date(2026, 8, 31),
            session_reader=FakeSessionReader(
                []
            ),
            activity_reader=FakeActivityReader(
                []
            ),
        )


def test_negative_activity_values_are_not_counted() -> None:
    facts = (
        build_weekly_debrief_facts_from_history(
            athlete_profile_id=uuid4(),
            week_start=date(2026, 8, 31),
            week_end=date(2026, 9, 6),
            session_reader=FakeSessionReader(
                []
            ),
            activity_reader=FakeActivityReader(
                [
                    FakeActivity(
                        id=uuid4(),
                        moving_time_seconds=-60,
                        training_load=-5.0,
                    )
                ]
            ),
        )
    )

    assert facts.actual_duration_minutes == 0.0
    assert facts.actual_load == 0.0


@dataclass(frozen=True)
class T652Session:
    id: UUID
    status: str
    duration_minutes: int
    activity_id: UUID | None = None


@dataclass(frozen=True)
class FakeWeeklyPlan:
    target_load: float | None


@dataclass(frozen=True)
class FakeExecutionAnalysis:
    training_session_id: UUID
    overall_status: str
    technical_status: str | None = None


def test_uses_weekly_plan_target_load() -> None:
    activity_id = uuid4()

    facts = build_weekly_debrief_facts_from_history(
        athlete_profile_id=uuid4(),
        week_start=date(2026, 8, 31),
        week_end=date(2026, 9, 6),
        session_reader=FakeSessionReader([]),
        activity_reader=FakeActivityReader(
            [
                FakeActivity(
                    id=activity_id,
                    moving_time_seconds=60,
                )
            ]
        ),
        weekly_plan=FakeWeeklyPlan(
            target_load=321.5
        ),
    )

    assert facts.planned_load == 321.5
    assert facts.history_confidence == 1.0


def test_counts_key_sessions_from_explicit_snapshot() -> None:
    key_completed = uuid4()
    key_skipped = uuid4()
    support = uuid4()

    facts = build_weekly_debrief_facts_from_history(
        athlete_profile_id=uuid4(),
        week_start=date(2026, 8, 31),
        week_end=date(2026, 9, 6),
        session_reader=FakeSessionReader(
            [
                T652Session(
                    id=key_completed,
                    status="completed",
                    duration_minutes=60,
                ),
                T652Session(
                    id=key_skipped,
                    status="skipped",
                    duration_minutes=75,
                ),
                T652Session(
                    id=support,
                    status="completed",
                    duration_minutes=45,
                ),
            ]
        ),
        activity_reader=FakeActivityReader([]),
        key_session_ids=frozenset(
            {
                key_completed,
                key_skipped,
            }
        ),
    )

    assert facts.key_sessions_planned == 2
    assert facts.key_sessions_completed == 1


def test_counts_execution_compliance() -> None:
    compliant = uuid4()
    partial = uuid4()
    non_compliant = uuid4()

    sessions = [
        T652Session(
            id=compliant,
            status="completed",
            duration_minutes=45,
        ),
        T652Session(
            id=partial,
            status="completed",
            duration_minutes=45,
        ),
        T652Session(
            id=non_compliant,
            status="completed",
            duration_minutes=45,
        ),
    ]

    facts = build_weekly_debrief_facts_from_history(
        athlete_profile_id=uuid4(),
        week_start=date(2026, 8, 31),
        week_end=date(2026, 9, 6),
        session_reader=FakeSessionReader(
            sessions
        ),
        activity_reader=FakeActivityReader([]),
        execution_analyses={
            compliant: FakeExecutionAnalysis(
                training_session_id=compliant,
                overall_status="compliant",
            ),
            partial: FakeExecutionAnalysis(
                training_session_id=partial,
                overall_status="partial",
            ),
            non_compliant: FakeExecutionAnalysis(
                training_session_id=non_compliant,
                overall_status="non_compliant",
            ),
        },
    )

    assert facts.analyzed_intensity_sessions == 3
    assert facts.compliant_intensity_sessions == 1


def test_non_evaluable_execution_analysis_is_neutral() -> None:
    compliant = uuid4()
    not_applicable = uuid4()
    insufficient = uuid4()

    sessions = [
        T652Session(
            id=compliant,
            status="completed",
            duration_minutes=45,
        ),
        T652Session(
            id=not_applicable,
            status="completed",
            duration_minutes=45,
        ),
        T652Session(
            id=insufficient,
            status="completed",
            duration_minutes=45,
        ),
    ]

    facts = build_weekly_debrief_facts_from_history(
        athlete_profile_id=uuid4(),
        week_start=date(2026, 8, 31),
        week_end=date(2026, 9, 6),
        session_reader=FakeSessionReader(
            sessions
        ),
        activity_reader=FakeActivityReader([]),
        execution_analyses={
            compliant: FakeExecutionAnalysis(
                training_session_id=compliant,
                overall_status="compliant",
            ),
            not_applicable: FakeExecutionAnalysis(
                training_session_id=not_applicable,
                overall_status="not_applicable",
            ),
            insufficient: FakeExecutionAnalysis(
                training_session_id=insufficient,
                overall_status="insufficient_data",
            ),
        },
    )

    assert facts.analyzed_intensity_sessions == 1
    assert facts.compliant_intensity_sessions == 1


def test_analysis_for_non_completed_session_is_ignored() -> None:
    completed = uuid4()
    skipped = uuid4()

    facts = build_weekly_debrief_facts_from_history(
        athlete_profile_id=uuid4(),
        week_start=date(2026, 8, 31),
        week_end=date(2026, 9, 6),
        session_reader=FakeSessionReader(
            [
                T652Session(
                    id=completed,
                    status="completed",
                    duration_minutes=45,
                ),
                T652Session(
                    id=skipped,
                    status="skipped",
                    duration_minutes=45,
                ),
            ]
        ),
        activity_reader=FakeActivityReader([]),
        execution_analyses={
            completed: FakeExecutionAnalysis(
                training_session_id=completed,
                overall_status="compliant",
            ),
            skipped: FakeExecutionAnalysis(
                training_session_id=skipped,
                overall_status="non_compliant",
            ),
        },
    )

    assert facts.analyzed_intensity_sessions == 1
    assert facts.compliant_intensity_sessions == 1

