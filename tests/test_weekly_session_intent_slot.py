import pytest

from opencoach.planning.session_intent import (
    SessionIntentImportance,
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
    Weekday,
)


def create_intent(
    *,
    duration_min_minutes: int | None = None,
):
    requirement = TrainingStimulusRequirement(
        stimulus=TrainingStimulus.AEROBIC_EASY,
        priority=StimulusPriority.SUPPORT,
        specificity=SpecificityLevel.LOW,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.RUNNING,
        ),
        duration_min_minutes=(
            duration_min_minutes
        ),
    )

    return build_session_intent(
        primary=requirement
    )


def test_slot_accepts_session_intent() -> None:
    intent = create_intent()

    slot = WeeklySessionIntentSlot(
        slot_id="session-1",
        day=Weekday.MONDAY,
        intent=intent,
        fatigue_budget=FatigueBudget.LOW,
    )

    assert slot.intent is intent

    assert (
        slot.day
        is Weekday.MONDAY
    )


def test_key_property_is_false_for_support() -> None:
    slot = WeeklySessionIntentSlot(
        slot_id="session-1",
        day=Weekday.MONDAY,
        intent=create_intent(),
        fatigue_budget=FatigueBudget.LOW,
    )

    assert slot.is_key is False


def test_empty_slot_id_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="identifiant",
    ):
        WeeklySessionIntentSlot(
            slot_id=" ",
            day=Weekday.MONDAY,
            intent=create_intent(),
            fatigue_budget=(
                FatigueBudget.LOW
            ),
        )


def test_insufficient_duration_is_rejected() -> None:
    intent = create_intent(
        duration_min_minutes=60,
    )

    with pytest.raises(
        ValueError,
        match="insuffisante",
    ):
        WeeklySessionIntentSlot(
            slot_id="session-1",
            day=Weekday.MONDAY,
            intent=intent,
            fatigue_budget=(
                FatigueBudget.LOW
            ),
            duration_available_minutes=45,
        )


def test_negative_recovery_before_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="avant",
    ):
        WeeklySessionIntentSlot(
            slot_id="session-1",
            day=Weekday.MONDAY,
            intent=create_intent(),
            fatigue_budget=(
                FatigueBudget.LOW
            ),
            preferred_recovery_before_hours=-1,
        )
