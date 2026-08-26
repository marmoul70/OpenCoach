from datetime import date

from opencoach.planning.sessions.intent_builder import (
    SessionIntentPlan,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.planning.stimulus.weekly_demand import (
    StimulusDemandDensity,
    WeeklyStimulusDemand,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope_builder import (
    _inject_pre_race_activation,
)
from opencoach.planning.weekly.session_intent_scheduler import (
    schedule_session_intents,
)


def empty_plan() -> SessionIntentPlan:
    return SessionIntentPlan(
        intents=(),
        source_demand=WeeklyStimulusDemand(
            phase=TrainingPhase.BUILD,
            week_type=TrajectoryWeekType.LOADING,
            target_load=200.0,
            reference_load=200.0,
            load_ratio=1.0,
            density=StimulusDemandDensity.MODERATE,
            demands=(),
            maximum_key_exposures=2,
            maximum_quality_exposures=2,
        ),
        represented_stimuli=(),
        unrepresented_stimuli=(),
    )


def activation_intent(
    plan: SessionIntentPlan,
):
    return next(
        intent
        for intent in plan.intents
        if (
            intent.primary_stimulus
            is TrainingStimulus
            .PRE_RACE_ACTIVATION
        )
    )


def test_sunday_race_prefers_friday_activation() -> None:
    plan = _inject_pre_race_activation(
        plan=empty_plan(),
        week_start=date(
            2026,
            8,
            24,
        ),
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
        ),
        reserved_race_dates=(
            date(
                2026,
                8,
                30,
            ),
        ),
        protection_dates=(
            date(
                2026,
                8,
                27,
            ),
        ),
    )

    intent = activation_intent(
        plan
    )

    assert intent.preferred_days == (
        Weekday.FRIDAY.value,
        Weekday.SATURDAY.value,
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

    assert (
        schedule.slots[0].day
        is Weekday.FRIDAY
    )


def test_sunday_race_uses_saturday_when_friday_unavailable(
) -> None:
    plan = _inject_pre_race_activation(
        plan=empty_plan(),
        week_start=date(
            2026,
            8,
            24,
        ),
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.SATURDAY,
        ),
        reserved_race_dates=(
            date(
                2026,
                8,
                30,
            ),
        ),
        protection_dates=(
            date(
                2026,
                8,
                27,
            ),
        ),
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.SATURDAY,
        ),
    )

    assert (
        schedule.slots[0].day
        is Weekday.SATURDAY
    )


def test_activation_is_not_created_without_j1_or_j2(
) -> None:
    plan = _inject_pre_race_activation(
        plan=empty_plan(),
        week_start=date(
            2026,
            8,
            24,
        ),
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
        ),
        reserved_race_dates=(
            date(
                2026,
                8,
                30,
            ),
        ),
        protection_dates=(
            date(
                2026,
                8,
                27,
            ),
        ),
    )

    assert plan.intents == ()


def test_small_race_without_protection_has_no_activation(
) -> None:
    plan = _inject_pre_race_activation(
        plan=empty_plan(),
        week_start=date(
            2026,
            8,
            24,
        ),
        available_days=(
            Weekday.FRIDAY,
            Weekday.SATURDAY,
        ),
        reserved_race_dates=(
            date(
                2026,
                8,
                30,
            ),
        ),
        protection_dates=(),
    )

    assert plan.intents == ()
