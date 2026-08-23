import pytest

from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)


def test_easy_aerobic_stimulus_can_be_substitutable() -> None:
    requirement = TrainingStimulusRequirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
        specificity=SpecificityLevel.LOW,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.CYCLING,
        ),
        duration_min_minutes=40,
        duration_max_minutes=90,
    )

    assert requirement.substitution is SubstitutionPolicy.ALLOWED
    assert TrainingModality.RUNNING in requirement.preferred_modalities
    assert TrainingModality.CYCLING in requirement.preferred_modalities


def test_specific_uphill_stimulus_can_forbid_substitution() -> None:
    requirement = TrainingStimulusRequirement(
        stimulus=TrainingStimulus.UPHILL_THRESHOLD,
        priority=StimulusPriority.KEY,
        specificity=SpecificityLevel.VERY_HIGH,
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
    )

    assert requirement.substitution is SubstitutionPolicy.FORBIDDEN
    assert requirement.required_modalities == (
        TrainingModality.TRAIL_RUNNING,
    )


def test_forbidden_substitution_requires_modality() -> None:
    with pytest.raises(
        ValueError,
        match="modalité obligatoire",
    ):
        TrainingStimulusRequirement(
            stimulus=TrainingStimulus.RACE_SPECIFIC,
            priority=StimulusPriority.KEY,
            specificity=SpecificityLevel.VERY_HIGH,
            substitution=SubstitutionPolicy.FORBIDDEN,
        )


def test_duration_range_must_be_valid() -> None:
    with pytest.raises(
        ValueError,
        match="durée minimale",
    ):
        TrainingStimulusRequirement(
            stimulus=TrainingStimulus.AEROBIC_ENDURANCE,
            priority=StimulusPriority.IMPORTANT,
            specificity=SpecificityLevel.MODERATE,
            substitution=SubstitutionPolicy.ALLOWED,
            duration_min_minutes=90,
            duration_max_minutes=60,
        )


@pytest.mark.parametrize(
    "duration",
    [
        0,
        -1,
    ],
)
def test_minimum_duration_must_be_positive(
    duration: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        TrainingStimulusRequirement(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            priority=StimulusPriority.SUPPORT,
            specificity=SpecificityLevel.LOW,
            substitution=SubstitutionPolicy.ALLOWED,
            duration_min_minutes=duration,
        )


@pytest.mark.parametrize(
    "duration",
    [
        0,
        -1,
    ],
)
def test_maximum_duration_must_be_positive(
    duration: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        TrainingStimulusRequirement(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            priority=StimulusPriority.SUPPORT,
            specificity=SpecificityLevel.LOW,
            substitution=SubstitutionPolicy.ALLOWED,
            duration_max_minutes=duration,
        )
