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


def create_strength_requirement():
    return TrainingStimulusRequirement(
        stimulus=(
            TrainingStimulus.STRENGTH_LOWER_BODY
        ),
        priority=StimulusPriority.IMPORTANT,
        specificity=SpecificityLevel.MODERATE,
        substitution=SubstitutionPolicy.ALLOWED,
        preferred_modalities=(
            TrainingModality.STRENGTH,
        ),
        duration_min_minutes=25,
        duration_max_minutes=45,
    )


def create_threshold_requirement():
    return TrainingStimulusRequirement(
        stimulus=TrainingStimulus.THRESHOLD,
        priority=StimulusPriority.KEY,
        specificity=SpecificityLevel.HIGH,
        substitution=SubstitutionPolicy.CONDITIONAL,
        preferred_modalities=(
            TrainingModality.RUNNING,
            TrainingModality.TRAIL_RUNNING,
        ),
        duration_min_minutes=45,
        duration_max_minutes=90,
    )


def test_strength_slot_can_preserve_future_key_session() -> None:
    slot = WeeklyStimulusSlot(
        slot_id="strength-tuesday",
        day=Weekday.TUESDAY,
        requirement=create_strength_requirement(),
        importance=SlotImportance.SUPPORT,
        fatigue_budget=FatigueBudget.MODERATE,
        duration_available_minutes=40,
        preserve_next_key_session=True,
    )

    assert slot.day is Weekday.TUESDAY

    assert (
        slot.preserve_next_key_session
        is True
    )

    assert (
        slot.fatigue_budget
        is FatigueBudget.MODERATE
    )


def test_threshold_can_be_key_session() -> None:
    slot = WeeklyStimulusSlot(
        slot_id="threshold-thursday",
        day=Weekday.THURSDAY,
        requirement=create_threshold_requirement(),
        importance=SlotImportance.KEY,
        fatigue_budget=FatigueBudget.HIGH,
        duration_available_minutes=75,
        preferred_recovery_before_hours=36,
        preferred_recovery_after_hours=36,
    )

    assert (
        slot.importance
        is SlotImportance.KEY
    )

    assert (
        slot.requirement.stimulus
        is TrainingStimulus.THRESHOLD
    )


def test_slot_id_cannot_be_empty() -> None:
    with pytest.raises(
        ValueError,
        match="identifiant",
    ):
        WeeklyStimulusSlot(
            slot_id="",
            day=Weekday.MONDAY,
            requirement=create_strength_requirement(),
            importance=SlotImportance.SUPPORT,
            fatigue_budget=FatigueBudget.LOW,
        )


@pytest.mark.parametrize(
    "duration",
    [
        0,
        -1,
    ],
)
def test_available_duration_must_be_positive(
    duration: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="strictement positive",
    ):
        WeeklyStimulusSlot(
            slot_id="invalid-duration",
            day=Weekday.TUESDAY,
            requirement=create_strength_requirement(),
            importance=SlotImportance.SUPPORT,
            fatigue_budget=FatigueBudget.LOW,
            duration_available_minutes=duration,
        )


def test_available_duration_must_fit_stimulus() -> None:
    with pytest.raises(
        ValueError,
        match="insuffisante",
    ):
        WeeklyStimulusSlot(
            slot_id="too-short",
            day=Weekday.TUESDAY,
            requirement=create_strength_requirement(),
            importance=SlotImportance.SUPPORT,
            fatigue_budget=FatigueBudget.LOW,
            duration_available_minutes=20,
        )


@pytest.mark.parametrize(
    "hours",
    [
        -1,
        -12,
    ],
)
def test_recovery_before_cannot_be_negative(
    hours: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="avant",
    ):
        WeeklyStimulusSlot(
            slot_id="invalid-recovery-before",
            day=Weekday.WEDNESDAY,
            requirement=create_threshold_requirement(),
            importance=SlotImportance.KEY,
            fatigue_budget=FatigueBudget.HIGH,
            preferred_recovery_before_hours=hours,
        )


@pytest.mark.parametrize(
    "hours",
    [
        -1,
        -12,
    ],
)
def test_recovery_after_cannot_be_negative(
    hours: int,
) -> None:
    with pytest.raises(
        ValueError,
        match="après",
    ):
        WeeklyStimulusSlot(
            slot_id="invalid-recovery-after",
            day=Weekday.THURSDAY,
            requirement=create_threshold_requirement(),
            importance=SlotImportance.KEY,
            fatigue_budget=FatigueBudget.HIGH,
            preferred_recovery_after_hours=hours,
        )
