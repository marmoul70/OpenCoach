from opencoach.planning.stimulus.contextual_prescription import (
    ContextualStimulusPrescription,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.knowledge.race_demand_profile import (
    build_race_demand_profile,
)
from opencoach.planning.sessions.intent_builder import (
    build_session_intent_plan,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusPriority,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    TrainingStimulusRequirement,
)
from opencoach.planning.weekly.schedule_capacity import (
    DayScheduleCapacity,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.session_intent_scheduler import (
    schedule_session_intents,
)
from opencoach.planning.stimulus.weekly_demand import (
    build_weekly_stimulus_demand,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def create_requirement(
    *,
    stimulus: TrainingStimulus,
    priority: StimulusPriority,
    duration_min_minutes: int | None = None,
    duration_max_minutes: int | None = None,
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=stimulus,
        priority=priority,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        duration_min_minutes=(
            duration_min_minutes
        ),
        duration_max_minutes=(
            duration_max_minutes
        ),
    )


def create_plan(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
):
    prescription = ContextualStimulusPrescription(
        phase=TrainingPhase.BUILD,
        race_profile=build_race_demand_profile(
            distance_km=50.0,
            elevation_gain_m=2500.0,
        ),
        requirements=requirements,
    )

    demand = build_weekly_stimulus_demand(
        prescription=prescription,
        week_type=TrajectoryWeekType.LOADING,
        target_load=500.0,
        reference_load=500.0,
    )

    return build_session_intent_plan(
        weekly_demand=demand,
    )


def test_long_session_is_placed_on_only_compatible_day() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.LONG_ENDURANCE
                ),
                priority=StimulusPriority.KEY,
                duration_min_minutes=120,
                duration_max_minutes=180,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.SUNDAY,
        ),
        day_capacities=(
            DayScheduleCapacity(
                day=Weekday.MONDAY,
                max_duration_minutes=60,
            ),
            DayScheduleCapacity(
                day=Weekday.WEDNESDAY,
                max_duration_minutes=45,
            ),
            DayScheduleCapacity(
                day=Weekday.SUNDAY,
                max_duration_minutes=180,
            ),
        ),
    )

    assert schedule.session_count == 1

    slot = schedule.slots[0]

    assert slot.day is Weekday.SUNDAY

    assert (
        slot.duration_available_minutes
        == 180
    )


def test_intent_is_omitted_when_no_day_has_enough_time() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.LONG_ENDURANCE
                ),
                priority=StimulusPriority.KEY,
                duration_min_minutes=120,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
        ),
        day_capacities=(
            DayScheduleCapacity(
                day=Weekday.MONDAY,
                max_duration_minutes=60,
            ),
            DayScheduleCapacity(
                day=Weekday.WEDNESDAY,
                max_duration_minutes=45,
            ),
        ),
    )

    assert schedule.session_count == 0

    assert schedule.constrained is True

    assert len(
        schedule.omitted_intents
    ) == 1


def test_long_intent_is_placed_before_short_support_intent() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.LONG_ENDURANCE
                ),
                priority=StimulusPriority.KEY,
                duration_min_minutes=120,
            ),
            create_requirement(
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
                priority=StimulusPriority.SUPPORT,
                duration_min_minutes=30,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.SUNDAY,
        ),
        day_capacities=(
            DayScheduleCapacity(
                day=Weekday.MONDAY,
                max_duration_minutes=60,
            ),
            DayScheduleCapacity(
                day=Weekday.SUNDAY,
                max_duration_minutes=180,
            ),
        ),
    )

    assert any(
        (
            slot.day is Weekday.SUNDAY
            and slot.intent.primary_stimulus
            is TrainingStimulus.LONG_ENDURANCE
        )
        for slot in schedule.slots
    )

    assert any(
        (
            slot.day is Weekday.MONDAY
            and slot.intent.primary_stimulus
            is TrainingStimulus.AEROBIC_EASY
        )
        for slot in schedule.slots
    )


def test_unknown_capacity_keeps_historical_unlimited_behavior() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.LONG_ENDURANCE
                ),
                priority=StimulusPriority.KEY,
                duration_min_minutes=120,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
        ),
    )

    assert schedule.session_count == 1

    assert schedule.slots[0].day is Weekday.MONDAY

    assert (
        schedule.slots[0]
        .duration_available_minutes
        is None
    )


def test_duplicate_day_capacity_is_rejected() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
                duration_min_minutes=45,
            ),
        )
    )

    try:
        schedule_session_intents(
            plan=plan,
            available_days=(
                Weekday.MONDAY,
            ),
            day_capacities=(
                DayScheduleCapacity(
                    day=Weekday.MONDAY,
                    max_duration_minutes=60,
                ),
                DayScheduleCapacity(
                    day=Weekday.MONDAY,
                    max_duration_minutes=90,
                ),
            ),
        )

        raised = False

    except ValueError:
        raised = True

    assert raised is True
