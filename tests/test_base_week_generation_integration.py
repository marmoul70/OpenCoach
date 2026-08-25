from datetime import date

from opencoach.coaching.generation.service import (
    WeeklyTrainingGenerationService,
)
from opencoach.planning.sessions.generators import (
    DeterministicSessionGenerator,
)
from opencoach.planning.stimulus.contextual_prescription import (
    build_contextual_stimulus_prescription,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.planning.trajectory.load_recovery_cycle import (
    decide_load_recovery,
)
from opencoach.planning.weekly.load_progression import (
    calculate_weekly_load_target,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)
from opencoach.planning.weekly.training_envelope_builder import (
    WeeklyTrainingEnvelopeInput,
    build_weekly_training_envelope,
)


def test_base_loading_week_generates_quality_easy_strength_and_long_run() -> None:
    phase = TrainingPhase.BASE

    load_target = calculate_weekly_load_target(
        previous_load=150.0,
        phase=phase,
    )

    recovery = decide_load_recovery(
        phase=phase,
        loading_weeks_since_recovery=1,
    )

    prescription = build_contextual_stimulus_prescription(
        phase=phase,
        race_profile=None,
    )

    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=date(
                2026,
                8,
                24,
            ),
            phase=phase,
            load_target=load_target,
            recovery=recovery,
            prescription=prescription,
            available_days=(
                Weekday.MONDAY,
                Weekday.WEDNESDAY,
                Weekday.FRIDAY,
                Weekday.SUNDAY,
            ),
            phase_week_index=1,
            target_session_count=4,
            reference_weekly_duration_minutes=300.0,
            target_weekly_duration_minutes=300.0,
            long_endurance_reference_minutes=150.0,
        )
    )

    assert envelope.athlete_schedule_constrained is False

    assert len(envelope.session_slots) == 5

    slot_stimuli = tuple(
        slot.intent.primary_stimulus
        for slot in envelope.session_slots
    )

    assert TrainingStimulus.SPEED_DEVELOPMENT in slot_stimuli
    assert TrainingStimulus.LONG_ENDURANCE in slot_stimuli

    assert (
        slot_stimuli.count(
            TrainingStimulus.AEROBIC_EASY
        )
        == 2
    )

    strength_slot = next(
        slot
        for slot in envelope.session_slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.STRENGTH_LOWER_BODY
        )
    )

    assert (
        TrainingStimulus.STRENGTH_CORE
        in strength_slot.intent.secondary_stimuli
    )

    easy_days = {
        slot.day
        for slot in envelope.session_slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.AEROBIC_EASY
        )
    }

    assert strength_slot.day in easy_days

    vo2_slot = next(
        slot
        for slot in envelope.session_slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.SPEED_DEVELOPMENT
        )
    )

    long_slot = next(
        slot
        for slot in envelope.session_slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.LONG_ENDURANCE
        )
    )

    assert strength_slot.day is not vo2_slot.day
    assert strength_slot.day is not long_slot.day

    service = WeeklyTrainingGenerationService(
        session_generator=DeterministicSessionGenerator()
    )

    generated = service.generate(
        envelope=envelope
    )

    assert generated.session_count == 5

    generated_stimuli = tuple(
        session.proposal.covered_stimuli
        for session in generated.sessions
    )

    assert any(
        TrainingStimulus.SPEED_DEVELOPMENT in stimuli
        for stimuli in generated_stimuli
    )

    assert any(
        TrainingStimulus.LONG_ENDURANCE in stimuli
        for stimuli in generated_stimuli
    )

    assert any(
        TrainingStimulus.STRENGTH_LOWER_BODY
        in stimuli
        for stimuli in generated_stimuli
    )

    strength_day_sessions = (
        generated.sessions_for_day(
            strength_slot.day
        )
    )

    assert len(strength_day_sessions) == 2

    assert {
        session.proposal.covered_stimuli[0]
        for session in strength_day_sessions
    } == {
        TrainingStimulus.AEROBIC_EASY,
        TrainingStimulus.STRENGTH_LOWER_BODY,
    }

    vo2_session = next(
        session
        for session in generated.sessions
        if (
            TrainingStimulus.SPEED_DEVELOPMENT
            in session.proposal.covered_stimuli
        )
    )

    assert vo2_session.proposal.work_structure is not None

    assert (
        vo2_session.proposal.work_structure.stimulus
        is TrainingStimulus.SPEED_DEVELOPMENT
    )
