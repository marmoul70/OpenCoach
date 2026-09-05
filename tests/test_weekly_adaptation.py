from __future__ import annotations
from dataclasses import replace
from datetime import date
import pytest
from opencoach.coaching.weekly_adaptation import WeeklyAdaptationDecision, WeeklyIntensityPolicy, WeeklyLongRunPolicy, WeeklyStrengthPolicy, build_weekly_adaptation_decision
from opencoach.coaching.weekly_debrief import WeeklyAdaptationDirection, WeeklyDebrief, WeeklyDebriefFacts, WeeklyDebriefVerdict
from opencoach.planning.trajectory.adjustment import LoadAdjustment, ProgressionAdjustment

def _facts() -> WeeklyDebriefFacts:
    return WeeklyDebriefFacts(week_start=date(2026, 8, 31), week_end=date(2026, 9, 6), planned_sessions=5, completed_sessions=5, skipped_sessions=0, supplementary_sessions=0, planned_duration_minutes=300.0, actual_duration_minutes=300.0, planned_load=500.0, actual_load=500.0, key_sessions_planned=2, key_sessions_completed=2, history_confidence=1.0)

def _debrief(*, verdict: WeeklyDebriefVerdict, direction: WeeklyAdaptationDirection) -> WeeklyDebrief:
    return WeeklyDebrief(week_start=_facts().week_start, week_end=_facts().week_end, verdict=verdict, adaptation_direction=direction, overall_score=90.0, adherence_score=100.0, duration_score=100.0, load_score=100.0, key_sessions_score=100.0, intensity_score=100.0, completion_ratio=1.0, duration_ratio=1.0, load_ratio=1.0, headline='Test', analysis='Test', strengths=('Test',), warnings=())

@pytest.mark.parametrize(('verdict', 'direction', 'load_adjustment', 'progression', 'load_factor', 'volume_factor', 'maximum_progression_rate'), [(WeeklyDebriefVerdict.VERY_PRODUCTIVE, WeeklyAdaptationDirection.PROGRESS, LoadAdjustment.MAINTAIN, ProgressionAdjustment.CONTINUE, 1.0, 1.0, 0.1), (WeeklyDebriefVerdict.PRODUCTIVE, WeeklyAdaptationDirection.MAINTAIN, LoadAdjustment.MAINTAIN, ProgressionAdjustment.CONTINUE, 1.0, 1.0, 0.1), (WeeklyDebriefVerdict.CORRECT, WeeklyAdaptationDirection.MAINTAIN, LoadAdjustment.MAINTAIN, ProgressionAdjustment.CONTINUE, 1.0, 1.0, 0.1), (WeeklyDebriefVerdict.PARTIALLY_COMPLIANT, WeeklyAdaptationDirection.REDUCE, LoadAdjustment.REDUCE_SLIGHTLY, ProgressionAdjustment.SLOW, 0.9, 0.9, 0.0), (WeeklyDebriefVerdict.INSUFFICIENT, WeeklyAdaptationDirection.RECOVER, LoadAdjustment.REDUCE, ProgressionAdjustment.PAUSE, 0.8, 0.8, 0.0), (WeeklyDebriefVerdict.OVERLOAD, WeeklyAdaptationDirection.RECOVER, LoadAdjustment.REDUCE, ProgressionAdjustment.PAUSE, 0.75, 0.75, 0.0), (WeeklyDebriefVerdict.UNKNOWN, WeeklyAdaptationDirection.OBSERVE, LoadAdjustment.MAINTAIN, ProgressionAdjustment.PAUSE, 1.0, 1.0, 0.0)])
def test_decision_matrix(verdict, direction, load_adjustment, progression, load_factor, volume_factor, maximum_progression_rate) -> None:
    decision = build_weekly_adaptation_decision(_debrief(verdict=verdict, direction=direction))
    assert decision.direction is direction
    assert decision.load_adjustment is load_adjustment
    assert decision.progression_adjustment is progression
    assert decision.load_factor == load_factor
    assert decision.volume_factor == volume_factor
    assert decision.maximum_progression_rate == maximum_progression_rate

def test_progress_does_not_add_a_second_progression_factor() -> None:
    decision = build_weekly_adaptation_decision(_debrief(verdict=WeeklyDebriefVerdict.VERY_PRODUCTIVE, direction=WeeklyAdaptationDirection.PROGRESS))
    assert decision.load_factor == 1.0
    assert decision.volume_factor == 1.0
    assert decision.load_adjustment is LoadAdjustment.MAINTAIN
    assert decision.intensity_policy is WeeklyIntensityPolicy.PROTECT_KEY
    assert decision.long_run_policy is WeeklyLongRunPolicy.PROTECT

