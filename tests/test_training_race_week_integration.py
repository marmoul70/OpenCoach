from datetime import date

from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.sessions.intent_builder import (
    SessionIntentPlan,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    StimulusLoadCategory,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
    stimulus_load_category,
)
from opencoach.planning.stimulus.weekly_demand import (
    StimulusDemandDensity,
    WeeklyStimulusDemand,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
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
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)
from opencoach.planning.weekly.training_envelope_builder import (
    _apply_race_protection,
    _inject_pre_race_activation,
)


def _empty_plan() -> SessionIntentPlan:
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


def _intent(
    *,
    stimulus: TrainingStimulus,
    importance: SessionIntentImportance,
    duration: int,
) -> SessionIntent:
    return SessionIntent(
        primary_stimulus=stimulus,
        secondary_stimuli=(),
        importance=importance,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        required_modalities=(),
        duration_min_minutes=duration,
        duration_max_minutes=duration,
        required=False,
    )


def test_critical_training_race_shapes_end_of_week() -> None:
    week_start = date(
        2026,
        8,
        24,
    )

    available_days = (
        Weekday.MONDAY,
        Weekday.WEDNESDAY,
        Weekday.THURSDAY,
        Weekday.FRIDAY,
        Weekday.SATURDAY,
    )

    plan = _empty_plan()

    plan = SessionIntentPlan(
        intents=(
            _intent(
                stimulus=TrainingStimulus.THRESHOLD,
                importance=SessionIntentImportance.KEY,
                duration=60,
            ),
            _intent(
                stimulus=TrainingStimulus.AEROBIC_EASY,
                importance=SessionIntentImportance.SUPPORT,
                duration=45,
            ),
            _intent(
                stimulus=TrainingStimulus.AEROBIC_EASY,
                importance=SessionIntentImportance.SUPPORT,
                duration=40,
            ),
        ),
        source_demand=plan.source_demand,
        represented_stimuli=(
            TrainingStimulus.THRESHOLD,
            TrainingStimulus.AEROBIC_EASY,
        ),
        unrepresented_stimuli=(),
    )

    plan = _inject_pre_race_activation(
        plan=plan,
        week_start=week_start,
        available_days=available_days,
        reserved_race_dates=(
            date(
                2026,
                8,
                30,
            ),
        ),
        protection_dates=(
            date(2026, 8, 24),
            date(2026, 8, 25),
            date(2026, 8, 26),
            date(2026, 8, 27),
            date(2026, 8, 28),
            date(2026, 8, 29),
        ),
    )

    capacities = _apply_race_protection(
        week_start=week_start,
        available_days=available_days,
        day_capacities=(),
        protection_dates=(
            date(2026, 8, 24),
            date(2026, 8, 25),
            date(2026, 8, 26),
            date(2026, 8, 27),
            date(2026, 8, 28),
            date(2026, 8, 29),
        ),
    )

    schedule = schedule_session_intents(
        plan=plan,
        available_days=available_days,
        day_capacities=capacities,
    )

    activation_slots = tuple(
        slot
        for slot in schedule.slots
        if (
            slot.intent.primary_stimulus
            is TrainingStimulus.PRE_RACE_ACTIVATION
        )
    )

    assert len(
        activation_slots
    ) == 1

    assert (
        activation_slots[0].day
        is Weekday.FRIDAY
    )

    for slot in schedule.slots:
        if slot.day in {
            Weekday.THURSDAY,
            Weekday.FRIDAY,
            Weekday.SATURDAY,
        }:
            assert (
                stimulus_load_category(
                    slot.intent.primary_stimulus
                )
                is not StimulusLoadCategory.QUALITY
            )

            assert (
                stimulus_load_category(
                    slot.intent.primary_stimulus
                )
                is not StimulusLoadCategory.STRENGTH
            )


def test_activation_remains_support_load() -> None:
    assert (
        stimulus_load_category(
            TrainingStimulus.PRE_RACE_ACTIVATION
        )
        is StimulusLoadCategory.SUPPORT
    )
