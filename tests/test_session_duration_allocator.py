"""Tests de l'allocation déterministe des durées hebdomadaires."""

from dataclasses import replace
from datetime import date

import pytest

from opencoach.planning.sessions.duration.allocator import (
    allocate_session_durations,
)
from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.stimulus.training import (
    SpecificityLevel,
    SubstitutionPolicy,
    TrainingModality,
    TrainingStimulus,
)
from opencoach.planning.weekly.session_intent_slot import (
    WeeklySessionIntentSlot,
)
from opencoach.planning.weekly.schedule_types import (
    FatigueBudget,
    Weekday,
)


def create_intent(
    *,
    stimulus=TrainingStimulus.AEROBIC_EASY,
    importance=SessionIntentImportance.SUPPORT,
    minimum=30,
    maximum=120,
):
    return SessionIntent(
        primary_stimulus=stimulus,
        secondary_stimuli=(),
        importance=importance,
        specificity=SpecificityLevel.LOW,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        required_modalities=(),
        duration_min_minutes=minimum,
        duration_max_minutes=maximum,
    )


def create_slot(
    *,
    slot_id,
    day,
    intent,
    available=None,
):
    return WeeklySessionIntentSlot(
        slot_id=slot_id,
        day=day,
        intent=intent,
        duration_available_minutes=available,
        fatigue_budget=FatigueBudget.MODERATE,
    )


def test_allocator_preserves_four_session_frequency():
    slots = tuple(
        create_slot(
            slot_id=f"session-{index}",
            day=day,
            intent=create_intent(),
        )
        for index, day in enumerate(
            (
                Weekday.MONDAY,
                Weekday.WEDNESDAY,
                Weekday.FRIDAY,
                Weekday.SUNDAY,
            ),
            start=1,
        )
    )

    result = allocate_session_durations(
        slots=slots,
        target_load=150.0,
    )

    assert len(result) == 4


def test_allocator_respects_intent_bounds():
    slot = create_slot(
        slot_id="session-1",
        day=Weekday.MONDAY,
        intent=create_intent(
            minimum=30,
            maximum=90,
        ),
    )

    result = allocate_session_durations(
        slots=(slot,),
        target_load=150.0,
    )

    assert 30 <= result[0].duration_minutes <= 90


def test_allocator_respects_day_capacity():
    slot = create_slot(
        slot_id="session-1",
        day=Weekday.MONDAY,
        intent=create_intent(
            minimum=30,
            maximum=120,
        ),
        available=50,
    )

    result = allocate_session_durations(
        slots=(slot,),
        target_load=150.0,
    )

    assert result[0].duration_minutes <= 50


def test_key_session_receives_more_time_than_support_session():
    support = create_slot(
        slot_id="support",
        day=Weekday.MONDAY,
        intent=create_intent(
            importance=SessionIntentImportance.SUPPORT,
        ),
    )

    key = create_slot(
        slot_id="key",
        day=Weekday.SUNDAY,
        intent=create_intent(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            importance=SessionIntentImportance.KEY,
        ),
    )

    result = allocate_session_durations(
        slots=(support, key),
        target_load=180.0,
    )

    durations = {
        item.slot_id: item.duration_minutes
        for item in result
    }

    assert durations["key"] > durations["support"]


def test_long_endurance_receives_more_time_than_easy_support():
    easy = create_slot(
        slot_id="easy",
        day=Weekday.MONDAY,
        intent=create_intent(),
    )

    long_run = create_slot(
        slot_id="long",
        day=Weekday.SUNDAY,
        intent=create_intent(
            stimulus=TrainingStimulus.LONG_ENDURANCE,
            importance=SessionIntentImportance.KEY,
        ),
    )

    result = allocate_session_durations(
        slots=(easy, long_run),
        target_load=180.0,
    )

    durations = {
        item.slot_id: item.duration_minutes
        for item in result
    }

    assert durations["long"] > durations["easy"]


