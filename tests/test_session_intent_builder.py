import pytest

from opencoach.planning.contextual_stimulus_prescription import (
    ContextualStimulusPrescription,
)
from opencoach.planning.multi_week_trajectory import (
    TrajectoryWeekType,
)
from opencoach.planning.race_demand_profile import (
    build_race_demand_profile,
)
from opencoach.planning.session_intent import (
    SessionIntentImportance,
)
from opencoach.planning.session_intent_builder import (
    build_session_intent_plan,
)
from opencoach.planning.training_stimulus import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.weekly_stimulus_demand import (
    build_weekly_stimulus_demand,
)
from opencoach.planning.weekly_training_envelope import (
    TrainingPhase,
)


def create_requirement(
    *,
    stimulus: TrainingStimulus,
    priority: StimulusPriority,
    specificity: SpecificityLevel = (
        SpecificityLevel.MODERATE
    ),
    substitution: SubstitutionPolicy = (
        SubstitutionPolicy.ALLOWED
    ),
    preferred_modalities: tuple[
        TrainingModality,
        ...
    ] = (),
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


def create_prescription(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
) -> ContextualStimulusPrescription:
    return ContextualStimulusPrescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=build_race_demand_profile(
            distance_km=50.0,
            elevation_gain_m=2500.0,
        ),
        requirements=requirements,
    )


def build_demand(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
):
    return build_weekly_stimulus_demand(
        prescription=create_prescription(
            requirements
        ),
        week_type=TrajectoryWeekType.LOADING,
        target_load=500.0,
        reference_load=500.0,
    )


def test_empty_demand_creates_empty_plan() -> None:
    demand = build_weekly_stimulus_demand(
        prescription=create_prescription(
            (
                create_requirement(
                    stimulus=(
                        TrainingStimulus.AEROBIC_EASY
                    ),
                    priority=(
                        StimulusPriority.SUPPORT
                    ),
                ),
            )
        ),
        week_type=TrajectoryWeekType.SUSPENDED,
        target_load=0.0,
        reference_load=500.0,
    )

    result = build_session_intent_plan(
        weekly_demand=demand,
    )

    assert result.intents == ()
    assert result.session_count == 0
    assert result.represented_stimuli == ()


def test_long_endurance_can_absorb_trail_specific_stimuli() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            priority=StimulusPriority.KEY,
            substitution=SubstitutionPolicy.CONDITIONAL,
            preferred_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            duration_min_minutes=90,
            duration_max_minutes=300,
        ),
        create_requirement(
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            priority=StimulusPriority.IMPORTANT,
            substitution=SubstitutionPolicy.FORBIDDEN,
            preferred_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            required_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            duration_min_minutes=30,
            duration_max_minutes=180,
        ),
        create_requirement(
            stimulus=(
                TrainingStimulus.DOWNHILL_SPECIFICITY
            ),
            priority=StimulusPriority.IMPORTANT,
            substitution=SubstitutionPolicy.FORBIDDEN,
            preferred_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            required_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            duration_min_minutes=30,
            duration_max_minutes=180,
        ),
        create_requirement(
            stimulus=TrainingStimulus.RACE_SPECIFIC,
            priority=StimulusPriority.KEY,
            substitution=SubstitutionPolicy.FORBIDDEN,
            preferred_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            required_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            duration_min_minutes=60,
            duration_max_minutes=240,
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.session_count == 1

    intent = result.intents[0]

    assert (
        intent.primary_stimulus
        is TrainingStimulus.LONG_ENDURANCE
    )

    assert set(
        intent.secondary_stimuli
    ) == {
        TrainingStimulus.UPHILL_STRENGTH,
        TrainingStimulus.DOWNHILL_SPECIFICITY,
        TrainingStimulus.RACE_SPECIFIC,
    }

    assert (
        intent.importance
        is SessionIntentImportance.KEY
    )

    assert intent.required_modalities == (
        TrainingModality.TRAIL_RUNNING,
    )


def test_threshold_stays_separate_from_long_trail_session() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            priority=StimulusPriority.KEY,
            preferred_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
        ),
        create_requirement(
            stimulus=TrainingStimulus.THRESHOLD,
            priority=StimulusPriority.KEY,
            substitution=SubstitutionPolicy.FORBIDDEN,
            required_modalities=(
                TrainingModality.RUNNING,
                TrainingModality.TRAIL_RUNNING,
            ),
        ),
        create_requirement(
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            priority=StimulusPriority.IMPORTANT,
            substitution=SubstitutionPolicy.FORBIDDEN,
            required_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.session_count == 2

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.LONG_ENDURANCE
        for intent in result.intents
    )

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.THRESHOLD
        for intent in result.intents
    )


