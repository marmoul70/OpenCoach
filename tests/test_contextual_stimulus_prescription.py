from opencoach.planning.contextual_stimulus_prescription import (
    build_contextual_stimulus_prescription,
)
from opencoach.planning.race_demand_profile import (
    build_race_demand_profile,
)
from opencoach.planning.training_stimulus import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingStimulus,
)
from opencoach.planning.weekly_training_envelope import (
    TrainingPhase,
)


def create_mountain_50k():
    return build_race_demand_profile(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )


def create_flat_10k():
    return build_race_demand_profile(
        distance_km=10.0,
        elevation_gain_m=0.0,
    )


def test_mountain_50k_adds_uphill_strength() -> None:
    prescription = build_contextual_stimulus_prescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=create_mountain_50k(),
    )

    requirement = prescription.requirement_for(
        TrainingStimulus.UPHILL_STRENGTH,
    )

    assert requirement is not None


def test_mountain_50k_adds_uphill_threshold() -> None:
    prescription = build_contextual_stimulus_prescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=create_mountain_50k(),
    )

    requirement = prescription.requirement_for(
        TrainingStimulus.UPHILL_THRESHOLD,
    )

    assert requirement is not None
    assert requirement.priority is StimulusPriority.KEY


def test_mountain_50k_adds_downhill_specificity() -> None:
    prescription = build_contextual_stimulus_prescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=create_mountain_50k(),
    )

    requirement = prescription.requirement_for(
        TrainingStimulus.DOWNHILL_SPECIFICITY,
    )

    assert requirement is not None

    assert (
        requirement.specificity
        is SpecificityLevel.VERY_HIGH
    )


def test_mountain_50k_adds_race_specific_work() -> None:
    prescription = build_contextual_stimulus_prescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=create_mountain_50k(),
    )

    requirement = prescription.requirement_for(
        TrainingStimulus.RACE_SPECIFIC,
    )

    assert requirement is not None

    assert (
        requirement.substitution
        is SubstitutionPolicy.FORBIDDEN
    )


def test_flat_10k_does_not_add_downhill_specificity() -> None:
    prescription = build_contextual_stimulus_prescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=create_flat_10k(),
    )

    assert (
        prescription.requirement_for(
            TrainingStimulus.DOWNHILL_SPECIFICITY,
        )
        is None
    )


def test_flat_10k_does_not_add_uphill_strength() -> None:
    prescription = build_contextual_stimulus_prescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=create_flat_10k(),
    )

    assert (
        prescription.requirement_for(
            TrainingStimulus.UPHILL_STRENGTH,
        )
        is None
    )


def test_build_phase_uses_lower_specificity_than_specific_phase() -> None:
    build = build_contextual_stimulus_prescription(
        phase=TrainingPhase.BUILD,
        race_profile=create_mountain_50k(),
    )

    specific = build_contextual_stimulus_prescription(
        phase=TrainingPhase.SPECIFIC,
        race_profile=create_mountain_50k(),
    )

    build_requirement = build.requirement_for(
        TrainingStimulus.UPHILL_STRENGTH,
    )

    specific_requirement = specific.requirement_for(
        TrainingStimulus.UPHILL_STRENGTH,
    )

    assert build_requirement is not None
    assert specific_requirement is not None

    assert (
        build_requirement.specificity
        is SpecificityLevel.HIGH
    )

    assert (
        specific_requirement.specificity
        is SpecificityLevel.VERY_HIGH
    )


def test_base_phase_does_not_force_specific_trail_stimuli() -> None:
    prescription = build_contextual_stimulus_prescription(
        phase=TrainingPhase.BASE,
        race_profile=create_mountain_50k(),
    )

    assert (
        prescription.requirement_for(
            TrainingStimulus.UPHILL_THRESHOLD,
        )
        is None
    )

    assert (
        prescription.requirement_for(
            TrainingStimulus.DOWNHILL_SPECIFICITY,
        )
        is None
    )
