import pytest

from opencoach.planning.load_recovery_cycle import (
    LoadRecoveryDecision,
    LoadRecoveryPolicy,
    RecoveryTrigger,
    decide_load_recovery,
)
from opencoach.planning.weekly_training_envelope import (
    TrainingPhase,
)


def test_normal_loading_week_continues() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BASE,
        loading_weeks_since_recovery=1,
    )

    assert decision.recovery_week is False
    assert decision.trigger is RecoveryTrigger.NONE
    assert decision.load_factor == 1.0


def test_planned_recovery_after_loading_cycle() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BASE,
        loading_weeks_since_recovery=3,
    )

    assert decision.recovery_week is True
    assert decision.trigger is RecoveryTrigger.PLANNED
    assert decision.load_factor == pytest.approx(0.80)


def test_build_recovery_is_more_pronounced() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BUILD,
        loading_weeks_since_recovery=3,
    )

    assert decision.recovery_week is True
    assert decision.load_factor == pytest.approx(0.75)


def test_specific_phase_recovers_sooner() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.SPECIFIC,
        loading_weeks_since_recovery=2,
    )

    assert decision.recovery_week is True
    assert decision.trigger is RecoveryTrigger.PLANNED


def test_fatigue_can_trigger_early_recovery() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BUILD,
        loading_weeks_since_recovery=1,
        fatigue_requires_recovery=True,
    )

    assert decision.recovery_week is True
    assert decision.trigger is RecoveryTrigger.FATIGUE


def test_event_can_trigger_early_recovery() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BASE,
        loading_weeks_since_recovery=1,
        event_requires_recovery=True,
    )

    assert decision.recovery_week is True
    assert decision.trigger is RecoveryTrigger.EVENT


def test_fatigue_has_priority_over_event() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BUILD,
        loading_weeks_since_recovery=1,
        fatigue_requires_recovery=True,
        event_requires_recovery=True,
    )

    assert decision.trigger is RecoveryTrigger.FATIGUE


def test_phase_transition_can_trigger_recovery() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.BUILD,
        loading_weeks_since_recovery=1,
        phase_transition_requires_recovery=True,
    )

    assert decision.recovery_week is True

    assert (
        decision.trigger
        is RecoveryTrigger.PHASE_TRANSITION
    )


def test_taper_does_not_add_an_extra_recovery_cycle() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.TAPER,
        loading_weeks_since_recovery=3,
    )

    assert decision.recovery_week is False
    assert decision.load_factor == 1.0


def test_recovery_phase_does_not_add_recovery_again() -> None:
    decision = decide_load_recovery(
        phase=TrainingPhase.RECOVERY,
        loading_weeks_since_recovery=3,
    )

    assert decision.recovery_week is False


def test_negative_loading_weeks_are_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="ne peut pas être négatif",
    ):
        decide_load_recovery(
            phase=TrainingPhase.BASE,
            loading_weeks_since_recovery=-1,
        )


def test_invalid_recovery_factor_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="facteur de récupération",
    ):
        LoadRecoveryPolicy(
            phase=TrainingPhase.BASE,
            preferred_loading_weeks=3,
            recovery_factor=1.2,
        )


def test_recovery_decision_requires_trigger() -> None:
    with pytest.raises(
        ValueError,
        match="déclencheur",
    ):
        LoadRecoveryDecision(
            recovery_week=True,
            trigger=RecoveryTrigger.NONE,
            load_factor=0.8,
            loading_weeks_since_recovery=0,
        )
