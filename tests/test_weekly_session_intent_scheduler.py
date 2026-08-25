from dataclasses import replace

from opencoach.planning.stimulus.contextual_prescription import (
    ContextualStimulusPrescription,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.knowledge.race_demand_profile import (
    build_race_demand_profile,
)
from opencoach.planning.sessions.intent import (
    SessionIntentImportance,
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
from opencoach.planning.weekly.session_intent_scheduler import (
    schedule_session_intents,
)
from opencoach.planning.stimulus.weekly_demand import (
    build_weekly_stimulus_demand,
)
from opencoach.planning.weekly.schedule_types import (
    FatigueBudget,
    Weekday,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)


def create_requirement(
    *,
    stimulus: TrainingStimulus,
    priority: StimulusPriority,
    preferred_modalities: tuple[
        TrainingModality,
        ...
    ] = (),
) -> TrainingStimulusRequirement:
    return TrainingStimulusRequirement(
        stimulus=stimulus,
        priority=priority,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            preferred_modalities
        ),
    )


def create_plan(
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
    *,
    target_load: float = 500.0,
    reference_load: float = 500.0,
):
    prescription = (
        ContextualStimulusPrescription(
            phase=TrainingPhase.SPECIFIC,
            race_profile=(
                build_race_demand_profile(
                    distance_km=50.0,
                    elevation_gain_m=2500.0,
                )
            ),
            requirements=requirements,
        )
    )

    demand = build_weekly_stimulus_demand(
        prescription=prescription,
        week_type=TrajectoryWeekType.LOADING,
        target_load=target_load,
        reference_load=reference_load,
    )

    return build_session_intent_plan(
        weekly_demand=demand,
    )


def test_no_availability_returns_constrained_schedule() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(),
    )

    assert schedule.slots == ()

    assert schedule.constrained is True

    assert len(
        schedule.omitted_intents
    ) == 1


def test_empty_plan_returns_empty_unconstrained_schedule() -> None:
    plan = create_plan(
        ()
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
        ),
    )

    assert schedule.session_count == 0

    assert schedule.constrained is False


def test_key_intent_is_selected_before_support() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
                priority=(
                    StimulusPriority.SUPPORT
                ),
            ),
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.THURSDAY,
        ),
    )

    assert schedule.session_count == 1

    assert (
        schedule.slots[0]
        .intent.primary_stimulus
        is TrainingStimulus.THRESHOLD
    )

    assert schedule.constrained is False


def test_important_intent_is_selected_before_support() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
                priority=(
                    StimulusPriority.SUPPORT
                ),
            ),
            create_requirement(
                stimulus=(
                    TrainingStimulus.UPHILL_STRENGTH
                ),
                priority=(
                    StimulusPriority.IMPORTANT
                ),
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
        ),
    )

    assert (
        schedule.slots[0]
        .intent.primary_stimulus
        is TrainingStimulus.UPHILL_STRENGTH
    )


def test_multiple_stimuli_in_one_intent_use_one_day() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.LONG_ENDURANCE
                ),
                priority=StimulusPriority.KEY,
                preferred_modalities=(
                    TrainingModality.TRAIL_RUNNING,
                ),
            ),
            create_requirement(
                stimulus=(
                    TrainingStimulus.UPHILL_STRENGTH
                ),
                priority=(
                    StimulusPriority.IMPORTANT
                ),
                preferred_modalities=(
                    TrainingModality.TRAIL_RUNNING,
                ),
            ),
            create_requirement(
                stimulus=(
                    TrainingStimulus.DOWNHILL_SPECIFICITY
                ),
                priority=(
                    StimulusPriority.IMPORTANT
                ),
                preferred_modalities=(
                    TrainingModality.TRAIL_RUNNING,
                ),
            ),
        )
    )

    assert plan.session_count == 1

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.SUNDAY,
        ),
    )

    assert schedule.session_count == 1

    assert len(
        schedule.slots[0].intent.stimuli
    ) == 3


