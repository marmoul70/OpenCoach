from opencoach.planning.sessions.coach_port import (
    SessionCoachPort,
    SessionCoachRequest,
)
from opencoach.planning.sessions.generators import (
    SESSION_RECIPES,
    DeterministicSessionGenerator,
    validate_session_recipe_catalog,
)
from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
)
from opencoach.planning.weekly.schedule_types import (
    FatigueBudget,
    Weekday,
)
from opencoach.planning.weekly.session_intent_slot import (
    WeeklySessionIntentSlot,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)
from opencoach.planning.sessions.prescription import (
    IntensityReference,
    WorkStructureType,
    WorkDurationUnit,
)

def create_request(
    *,
    primary_stimulus=(
        TrainingStimulus.LONG_ENDURANCE
    ),
    secondary_stimuli=(),
    importance=SessionIntentImportance.KEY,
    minimum=120,
    maximum=180,
    available=180,
    required_modalities=(
        TrainingModality.TRAIL_RUNNING,
    ),
    preferred_modalities=(),
) -> SessionCoachRequest:
    intent = SessionIntent(
        primary_stimulus=primary_stimulus,
        secondary_stimuli=secondary_stimuli,
        importance=importance,
        specificity=SpecificityLevel.HIGH,
        substitution=(
            SubstitutionPolicy.FORBIDDEN
            if required_modalities
            else SubstitutionPolicy.ALLOWED
        ),
        preferred_modalities=(
            preferred_modalities
        ),
        required_modalities=(
            required_modalities
        ),
        duration_min_minutes=minimum,
        duration_max_minutes=maximum,
    )

    slot = WeeklySessionIntentSlot(
        slot_id="sunday-key",
        day=Weekday.SUNDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.HIGH,
        duration_available_minutes=available,
    )

    return SessionCoachRequest(
        phase=TrainingPhase.SPECIFIC,
        slot=slot,
        target_load=500.0,
    )


def test_catalog_covers_every_training_stimulus() -> None:
    validate_session_recipe_catalog()

    assert set(
        SESSION_RECIPES
    ) == set(
        TrainingStimulus
    )


def test_generator_implements_session_coach_port() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    assert isinstance(
        generator,
        SessionCoachPort,
    )


def test_long_endurance_uses_midpoint_duration() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(),
    )

    assert proposal.title == "Sortie longue"

    assert (
        proposal.modality
        is TrainingModality.TRAIL_RUNNING
    )

    assert proposal.duration_minutes == 150

    assert (
        proposal.covered_stimuli
        == (
            TrainingStimulus.LONG_ENDURANCE,
        )
    )

    assert sum(
        block.duration_minutes
        for block in proposal.blocks
    ) == 150


def test_generator_covers_secondary_stimuli() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            secondary_stimuli=(
                TrainingStimulus.UPHILL_STRENGTH,
                TrainingStimulus.DOWNHILL_SPECIFICITY,
            ),
        ),
    )

    assert (
        proposal.covered_stimuli
        == (
            TrainingStimulus.LONG_ENDURANCE,
            TrainingStimulus.UPHILL_STRENGTH,
            TrainingStimulus.DOWNHILL_SPECIFICITY,
        )
    )


def test_required_modality_has_priority() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            required_modalities=(
                TrainingModality.TRAIL_RUNNING,
            ),
            preferred_modalities=(
                TrainingModality.RUNNING,
            ),
        ),
    )

    assert (
        proposal.modality
        is TrainingModality.TRAIL_RUNNING
    )


def test_preferred_modality_is_used_without_requirement() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            primary_stimulus=(
                TrainingStimulus.AEROBIC_EASY
            ),
            importance=(
                SessionIntentImportance.SUPPORT
            ),
            minimum=None,
            maximum=None,
            available=60,
            required_modalities=(),
            preferred_modalities=(
                TrainingModality.CYCLING,
            ),
        ),
    )

    assert (
        proposal.modality
        is TrainingModality.CYCLING
    )

    assert proposal.duration_minutes == 45


def test_recipe_default_modality_is_fallback() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            primary_stimulus=(
                TrainingStimulus.STRENGTH_CORE
            ),
            importance=(
                SessionIntentImportance.SUPPORT
            ),
            minimum=None,
            maximum=None,
            available=60,
            required_modalities=(),
            preferred_modalities=(),
        ),
    )

    assert (
        proposal.modality
        is TrainingModality.STRENGTH
    )


