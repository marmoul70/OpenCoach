from datetime import date

import pytest

from opencoach.coaching.weekly_debrief import (
    WeeklyAdaptationDirection,
    WeeklyDebriefFacts,
    WeeklyDebriefVerdict,
    build_weekly_debrief,
)


WEEK_START = date(2026, 8, 31)
WEEK_END = date(2026, 9, 6)


def facts(**overrides: object) -> WeeklyDebriefFacts:
    values = {
        "week_start": WEEK_START,
        "week_end": WEEK_END,
        "planned_sessions": 5,
        "completed_sessions": 5,
        "skipped_sessions": 0,
        "supplementary_sessions": 0,
        "planned_duration_minutes": 300,
        "actual_duration_minutes": 300,
        "planned_load": 300.0,
        "actual_load": 300.0,
        "key_sessions_planned": 2,
        "key_sessions_completed": 2,
        "compliant_intensity_sessions": 4,
        "analyzed_intensity_sessions": 4,
        "history_confidence": 1.0,
    }
    values.update(overrides)
    return WeeklyDebriefFacts(**values)


def test_perfect_week_is_very_productive() -> None:
    result = build_weekly_debrief(facts())

    assert result.overall_score == 100
    assert result.verdict is WeeklyDebriefVerdict.VERY_PRODUCTIVE
    assert (
        result.adaptation_direction
        is WeeklyAdaptationDirection.PROGRESS
    )
    assert result.adherence_score == 100
    assert result.key_sessions_score == 100
    assert result.intensity_score == 100


def test_productive_week_can_miss_secondary_session() -> None:
    result = build_weekly_debrief(
        facts(
            completed_sessions=4,
            skipped_sessions=1,
            actual_duration_minutes=275,
            actual_load=285.0,
        )
    )

    assert result.verdict in {
        WeeklyDebriefVerdict.PRODUCTIVE,
        WeeklyDebriefVerdict.CORRECT,
    }
    assert result.key_sessions_score == 100
    assert result.overall_score is not None
    assert result.overall_score >= 70
    assert (
        result.verdict
        is not WeeklyDebriefVerdict.VERY_PRODUCTIVE
    )


def test_skipped_session_blocks_very_productive_verdict() -> None:
    result = build_weekly_debrief(
        facts(
            completed_sessions=4,
            skipped_sessions=1,
            actual_duration_minutes=300,
            actual_load=300.0,
        )
    )

    assert result.overall_score is not None
    assert result.overall_score >= 90
    assert (
        result.verdict
        is WeeklyDebriefVerdict.PRODUCTIVE
    )
    assert (
        result.adaptation_direction
        is WeeklyAdaptationDirection.MAINTAIN
    )


def test_missing_key_session_is_penalized() -> None:
    complete = build_weekly_debrief(
        facts(
            completed_sessions=4,
            skipped_sessions=1,
            key_sessions_completed=2,
        )
    )
    missing_key = build_weekly_debrief(
        facts(
            completed_sessions=4,
            skipped_sessions=1,
            key_sessions_completed=1,
        )
    )

    assert complete.overall_score is not None
    assert missing_key.overall_score is not None
    assert missing_key.overall_score < complete.overall_score
    assert any(
        "prioritaire" in warning
        for warning in missing_key.warnings
    )


def test_low_completion_produces_reduction_or_recovery() -> None:
    result = build_weekly_debrief(
        facts(
            completed_sessions=2,
            skipped_sessions=3,
            actual_duration_minutes=120,
            actual_load=120.0,
            key_sessions_completed=0,
            compliant_intensity_sessions=1,
        )
    )

    assert result.verdict in {
        WeeklyDebriefVerdict.PARTIALLY_COMPLIANT,
        WeeklyDebriefVerdict.INSUFFICIENT,
    }
    assert result.adaptation_direction in {
        WeeklyAdaptationDirection.REDUCE,
        WeeklyAdaptationDirection.RECOVER,
    }


def test_overload_has_priority_over_high_completion() -> None:
    result = build_weekly_debrief(
        facts(
            actual_duration_minutes=380,
            actual_load=390.0,
        )
    )

    assert result.load_ratio == pytest.approx(1.30)
    assert result.verdict is WeeklyDebriefVerdict.OVERLOAD
    assert (
        result.adaptation_direction
        is WeeklyAdaptationDirection.RECOVER
    )


def test_supplementary_session_is_reported_without_inflating_adherence() -> None:
    result = build_weekly_debrief(
        facts(
            supplementary_sessions=1,
            actual_duration_minutes=340,
            actual_load=330.0,
        )
    )

    assert result.adherence_score == 100
    assert any(
        "supplémentaire" in warning
        for warning in result.warnings
    )


def test_intensity_non_compliance_reduces_score() -> None:
    compliant = build_weekly_debrief(facts())

    poor = build_weekly_debrief(
        facts(
            compliant_intensity_sessions=1,
            analyzed_intensity_sessions=4,
        )
    )

    assert compliant.overall_score is not None
    assert poor.overall_score is not None
    assert poor.overall_score < compliant.overall_score
    assert poor.intensity_score == 25


def test_no_plan_returns_unknown_without_fake_score() -> None:
    result = build_weekly_debrief(
        facts(
            planned_sessions=0,
            completed_sessions=0,
            planned_duration_minutes=0,
            actual_duration_minutes=0,
            planned_load=0.0,
            actual_load=0.0,
            key_sessions_planned=0,
            key_sessions_completed=0,
            compliant_intensity_sessions=0,
            analyzed_intensity_sessions=0,
        )
    )

    assert result.verdict is WeeklyDebriefVerdict.UNKNOWN
    assert result.overall_score is None
    assert (
        result.adaptation_direction
        is WeeklyAdaptationDirection.OBSERVE
    )


def test_scores_are_bounded_when_actual_volume_is_extreme() -> None:
    result = build_weekly_debrief(
        facts(
            actual_duration_minutes=1200,
            actual_load=1500.0,
        )
    )

    scores = (
        result.overall_score,
        result.adherence_score,
        result.duration_score,
        result.load_score,
        result.key_sessions_score,
        result.intensity_score,
    )

    assert all(
        score is None or 0 <= score <= 100
        for score in scores
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"planned_sessions": -1},
        {"actual_load": -1.0},
        {"history_confidence": 1.01},
        {
            "completed_sessions": 5,
            "skipped_sessions": 1,
        },
        {"key_sessions_completed": 3},
        {
            "compliant_intensity_sessions": 5,
            "analyzed_intensity_sessions": 4,
        },
    ],
)
def test_invalid_facts_are_rejected(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        build_weekly_debrief(facts(**overrides))


def test_analysis_exposes_objective_week_numbers() -> None:
    result = build_weekly_debrief(
        facts(
            completed_sessions=4,
            skipped_sessions=1,
            actual_duration_minutes=274,
            actual_load=280.0,
        )
    )

    assert "4/5" in result.analysis
    assert "274 min" in result.analysis
    assert "300 min" in result.analysis
    assert "280.0" in result.analysis