def test_two_key_sessions_are_spread_when_possible() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=(
                    TrainingStimulus.LONG_ENDURANCE
                ),
                priority=StimulusPriority.KEY,
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
    )

    key_days = {
        slot.day
        for slot in schedule.slots
        if slot.is_key
    }

    assert key_days == {
        Weekday.MONDAY,
        Weekday.SUNDAY,
    }


def test_key_slot_gets_high_fatigue_budget() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.THURSDAY,
        ),
    )

    slot = schedule.slots[0]

    assert (
        slot.fatigue_budget
        is FatigueBudget.HIGH
    )

    assert (
        slot.preferred_recovery_before_hours
        == 36
    )

    assert (
        slot.preferred_recovery_after_hours
        == 36
    )


def test_important_slot_gets_moderate_fatigue_budget() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.UPHILL_STRENGTH
                ),
                priority=(
                    StimulusPriority.IMPORTANT
                ),
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.WEDNESDAY,
        ),
    )

    slot = schedule.slots[0]

    assert (
        slot.intent.importance
        is SessionIntentImportance.IMPORTANT
    )

    assert (
        slot.fatigue_budget
        is FatigueBudget.MODERATE
    )


def test_support_slot_preserves_next_key_session() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
                priority=(
                    StimulusPriority.SUPPORT
                ),
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
        ),
    )

    assert all(
        slot.preserve_next_key_session
        for slot in schedule.slots
    )


def test_duplicate_available_days_are_normalized() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
                priority=(
                    StimulusPriority.SUPPORT
                ),
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.MONDAY,
        ),
    )

    assert schedule.available_days == (
        Weekday.MONDAY,
    )

    assert schedule.session_count == 1

    assert schedule.constrained is False


def test_omitted_intents_are_reported() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=(
                    TrainingStimulus.AEROBIC_EASY
                ),
                priority=(
                    StimulusPriority.SUPPORT
                ),
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.SUNDAY,
        ),
    )

    assert schedule.constrained is False

    assert len(
        schedule.omitted_intents
    ) >= 1


def test_long_endurance_prefers_sunday_when_available() -> None:
    """La sortie longue privilégie un jour de week-end disponible."""

    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                priority=StimulusPriority.KEY,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SUNDAY,
        ),
    )

    assert schedule.session_count == 1

    assert (
        schedule.slots[0].day
        is Weekday.SUNDAY
    )


def test_long_endurance_prefers_saturday_when_available() -> None:
    """Le samedi est préféré lorsqu'il est le week-end disponible."""

    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                priority=StimulusPriority.KEY,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
        ),
    )

    assert schedule.session_count == 1

    assert (
        schedule.slots[0].day
        is Weekday.SATURDAY
    )


def test_long_endurance_does_not_require_weekend() -> None:
    """La sortie longue reste possible sans disponibilité le week-end."""

    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                priority=StimulusPriority.KEY,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
        ),
    )

    assert schedule.session_count == 1

    assert schedule.slots[0].day in {
        Weekday.MONDAY,
        Weekday.WEDNESDAY,
        Weekday.FRIDAY,
    }


def test_key_spacing_remains_priority_over_weekend_preference() -> None:
    """La préférence week-end ne détruit pas l'espacement des séances clés."""

    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
            ),
        )
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SUNDAY,
        ),
    )

    long_slot = next(
        slot
        for slot in schedule.slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.LONG_ENDURANCE
        )
    )

    threshold_slot = next(
        slot
        for slot in schedule.slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.THRESHOLD
        )
    )

    assert long_slot.day is Weekday.SUNDAY
    assert threshold_slot.day is Weekday.MONDAY

