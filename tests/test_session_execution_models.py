from dataclasses import FrozenInstanceError
from uuid import uuid4

import pytest

from opencoach.training.session_execution import (
    AssessmentStatus,
    NumericMetricAssessment,
    NumericTarget,
    SessionExecutionAssessment,
    SessionExecutionIntensityAssessment,
    SessionExecutionLoadAssessment,
    SessionExecutionStructureAssessment,
    SessionExecutionVolumeAssessment,
)


def test_assessment_status_values_are_stable() -> None:
    assert AssessmentStatus.COMPLIANT == "compliant"
    assert AssessmentStatus.PARTIAL == "partial"

    assert (
        AssessmentStatus.NON_COMPLIANT
        == "non_compliant"
    )

    assert (
        AssessmentStatus.NOT_APPLICABLE
        == "not_applicable"
    )

    assert (
        AssessmentStatus.INSUFFICIENT_DATA
        == "insufficient_data"
    )


def test_numeric_target_supports_exact_value() -> None:
    target = NumericTarget.exact(
        60.0,
        "min",
    )

    assert target.minimum == 60.0
    assert target.maximum == 60.0
    assert target.unit == "min"
    assert target.is_exact is True


def test_numeric_target_supports_range() -> None:
    target = NumericTarget(
        minimum=130.0,
        maximum=150.0,
        unit="bpm",
    )

    assert target.minimum == 130.0
    assert target.maximum == 150.0
    assert target.is_exact is False


def test_numeric_target_rejects_inverted_range() -> None:
    with pytest.raises(
        ValueError,
        match="borne maximale",
    ):
        NumericTarget(
            minimum=150.0,
            maximum=130.0,
            unit="bpm",
        )


def test_numeric_target_rejects_empty_unit() -> None:
    with pytest.raises(
        ValueError,
        match="unité",
    ):
        NumericTarget(
            minimum=60.0,
            maximum=60.0,
            unit=" ",
        )


def test_numeric_metric_can_represent_duration() -> None:
    metric = NumericMetricAssessment(
        key="duration",
        label="Durée",
        status=AssessmentStatus.COMPLIANT,
        target=NumericTarget.exact(
            60.0,
            "min",
        ),
        actual_value=63.0,
        delta=3.0,
        delta_percent=5.0,
    )

    assert metric.target is not None
    assert metric.target.minimum == 60.0
    assert metric.actual_value == 63.0
    assert metric.delta == 3.0
    assert metric.delta_percent == 5.0


def test_numeric_metric_can_represent_hr_range() -> None:
    metric = NumericMetricAssessment(
        key="average_heart_rate",
        label="Fréquence cardiaque moyenne",
        status=AssessmentStatus.COMPLIANT,
        target=NumericTarget(
            minimum=130.0,
            maximum=150.0,
            unit="bpm",
        ),
        actual_value=143.0,
    )

    assert metric.target is not None
    assert metric.target.is_exact is False
    assert metric.actual_value == 143.0


def test_insufficient_data_metric_has_no_actual_value() -> None:
    metric = NumericMetricAssessment(
        key="time_in_heart_rate_target",
        label="Temps dans la cible cardiaque",
        status=AssessmentStatus.INSUFFICIENT_DATA,
        target=NumericTarget(
            minimum=80.0,
            maximum=100.0,
            unit="%",
        ),
        details="Streams cardiaques indisponibles.",
    )

    assert metric.actual_value is None

    assert (
        metric.status
        is AssessmentStatus.INSUFFICIENT_DATA
    )


def test_insufficient_data_rejects_actual_value() -> None:
    with pytest.raises(
        ValueError,
        match="données insuffisantes",
    ):
        NumericMetricAssessment(
            key="time_in_zone",
            label="Temps dans la zone",
            status=(
                AssessmentStatus.INSUFFICIENT_DATA
            ),
            actual_value=90.0,
        )


def test_session_execution_assessment_groups_sections() -> None:
    duration = NumericMetricAssessment(
        key="duration",
        label="Durée",
        status=AssessmentStatus.COMPLIANT,
        target=NumericTarget.exact(
            60.0,
            "min",
        ),
        actual_value=61.0,
    )

    assessment = SessionExecutionAssessment(
        session_id=uuid4(),
        activity_id=uuid4(),
        overall_status=(
            AssessmentStatus.COMPLIANT
        ),
        volume=(
            SessionExecutionVolumeAssessment(
                duration=duration,
            )
        ),
        intensity=(
            SessionExecutionIntensityAssessment()
        ),
        load=(
            SessionExecutionLoadAssessment()
        ),
        structure=(
            SessionExecutionStructureAssessment()
        ),
        observations=(
            "Durée conforme à la prescription.",
        ),
    )

    assert assessment.volume.duration == duration
    assert assessment.activity_id is not None

    assert assessment.observations == (
        "Durée conforme à la prescription.",
    )


def test_assessment_allows_missing_activity() -> None:
    assessment = SessionExecutionAssessment(
        session_id=uuid4(),
        activity_id=None,
        overall_status=(
            AssessmentStatus.NON_COMPLIANT
        ),
        volume=(
            SessionExecutionVolumeAssessment()
        ),
        intensity=(
            SessionExecutionIntensityAssessment()
        ),
        load=(
            SessionExecutionLoadAssessment()
        ),
        structure=(
            SessionExecutionStructureAssessment()
        ),
        observations=(
            "Aucune activité associée à la séance.",
        ),
    )

    assert assessment.activity_id is None


def test_assessment_models_are_immutable() -> None:
    metric = NumericMetricAssessment(
        key="distance",
        label="Distance",
        status=AssessmentStatus.COMPLIANT,
        target=NumericTarget.exact(
            10.0,
            "km",
        ),
        actual_value=10.2,
    )

    with pytest.raises(FrozenInstanceError):
        metric.actual_value = 11.0
