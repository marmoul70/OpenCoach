from opencoach.planning.training_stimulus import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.weekly_stimulus_scheduler import (
    schedule_weekly_stimuli,
)
from opencoach.planning.weekly_stimulus_slot import (
    SlotImportance,
    Weekday,
)


def create_requirement(
    stimulus: TrainingStimulus,
    priority: StimulusPriority,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=stimulus,
        priority=priority,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
    )


def test_empty_availability_returns_constrained_schedule() -> None:
    requirement = create_requirement(
        TrainingStimulus.AEROBIC_EASY,
        StimulusPriority.SUPPORT,
    )

    schedule = schedule_weekly_stimuli(
        requirements=(requirement,),
        available_days=(),
    )

    assert schedule.slots == ()
    assert schedule.constrained is True
    assert schedule.omitted_requirements == (
        requirement,
    )


def test_key_requirement_is_selected_before_support() -> None:
    support = create_requirement(
        TrainingStimulus.AEROBIC_EASY,
        StimulusPriority.SUPPORT,
    )

    key = create_requirement(
        TrainingStimulus.THRESHOLD,
        StimulusPriority.KEY,
    )

    schedule = schedule_weekly_stimuli(
        requirements=(
            support,
            key,
        ),
        available_days=(
            Weekday.TUESDAY,
        ),
    )

    assert len(schedule.slots) == 1

    assert (
        schedule.slots[0].requirement
        is key
    )

    assert (
        schedule.slots[0].importance
        is SlotImportance.KEY
    )


def test_support_is_omitted_before_key_when_week_is_constrained() -> None:
    key = create_requirement(
        TrainingStimulus.THRESHOLD,
        StimulusPriority.KEY,
    )

    support = create_requirement(
        TrainingStimulus.AEROBIC_EASY,
        StimulusPriority.SUPPORT,
    )

    schedule = schedule_weekly_stimuli(
        requirements=(
            support,
            key,
        ),
        available_days=(
            Weekday.THURSDAY,
        ),
    )

    assert schedule.constrained is True

    assert (
        schedule.omitted_requirements[0]
        is support
    )


def test_four_consecutive_available_days_remain_valid() -> None:
    requirements = (
        create_requirement(
            TrainingStimulus.THRESHOLD,
            StimulusPriority.KEY,
        ),
        create_requirement(
            TrainingStimulus.LONG_ENDURANCE,
            StimulusPriority.KEY,
        ),
        create_requirement(
            TrainingStimulus.AEROBIC_EASY,
            StimulusPriority.SUPPORT,
        ),
        create_requirement(
            TrainingStimulus.STRENGTH_CORE,
            StimulusPriority.SUPPORT,
        ),
    )

    schedule = schedule_weekly_stimuli(
        requirements=requirements,
        available_days=(
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
            Weekday.SUNDAY,
        ),
    )

    assert len(schedule.slots) == 4
    assert schedule.constrained is False

    assert {
        slot.day
        for slot in schedule.slots
    } == {
        Weekday.THURSDAY,
        Weekday.FRIDAY,
        Weekday.SATURDAY,
        Weekday.SUNDAY,
    }


def test_key_requirements_are_spread_when_possible() -> None:
    requirements = (
        create_requirement(
            TrainingStimulus.THRESHOLD,
            StimulusPriority.KEY,
        ),
        create_requirement(
            TrainingStimulus.LONG_ENDURANCE,
            StimulusPriority.KEY,
        ),
    )

    schedule = schedule_weekly_stimuli(
        requirements=requirements,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.SUNDAY,
        ),
    )

    key_days = {
        slot.day
        for slot in schedule.slots
    }

    assert key_days == {
        Weekday.MONDAY,
        Weekday.SUNDAY,
    }


def test_key_slot_has_recovery_preferences() -> None:
    requirement = create_requirement(
        TrainingStimulus.THRESHOLD,
        StimulusPriority.KEY,
    )

    schedule = schedule_weekly_stimuli(
        requirements=(requirement,),
        available_days=(
            Weekday.THURSDAY,
        ),
    )

    slot = schedule.slots[0]

    assert (
        slot.preferred_recovery_before_hours
        == 36
    )

    assert (
        slot.preferred_recovery_after_hours
        == 36
    )


def test_duplicate_available_days_are_normalized() -> None:
    requirement = create_requirement(
        TrainingStimulus.AEROBIC_EASY,
        StimulusPriority.SUPPORT,
    )

    schedule = schedule_weekly_stimuli(
        requirements=(requirement,),
        available_days=(
            Weekday.MONDAY,
            Weekday.MONDAY,
        ),
    )

    assert schedule.available_days == (
        Weekday.MONDAY,
    )

    assert len(schedule.slots) == 1
