from opencoach.planning.sessions.prescription import (
    WorkDurationUnit,
    WorkStructureType,
    build_work_structure,
)
from opencoach.planning.stimulus.training import (
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