def test_strength_lower_body_and_core_are_combined() -> None:
    requirements = (
        create_requirement(
            stimulus=(
                TrainingStimulus.STRENGTH_LOWER_BODY
            ),
            priority=StimulusPriority.SUPPORT,
            preferred_modalities=(
                TrainingModality.STRENGTH,
            ),
        ),
        create_requirement(
            stimulus=TrainingStimulus.STRENGTH_CORE,
            priority=StimulusPriority.SUPPORT,
            preferred_modalities=(
                TrainingModality.STRENGTH,
            ),
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.session_count == 1

    intent = result.intents[0]

    assert (
        intent.primary_stimulus
        is TrainingStimulus.STRENGTH_LOWER_BODY
    )

    assert intent.secondary_stimuli == (
        TrainingStimulus.STRENGTH_CORE,
    )


def test_strength_is_not_merged_with_running() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            priority=StimulusPriority.SUPPORT,
            preferred_modalities=(
                TrainingModality.RUNNING,
            ),
        ),
        create_requirement(
            stimulus=TrainingStimulus.STRENGTH_CORE,
            priority=StimulusPriority.SUPPORT,
            preferred_modalities=(
                TrainingModality.STRENGTH,
            ),
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.session_count == 3

    stimuli = tuple(
        intent.primary_stimulus
        for intent in result.intents
    )

    assert (
        TrainingStimulus.AEROBIC_EASY
        in stimuli
    )

    assert (
        TrainingStimulus.STRENGTH_CORE
        in stimuli
    )


def test_easy_aerobic_target_occurrences_create_multiple_intents() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            priority=StimulusPriority.SUPPORT,
            preferred_modalities=(
                TrainingModality.RUNNING,
                TrainingModality.CYCLING,
            ),
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.session_count == 2

    assert all(
        intent.primary_stimulus
        is TrainingStimulus.AEROBIC_EASY
        for intent in result.intents
    )


def test_important_non_mergeable_stimulus_gets_own_intent() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            priority=StimulusPriority.IMPORTANT,
            substitution=SubstitutionPolicy.FORBIDDEN,
            required_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.session_count == 1

    assert (
        result.intents[0].primary_stimulus
        is TrainingStimulus.UPHILL_STRENGTH
    )

    assert (
        result.intents[0].importance
        is SessionIntentImportance.IMPORTANT
    )


def test_represented_stimuli_are_reported() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.THRESHOLD,
            priority=StimulusPriority.KEY,
        ),
        create_requirement(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            priority=StimulusPriority.SUPPORT,
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert set(
        result.represented_stimuli
    ) == {
        TrainingStimulus.THRESHOLD,
        TrainingStimulus.AEROBIC_EASY,
    }

    assert result.unrepresented_stimuli == ()


def test_all_target_stimuli_are_represented() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            priority=StimulusPriority.KEY,
        ),
        create_requirement(
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            priority=StimulusPriority.IMPORTANT,
        ),
        create_requirement(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            priority=StimulusPriority.SUPPORT,
        ),
        create_requirement(
            stimulus=TrainingStimulus.STRENGTH_CORE,
            priority=StimulusPriority.SUPPORT,
            preferred_modalities=(
                TrainingModality.STRENGTH,
            ),
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.unrepresented_stimuli == ()


def test_incompatible_duration_prevents_long_session_merge() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            priority=StimulusPriority.KEY,
            preferred_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            duration_min_minutes=120,
            duration_max_minutes=300,
        ),
        create_requirement(
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            priority=StimulusPriority.IMPORTANT,
            preferred_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            duration_max_minutes=90,
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.session_count == 2

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.LONG_ENDURANCE
        for intent in result.intents
    )

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.UPHILL_STRENGTH
        for intent in result.intents
    )


def test_incompatible_modalities_prevent_merge() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            priority=StimulusPriority.KEY,
            substitution=SubstitutionPolicy.FORBIDDEN,
            required_modalities=(
                TrainingModality.RUNNING,
            ),
        ),
        create_requirement(
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            priority=StimulusPriority.IMPORTANT,
            substitution=SubstitutionPolicy.FORBIDDEN,
            required_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
        ),
    )

    result = build_session_intent_plan(
        weekly_demand=build_demand(
            requirements
        )
    )

    assert result.session_count == 2


def test_recovery_demand_does_not_create_suppressed_key_intents() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.THRESHOLD,
            priority=StimulusPriority.KEY,
        ),
        create_requirement(
            stimulus=TrainingStimulus.AEROBIC_EASY,
            priority=StimulusPriority.SUPPORT,
        ),
    )

    demand = build_weekly_stimulus_demand(
        prescription=create_prescription(
            requirements
        ),
        week_type=TrajectoryWeekType.RECOVERY,
        target_load=350.0,
        reference_load=500.0,
    )

    result = build_session_intent_plan(
        weekly_demand=demand,
    )

    assert all(
        intent.primary_stimulus
        is not TrainingStimulus.THRESHOLD
        for intent in result.intents
    )

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.AEROBIC_EASY
        for intent in result.intents
    )


def test_session_count_is_intent_count_not_exposure_count() -> None:
    requirements = (
        create_requirement(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            priority=StimulusPriority.KEY,
        ),
        create_requirement(
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            priority=StimulusPriority.IMPORTANT,
        ),
        create_requirement(
            stimulus=(
                TrainingStimulus.DOWNHILL_SPECIFICITY
            ),
            priority=StimulusPriority.IMPORTANT,
        ),
    )

    demand = build_demand(
        requirements
    )

    result = build_session_intent_plan(
        weekly_demand=demand,
    )

    assert (
        result.session_count
        < demand.target_exposure_count
    )
