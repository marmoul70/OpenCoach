import pytest

from opencoach.planning.session_intent import (
    SessionIntent,
    SessionIntentImportance,
    build_session_intent,
)
from opencoach.planning.training_stimulus import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)


def create_requirement(
    *,
    stimulus: TrainingStimulus,
    priority: StimulusPriority = (
        StimulusPriority.SUPPORT
    ),
    specificity: SpecificityLevel = (
        SpecificityLevel.MODERATE
    ),
    substitution: SubstitutionPolicy = (
        SubstitutionPolicy.ALLOWED
    ),
    preferred_modalities: tuple[
        TrainingModality,
        ...
    ] = (
        TrainingModality.RUNNING,
    ),
    required_modalities: tuple[
        TrainingModality,
        ...
    ] = (),
    duration_min_minutes: int | None = None,
    duration_max_minutes: int | None = None,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=stimulus,
        priority=priority,
        specificity=specificity,
        substitution=substitution,
        preferred_modalities=preferred_modalities,
        required_modalities=required_modalities,
        duration_min_minutes=duration_min_minutes,
        duration_max_minutes=duration_max_minutes,
    )


def test_single_requirement_builds_session_intent() -> None:
    requirement = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
    )

    result = build_session_intent(
        primary=requirement,
    )

    assert (
        result.primary_stimulus
        is TrainingStimulus.AEROBIC_EASY
    )

    assert result.secondary_stimuli == ()

    assert (
        result.importance
        is SessionIntentImportance.SUPPORT
    )


def test_session_can_cover_multiple_stimuli() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.LONG_ENDURANCE,
        priority=StimulusPriority.KEY,
    )

    uphill = create_requirement(
        stimulus=TrainingStimulus.UPHILL_STRENGTH,
        priority=StimulusPriority.IMPORTANT,
    )

    downhill = create_requirement(
        stimulus=(
            TrainingStimulus.DOWNHILL_SPECIFICITY
        ),
        priority=StimulusPriority.IMPORTANT,
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            uphill,
            downhill,
        ),
    )

    assert result.stimuli == (
        TrainingStimulus.LONG_ENDURANCE,
        TrainingStimulus.UPHILL_STRENGTH,
        TrainingStimulus.DOWNHILL_SPECIFICITY,
    )

    assert result.covers(
        TrainingStimulus.UPHILL_STRENGTH
    )

    assert result.covers(
        TrainingStimulus.DOWNHILL_SPECIFICITY
    )


def test_key_requirement_makes_intent_key() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.LONG_ENDURANCE,
        priority=StimulusPriority.KEY,
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.UPHILL_STRENGTH,
        priority=StimulusPriority.SUPPORT,
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert (
        result.importance
        is SessionIntentImportance.KEY
    )


def test_important_requirement_makes_intent_important() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_ENDURANCE,
        priority=StimulusPriority.SUPPORT,
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.UPHILL_STRENGTH,
        priority=StimulusPriority.IMPORTANT,
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert (
        result.importance
        is SessionIntentImportance.IMPORTANT
    )


def test_highest_specificity_is_preserved() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.LONG_ENDURANCE,
        specificity=SpecificityLevel.MODERATE,
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.RACE_SPECIFIC,
        specificity=SpecificityLevel.VERY_HIGH,
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert (
        result.specificity
        is SpecificityLevel.VERY_HIGH
    )


def test_most_restrictive_substitution_policy_wins() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_ENDURANCE,
        substitution=SubstitutionPolicy.ALLOWED,
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.RACE_SPECIFIC,
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert (
        result.substitution
        is SubstitutionPolicy.FORBIDDEN
    )

    assert result.required_modalities == (
        TrainingModality.TRAIL_RUNNING,
    )


def test_required_modalities_are_intersected() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.UPHILL_THRESHOLD,
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.TRAIL_RUNNING,
        ),
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.RACE_SPECIFIC,
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert result.required_modalities == (
        TrainingModality.TRAIL_RUNNING,
    )


def test_incompatible_required_modalities_are_rejected() -> None:
    running = create_requirement(
        stimulus=TrainingStimulus.THRESHOLD,
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.RUNNING,
        ),
    )

    strength = create_requirement(
        stimulus=TrainingStimulus.STRENGTH_CORE,
        substitution=SubstitutionPolicy.FORBIDDEN,
        required_modalities=(
            TrainingModality.STRENGTH,
        ),
    )

    with pytest.raises(
        ValueError,
        match="modalités incompatibles",
    ):
        build_session_intent(
            primary=running,
            secondary=(
                strength,
            ),
        )


