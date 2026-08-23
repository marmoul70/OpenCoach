from datetime import date

import pytest

from opencoach.planning.training_stimulus import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
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


def create_easy_slot(
    *,
    slot_id: str,
    day: Weekday,
):
    requirement = TrainingStimulusRequirement(
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

    return WeeklyStimulusSlot(
        slot_id=slot_id,
        day=day,
        requirement=requirement,
        importance=SlotImportance.SUPPORT,
        fatigue_budget=FatigueBudget.LOW,
        duration_available_minutes=90,
    )


def test_four_consecutive_days_are_allowed() -> None:
    envelope = WeeklyTrainingEnvelope(
        week_start=date(
            2027,
            3,
            1,
        ),
        week_end=date(
            2027,
            3,
            7,
        ),
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
        schedule_pressure=(
            SchedulePressure.HIGH
        ),
        athlete_schedule_constrained=True,
    )

    assert envelope.session_count == 4

    assert (
        envelope.consecutive_training_days
        == 4
    )

    assert (
        envelope.athlete_schedule_constrained
        is True
    )


def test_slot_cannot_use_unavailable_day() -> None:
    with pytest.raises(
        ValueError,
        match="jour indisponible",
    ):
        WeeklyTrainingEnvelope(
            week_start=date(
                2027,
                3,
                1,
            ),
            week_end=date(
                2027,
                3,
                7,
            ),
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


def test_load_range_must_be_consistent() -> None:
    with pytest.raises(
        ValueError,
        match="charge minimale",
    ):
        WeeklyTrainingEnvelope(
            week_start=date(
                2027,
                3,
                1,
            ),
            week_end=date(
                2027,
                3,
                7,
            ),
            phase=TrainingPhase.BASE,
            target_load=300.0,
            load_min=330.0,
            load_max=310.0,
            available_days=(),
            slots=(),
            schedule_pressure=(
                SchedulePressure.LOW
            ),
        )


def test_target_load_must_fit_allowed_range() -> None:
    with pytest.raises(
        ValueError,
        match="plage autorisée",
    ):
        WeeklyTrainingEnvelope(
            week_start=date(
                2027,
                3,
                1,
            ),
            week_end=date(
                2027,
                3,
                7,
            ),
            phase=TrainingPhase.BASE,
            target_load=350.0,
            load_min=280.0,
            load_max=320.0,
            available_days=(),
            slots=(),
            schedule_pressure=(
                SchedulePressure.LOW
            ),
        )


def test_empty_week_has_no_consecutive_days() -> None:
    envelope = WeeklyTrainingEnvelope(
        week_start=date(
            2027,
            3,
            1,
        ),
        week_end=date(
            2027,
            3,
            7,
        ),
        phase=TrainingPhase.RECOVERY,
        target_load=0.0,
        load_min=0.0,
        load_max=50.0,
        available_days=(),
        slots=(),
        schedule_pressure=(
            SchedulePressure.LOW
        ),
    )

    assert envelope.session_count == 0
    assert envelope.consecutive_training_days == 0
