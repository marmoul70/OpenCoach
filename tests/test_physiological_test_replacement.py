from opencoach.physiology.testing import (
    PhysiologicalTestType,
    PhysiologicalTestReplacementStimulus,
    get_test_replacement_stimulus,
)


def test_vma_test_replaced_by_aerobic_power() -> None:
    assert (
        get_test_replacement_stimulus(
            PhysiologicalTestType.HALF_COOPER
        )
        is PhysiologicalTestReplacementStimulus.AEROBIC_POWER
    )


def test_threshold_test_replaced_by_threshold() -> None:
    assert (
        get_test_replacement_stimulus(
            PhysiologicalTestType.THRESHOLD_30_MIN
        )
        is PhysiologicalTestReplacementStimulus.THRESHOLD
    )


def test_uphill_test_replaced_by_uphill_intensity() -> None:
    assert (
        get_test_replacement_stimulus(
            PhysiologicalTestType.UPHILL_6_MIN
        )
        is PhysiologicalTestReplacementStimulus.UPHILL_INTENSITY
    )


def test_durability_test_preserves_long_trail_quality() -> None:
    assert (
        get_test_replacement_stimulus(
            PhysiologicalTestType.TRAIL_DURABILITY
        )
        is PhysiologicalTestReplacementStimulus.LONG_TRAIL_QUALITY
    )
