from datetime import date

import pytest

from opencoach.planning.contextual_stimulus_prescription import (
    build_contextual_stimulus_prescription,
)
from opencoach.planning.load_recovery_cycle import (
    LoadRecoveryDecision,
    RecoveryTrigger,
)
from opencoach.planning.race_demand_profile import (
    build_race_demand_profile,
)
from opencoach.planning.trajectory_adjustment import (
    LoadAdjustment,
)
from opencoach.planning.weekly_load_progression import (
    calculate_weekly_load_target,
)
from opencoach.planning.weekly_stimulus_slot import (
    Weekday,
)
from opencoach.planning.weekly_training_envelope import (
    SchedulePressure,
    TrainingPhase,
)
from opencoach.planning.weekly_training_envelope_builder import (
    WeeklyTrainingEnvelopeInput,
    build_weekly_training_envelope,
)


def create_prescription():
    profile = build_race_demand_profile(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    return build_contextual_stimulus_prescription(
        phase=TrainingPhase.BUILD,
        race_profile=profile,
    )


def create_load_target():
    return calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BUILD,
        adjustment=LoadAdjustment.MAINTAIN,
    )


def test_builder_creates_full_week() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(
                2027,
                3,
                1,
            ),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=LoadRecoveryDecision(
                recovery_week=False,
                trigger=RecoveryTrigger.NONE,
                load_factor=1.0,
                loading_weeks_since_recovery=1,
            ),
            prescription=create_prescription(),
            available_days=(
                Weekday.MONDAY,
                Weekday.TUESDAY,
                Weekday.WEDNESDAY,
                Weekday.THURSDAY,
                Weekday.FRIDAY,
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            ),
        )
    )

    assert envelope.week_start == date(
        2027,
        3,
        1,
    )

    assert envelope.week_end == date(
        2027,
        3,
        7,
    )

    assert envelope.phase is TrainingPhase.BUILD

    assert envelope.session_count > 0


def test_recovery_reduces_load() -> None:
    load_target = create_load_target()

    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(
                2027,
                3,
                1,
            ),
            phase=TrainingPhase.BUILD,
            load_target=load_target,
            recovery=LoadRecoveryDecision(
                recovery_week=True,
                trigger=RecoveryTrigger.PLANNED,
                load_factor=0.75,
                loading_weeks_since_recovery=0,
            ),
            prescription=create_prescription(),
            available_days=(
                Weekday.MONDAY,
                Weekday.WEDNESDAY,
                Weekday.FRIDAY,
                Weekday.SUNDAY,
            ),
        )
    )

    assert envelope.target_load == pytest.approx(
        load_target.target_load
        * 0.75
    )

    assert any(
        "récupération"
        in note.lower()
        for note in envelope.notes
    )


def test_constrained_availability_is_preserved() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(
                2027,
                3,
                1,
            ),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=LoadRecoveryDecision(
                recovery_week=False,
                trigger=RecoveryTrigger.NONE,
                load_factor=1.0,
                loading_weeks_since_recovery=1,
            ),
            prescription=create_prescription(),
            available_days=(
                Weekday.THURSDAY,
                Weekday.FRIDAY,
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            ),
            athlete_schedule_constrained=True,
        )
    )

    assert envelope.available_days == (
        Weekday.THURSDAY,
        Weekday.FRIDAY,
        Weekday.SATURDAY,
        Weekday.SUNDAY,
    )

    assert (
        envelope.athlete_schedule_constrained
        is True
    )


def test_four_consecutive_days_are_not_rejected() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(
                2027,
                3,
                1,
            ),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=LoadRecoveryDecision(
                recovery_week=False,
                trigger=RecoveryTrigger.NONE,
                load_factor=1.0,
                loading_weeks_since_recovery=1,
            ),
            prescription=create_prescription(),
            available_days=(
                Weekday.THURSDAY,
                Weekday.FRIDAY,
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            ),
            athlete_schedule_constrained=True,
        )
    )

    assert envelope.consecutive_training_days == 4


def test_few_available_days_create_high_schedule_pressure() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(
                2027,
                3,
                1,
            ),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=LoadRecoveryDecision(
                recovery_week=False,
                trigger=RecoveryTrigger.NONE,
                load_factor=1.0,
                loading_weeks_since_recovery=1,
            ),
            prescription=create_prescription(),
            available_days=(
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            ),
        )
    )

    assert (
        envelope.schedule_pressure
        is SchedulePressure.HIGH
    )


def test_omitted_stimuli_are_explained() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(
                2027,
                3,
                1,
            ),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=LoadRecoveryDecision(
                recovery_week=False,
                trigger=RecoveryTrigger.NONE,
                load_factor=1.0,
                loading_weeks_since_recovery=1,
            ),
            prescription=create_prescription(),
            available_days=(
                Weekday.SUNDAY,
            ),
        )
    )

    assert any(
        "stimuli non positionnés"
        in note.lower()
        for note in envelope.notes
    )


def test_no_available_day_creates_empty_constrained_week() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(
                2027,
                3,
                1,
            ),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=LoadRecoveryDecision(
                recovery_week=False,
                trigger=RecoveryTrigger.NONE,
                load_factor=1.0,
                loading_weeks_since_recovery=1,
            ),
            prescription=create_prescription(),
            available_days=(),
            athlete_schedule_constrained=True,
        )
    )

    assert envelope.session_count == 0

    assert (
        envelope.athlete_schedule_constrained
        is True
    )
