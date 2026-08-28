from datetime import date

from opencoach.models import TrainingSession
from opencoach.training.session_execution import (
    AssessmentStatus,
    NumericMetricAssessment,
    NumericTarget,
    SessionExecutionIntensityAssessment,
    SessionExecutionLoadAssessment,
    SessionExecutionStructureAssessment,
    SessionExecutionVolumeAssessment,
)
from opencoach.training.session_execution.goal_analysis import (
    GoalComplianceStatus,
    MetricImportance,
    evaluate_session_goal,
)


def session(
    *,
    structured=False,
):
    prescription = {
        "version": 1,
    }

    if structured:
        prescription = {
            "work_structure": {
                "type": "repeats",
                "intervals": [
                    {
                        "repetitions": 7,
                        "work_distance_meters": 300,
                    },
                ],
            },
        }

    else:
        prescription["intensity"] = {
            "targets": [
                {
                    "reference": "heart_rate",
                    "minimum": 130,
                    "maximum": 150,
                },
            ],
        }

    return TrainingSession(
        id=None,
        date=date(2026, 8, 28),
        type="aerobic_easy",
        sport_type="Run",
        title="Test",
        description="Test",
        duration_minutes=60,
        intensity="easy",
        prescription=prescription,
    )


def metric(
    key,
    status,
    *,
    actual=None,
    target=None,
    delta=None,
):
    return NumericMetricAssessment(
        key=key,
        label=key,
        status=status,
        actual_value=actual,
        target=target,
        delta=delta,
    )


def empty_load():
    return SessionExecutionLoadAssessment()


def empty_structure():
    return SessionExecutionStructureAssessment()


def empty_volume():
    return SessionExecutionVolumeAssessment()


def empty_intensity():
    return SessionExecutionIntensityAssessment()


def test_easy_run_with_bad_zone_is_non_compliant() -> None:
    result = evaluate_session_goal(
        session=session(),
        volume=SessionExecutionVolumeAssessment(
            duration=metric(
                "duration",
                AssessmentStatus.COMPLIANT,
            ),
        ),
        intensity=SessionExecutionIntensityAssessment(
            time_in_heart_rate_target=metric(
                "time_in_heart_rate_target",
                AssessmentStatus.NON_COMPLIANT,
                actual=52.0,
            ),
        ),
        load=empty_load(),
        structure=empty_structure(),
    )

    assert (
        result.overall_status
        is GoalComplianceStatus.NON_COMPLIANT
    )

    # La durée verte ne compense pas une mauvaise Z2.
    assert any(
        "Seulement 52 %"
        in point
        for point in result.attention_points
    )


def test_easy_run_with_good_zone_and_duration_is_ok() -> None:
    result = evaluate_session_goal(
        session=session(),
        volume=SessionExecutionVolumeAssessment(
            duration=metric(
                "duration",
                AssessmentStatus.COMPLIANT,
            ),
        ),
        intensity=SessionExecutionIntensityAssessment(
            time_in_heart_rate_target=metric(
                "time_in_heart_rate_target",
                AssessmentStatus.COMPLIANT,
                actual=91.0,
            ),
        ),
        load=empty_load(),
        structure=empty_structure(),
    )

    assert (
        result.overall_status
        is GoalComplianceStatus.OK
    )


def test_distance_is_informational_for_endurance() -> None:
    result = evaluate_session_goal(
        session=session(),
        volume=SessionExecutionVolumeAssessment(
            duration=metric(
                "duration",
                AssessmentStatus.COMPLIANT,
            ),
            distance=metric(
                "distance",
                AssessmentStatus.NON_COMPLIANT,
            ),
        ),
        intensity=SessionExecutionIntensityAssessment(
            time_in_heart_rate_target=metric(
                "time_in_heart_rate_target",
                AssessmentStatus.COMPLIANT,
                actual=90.0,
            ),
        ),
        load=empty_load(),
        structure=empty_structure(),
    )

    assert (
        result.overall_status
        is GoalComplianceStatus.OK
    )

    distance = next(
        metric
        for metric in result.metrics
        if metric.key == "distance"
    )

    assert (
        distance.importance
        is MetricImportance.INFORMATIONAL
    )


def test_intervals_too_fast_are_non_compliant() -> None:
    result = evaluate_session_goal(
        session=session(
            structured=True,
        ),
        volume=empty_volume(),
        intensity=empty_intensity(),
        load=empty_load(),
        structure=SessionExecutionStructureAssessment(
            repetition_count=metric(
                "repetition_count",
                AssessmentStatus.COMPLIANT,
                actual=7.0,
                target=NumericTarget.exact(
                    7.0,
                    "rep",
                ),
            ),
            work_duration=metric(
                "work_duration",
                AssessmentStatus.NON_COMPLIANT,
                actual=60.0,
                target=NumericTarget(
                    minimum=70.0,
                    maximum=75.0,
                    unit="s",
                ),
                delta=-10.0,
            ),
            recovery_duration=metric(
                "recovery_duration",
                AssessmentStatus.COMPLIANT,
                actual=60.0,
            ),
        ),
    )

    assert (
        result.overall_status
        is GoalComplianceStatus.NON_COMPLIANT
    )

    assert any(
        "trop rapidement"
        in point
        for point in result.attention_points
    )


def test_secondary_failure_only_triggers_attention() -> None:
    result = evaluate_session_goal(
        session=session(
            structured=True,
        ),
        volume=empty_volume(),
        intensity=empty_intensity(),
        load=empty_load(),
        structure=SessionExecutionStructureAssessment(
            repetition_count=metric(
                "repetition_count",
                AssessmentStatus.COMPLIANT,
            ),
            work_duration=metric(
                "work_duration",
                AssessmentStatus.COMPLIANT,
            ),
            recovery_duration=metric(
                "recovery_duration",
                AssessmentStatus.NON_COMPLIANT,
                delta=20.0,
            ),
        ),
    )

    assert (
        result.overall_status
        is GoalComplianceStatus.ATTENTION
    )


def test_unused_metric_is_grey_and_does_not_affect_result() -> None:
    result = evaluate_session_goal(
        session=session(),
        volume=SessionExecutionVolumeAssessment(
            duration=metric(
                "duration",
                AssessmentStatus.COMPLIANT,
            ),
        ),
        intensity=SessionExecutionIntensityAssessment(
            time_in_heart_rate_target=metric(
                "time_in_heart_rate_target",
                AssessmentStatus.COMPLIANT,
                actual=90.0,
            ),
        ),
        load=empty_load(),
        structure=empty_structure(),
    )

    pace = next(
        metric
        for metric in result.metrics
        if metric.key == "time_in_pace_target"
    )

    assert (
        pace.status
        is GoalComplianceStatus.NOT_USED
    )