def test_higher_target_load_increases_allocated_volume():
    slots = (
        create_slot(
            slot_id="easy",
            day=Weekday.MONDAY,
            intent=create_intent(),
        ),
        create_slot(
            slot_id="long",
            day=Weekday.SUNDAY,
            intent=create_intent(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                importance=SessionIntentImportance.KEY,
            ),
        ),
    )

    low = allocate_session_durations(
        slots=slots,
        target_load=100.0,
    )

    high = allocate_session_durations(
        slots=slots,
        target_load=200.0,
    )

    assert sum(
        item.duration_minutes
        for item in high
    ) > sum(
        item.duration_minutes
        for item in low
    )


def test_reference_weekly_duration_controls_total_volume() -> None:
    """Le volume historique pilote le budget de durée hebdomadaire."""

    slots = (
        create_slot(
            slot_id="session-1",
            day=Weekday.MONDAY,
            intent=create_intent(),
        ),
        create_slot(
            slot_id="session-2",
            day=Weekday.WEDNESDAY,
            intent=create_intent(),
        ),
        create_slot(
            slot_id="session-3",
            day=Weekday.FRIDAY,
            intent=create_intent(),
        ),
        create_slot(
            slot_id="session-4",
            day=Weekday.SUNDAY,
            intent=create_intent(),
        ),
    )

    short_week = allocate_session_durations(
        slots=slots,
        target_load=150.0,
        reference_weekly_duration_minutes=180.0,
    )

    long_week = allocate_session_durations(
        slots=slots,
        target_load=150.0,
        reference_weekly_duration_minutes=360.0,
    )

    assert sum(
        item.duration_minutes
        for item in long_week
    ) > sum(
        item.duration_minutes
        for item in short_week
    )


def test_reference_weekly_duration_must_be_positive() -> None:
    """Une référence temporelle invalide est refusée."""

    slots = (
        create_slot(
            slot_id="session-1",
            day=Weekday.MONDAY,
            intent=create_intent(),
        ),
    )

    with pytest.raises(
        ValueError,
        match="durée hebdomadaire",
    ):
        allocate_session_durations(
            slots=slots,
            target_load=150.0,
            reference_weekly_duration_minutes=0.0,
        )

def test_long_endurance_reference_reserves_long_run_before_distribution() -> None:
    """La baseline longue est prioritaire dans le budget hebdomadaire."""

    slots = (
        create_slot(
            slot_id="long",
            day=Weekday.MONDAY,
            intent=create_intent(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                importance=SessionIntentImportance.KEY,
                minimum=60,
                maximum=240,
            ),
        ),
        create_slot(
            slot_id="quality",
            day=Weekday.WEDNESDAY,
            intent=create_intent(
                importance=SessionIntentImportance.IMPORTANT,
                minimum=30,
                maximum=90,
            ),
        ),
        create_slot(
            slot_id="easy",
            day=Weekday.FRIDAY,
            intent=create_intent(
                minimum=30,
                maximum=90,
            ),
        ),
        create_slot(
            slot_id="support",
            day=Weekday.SUNDAY,
            intent=create_intent(
                minimum=30,
                maximum=90,
            ),
        ),
    )

    result = allocate_session_durations(
        slots=slots,
        target_load=185.0,
        reference_weekly_duration_minutes=255.0,
        long_endurance_reference_minutes=173.0,
    )

    durations = {
        item.slot_id: item.duration_minutes
        for item in result
    }

    assert durations["long"] == 165

    assert all(
        durations[slot_id] >= 30
        for slot_id in (
            "quality",
            "easy",
            "support",
        )
    )

    assert sum(durations.values()) == 255


def test_long_endurance_reference_respects_slot_maximum() -> None:
    """La baseline longue ne dépasse jamais le plafond du créneau."""

    slots = (
        create_slot(
            slot_id="long",
            day=Weekday.MONDAY,
            intent=create_intent(
                stimulus=TrainingStimulus.LONG_ENDURANCE,
                importance=SessionIntentImportance.KEY,
                minimum=60,
                maximum=140,
            ),
        ),
        create_slot(
            slot_id="easy",
            day=Weekday.WEDNESDAY,
            intent=create_intent(
                minimum=30,
                maximum=90,
            ),
        ),
    )

    result = allocate_session_durations(
        slots=slots,
        target_load=185.0,
        reference_weekly_duration_minutes=255.0,
        long_endurance_reference_minutes=173.0,
    )

    durations = {
        item.slot_id: item.duration_minutes
        for item in result
    }

    assert durations["long"] == 140