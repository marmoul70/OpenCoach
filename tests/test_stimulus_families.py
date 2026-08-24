"""Tests des familles physiologiques de stimuli."""

from opencoach.planning.stimulus.families import (
    StimulusFamily,
    same_stimulus_family,
    stimulus_family,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)


def test_threshold_variants_share_same_family() -> None:
    assert (
        stimulus_family(
            TrainingStimulus.THRESHOLD
        )
        is StimulusFamily.THRESHOLD
    )

    assert (
        stimulus_family(
            TrainingStimulus.UPHILL_THRESHOLD
        )
        is StimulusFamily.THRESHOLD
    )

    assert same_stimulus_family(
        TrainingStimulus.THRESHOLD,
        TrainingStimulus.UPHILL_THRESHOLD,
    )


def test_long_endurance_is_aerobic_but_not_threshold() -> None:
    assert (
        stimulus_family(
            TrainingStimulus.LONG_ENDURANCE
        )
        is StimulusFamily.AEROBIC
    )

    assert not same_stimulus_family(
        TrainingStimulus.LONG_ENDURANCE,
        TrainingStimulus.THRESHOLD,
    )


def test_uphill_strength_endurance_is_strength_family() -> None:
    """L'endurance de force en côte appartient à la famille force."""

    assert (
        TrainingStimulus.UPHILL_STRENGTH_ENDURANCE.value
        == "uphill_strength_endurance"
    )

    assert (
        stimulus_family(
            TrainingStimulus.UPHILL_STRENGTH_ENDURANCE
        )
        is StimulusFamily.STRENGTH
    )

    assert same_stimulus_family(
        TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
        TrainingStimulus.UPHILL_STRENGTH,
    )
