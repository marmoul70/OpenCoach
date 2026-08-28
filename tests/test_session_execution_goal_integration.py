from datetime import date, datetime
from uuid import uuid4

from opencoach.models import (
    Activity,
    TrainingSession,
)
from opencoach.training.session_execution import (
    AssessmentStatus,
    analyze_session_execution,
)
from opencoach.training.session_execution.goal_analysis import (
    GoalComplianceStatus,
    GoalType,
)


def generic_session():
    return TrainingSession(
        id=uuid4(),
        date=date(2026, 8, 28),
        type="supplementary",
        sport_type="Run",
        title="Course",
        description="Course.",
        duration_minutes=60,
        intensity="easy",
        prescription={
            "version": 1,
        },
    )


def activity():
    return Activity(
        id=uuid4(),
        provider="intervals_icu",
        provider_activity_id="test",
        name="Course",
        sport_type="Run",
        start_at=datetime(
            2026,
            8,
            28,
            10,
            0,
        ),
        moving_time_seconds=3600,
        elapsed_time_seconds=3600,
        distance_m=10000.0,
    )


def test_analyzer_exposes_goal_analysis() -> None:
    result = analyze_session_execution(
        generic_session(),
        activity(),
    )

    assert result.goal_analysis is not None

    assert (
        result.goal_analysis.goal_type
        is GoalType.GENERIC
    )


def test_analyzer_keeps_technical_status() -> None:
    result = analyze_session_execution(
        generic_session(),
        activity(),
    )

    assert (
        result.technical_status
        is not None
    )


def test_overall_status_comes_from_goal_analysis() -> None:
    result = analyze_session_execution(
        generic_session(),
        activity(),
    )

    assert result.goal_analysis is not None

    mapping = {
        GoalComplianceStatus.OK:
            AssessmentStatus.COMPLIANT,
        GoalComplianceStatus.ATTENTION:
            AssessmentStatus.PARTIAL,
        GoalComplianceStatus.NON_COMPLIANT:
            AssessmentStatus.NON_COMPLIANT,
        GoalComplianceStatus.NOT_USED:
            AssessmentStatus.NOT_APPLICABLE,
    }

    assert (
        result.overall_status
        is mapping[
            result.goal_analysis.overall_status
        ]
    )


def test_rest_without_activity_is_coach_compliant() -> None:
    session = TrainingSession(
        id=uuid4(),
        date=date(2026, 8, 28),
        type="rest",
        sport_type="Run",
        title="Repos",
        description="Repos.",
        duration_minutes=0,
        intensity="rest",
        prescription={
            "version": 1,
        },
    )

    result = analyze_session_execution(
        session,
        None,
    )

    assert result.goal_analysis is not None

    assert (
        result.goal_analysis.overall_status
        is GoalComplianceStatus.OK
    )

    assert (
        result.overall_status
        is AssessmentStatus.COMPLIANT
    )
