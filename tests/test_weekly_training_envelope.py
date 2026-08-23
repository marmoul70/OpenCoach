from datetime import date

import pytest

from opencoach.planning.session_intent import (
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
from opencoach.planning.weekly_session_intent_slot import (
    WeeklySessionIntentSlot,
)
from opencoach.planning.weekly_stimulus_slot import (
    FatigueBudget,
    SlotImportance,
    Weekday,
    WeeklyStimulusSlot,
)
from opencoach.planning.weekly_training_envelope import (
    SchedulePressure,
    TrainingPhase,
    WeeklyTrainingEnvelope,
)


def create_easy_requirement():
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
        specificity=SpecificityLevel.LOW,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.CYCLING,
            TrainingModality.SWIMMING,
        ),
        duration_min_minutes=30,
        duration_max_minutes=90,
    )


def create_easy_slot(
    *,
    slot_id: str,
    day: Weekday,
):
    return WeeklyStimulusSlot(
        slot_id=slot_id,
        day=day,
        requirement=create_easy_requirement(),
        importance=SlotImportance.SUPPORT,
        fatigue_budget=FatigueBudget.LOW,
        duration_available_minutes=90,
    )


def create_easy_session_slot(
    *,
    slot_id: str,
    day: Weekday,
):
    intent = build_session_intent(
        primary=create_easy_requirement(),
    )

    return WeeklySessionIntentSlot(
        slot_id=slot_id,
        day=day,
        intent=intent,
        fatigue_budget=FatigueBudget.LOW,
        duration_available_minutes=90,
    )


def test_four_consecutive_legacy_days_are_allowed() -> None:
    envelope = WeeklyTrainingEnvelope(
        week_start=date(2027, 3, 1),
        week_end=date(2027, 3, 7),
        phase=TrainingPhase.BUILD,
        target_load=320.0,
        load_min=290.0,
        load_max=340.0,
        available_days=(
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        ),
        slots=(
            create_easy_slot(
                slot_id="thu",
                day=Weekday.THURSDAY,
            ),
            create_easy_slot(
                slot_id="fri",
                day=Weekday.FRIDAY,
            ),
            create_easy_slot(
                slot_id="sat",
                day=Weekday.SATURDAY,
            ),
            create_easy_slot(
                slot_id="sun",
                day=Weekday.SUNDAY,
            ),
        ),
        schedule_pressure=SchedulePressure.HIGH,
        athlete_schedule_constrained=True,
    )

    assert envelope.session_count == 4

    assert (
        envelope.consecutive_training_days
        == 4
    )


def test_session_slots_are_new_source_of_session_count() -> None:
    envelope = WeeklyTrainingEnvelope(
        week_start=date(2027, 3, 1),
        week_end=date(2027, 3, 7),
        phase=TrainingPhase.BUILD,
        target_load=320.0,
        load_min=290.0,
        load_max=340.0,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
        ),
        slots=(
            create_easy_slot(
                slot_id="legacy",
                day=Weekday.MONDAY,
            ),
        ),
        session_slots=(
            create_easy_session_slot(
                slot_id="monday",
                day=Weekday.MONDAY,
            ),
            create_easy_session_slot(
                slot_id="wednesday",
                day=Weekday.WEDNESDAY,
            ),
        ),
        schedule_pressure=(
            SchedulePressure.MODERATE
        ),
    )

    assert envelope.session_count == 2


def test_session_slots_drive_consecutive_days() -> None:
    envelope = WeeklyTrainingEnvelope(
        week_start=date(2027, 3, 1),
        week_end=date(2027, 3, 7),
        phase=TrainingPhase.BUILD,
        target_load=320.0,
        load_min=290.0,
        load_max=340.0,
        available_days=(
            Weekday.THURSDAY,
            Weekday.FRIDAY,
        ),
        slots=(),
        session_slots=(
            create_easy_session_slot(
                slot_id="thu",
                day=Weekday.THURSDAY,
            ),
            create_easy_session_slot(
                slot_id="fri",
                day=Weekday.FRIDAY,
            ),
        ),
        schedule_pressure=SchedulePressure.HIGH,
    )

    assert (
        envelope.consecutive_training_days
        == 2
    )


def test_legacy_slot_cannot_use_unavailable_day() -> None:
    with pytest.raises(
        ValueError,
        match="jour indisponible",
    ):
        WeeklyTrainingEnvelope(
            week_start=date(2027, 3, 1),
            week_end=date(2027, 3, 7),
            phase=TrainingPhase.BASE,
            target_load=300.0,
            load_min=280.0,
            load_max=320.0,
            available_days=(
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            ),
            slots=(
                create_easy_slot(
                    slot_id="tuesday",
                    day=Weekday.TUESDAY,
                ),
            ),
            schedule_pressure=(
                SchedulePressure.MODERATE
            ),
        )


def test_session_slot_cannot_use_unavailable_day() -> None:
    with pytest.raises(
        ValueError,
        match="jour indisponible",
    ):
        WeeklyTrainingEnvelope(
            week_start=date(2027, 3, 1),
            week_end=date(2027, 3, 7),
            phase=TrainingPhase.BASE,
            target_load=300.0,
            load_min=280.0,
            load_max=320.0,
            available_days=(
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            ),
            slots=(),
            session_slots=(
                create_easy_session_slot(
                    slot_id="tuesday",
                    day=Weekday.TUESDAY,
                ),
            ),
            schedule_pressure=(
                SchedulePressure.MODERATE
            ),
        )


def test_load_range_must_be_consistent() -> None:
    with pytest.raises(
        ValueError,
        match="charge minimale",
    ):
        WeeklyTrainingEnvelope(
            week_start=date(2027, 3, 1),
            week_end=date(2027, 3, 7),
            phase=TrainingPhase.BASE,
            target_load=300.0,
            load_min=330.0,
            load_max=310.0,
            available_days=(),
            slots=(),
            schedule_pressure=SchedulePressure.LOW,
        )


def test_target_load_must_fit_allowed_range() -> None:
    with pytest.raises(
        ValueError,
        match="plage autorisée",
    ):
        WeeklyTrainingEnvelope(
            week_start=date(2027, 3, 1),
            week_end=date(2027, 3, 7),
            phase=TrainingPhase.BASE,
            target_load=350.0,
            load_min=280.0,
            load_max=320.0,
            available_days=(),
            slots=(),
            schedule_pressure=SchedulePressure.LOW,
        )


def test_empty_week_has_no_consecutive_days() -> None:
    envelope = WeeklyTrainingEnvelope(
        week_start=date(2027, 3, 1),
        week_end=date(2027, 3, 7),
        phase=TrainingPhase.RECOVERY,
        target_load=0.0,
        load_min=0.0,
        load_max=50.0,
        available_days=(),
        slots=(),
        session_slots=(),
        schedule_pressure=SchedulePressure.LOW,
    )

    assert envelope.session_count == 0
    assert envelope.consecutive_training_days == 0