def test_strength_can_share_day_with_easy_aerobic_when_days_are_limited() -> None:
    """Le renforcement peut partager la journée d'une EF.

    Cette règle permet de préserver le contenu hebdomadaire lorsque
    le nombre d'intentions dépasse le nombre de jours disponibles.

    Le renforcement reste une intention distincte : il partage
    uniquement le jour de planification avec l'EF.
    """

    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.VO2MAX,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=TrainingStimulus.AEROBIC_EASY,
                priority=StimulusPriority.SUPPORT,
            ),
            create_requirement(
                stimulus=TrainingStimulus.STRENGTH_LOWER_BODY,
                priority=StimulusPriority.SUPPORT,
                preferred_modalities=(
                    TrainingModality.STRENGTH,
                ),
            ),
        ),
        target_load=400.0,
        reference_load=500.0,
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.SUNDAY,
        ),
    )

    assert schedule.session_count == 4

    assert schedule.constrained is False

    assert schedule.omitted_intents == ()

    easy_slot = next(
        slot
        for slot in schedule.slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.AEROBIC_EASY
        )
    )

    strength_slot = next(
        slot
        for slot in schedule.slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.STRENGTH_LOWER_BODY
        )
    )

    assert strength_slot.day is easy_slot.day

def test_strength_does_not_share_day_with_vo2max() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.VO2MAX,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=TrainingStimulus.STRENGTH_LOWER_BODY,
                priority=StimulusPriority.SUPPORT,
                preferred_modalities=(
                    TrainingModality.STRENGTH,
                ),
            ),
        ),
        target_load=400.0,
        reference_load=500.0,
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
        ),
    )

    assert schedule.session_count == 1
    assert schedule.constrained is True

    assert (
        schedule.slots[0].intent.primary_stimulus
        is TrainingStimulus.VO2MAX
    )

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.STRENGTH_LOWER_BODY
        for intent in schedule.omitted_intents
    )


def test_strength_does_not_share_day_with_long_endurance() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=TrainingStimulus.STRENGTH_LOWER_BODY,
                priority=StimulusPriority.SUPPORT,
                preferred_modalities=(
                    TrainingModality.STRENGTH,
                ),
            ),
        ),
        target_load=400.0,
        reference_load=500.0,
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.SUNDAY,
        ),
    )

    assert schedule.session_count == 1
    assert schedule.constrained is True

    assert (
        schedule.slots[0].intent.primary_stimulus
        is TrainingStimulus.LONG_ENDURANCE
    )

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.STRENGTH_LOWER_BODY
        for intent in schedule.omitted_intents
    )

def test_omitted_optional_intent_does_not_constrain_schedule() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=TrainingStimulus.AEROBIC_EASY,
                priority=StimulusPriority.SUPPORT,
            ),
        )
    )

    intents = tuple(
        replace(
            intent,
            required=False,
        )
        if (
            intent.primary_stimulus
            is TrainingStimulus.AEROBIC_EASY
        )
        else intent
        for intent in plan.intents
    )

    plan = replace(
        plan,
        intents=intents,
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
        ),
    )

    assert schedule.session_count == 1

    assert (
        schedule.slots[0].intent.primary_stimulus
        is TrainingStimulus.THRESHOLD
    )

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.AEROBIC_EASY
        and intent.required is False
        for intent in schedule.omitted_intents
    )

    assert schedule.constrained is False


def test_omitted_required_intent_constrains_schedule() -> None:
    plan = create_plan(
        (
            create_requirement(
                stimulus=TrainingStimulus.THRESHOLD,
                priority=StimulusPriority.KEY,
            ),
            create_requirement(
                stimulus=TrainingStimulus.AEROBIC_EASY,
                priority=StimulusPriority.SUPPORT,
            ),
        )
    )

    intents = tuple(
        replace(
            intent,
            required=True,
        )
        if (
            intent.primary_stimulus
            is TrainingStimulus.AEROBIC_EASY
        )
        else intent
        for intent in plan.intents
    )

    plan = replace(
        plan,
        intents=intents,
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
        ),
    )

    assert schedule.session_count == 1

    assert any(
        intent.primary_stimulus
        is TrainingStimulus.AEROBIC_EASY
        and intent.required is True
        for intent in schedule.omitted_intents
    )

    assert schedule.constrained is True