def test_partial_week_never_requests_catchup() -> None:
    decision = build_weekly_adaptation_decision(_debrief(verdict=WeeklyDebriefVerdict.PARTIALLY_COMPLIANT, direction=WeeklyAdaptationDirection.REDUCE))
    assert not decision.allow_missed_volume_catchup
    assert decision.maximum_progression_rate == 0.0

def test_overload_forces_recovery_policy() -> None:
    decision = build_weekly_adaptation_decision(_debrief(verdict=WeeklyDebriefVerdict.OVERLOAD, direction=WeeklyAdaptationDirection.RECOVER))
    assert decision.load_factor == 0.75
    assert decision.volume_factor == 0.75
    assert decision.intensity_policy is WeeklyIntensityPolicy.RECOVERY_ONLY
    assert decision.long_run_policy is WeeklyLongRunPolicy.OPTIONAL
    assert decision.strength_policy is WeeklyStrengthPolicy.REDUCE

def test_unknown_week_freezes_progression() -> None:
    decision = build_weekly_adaptation_decision(_debrief(verdict=WeeklyDebriefVerdict.UNKNOWN, direction=WeeklyAdaptationDirection.OBSERVE))
    assert decision.progression_adjustment is ProgressionAdjustment.PAUSE
    assert decision.maximum_progression_rate == 0.0

def test_inconsistent_debrief_is_rejected() -> None:
    debrief = _debrief(verdict=WeeklyDebriefVerdict.OVERLOAD, direction=WeeklyAdaptationDirection.MAINTAIN)
    with pytest.raises(ValueError, match='incohérents'):
        build_weekly_adaptation_decision(debrief)

def test_decision_rejects_factor_above_one() -> None:
    decision = build_weekly_adaptation_decision(_debrief(verdict=WeeklyDebriefVerdict.CORRECT, direction=WeeklyAdaptationDirection.MAINTAIN))
    with pytest.raises(ValueError, match='load_factor'):
        replace(decision, load_factor=1.01)

def test_decision_rejects_catchup_policy() -> None:
    decision = build_weekly_adaptation_decision(_debrief(verdict=WeeklyDebriefVerdict.CORRECT, direction=WeeklyAdaptationDirection.MAINTAIN))
    with pytest.raises(ValueError, match='rattraper'):
        replace(decision, allow_missed_volume_catchup=True)

def test_all_decisions_have_guardrails() -> None:
    for verdict, direction in ((WeeklyDebriefVerdict.VERY_PRODUCTIVE, WeeklyAdaptationDirection.PROGRESS), (WeeklyDebriefVerdict.PRODUCTIVE, WeeklyAdaptationDirection.MAINTAIN), (WeeklyDebriefVerdict.CORRECT, WeeklyAdaptationDirection.MAINTAIN), (WeeklyDebriefVerdict.PARTIALLY_COMPLIANT, WeeklyAdaptationDirection.REDUCE), (WeeklyDebriefVerdict.INSUFFICIENT, WeeklyAdaptationDirection.RECOVER), (WeeklyDebriefVerdict.OVERLOAD, WeeklyAdaptationDirection.RECOVER), (WeeklyDebriefVerdict.UNKNOWN, WeeklyAdaptationDirection.OBSERVE)):
        decision = build_weekly_adaptation_decision(_debrief(verdict=verdict, direction=direction))
        assert decision.guardrails
        assert not decision.allow_missed_volume_catchup

def test_domain_object_can_be_constructed_directly() -> None:
    decision = WeeklyAdaptationDecision(direction=WeeklyAdaptationDirection.MAINTAIN, load_adjustment=LoadAdjustment.MAINTAIN, progression_adjustment=ProgressionAdjustment.CONTINUE, load_factor=1.0, volume_factor=1.0, maximum_progression_rate=0.1, intensity_policy=WeeklyIntensityPolicy.MAINTAIN, long_run_policy=WeeklyLongRunPolicy.MAINTAIN, strength_policy=WeeklyStrengthPolicy.MAINTAIN, allow_missed_volume_catchup=False, reason='Trajectoire maintenue.', guardrails=('Pas de rattrapage.',))
    assert decision.volume_factor == 1.0