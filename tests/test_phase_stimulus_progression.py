import pytest

from opencoach.planning.stimulus.phase_prescription import (
    build_phase_stimulus_prescription,
)
from opencoach.planning.stimulus.phase_progression import (
    apply_phase_stimulus_progression,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


@pytest.mark.parametrize(
    (
        "phase_week_index",
        "expected_stimulus",
    ),
    (
        (
            1,
            TrainingStimulus.SPEED_DEVELOPMENT,
        ),
        (
            2,
            TrainingStimulus.SPEED_DEVELOPMENT,
        ),
        (
            3,
            TrainingStimulus.VO2MAX,
        ),
        (
            4,
            TrainingStimulus.SPEED_DEVELOPMENT,
        ),
        (
            5,
            TrainingStimulus.SPEED_DEVELOPMENT,
        ),
        (
            6,
            TrainingStimulus.VO2MAX,
        ),
    ),
)
def test_base_quality_progression(
    phase_week_index: int,
    expected_stimulus: TrainingStimulus,
) -> None:
    base = build_phase_stimulus_prescription(
        TrainingPhase.BASE
    )

    prescription = apply_phase_stimulus_progression(
        prescription=base,
        phase_week_index=phase_week_index,
    )

    assert (
        prescription.requirement_for(
            expected_stimulus
        )
        is not None
    )

    quality_stimuli = {
        TrainingStimulus.SPEED_DEVELOPMENT,
        TrainingStimulus.VO2MAX,
    }

    present_quality = {
        stimulus
        for stimulus in quality_stimuli
        if (
            prescription.requirement_for(
                stimulus
            )
            is not None
        )
    }

    assert present_quality == {
        expected_stimulus
    }


def test_non_base_phase_is_not_modified() -> None:
    original = build_phase_stimulus_prescription(
        TrainingPhase.BUILD
    )

    progressed = apply_phase_stimulus_progression(
        prescription=original,
        phase_week_index=2,
    )

    assert progressed == original


def test_phase_progression_rejects_invalid_week_index() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.BASE
    )

    with pytest.raises(
        ValueError,
        match="supérieur ou égal à 1",
    ):
        apply_phase_stimulus_progression(
            prescription=prescription,
            phase_week_index=0,
        )
