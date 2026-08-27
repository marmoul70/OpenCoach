from datetime import date

import pytest

from opencoach.coaching.weekly_assessment import (
    CoachHistoryConfidenceLevel,
    CoachWeeklyStatus,
    build_coach_weekly_assessment,
)
from opencoach.training.weekly_load_projection import (
    WeeklyLoadProjection,
)


def create_projection(
    *,
    target_load: float | None = 153.0,
    projected_week_load: float = 151.5,
    projected_gap: float | None = -1.5,
    projected_gap_percent: float | None = -1.0,
    adaptation_opportunity: bool = False,
    adaptation_direction: str | None = None,
) -> WeeklyLoadProjection:
    return WeeklyLoadProjection(
        week_start=date(
            2026,
            8,
            24,
        ),
        week_end=date(
            2026,
            8,
            30,
        ),
        as_of_date=date(
            2026,
            8,
            27,
        ),

        actual_load_to_date=72.0,
        remaining_planned_load=79.5,
        projected_week_load=(
            projected_week_load
        ),

        target_load=target_load,
        load_min=145.0,
        load_max=161.0,

        projected_gap=projected_gap,
        projected_gap_percent=(
            projected_gap_percent
        ),

        remaining_days=3,

        adaptation_opportunity=(
            adaptation_opportunity
        ),
        adaptation_direction=(
            adaptation_direction
        ),

        completed_sessions_count=0,
        missed_sessions_count=1,
        remaining_sessions_count=4,
        planned_sessions_count=5,
        supplementary_sessions_count=1,
    )


def test_aligned_week_keeps_program() -> None:
    assessment = (
        build_coach_weekly_assessment(
            projection=(
                create_projection()
            ),
            history_window_days=7,
            history_confidence=0.25,
        )
    )

    assert (
        assessment.status
        is CoachWeeklyStatus.ALIGNED
    )

    assert (
        assessment.adaptation_opportunity
        is False
    )

    assert (
        assessment.history_confidence_level
        is CoachHistoryConfidenceLevel.LOW
    )

    assert (
        assessment.projected_gap_percent
        == -1.0
    )

    assert (
        "Conservez le programme prévu"
        in assessment.instruction
    )

    assert (
        "1 semaine"
        in assessment.analysis
    )


def test_under_target_can_propose_adaptation() -> None:
    assessment = (
        build_coach_weekly_assessment(
            projection=(
                create_projection(
                    projected_week_load=120.0,
                    projected_gap=-33.0,
                    projected_gap_percent=-21.6,
                    adaptation_opportunity=True,
                    adaptation_direction="increase",
                )
            ),
            history_window_days=28,
            history_confidence=1.0,
        )
    )

    assert (
        assessment.status
        is CoachWeeklyStatus.UNDER_TARGET
    )

    assert (
        assessment.adaptation_opportunity
        is True
    )

    assert (
        assessment.adaptation_direction
        == "increase"
    )

    assert (
        "validation"
        in assessment.instruction
    )


def test_over_target_can_propose_reduction() -> None:
    assessment = (
        build_coach_weekly_assessment(
            projection=(
                create_projection(
                    projected_week_load=185.0,
                    projected_gap=32.0,
                    projected_gap_percent=20.9,
                    adaptation_opportunity=True,
                    adaptation_direction="reduce",
                )
            ),
            history_window_days=21,
            history_confidence=0.75,
        )
    )

    assert (
        assessment.status
        is CoachWeeklyStatus.OVER_TARGET
    )

    assert (
        assessment.adaptation_direction
        == "reduce"
    )

    assert (
        "allègement"
        in assessment.instruction
    )


def test_missing_target_returns_unknown() -> None:
    assessment = (
        build_coach_weekly_assessment(
            projection=(
                create_projection(
                    target_load=None,
                    projected_gap=None,
                    projected_gap_percent=None,
                )
            ),
            history_window_days=7,
            history_confidence=0.25,
        )
    )

    assert (
        assessment.status
        is CoachWeeklyStatus.UNKNOWN
    )

    assert (
        "apprentissage"
        in assessment.headline
    )


@pytest.mark.parametrize(
    (
        "confidence",
        "expected",
    ),
    [
        (
            0.25,
            CoachHistoryConfidenceLevel.LOW,
        ),
        (
            0.50,
            CoachHistoryConfidenceLevel.MODERATE,
        ),
        (
            0.75,
            CoachHistoryConfidenceLevel.GOOD,
        ),
        (
            1.0,
            CoachHistoryConfidenceLevel.HIGH,
        ),
    ],
)
def test_history_confidence_level(
    confidence: float,
    expected: CoachHistoryConfidenceLevel,
) -> None:
    assessment = (
        build_coach_weekly_assessment(
            projection=(
                create_projection()
            ),
            history_window_days=28,
            history_confidence=confidence,
        )
    )

    assert (
        assessment.history_confidence_level
        is expected
    )


@pytest.mark.parametrize(
    "confidence",
    [
        -0.01,
        1.01,
    ],
)
def test_invalid_history_confidence_is_rejected(
    confidence: float,
) -> None:
    with pytest.raises(
        ValueError
    ):
        build_coach_weekly_assessment(
            projection=(
                create_projection()
            ),
            history_window_days=7,
            history_confidence=confidence,
        )