def test_recovery_session_uses_single_block() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            primary_stimulus=(
                TrainingStimulus.RECOVERY
            ),
            importance=(
                SessionIntentImportance.SUPPORT
            ),
            minimum=30,
            maximum=40,
            available=40,
            required_modalities=(),
        ),
    )

    assert proposal.duration_minutes == 35

    assert len(
        proposal.blocks
    ) == 1

    assert (
        proposal.blocks[0].duration_minutes
        == 35
    )


def test_available_duration_caps_generated_duration() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            minimum=120,
            maximum=180,
            available=130,
        ),
    )

    assert proposal.duration_minutes == 130


def test_notes_identify_python_generation() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(),
    )

    assert any(
        "Python OpenCoach"
        in note
        for note in proposal.coach_notes
    )

from opencoach.planning.sessions.prescription import (
    IntensityReference,
)


def test_generated_session_contains_intensity_prescription() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(),
    )

    assert (
        proposal.intensity_prescription
        is not None
    )

    assert (
        proposal.intensity_prescription.stimulus
        is TrainingStimulus.LONG_ENDURANCE
    )


def test_generator_uses_rpe_without_physiology() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(),
    )

    prescription = (
        proposal.intensity_prescription
    )

    assert prescription is not None

    assert (
        prescription.primary_target.reference
        is IntensityReference.RPE
    )

    assert (
        prescription.primary_target.minimum
        == 3
    )

    assert (
        prescription.primary_target.maximum
        == 4
    )


def test_generator_reports_missing_physiological_calibration() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(),
    )

    assert any(
        "calibration"
        in note.lower()
        for note in proposal.coach_notes
    )

def test_generated_session_contains_work_structure() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(),
    )

    assert proposal.work_structure is not None

    assert (
        proposal.work_structure.stimulus
        is TrainingStimulus.LONG_ENDURANCE
    )

    assert (
        proposal.work_structure.structure_type
        is WorkStructureType.CONTINUOUS
    )


def test_threshold_session_contains_real_intervals() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            primary_stimulus=(
                TrainingStimulus.THRESHOLD
            ),
            minimum=70,
            maximum=70,
            available=70,
            required_modalities=(),
            preferred_modalities=(
                TrainingModality.RUNNING,
            ),
        ),
    )

    structure = proposal.work_structure

    assert structure is not None

    assert (
        structure.structure_type
        is WorkStructureType.INTERVALS
    )

    assert structure.intervals

    interval = structure.intervals[0]

    assert interval.repetitions >= 2

    assert (
        interval.work_unit
        is WorkDurationUnit.MINUTES
    )

    assert interval.work_duration >= 8

    assert (
        interval.total_duration_minutes
        <= structure.available_minutes
    )


def test_threshold_blocks_preserve_total_session_duration() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            primary_stimulus=(
                TrainingStimulus.THRESHOLD
            ),
            minimum=70,
            maximum=70,
            available=70,
            required_modalities=(),
            preferred_modalities=(
                TrainingModality.RUNNING,
            ),
        ),
    )

    assert sum(
        block.duration_minutes
        for block in proposal.blocks
    ) == 70


def test_threshold_main_block_contains_structure_description() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            primary_stimulus=(
                TrainingStimulus.THRESHOLD
            ),
            minimum=70,
            maximum=70,
            available=70,
            required_modalities=(),
            preferred_modalities=(
                TrainingModality.RUNNING,
            ),
        ),
    )

    main_block = next(
        block
        for block in proposal.blocks
        if block.name == "Bloc seuil"
    )

    assert "×" in main_block.description

    assert "récupération" in (
        main_block.description.lower()
    )


def test_unused_quality_time_becomes_easy_complement() -> None:
    generator = (
        DeterministicSessionGenerator()
    )

    proposal = generator.generate_session(
        request=create_request(
            primary_stimulus=(
                TrainingStimulus.THRESHOLD
            ),
            minimum=70,
            maximum=70,
            available=70,
            required_modalities=(),
            preferred_modalities=(
                TrainingModality.RUNNING,
            ),
        ),
    )

    assert any(
        block.name == "Complément facile"
        for block in proposal.blocks
    )