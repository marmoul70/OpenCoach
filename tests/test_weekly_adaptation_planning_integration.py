"""Tests d'intégration T6.4 du débrief hebdomadaire."""

from __future__ import annotations

from dataclasses import replace
from datetime import date
from uuid import uuid4

import pytest

from opencoach.coaching.generation import (
    GeneratePlannedTrainingWeekService,
)
from opencoach.coaching.weekly_adaptation import (
    build_weekly_adaptation_decision,
)
from opencoach.coaching.weekly_debrief import (
    WeeklyAdaptationDirection,
    WeeklyDebrief,
    WeeklyDebriefVerdict,
)
from opencoach.planning.stimulus.training import (
    StimulusLoadCategory,
    TrainingStimulus,
    stimulus_load_category,
)

from test_generate_planned_training_week_service import (
    FakeGenerateAndPersistService,
    create_planning_input,
)


def _debrief(
    *,
    verdict: WeeklyDebriefVerdict,
    direction: WeeklyAdaptationDirection,
    score: int,
) -> WeeklyDebrief:
    return WeeklyDebrief(
        week_start=date(2027, 6, 28),
        week_end=date(2027, 7, 4),
        verdict=verdict,
        adaptation_direction=direction,
        overall_score=score,
        adherence_score=score,
        duration_score=score,
        load_score=score,
        key_sessions_score=score,
        intensity_score=score,
        completion_ratio=1.0,
        duration_ratio=1.0,
        load_ratio=1.0,
        headline="Test T6.4.2",
        analysis="Test intégration planning.",
        strengths=(),
        warnings=(),
    )


def _execute(
    debrief: WeeklyDebrief | None = None,
):
    planning_input = replace(
        create_planning_input(),
        reference_weekly_duration_minutes=300.0,
        long_endurance_reference_minutes=120.0,
    )

    generator = FakeGenerateAndPersistService()

    service = GeneratePlannedTrainingWeekService(
        generation_service=generator,
    )

    decision = (
        None
        if debrief is None
        else build_weekly_adaptation_decision(
            debrief
        )
    )

    result = service.execute(
        athlete_profile_id=uuid4(),
        planning_input=planning_input,
        weekly_adaptation=decision,
    )

    assert len(generator.calls) == 1

    envelope = generator.calls[0]["envelope"]

    assert (
        envelope
        is result.planning.coaching.envelope
    )

    return envelope


def _stimuli(
    envelope,
) -> set[TrainingStimulus]:
    stimuli: set[TrainingStimulus] = set()

    for slot in envelope.session_slots:
        stimuli.update(
            slot.intent.stimuli
        )

    return stimuli


def _quality_stimuli(
    envelope,
) -> set[TrainingStimulus]:
    return {
        stimulus
        for stimulus in _stimuli(envelope)
        if (
            stimulus_load_category(stimulus)
            is StimulusLoadCategory.QUALITY
        )
    }


def test_productive_preserves_baseline() -> None:
    baseline = _execute()

    adapted = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.PRODUCTIVE,
            direction=WeeklyAdaptationDirection.MAINTAIN,
            score=85,
        )
    )

    assert adapted.target_load == baseline.target_load

    assert (
        adapted.target_duration_minutes
        == baseline.target_duration_minutes
    )

    assert (
        adapted.long_endurance_reference_minutes
        == baseline.long_endurance_reference_minutes
    )

    assert _stimuli(adapted) == _stimuli(baseline)


def test_very_productive_does_not_double_progress() -> None:
    baseline = _execute()

    adapted = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.VERY_PRODUCTIVE,
            direction=WeeklyAdaptationDirection.PROGRESS,
            score=95,
        )
    )

    assert adapted.target_load == baseline.target_load

    assert (
        adapted.target_duration_minutes
        == baseline.target_duration_minutes
    )


def test_partially_compliant_reduces_to_90_percent() -> None:
    baseline = _execute()

    adapted = _execute(
        _debrief(
            verdict=(
                WeeklyDebriefVerdict.PARTIALLY_COMPLIANT
            ),
            direction=WeeklyAdaptationDirection.REDUCE,
            score=60,
        )
    )

    assert adapted.target_load == pytest.approx(
        baseline.target_load * 0.90
    )

    assert adapted.target_duration_minutes == pytest.approx(
        round(
            baseline.target_duration_minutes
            * 0.90,
            1,
        )
    )

    assert not _quality_stimuli(adapted)


