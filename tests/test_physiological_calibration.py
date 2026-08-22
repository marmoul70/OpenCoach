from opencoach.models import AthleteProfile
from opencoach.planning import (
    assess_physiological_calibration,
)


def create_athlete() -> AthleteProfile:
    return AthleteProfile()


def test_complete_physiology_is_ready() -> None:
    athlete = create_athlete()

    athlete.physiology.max_heart_rate = 190
    athlete.physiology.resting_heart_rate = 50
    athlete.physiology.vma = 16.0
    athlete.physiology.threshold_heart_rate_1 = 145
    athlete.physiology.threshold_heart_rate_2 = 170

    assessment = assess_physiological_calibration(
        athlete
    )

    assert (
        assessment.basic_intensity_prescription_ready
        is True
    )

    assert (
        assessment.threshold_prescription_ready
        is True
    )

    assert (
        assessment.recommended_assessments
        == ()
    )

    assert assessment.has_missing_metrics is False


def test_empty_physiology_requires_calibration() -> None:
    assessment = assess_physiological_calibration(
        create_athlete()
    )

    assert (
        assessment.basic_intensity_prescription_ready
        is False
    )

    assert (
        assessment.threshold_prescription_ready
        is False
    )

    assert assessment.has_missing_metrics is True

    assert "vma_calibration" in (
        assessment.recommended_assessments
    )

    assert "max_heart_rate_calibration" in (
        assessment.recommended_assessments
    )

    assert "threshold_calibration" in (
        assessment.recommended_assessments
    )


def test_vma_allows_basic_intensity_prescription() -> None:
    athlete = create_athlete()

    athlete.physiology.vma = 15.0

    assessment = assess_physiological_calibration(
        athlete
    )

    assert (
        assessment.basic_intensity_prescription_ready
        is True
    )

    assert (
        assessment.threshold_prescription_ready
        is False
    )

    assert "vma_calibration" not in (
        assessment.recommended_assessments
    )

    assert "threshold_calibration" in (
        assessment.recommended_assessments
    )


def test_max_heart_rate_allows_basic_intensity_prescription() -> None:
    athlete = create_athlete()

    athlete.physiology.max_heart_rate = 185

    assessment = assess_physiological_calibration(
        athlete
    )

    assert (
        assessment.basic_intensity_prescription_ready
        is True
    )


def test_thresholds_require_both_sv1_and_sv2() -> None:
    athlete = create_athlete()

    athlete.physiology.threshold_heart_rate_1 = 145

    assessment = assess_physiological_calibration(
        athlete
    )

    assert (
        assessment.threshold_prescription_ready
        is False
    )

    assert "threshold_calibration" in (
        assessment.recommended_assessments
    )


def test_resting_heart_rate_does_not_require_field_test() -> None:
    assessment = assess_physiological_calibration(
        create_athlete()
    )

    assert (
        assessment.resting_heart_rate.status
        == "missing"
    )

    assert (
        assessment.resting_heart_rate.calibration_recommended
        is False
    )
