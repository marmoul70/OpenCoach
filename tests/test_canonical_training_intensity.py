import pytest

from opencoach.planning.sessions.prescription.physiological import (
    canonical_intensity_for_stimulus,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)


@pytest.mark.parametrize(
    (
        "stimulus",
        "expected",
    ),
    (
        (
            TrainingStimulus.RECOVERY,
            "very_easy",
        ),
        (
            TrainingStimulus.AEROBIC_EASY,
            "easy",
        ),
        (
            TrainingStimulus.AEROBIC_ENDURANCE,
            "easy",
        ),
        (
            TrainingStimulus.LONG_ENDURANCE,
            "easy",
        ),
        (
            TrainingStimulus.DOWNHILL_SPECIFICITY,
            "moderate",
        ),
        (
            TrainingStimulus.THRESHOLD,
            "hard",
        ),
        (
            TrainingStimulus.UPHILL_THRESHOLD,
            "hard",
        ),
        (
            TrainingStimulus.RACE_SPECIFIC,
            "hard",
        ),
        (
            TrainingStimulus.VO2MAX,
            "very_hard",
        ),
        (
            TrainingStimulus.SPEED_DEVELOPMENT,
            "very_hard",
        ),
    ),
)
def test_stimulus_maps_to_canonical_intensity(
    stimulus: TrainingStimulus,
    expected: str,
) -> None:
    assert (
        canonical_intensity_for_stimulus(
            stimulus
        )
        == expected
    )