def test_preferred_modalities_are_merged_without_duplicates() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        preferred_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.CYCLING,
        ),
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_ENDURANCE,
        preferred_modalities=(
            TrainingModality.CYCLING,
            TrainingModality.SWIMMING,
        ),
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert result.preferred_modalities == (
        TrainingModality.RUNNING,
        TrainingModality.CYCLING,
        TrainingModality.SWIMMING,
    )


def test_required_modality_filters_preferences() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_ENDURANCE,
        preferred_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.TRAIL_RUNNING,
        ),
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.RACE_SPECIFIC,
        substitution=SubstitutionPolicy.FORBIDDEN,
        preferred_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert result.preferred_modalities == (
        TrainingModality.TRAIL_RUNNING,
    )


def test_required_modality_becomes_preference_when_needed() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.RACE_SPECIFIC,
        substitution=SubstitutionPolicy.FORBIDDEN,
        preferred_modalities=(),
        required_modalities=(
            TrainingModality.TRAIL_RUNNING,
        ),
    )

    result = build_session_intent(
        primary=primary,
    )

    assert result.preferred_modalities == (
        TrainingModality.TRAIL_RUNNING,
    )


def test_duration_minimum_uses_strongest_lower_bound() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.LONG_ENDURANCE,
        duration_min_minutes=90,
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.RACE_SPECIFIC,
        duration_min_minutes=120,
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert result.duration_min_minutes == 120


def test_duration_maximum_uses_strongest_upper_bound() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_ENDURANCE,
        duration_max_minutes=120,
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.UPHILL_STRENGTH,
        duration_max_minutes=90,
    )

    result = build_session_intent(
        primary=primary,
        secondary=(
            secondary,
        ),
    )

    assert result.duration_max_minutes == 90


def test_incompatible_duration_constraints_are_rejected() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.LONG_ENDURANCE,
        duration_min_minutes=120,
    )

    secondary = create_requirement(
        stimulus=TrainingStimulus.UPHILL_STRENGTH,
        duration_max_minutes=90,
    )

    with pytest.raises(
        ValueError,
        match="durée",
    ):
        build_session_intent(
            primary=primary,
            secondary=(
                secondary,
            ),
        )


def test_duplicate_stimulus_is_rejected() -> None:
    primary = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
    )

    duplicate = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
    )

    with pytest.raises(
        ValueError,
        match="même stimulus",
    ):
        build_session_intent(
            primary=primary,
            secondary=(
                duplicate,
            ),
        )


def test_primary_cannot_be_secondary_in_direct_model() -> None:
    requirement = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
    )

    with pytest.raises(
        ValueError,
        match="principal",
    ):
        SessionIntent(
            primary_stimulus=(
                TrainingStimulus.AEROBIC_EASY
            ),
            secondary_stimuli=(
                TrainingStimulus.AEROBIC_EASY,
            ),
            importance=(
                SessionIntentImportance.SUPPORT
            ),
            specificity=SpecificityLevel.LOW,
            substitution=SubstitutionPolicy.ALLOWED,
            preferred_modalities=(
                TrainingModality.RUNNING,
            ),
            required_modalities=(),
            source_requirements=(
                requirement,
            ),
        )


def test_duplicate_secondary_stimulus_is_rejected() -> None:
    requirement = create_requirement(
        stimulus=TrainingStimulus.LONG_ENDURANCE,
    )

    with pytest.raises(
        ValueError,
        match="secondaire",
    ):
        SessionIntent(
            primary_stimulus=(
                TrainingStimulus.LONG_ENDURANCE
            ),
            secondary_stimuli=(
                TrainingStimulus.UPHILL_STRENGTH,
                TrainingStimulus.UPHILL_STRENGTH,
            ),
            importance=(
                SessionIntentImportance.KEY
            ),
            specificity=SpecificityLevel.HIGH,
            substitution=SubstitutionPolicy.ALLOWED,
            preferred_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            required_modalities=(),
            source_requirements=(
                requirement,
            ),
        )


def test_intent_without_durations_keeps_none() -> None:
    requirement = create_requirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
    )

    result = build_session_intent(
        primary=requirement,
    )

    assert result.duration_min_minutes is None
    assert result.duration_max_minutes is None
