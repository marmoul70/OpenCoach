from opencoach.planning.physiology.snapshot import (
    PhysiologicalCalibrationMetric,
    PhysiologicalCalibrationSnapshot,
)
from opencoach.planning.sessions.prescription import (
    INTENSITY_POLICIES,
    IntensityReference,
    build_intensity_prescription,
    validate_intensity_policy_catalog,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)


def metric(
    *,
    value,
    usable=True,
):
    return PhysiologicalCalibrationMetric(
        metric="vma",
        value=value,
        source=(
            "history"
            if value is not None
            else "missing"
        ),
        measurement=None,
        freshness=None,
        usable=usable,
        recalibration_recommended=False,
        reason="test",
    )


def snapshot(
    *,
    vma=15.0,
    max_hr=190.0,
    resting_hr=50.0,
    threshold_hr1=145.0,
    threshold_hr2=170.0,
):
    return PhysiologicalCalibrationSnapshot(
        vma=metric(
            value=vma
        ),
        max_heart_rate=metric(
            value=max_hr
        ),
        resting_heart_rate=metric(
            value=resting_hr
        ),
        threshold_heart_rate_1=metric(
            value=threshold_hr1
        ),
        threshold_heart_rate_2=metric(
            value=threshold_hr2
        ),
    )


def test_every_stimulus_has_intensity_policy() -> None:
    validate_intensity_policy_catalog()

    assert set(
        INTENSITY_POLICIES
    ) == set(
        TrainingStimulus
    )


def test_without_physiology_rpe_is_primary() -> None:
    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.AEROBIC_EASY
            ),
            physiology=None,
        )
    )

    assert (
        prescription.primary_target.reference
        is IntensityReference.RPE
    )

    assert (
        prescription.primary_target.minimum
        == 2
    )

    assert (
        prescription.primary_target.maximum
        == 3
    )


def test_easy_running_uses_heart_rate_reserve() -> None:
    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.AEROBIC_EASY
            ),
            physiology=snapshot(),
        )
    )

    target = prescription.target_for(
        IntensityReference.HEART_RATE_RESERVE
    )

    assert target is not None

    # FC réserve = 190 - 50 = 140.
    # 55 % : 50 + 140 * 0.55 = 127.
    # 70 % : 50 + 140 * 0.70 = 148.
    assert target.minimum == 127
    assert target.maximum == 148


def test_easy_running_also_exposes_vma_percent() -> None:
    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.AEROBIC_EASY
            ),
            physiology=snapshot(),
        )
    )

    target = prescription.target_for(
        IntensityReference.VMA_PERCENT
    )

    assert target is not None

    assert target.minimum == 60
    assert target.maximum == 70


def test_threshold_prefers_threshold_heart_rate() -> None:
    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.THRESHOLD
            ),
            physiology=snapshot(
                threshold_hr2=170.0
            ),
        )
    )

    assert (
        prescription.primary_target.reference
        is IntensityReference.HEART_RATE
    )

    assert (
        prescription.primary_target.maximum
        == 170
    )

    assert (
        prescription.primary_target.minimum
        == 162
    )


def test_threshold_exposes_vma_fallback() -> None:
    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.THRESHOLD
            ),
            physiology=snapshot(),
        )
    )

    target = prescription.target_for(
        IntensityReference.VMA_PERCENT
    )

    assert target is not None

    assert target.minimum == 80
    assert target.maximum == 90


def test_vo2max_uses_vma_as_primary_when_available() -> None:
    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.VO2MAX
            ),
            physiology=snapshot(),
        )
    )

    assert (
        prescription.primary_target.reference
        is IntensityReference.VMA_PERCENT
    )

    assert (
        prescription.primary_target.minimum
        == 95
    )

    assert (
        prescription.primary_target.maximum
        == 105
    )


def test_vo2max_falls_back_to_rpe_without_vma() -> None:
    physiology = snapshot()

    object.__setattr__(
        physiology,
        "vma",
        metric(
            value=None,
            usable=False,
        ),
    )

    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.VO2MAX
            ),
            physiology=physiology,
        )
    )

    assert (
        prescription.primary_target.reference
        is IntensityReference.RPE
    )

    assert (
        prescription.primary_target.minimum
        == 8
    )

    assert (
        prescription.primary_target.maximum
        == 9
    )


def test_recovery_keeps_rpe_as_secondary_reference() -> None:
    prescription = (
        build_intensity_prescription(
            stimulus=(
                TrainingStimulus.RECOVERY
            ),
            physiology=snapshot(),
        )
    )

    rpe = prescription.target_for(
        IntensityReference.RPE
    )

    assert rpe is not None
    assert rpe.minimum == 1
    assert rpe.maximum == 2


def test_uphill_strength_endurance_uses_rpe_without_hr_or_vma() -> None:
    """Le circuit force-endurance en côte est piloté par l'effort perçu."""

    prescription = build_intensity_prescription(
        stimulus=TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
        physiology=None,
    )

    assert (
        prescription.primary_target.reference
        is IntensityReference.RPE
    )

    assert prescription.primary_target.minimum == 7
    assert prescription.primary_target.maximum == 8

    assert not prescription.secondary_targets

    guidance = " ".join(
        prescription.guidance
    ).lower()

    assert "échec" in guidance
    assert "côte" in guidance
