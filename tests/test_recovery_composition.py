from datetime import date
from types import SimpleNamespace

from opencoach.planning.stimulus.training import (
    StimulusLoadCategory,
)
from opencoach.planning.trajectory.load_recovery_cycle import (
    RecoveryTrigger,
    decide_load_recovery,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
)
from opencoach.planning.weekly.training_envelope_builder import (
    _apply_post_race_recovery,
    _apply_recovery_factor,
)


def test_fatigue_reduces_weekly_load() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BUILD,
        loading_weeks_since_recovery=1,
        fatigue_requires_recovery=True,
    )

    assert decision.recovery_week
    assert (
        decision.trigger
        is RecoveryTrigger.FATIGUE
    )

    load_target = SimpleNamespace(
        target_load=300.0,
        load_min=270.0,
        load_max=330.0,
    )

    adjusted = _apply_recovery_factor(
        load_target=load_target,
        recovery=decision,
    )

    assert adjusted.target_load == 225.0
    assert adjusted.load_min == 202.5
    assert adjusted.load_max == 247.5


def test_fatigue_has_priority_over_event_recovery() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BUILD,
        loading_weeks_since_recovery=1,
        fatigue_requires_recovery=True,
        event_requires_recovery=True,
    )

    assert decision.recovery_week

    assert (
        decision.trigger
        is RecoveryTrigger.FATIGUE
    )


def test_post_race_recovery_controls_daily_capacity() -> None:
    capacities = _apply_post_race_recovery(
        week_start=date(
            2026,
            9,
            7,
        ),
        available_days=(
            Weekday.WEDNESDAY,
        ),
        day_capacities=(),
        recovery_dates=(
            date(2026, 9, 7),
            date(2026, 9, 8),
            date(2026, 9, 9),
            date(2026, 9, 10),
            date(2026, 9, 11),
            date(2026, 9, 12),
        ),
    )

    capacity = capacities[0]

    # Mercredi = J+3.
    assert (
        capacity.max_duration_minutes
        == 45
    )

    assert capacity.allows_load_category(
        StimulusLoadCategory.ENDURANCE
    )

    assert capacity.allows_load_category(
        StimulusLoadCategory.SUPPORT
    )

    assert not capacity.allows_load_category(
        StimulusLoadCategory.QUALITY
    )

    assert not capacity.allows_load_category(
        StimulusLoadCategory.STRENGTH
    )


def test_weekly_and_daily_recovery_are_complementary() -> None:
    """La fatigue réduit la semaine sans supprimer les règles post-course."""

    decision = decide_load_recovery(
        phase=TrainingPhase.BUILD,
        loading_weeks_since_recovery=2,
        fatigue_requires_recovery=True,
    )

    assert decision.recovery_week
    assert decision.load_factor < 1.0

    capacities = _apply_post_race_recovery(
        week_start=date(
            2026,
            9,
            7,
        ),
        available_days=(
            Weekday.MONDAY,
            Weekday.WEDNESDAY,
            Weekday.FRIDAY,
        ),
        day_capacities=(),
        recovery_dates=(
            date(2026, 9, 7),
            date(2026, 9, 8),
            date(2026, 9, 9),
            date(2026, 9, 10),
            date(2026, 9, 11),
            date(2026, 9, 12),
        ),
    )

    by_day = {
        capacity.day: capacity
        for capacity in capacities
    }

    # J+1 : socle protecteur incompressible.
    monday = by_day[
        Weekday.MONDAY
    ]

    assert (
        monday.max_duration_minutes
        == 30
    )

    assert not monday.allows_load_category(
        StimulusLoadCategory.ENDURANCE
    )

    # J+3 : reprise possible mais contrôlée.
    wednesday = by_day[
        Weekday.WEDNESDAY
    ]

    assert (
        wednesday.max_duration_minutes
        == 45
    )

    assert wednesday.allows_load_category(
        StimulusLoadCategory.ENDURANCE
    )

    assert not wednesday.allows_load_category(
        StimulusLoadCategory.QUALITY
    )

    # J+5 : endurance possible, qualité toujours protégée.
    friday = by_day[
        Weekday.FRIDAY
    ]

    assert (
        friday.max_duration_minutes
        == 60
    )

    assert friday.allows_load_category(
        StimulusLoadCategory.ENDURANCE
    )

    assert not friday.allows_load_category(
        StimulusLoadCategory.QUALITY
    )
