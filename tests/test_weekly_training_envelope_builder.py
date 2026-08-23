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
from opencoach.planning.training_stimulus import (
    TrainingStimulus,
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


def create_prescription(
    *,
    phase: TrainingPhase = TrainingPhase.BUILD,
):
    profile = build_race_demand_profile(
        distance_km=50.0,
        elevation_gain_m=2500.0,
    )

    return build_contextual_stimulus_prescription(
        phase=phase,
        race_profile=profile,
    )


def create_load_target(
    *,
    phase: TrainingPhase = TrainingPhase.BUILD,
):
    return calculate_weekly_load_target(
        previous_load=100.0,
        phase=phase,
        adjustment=LoadAdjustment.MAINTAIN,
    )


def create_recovery(
    *,
    recovery_week: bool = False,
    factor: float = 1.0,
):
    return LoadRecoveryDecision(
        recovery_week=recovery_week,
        trigger=(
            RecoveryTrigger.PLANNED
            if recovery_week
            else RecoveryTrigger.NONE
        ),
        load_factor=factor,
        loading_weeks_since_recovery=(
            0
            if recovery_week
            else 1
        ),
    )


def test_builder_creates_session_intent_pipeline() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
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

    assert envelope.session_slots


def test_legacy_slots_are_kept_as_compatibility_view() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
            prescription=create_prescription(),
            available_days=(
                Weekday.MONDAY,
                Weekday.WEDNESDAY,
                Weekday.FRIDAY,
                Weekday.SUNDAY,
            ),
        )
    )

    assert len(
        envelope.slots
    ) == len(
        envelope.session_slots
    )

    assert [
        slot.day
        for slot in envelope.slots
    ] == [
        slot.day
        for slot in envelope.session_slots
    ]


def test_session_intents_can_cover_multiple_stimuli() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
            prescription=create_prescription(),
            available_days=(
                Weekday.MONDAY,
                Weekday.WEDNESDAY,
                Weekday.FRIDAY,
                Weekday.SUNDAY,
            ),
        )
    )

    assert any(
        len(slot.intent.stimuli) > 1
        for slot in envelope.session_slots
    )


def test_recovery_reduces_load() -> None:
    load_target = create_load_target()

    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=load_target,
            recovery=create_recovery(
                recovery_week=True,
                factor=0.75,
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


def test_recovery_reduces_qualitative_density() -> None:
    normal = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
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

    recovery = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(
                recovery_week=True,
                factor=0.75,
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

    normal_key_stimuli = {
        stimulus
        for slot in normal.session_slots
        for stimulus in slot.intent.stimuli
        if stimulus in {
            TrainingStimulus.THRESHOLD,
            TrainingStimulus.LONG_ENDURANCE,
            TrainingStimulus.RACE_SPECIFIC,
        }
    }

    recovery_key_stimuli = {
        stimulus
        for slot in recovery.session_slots
        for stimulus in slot.intent.stimuli
        if stimulus in {
            TrainingStimulus.THRESHOLD,
            TrainingStimulus.LONG_ENDURANCE,
            TrainingStimulus.RACE_SPECIFIC,
        }
    }

    assert len(
        recovery_key_stimuli
    ) <= len(
        normal_key_stimuli
    )


def test_constrained_availability_is_preserved() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
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
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
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

    assert (
        envelope.consecutive_training_days
        <= 4
    )


def test_few_available_days_create_high_schedule_pressure() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
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


def test_omitted_intentions_are_explained() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
            prescription=create_prescription(),
            available_days=(
                Weekday.SUNDAY,
            ),
        )
    )

    assert any(
        "intentions non positionnées"
        in note.lower()
        for note in envelope.notes
    )


def test_no_available_day_creates_empty_constrained_week() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=create_load_target(),
            recovery=create_recovery(),
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


def test_zero_load_suppresses_all_session_intents() -> None:
    load_target = calculate_weekly_load_target(
        previous_load=100.0,
        phase=TrainingPhase.BUILD,
        adjustment=LoadAdjustment.SUSPEND,
    )

    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.BUILD,
            load_target=load_target,
            recovery=create_recovery(),
            prescription=create_prescription(),
            available_days=(
                Weekday.MONDAY,
                Weekday.WEDNESDAY,
                Weekday.FRIDAY,
            ),
        )
    )

    assert envelope.target_load == 0.0
    assert envelope.session_slots == ()
    assert envelope.slots == ()
    assert envelope.session_count == 0


def test_taper_uses_taper_stimulus_demand() -> None:
    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(2027, 3, 1),
            phase=TrainingPhase.TAPER,
            load_target=create_load_target(
                phase=TrainingPhase.TAPER
            ),
            recovery=create_recovery(),
            prescription=create_prescription(
                phase=TrainingPhase.TAPER
            ),
            available_days=(
                Weekday.MONDAY,
                Weekday.WEDNESDAY,
                Weekday.FRIDAY,
                Weekday.SUNDAY,
            ),
        )
    )

    threshold_slots = tuple(
        slot
        for slot in envelope.session_slots
        if (
            TrainingStimulus.THRESHOLD
            in slot.intent.stimuli
        )
    )

    assert len(
        threshold_slots
    ) <= 1