def test_insufficient_uses_75_load_80_volume() -> None:
    baseline = _execute()

    adapted = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.INSUFFICIENT,
            direction=WeeklyAdaptationDirection.RECOVER,
            score=40,
        )
    )

    assert adapted.target_load == pytest.approx(
        baseline.target_load * 0.75
    )

    assert adapted.target_duration_minutes == pytest.approx(
        round(
            baseline.target_duration_minutes
            * 0.80,
            1,
        )
    )

    stimuli = _stimuli(adapted)

    assert not _quality_stimuli(adapted)

    assert (
        TrainingStimulus.LONG_ENDURANCE
        not in stimuli
    )

    assert (
        TrainingStimulus.STRENGTH_LOWER_BODY
        not in stimuli
    )


def test_overload_uses_75_load_75_volume() -> None:
    baseline = _execute()

    adapted = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.OVERLOAD,
            direction=WeeklyAdaptationDirection.RECOVER,
            score=40,
        )
    )

    assert adapted.target_load == pytest.approx(
        baseline.target_load * 0.75
    )

    assert adapted.target_duration_minutes == pytest.approx(
        round(
            baseline.target_duration_minutes
            * 0.75,
            1,
        )
    )

    stimuli = _stimuli(adapted)

    assert not _quality_stimuli(adapted)

    assert (
        TrainingStimulus.LONG_ENDURANCE
        not in stimuli
    )

    assert (
        TrainingStimulus.STRENGTH_LOWER_BODY
        not in stimuli
    )


def test_overload_is_more_restrictive_than_insufficient() -> None:
    insufficient = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.INSUFFICIENT,
            direction=WeeklyAdaptationDirection.RECOVER,
            score=40,
        )
    )

    overload = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.OVERLOAD,
            direction=WeeklyAdaptationDirection.RECOVER,
            score=40,
        )
    )

    assert (
        overload.target_load
        == pytest.approx(
            insufficient.target_load
        )
    )

    assert (
        overload.target_duration_minutes
        < insufficient.target_duration_minutes
    )


def test_without_weekly_adaptation_keeps_historical_behavior() -> None:
    first = _execute()
    second = _execute()

    assert first.target_load == second.target_load

    assert (
        first.target_duration_minutes
        == second.target_duration_minutes
    )

    assert (
        first.long_endurance_reference_minutes
        == second.long_endurance_reference_minutes
    )

    assert _stimuli(first) == _stimuli(second)


def test_unknown_observe_freezes_native_progression() -> None:
    baseline = _execute()

    adapted = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.UNKNOWN,
            direction=WeeklyAdaptationDirection.OBSERVE,
            score=0,
        )
    )

    planning_input = create_planning_input()

    generator = FakeGenerateAndPersistService()

    service = GeneratePlannedTrainingWeekService(
        generation_service=generator,
    )

    raw_result = service.execute(
        athlete_profile_id=uuid4(),
        planning_input=planning_input,
    )

    trajectory_week = (
        raw_result.planning.coaching.trajectory_week
    )

    assert trajectory_week is not None

    assert adapted.target_load == pytest.approx(
        trajectory_week.progression_reference_before
    )

    assert adapted.target_load < baseline.target_load


def test_productive_progression_cap_preserves_baseline_exactly() -> None:
    baseline = _execute()

    adapted = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.PRODUCTIVE,
            direction=WeeklyAdaptationDirection.MAINTAIN,
            score=85,
        )
    )

    assert adapted.target_load == baseline.target_load
    assert adapted.load_min == baseline.load_min
    assert adapted.load_max == baseline.load_max


def test_very_productive_progression_cap_preserves_baseline_exactly() -> None:
    baseline = _execute()

    adapted = _execute(
        _debrief(
            verdict=WeeklyDebriefVerdict.VERY_PRODUCTIVE,
            direction=WeeklyAdaptationDirection.PROGRESS,
            score=95,
        )
    )

    assert adapted.target_load == baseline.target_load
    assert adapted.load_min == baseline.load_min
    assert adapted.load_max == baseline.load_max
