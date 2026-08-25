import pytest

from opencoach.planning.sessions.prescription import (
    CircuitStepType,
    WorkDurationUnit,
    WorkInterval,
    WorkStructureType,
    build_work_structure,
)
from opencoach.planning.stimulus.training import (
    TrainingModality,
    TrainingStimulus,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def test_threshold_specific_builds_long_intervals() -> None:
    structure = build_work_structure(
        stimulus=TrainingStimulus.THRESHOLD,
        phase=TrainingPhase.SPECIFIC,
        available_minutes=40,
    )

    assert (
        structure.structure_type
        is WorkStructureType.INTERVALS
    )

    assert structure.intervals

    interval = structure.intervals[0]

    assert interval.total_work_minutes >= 30

    assert (
        interval.total_duration_minutes
        <= 40
    )


def test_threshold_short_window_falls_back_to_continuous() -> None:
    structure = build_work_structure(
        stimulus=TrainingStimulus.THRESHOLD,
        phase=TrainingPhase.BASE,
        available_minutes=12,
    )

    assert (
        structure.structure_type
        is WorkStructureType.CONTINUOUS
    )

    assert structure.continuous_minutes == 12


def test_vo2max_can_use_second_based_intervals() -> None:
    structure = build_work_structure(
        stimulus=TrainingStimulus.VO2MAX,
        phase=TrainingPhase.BASE,
        available_minutes=20,
    )

    assert (
        structure.structure_type
        is WorkStructureType.INTERVALS
    )

    interval = structure.intervals[0]

    assert (
        interval.work_unit
        is WorkDurationUnit.SECONDS
    )

    assert interval.work_duration in {
        60,
        90,
    }


def test_vo2max_build_phase_can_use_longer_intervals() -> None:
    structure = build_work_structure(
        stimulus=TrainingStimulus.VO2MAX,
        phase=TrainingPhase.BUILD,
        available_minutes=30,
    )

    assert (
        structure.structure_type
        is WorkStructureType.INTERVALS
    )

    interval = structure.intervals[0]

    assert interval.repetitions >= 5


def test_uphill_strength_uses_short_repeats() -> None:
    structure = build_work_structure(
        stimulus=(
            TrainingStimulus.UPHILL_STRENGTH
        ),
        phase=TrainingPhase.SPECIFIC,
        available_minutes=20,
    )

    assert (
        structure.structure_type
        is WorkStructureType.REPEATS
    )

    interval = structure.intervals[0]

    assert (
        interval.work_unit
        is WorkDurationUnit.SECONDS
    )

    assert interval.work_duration in {
        30,
        45,
        60,
    }


def test_downhill_uses_technical_structure() -> None:
    structure = build_work_structure(
        stimulus=(
            TrainingStimulus.DOWNHILL_SPECIFICITY
        ),
        phase=TrainingPhase.SPECIFIC,
        available_minutes=30,
    )

    assert (
        structure.structure_type
        is WorkStructureType.TECHNICAL
    )


def test_long_endurance_is_continuous() -> None:
    structure = build_work_structure(
        stimulus=(
            TrainingStimulus.LONG_ENDURANCE
        ),
        phase=TrainingPhase.SPECIFIC,
        available_minutes=120,
    )

    assert (
        structure.structure_type
        is WorkStructureType.CONTINUOUS
    )

    assert structure.continuous_minutes == 120


def test_strength_core_uses_strength_structure() -> None:
    structure = build_work_structure(
        stimulus=(
            TrainingStimulus.STRENGTH_CORE
        ),
        phase=TrainingPhase.BASE,
        available_minutes=25,
    )

    assert (
        structure.structure_type
        is WorkStructureType.STRENGTH
    )

    assert structure.planned_minutes == 25


def test_interval_structure_never_exceeds_available_time() -> None:
    for available_minutes in range(
        10,
        61,
        5,
    ):
        structure = build_work_structure(
            stimulus=TrainingStimulus.THRESHOLD,
            phase=TrainingPhase.BUILD,
            available_minutes=available_minutes,
        )

        assert (
            structure.planned_seconds
            <= available_minutes * 60
        )


def test_every_stimulus_can_build_structure() -> None:
    for stimulus in TrainingStimulus:
        structure = build_work_structure(
            stimulus=stimulus,
            phase=TrainingPhase.BUILD,
            available_minutes=40,
        )

        assert structure.stimulus is stimulus

        assert (
            structure.planned_seconds
            <= 40 * 60
        )


def test_short_interval_calculates_exact_seconds() -> None:
    structure = build_work_structure(
        stimulus=(
            TrainingStimulus.UPHILL_STRENGTH
        ),
        phase=TrainingPhase.SPECIFIC,
        available_minutes=15,
    )

    interval = structure.intervals[0]

    assert (
        interval.total_duration_seconds
        <= 15 * 60
    )


def test_second_based_description_is_human_readable() -> None:
    structure = build_work_structure(
        stimulus=(
            TrainingStimulus.UPHILL_STRENGTH
        ),
        phase=TrainingPhase.SPECIFIC,
        available_minutes=15,
    )

    assert " s" in structure.description

def test_short_vo2_window_keeps_interval_structure() -> None:
    """Un créneau VO2 court conserve une structure fractionnée."""

    structure = build_work_structure(
        stimulus=TrainingStimulus.VO2MAX,
        phase=TrainingPhase.BASE,
        available_minutes=10,
    )

    assert (
        structure.structure_type
        is WorkStructureType.INTERVALS
    )

    assert structure.intervals

    interval = structure.intervals[0]

    assert interval.repetitions >= 2

    assert (
        interval.total_duration_minutes
        <= 10
    )

    assert (
        interval.total_work_minutes
        < interval.total_duration_minutes
    )


def test_circuit_structure_can_describe_multiple_steps() -> None:
    """Un circuit peut contenir plusieurs étapes de nature différente."""

    from opencoach.planning.sessions.prescription import (
        CircuitStep,
        CircuitStepType,
        WorkCircuit,
        WorkStructure,
    )

    circuit = WorkCircuit(
        repetitions=6,
        steps=(
            CircuitStep(
                step_type=CircuitStepType.STRENGTH,
                duration_seconds=60,
                description="Chaise isométrique",
            ),
            CircuitStep(
                step_type=CircuitStepType.WORK,
                duration_seconds=45,
                description="Course en côte",
            ),
            CircuitStep(
                step_type=CircuitStepType.RECOVERY,
                duration_seconds=60,
                description="Récupération en descente",
            ),
        ),
    )

    assert circuit.repetitions == 6
    assert len(circuit.steps) == 3

    assert circuit.cycle_duration_seconds == 165
    assert circuit.total_duration_seconds == 990


def test_circuit_rejects_empty_steps() -> None:
    """Un circuit doit obligatoirement contenir au moins une étape."""

    import pytest

    from opencoach.planning.sessions.prescription import (
        WorkCircuit,
    )

    with pytest.raises(
        ValueError,
        match="étape",
    ):
        WorkCircuit(
            repetitions=6,
            steps=(),
        )


def test_circuit_rejects_non_positive_repetitions() -> None:
    """Un circuit doit comporter au moins une répétition."""

    import pytest

    from opencoach.planning.sessions.prescription import (
        CircuitStep,
        CircuitStepType,
        WorkCircuit,
    )

    with pytest.raises(
        ValueError,
        match="répétitions",
    ):
        WorkCircuit(
            repetitions=0,
            steps=(
                CircuitStep(
                    step_type=CircuitStepType.WORK,
                    duration_seconds=60,
                    description="Course en côte",
                ),
            ),
        )


def test_circuit_step_rejects_non_positive_duration() -> None:
    """Une étape de circuit doit avoir une durée positive."""

    import pytest

    from opencoach.planning.sessions.prescription import (
        CircuitStep,
        CircuitStepType,
    )

    with pytest.raises(
        ValueError,
        match="durée",
    ):
        CircuitStep(
            step_type=CircuitStepType.STRENGTH,
            duration_seconds=0,
            description="Chaise isométrique",
        )


def test_work_structure_can_hold_circuit() -> None:
    """Une structure de travail peut contenir un circuit composite."""

    from opencoach.planning.sessions.prescription import (
        CircuitStep,
        CircuitStepType,
        WorkCircuit,
        WorkStructure,
    )

    circuit = WorkCircuit(
        repetitions=6,
        steps=(
            CircuitStep(
                step_type=CircuitStepType.STRENGTH,
                duration_seconds=60,
                description="Chaise isométrique",
            ),
            CircuitStep(
                step_type=CircuitStepType.WORK,
                duration_seconds=45,
                description="Course en côte",
            ),
            CircuitStep(
                step_type=CircuitStepType.RECOVERY,
                duration_seconds=60,
                description="Récupération en descente",
            ),
        ),
    )

    structure = WorkStructure(
        structure_type=WorkStructureType.CIRCUIT,
        stimulus=TrainingStimulus.UPHILL_STRENGTH,
        available_minutes=20,
        circuit=circuit,
        description="Circuit force-endurance en côte.",
    )

    assert structure.circuit is circuit
    assert structure.planned_seconds == 990
    assert structure.planned_minutes == 16.5


def test_work_structure_rejects_intervals_and_circuit_together() -> None:
    """Une structure ne mélange pas intervalles classiques et circuit."""

    import pytest

    from opencoach.planning.sessions.prescription import (
        CircuitStep,
        CircuitStepType,
        WorkCircuit,
        WorkInterval,
        WorkStructure,
    )

    circuit = WorkCircuit(
        repetitions=2,
        steps=(
            CircuitStep(
                step_type=CircuitStepType.WORK,
                duration_seconds=60,
                description="Course en côte",
            ),
        ),
    )

    interval = WorkInterval(
        repetitions=2,
        work_duration=1,
        work_unit=WorkDurationUnit.MINUTES,
        recovery_duration=1,
        recovery_unit=WorkDurationUnit.MINUTES,
    )

    with pytest.raises(
        ValueError,
        match="circuit",
    ):
        WorkStructure(
            structure_type=WorkStructureType.CIRCUIT,
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            available_minutes=10,
            intervals=(interval,),
            circuit=circuit,
            description="Structure invalide.",
        )


def test_work_structure_rejects_continuous_and_circuit_together() -> None:
    """Une structure ne mélange pas continu et circuit."""

    import pytest

    from opencoach.planning.sessions.prescription import (
        CircuitStep,
        CircuitStepType,
        WorkCircuit,
        WorkStructure,
    )

    circuit = WorkCircuit(
        repetitions=2,
        steps=(
            CircuitStep(
                step_type=CircuitStepType.WORK,
                duration_seconds=60,
                description="Course en côte",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="circuit",
    ):
        WorkStructure(
            structure_type=WorkStructureType.CIRCUIT,
            stimulus=TrainingStimulus.UPHILL_STRENGTH,
            available_minutes=10,
            continuous_minutes=5,
            circuit=circuit,
            description="Structure invalide.",
        )


def test_uphill_strength_endurance_build_uses_short_circuit() -> None:
    """BUILD utilise le circuit court de force-endurance en côte."""

    structure = build_work_structure(
        stimulus=TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
        phase=TrainingPhase.BUILD,
        available_minutes=20,
    )

    assert (
        structure.structure_type
        is WorkStructureType.CIRCUIT
    )

    assert structure.circuit is not None

    circuit = structure.circuit

    assert circuit.repetitions >= 4

    assert tuple(
        step.duration_seconds
        for step in circuit.steps
    ) == (
        60,
        45,
        60,
    )

    assert (
        circuit.total_duration_seconds
        <= 20 * 60
    )


def test_uphill_strength_endurance_specific_uses_long_circuit() -> None:
    """SPECIFIC utilise la variante longue du circuit."""

    structure = build_work_structure(
        stimulus=TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
        phase=TrainingPhase.SPECIFIC,
        available_minutes=25,
    )

    assert (
        structure.structure_type
        is WorkStructureType.CIRCUIT
    )

    assert structure.circuit is not None

    assert tuple(
        step.duration_seconds
        for step in structure.circuit.steps
    ) == (
        60,
        60,
        90,
    )

    assert (
        structure.circuit.total_duration_seconds
        <= 25 * 60
    )


def test_uphill_strength_endurance_circuit_uses_expected_steps() -> None:
    """Le circuit décrit explicitement chaise, côte et descente."""

    structure = build_work_structure(
        stimulus=TrainingStimulus.UPHILL_STRENGTH_ENDURANCE,
        phase=TrainingPhase.BUILD,
        available_minutes=20,
    )

    assert structure.circuit is not None

    steps = structure.circuit.steps

    assert tuple(
        step.step_type
        for step in steps
    ) == (
        CircuitStepType.STRENGTH,
        CircuitStepType.WORK,
        CircuitStepType.RECOVERY,
    )

    assert "chaise" in steps[0].description.lower()
    assert "côte" in steps[1].description.lower()
    assert "descente" in steps[2].description.lower()


def test_uphill_strength_endurance_has_session_recipe() -> None:
    """L'endurance de force en côte possède une recette métier."""

    from opencoach.planning.sessions.generators.catalog import (
        get_session_recipe,
    )

    recipe = get_session_recipe(
        TrainingStimulus.UPHILL_STRENGTH_ENDURANCE
    )

    assert recipe.title == "Force-endurance en côte"

    assert "pré-fatigue" in recipe.objective.lower()

    assert (
        recipe.default_modality
        is TrainingModality.TRAIL_RUNNING
    )

    assert "chaise" in recipe.main_block_name.lower()

def test_work_interval_can_use_distance_in_meters() -> None:
    interval = WorkInterval(
        repetitions=8,
        work_distance_meters=200,
        recovery_duration=60,
        recovery_unit=WorkDurationUnit.SECONDS,
    )

    assert interval.work_distance_meters == 200
    assert interval.total_work_distance_meters == 1600

def test_work_interval_rejects_duration_and_distance_together() -> None:
    with pytest.raises(
        ValueError,
        match="durée ou une distance",
    ):
        WorkInterval(
            repetitions=8,
            work_duration=60,
            work_unit=WorkDurationUnit.SECONDS,
            work_distance_meters=200,
            recovery_duration=60,
            recovery_unit=WorkDurationUnit.SECONDS,
        )

def test_speed_development_progresses_with_phase_week_index() -> None:
    descriptions = []

    for phase_week_index in (
        1,
        2,
        3,
        4,
    ):
        structure = build_work_structure(
            stimulus=TrainingStimulus.SPEED_DEVELOPMENT,
            phase=TrainingPhase.BASE,
            available_minutes=30,
            phase_week_index=phase_week_index,
        )

        descriptions.append(
            structure.description
        )

    assert descriptions == [
        "8 × 100 m / récupération 45 s.",
        "8 × 200 m / récupération 60 s.",
        "6 × 300 m / récupération 75 s.",
        "6 × 400 m / récupération 90 s.",
    ]

def test_first_taper_week_uses_reduced_threshold_volume() -> None:
    structure = build_work_structure(
        stimulus=TrainingStimulus.THRESHOLD,
        phase=TrainingPhase.TAPER,
        available_minutes=45,
        phase_week_index=1,
    )

    assert (
        structure.description
        == "3 × 6 min / récupération 2 min."
    )


def test_second_taper_week_reduces_threshold_volume_again() -> None:
    structure = build_work_structure(
        stimulus=TrainingStimulus.THRESHOLD,
        phase=TrainingPhase.TAPER,
        available_minutes=45,
        phase_week_index=2,
    )

    assert (
        structure.description
        == "2 × 5 min / récupération 2 min."
    )