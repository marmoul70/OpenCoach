from __future__ import annotations

from dataclasses import replace

import pytest

from opencoach.coaching.weekly_adaptation import (
    WeeklyAdaptationDecision,
    WeeklyIntensityPolicy,
    WeeklyLongRunPolicy,
    WeeklyStrengthPolicy,
)
from opencoach.coaching.weekly_adaptation_planning import (
    build_weekly_trajectory_adjustment,
)
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
)
from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
    ProgressionAdjustment,
)
from opencoach.coaching.weekly_debrief import (
    WeeklyAdaptationDirection,
)


def _decision(
    *,
    load_factor: float = 1.0,
    volume_factor: float = 1.0,
    load_adjustment=LoadAdjustment.MAINTAIN,
    progression=ProgressionAdjustment.CONTINUE,
    intensity=WeeklyIntensityPolicy.MAINTAIN,
    long_run=WeeklyLongRunPolicy.MAINTAIN,
    strength=WeeklyStrengthPolicy.MAINTAIN,
) -> WeeklyAdaptationDecision:
    return WeeklyAdaptationDecision(
        direction=WeeklyAdaptationDirection.MAINTAIN,
        load_adjustment=load_adjustment,
        progression_adjustment=progression,
        load_factor=load_factor,
        volume_factor=volume_factor,
        maximum_progression_rate=0.10,
        intensity_policy=intensity,
        long_run_policy=long_run,
        strength_policy=strength,
        allow_missed_volume_catchup=False,
        reason="Test T6.4",
        guardrails=("Pas de rattrapage.",),
    )


def test_maintain_does_not_suppress_stimuli() -> None:
    adjustment = build_weekly_trajectory_adjustment(
        _decision()
    )

    assert adjustment.suppressed_stimuli == ()
    assert adjustment.load is LoadAdjustment.MAINTAIN
    assert (
        adjustment.progression
        is ProgressionAdjustment.CONTINUE
    )


def test_reduce_intensity_removes_only_highest_intensity() -> None:
    adjustment = build_weekly_trajectory_adjustment(
        _decision(
            load_factor=0.90,
            volume_factor=0.90,
            load_adjustment=(
                LoadAdjustment.REDUCE_SLIGHTLY
            ),
            progression=ProgressionAdjustment.SLOW,
            intensity=WeeklyIntensityPolicy.REDUCE,
        )
    )

    assert TrainingStimulus.VO2MAX in (
        adjustment.suppressed_stimuli
    )

    assert TrainingStimulus.SPEED_DEVELOPMENT in (
        adjustment.suppressed_stimuli
    )

    assert TrainingStimulus.THRESHOLD not in (
        adjustment.suppressed_stimuli
    )


def test_recovery_only_removes_quality_but_not_recovery() -> None:
    adjustment = build_weekly_trajectory_adjustment(
        _decision(
            load_factor=0.75,
            volume_factor=0.75,
            load_adjustment=LoadAdjustment.REDUCE,
            progression=ProgressionAdjustment.PAUSE,
            intensity=(
                WeeklyIntensityPolicy.RECOVERY_ONLY
            ),
        )
    )

    assert TrainingStimulus.THRESHOLD in (
        adjustment.suppressed_stimuli
    )

    assert TrainingStimulus.RACE_SPECIFIC in (
        adjustment.suppressed_stimuli
    )

    assert TrainingStimulus.RECOVERY not in (
        adjustment.suppressed_stimuli
    )

    assert TrainingStimulus.PRE_RACE_ACTIVATION not in (
        adjustment.suppressed_stimuli
    )


def test_optional_long_run_suppresses_long_endurance() -> None:
    adjustment = build_weekly_trajectory_adjustment(
        _decision(
            long_run=WeeklyLongRunPolicy.OPTIONAL,
        )
    )

    assert TrainingStimulus.LONG_ENDURANCE in (
        adjustment.suppressed_stimuli
    )


def test_strength_reduction_preserves_core_support() -> None:
    adjustment = build_weekly_trajectory_adjustment(
        _decision(
            strength=WeeklyStrengthPolicy.REDUCE,
        )
    )

    assert TrainingStimulus.STRENGTH_LOWER_BODY in (
        adjustment.suppressed_stimuli
    )

    assert TrainingStimulus.STRENGTH_CORE not in (
        adjustment.suppressed_stimuli
    )


def test_bridge_never_enables_schedule_compression() -> None:
    adjustment = build_weekly_trajectory_adjustment(
        _decision()
    )

    assert not adjustment.allow_schedule_compression


def test_progression_cap_uses_trajectory_reference() -> None:
    from opencoach.coaching.weekly_adaptation_planning import (
        _apply_maximum_progression_rate,
    )

    assert _apply_maximum_progression_rate(
        target_load=351.54249728,
        progression_reference_before=338.021632,
        maximum_progression_rate=0.0,
    ) == pytest.approx(
        338.021632
    )


def test_progression_cap_preserves_native_progression_under_ten_percent() -> None:
    from opencoach.coaching.weekly_adaptation_planning import (
        _apply_maximum_progression_rate,
    )

    assert _apply_maximum_progression_rate(
        target_load=351.54249728,
        progression_reference_before=338.021632,
        maximum_progression_rate=0.10,
    ) == pytest.approx(
        351.54249728
    )


def test_progression_cap_never_cancels_existing_reduction() -> None:
    from opencoach.coaching.weekly_adaptation_planning import (
        _apply_maximum_progression_rate,
    )

    assert _apply_maximum_progression_rate(
        target_load=316.388247552,
        progression_reference_before=338.021632,
        maximum_progression_rate=0.0,
    ) == pytest.approx(
        316.388247552
    )


def test_progression_cap_limits_abnormal_positive_progression() -> None:
    from opencoach.coaching.weekly_adaptation_planning import (
        _apply_maximum_progression_rate,
    )

    assert _apply_maximum_progression_rate(
        target_load=390.0,
        progression_reference_before=338.021632,
        maximum_progression_rate=0.10,
    ) == pytest.approx(
        371.8237952
    )
