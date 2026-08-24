import pytest

from opencoach.planning.stimulus.phase_prescription import (
    PhaseStimulusPrescription,
    build_phase_stimulus_prescription,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def test_base_contains_aerobic_long_endurance_and_strength() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.BASE,
    )

    stimuli = {
        requirement.stimulus
        for requirement in prescription.requirements
    }

    assert TrainingStimulus.AEROBIC_EASY in stimuli
    assert TrainingStimulus.LONG_ENDURANCE in stimuli
    assert TrainingStimulus.STRENGTH_LOWER_BODY in stimuli
    assert TrainingStimulus.STRENGTH_CORE in stimuli

def test_build_adds_quality_stimulus() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.BUILD,
    )

    threshold = prescription.requirement_for(
        TrainingStimulus.THRESHOLD,
    )

    assert threshold is not None
    assert threshold.priority is StimulusPriority.KEY


def test_specific_long_endurance_has_high_specificity() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.SPECIFIC,
    )

    requirement = prescription.requirement_for(
        TrainingStimulus.LONG_ENDURANCE,
    )

    assert requirement is not None

    assert (
        requirement.specificity
        is SpecificityLevel.HIGH
    )


def test_easy_aerobic_work_can_use_cross_training() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.BASE,
    )

    requirement = prescription.requirement_for(
        TrainingStimulus.AEROBIC_EASY,
    )

    assert requirement is not None

    assert (
        requirement.substitution
        is SubstitutionPolicy.ALLOWED
    )

    assert (
        TrainingModality.CYCLING
        in requirement.preferred_modalities
    )

    assert (
        TrainingModality.SWIMMING
        in requirement.preferred_modalities
    )


def test_threshold_is_not_freely_substitutable() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.BUILD,
    )

    requirement = prescription.requirement_for(
        TrainingStimulus.THRESHOLD,
    )

    assert requirement is not None

    assert (
        requirement.substitution
        is SubstitutionPolicy.FORBIDDEN
    )


def test_recovery_only_requires_easy_aerobic_stimulus() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.RECOVERY,
    )

    assert len(prescription.requirements) == 1

    assert (
        prescription.requirements[0].stimulus
        is TrainingStimulus.AEROBIC_EASY
    )


def test_taper_keeps_quality_without_long_endurance() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.TAPER,
    )

    stimuli = {
        requirement.stimulus
        for requirement in prescription.requirements
    }

    assert TrainingStimulus.THRESHOLD in stimuli
    assert TrainingStimulus.LONG_ENDURANCE not in stimuli


def test_duplicate_stimulus_is_rejected() -> None:
    requirement = TrainingStimulusRequirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
        specificity=SpecificityLevel.LOW,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        duration_min_minutes=30,
        duration_max_minutes=60,
    )

    with pytest.raises(
        ValueError,
        match="une seule fois",
    ):
        PhaseStimulusPrescription(
            phase=TrainingPhase.BASE,
            requirements=(
                requirement,
                requirement,
            ),
        )


def test_unknown_requirement_returns_none() -> None:
    prescription = build_phase_stimulus_prescription(
        TrainingPhase.FOUNDATION,
    )

    assert (
        prescription.requirement_for(
            TrainingStimulus.THRESHOLD,
        )
        is None
    )


def test_aerobic_easy_has_minimum_duration_of_45_minutes() -> None:
    """Une endurance facile dure au minimum 45 minutes."""

    prescription = build_phase_stimulus_prescription(
        TrainingPhase.SPECIFIC
    )

    requirement = prescription.requirement_for(
        TrainingStimulus.AEROBIC_EASY
    )

    assert requirement is not None

    assert (
        requirement.duration_min_minutes
        == 45
    )
