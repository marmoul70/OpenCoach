import pytest

from opencoach.planning.load_reconciliation_history import (
    ReconciliationHistoryPolicy,
    ReconciliationTrendStatus,
    analyze_reconciliation_history,
)
from opencoach.planning.weekly_load_reconciliation import (
    reconcile_weekly_load,
)
from opencoach.planning.weekly_load_reconciliation_context import (
    ContextualWeeklyLoadReconciliation,
    LoadDeviationCause,
    contextualize_weekly_load_reconciliation,
)


def create_week(
    *,
    planned_load: float = 500.0,
    actual_load: float,
    cause: LoadDeviationCause | None = None,
) -> ContextualWeeklyLoadReconciliation:
    reconciliation = reconcile_weekly_load(
        planned_load=planned_load,
        actual_load=actual_load,
    )

    return contextualize_weekly_load_reconciliation(
        reconciliation=reconciliation,
        cause=cause,
    )


def test_empty_history_keeps_reference() -> None:
    result = analyze_reconciliation_history(
        history=(),
        current_reference_load=500.0,
    )

    assert result.status is ReconciliationTrendStatus.STABLE
    assert result.reanchoring_applied is False

    assert result.recommended_reference_load == pytest.approx(
        500.0
    )


def test_single_professional_underload_does_not_reanchor() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
        ),
        current_reference_load=500.0,
    )

    assert result.status is ReconciliationTrendStatus.STABLE

    assert result.consecutive_under_target_weeks == 1

    assert result.reanchoring_applied is False

    assert result.recommended_reference_load == pytest.approx(
        500.0
    )


def test_two_professional_underloads_trigger_watch() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=340.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
        ),
        current_reference_load=500.0,
    )

    assert result.status is ReconciliationTrendStatus.WATCH

    assert result.consecutive_under_target_weeks == 2

    assert result.reanchoring_applied is False


def test_three_professional_underloads_reanchor_reference() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=325.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
        ),
        current_reference_load=500.0,
    )

    observed_average = (
        350.0
        + 325.0
        + 350.0
    ) / 3

    expected_reference = (
        500.0
        + (
            observed_average
            - 500.0
        )
        * 0.50
    )

    assert result.status is ReconciliationTrendStatus.REANCHOR

    assert result.consecutive_under_target_weeks == 3

    assert result.observed_load_reference == pytest.approx(
        observed_average
    )

    assert result.recommended_reference_load == pytest.approx(
        expected_reference
    )

    assert result.reanchoring_applied is True


def test_reanchoring_is_progressive_not_brutal() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
        ),
        current_reference_load=500.0,
    )

    assert result.recommended_reference_load == pytest.approx(
        425.0
    )

    assert (
        result.observed_load_reference
        < result.recommended_reference_load
        < result.current_reference_load
    )


def test_on_target_week_breaks_underload_sequence() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=500.0,
            ),
        ),
        current_reference_load=500.0,
    )

    assert result.status is ReconciliationTrendStatus.STABLE

    assert result.consecutive_under_target_weeks == 0

    assert result.reanchoring_applied is False


def test_only_recent_consecutive_sequence_is_considered() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=300.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=500.0,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
        ),
        current_reference_load=500.0,
    )

    assert result.status is ReconciliationTrendStatus.WATCH

    assert result.consecutive_under_target_weeks == 2

    assert result.considered_weeks == 2


def test_incomplete_data_is_excluded_from_analysis() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=300.0,
                cause=LoadDeviationCause.INCOMPLETE_DATA,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
        ),
        current_reference_load=500.0,
    )

    assert result.status is ReconciliationTrendStatus.WATCH

    assert result.consecutive_under_target_weeks == 2

    assert result.reanchoring_applied is False


def test_three_small_underloads_do_not_reanchor_when_deficit_is_too_small() -> None:
    policy = ReconciliationHistoryPolicy(
        minimum_reanchor_deficit=0.20,
    )

    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=440.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=440.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
            create_week(
                actual_load=440.0,
                cause=LoadDeviationCause.PROFESSIONAL_CONSTRAINT,
            ),
        ),
        current_reference_load=500.0,
        policy=policy,
    )

    assert result.status is ReconciliationTrendStatus.WATCH

    assert result.reanchoring_applied is False

    assert result.recommended_reference_load == pytest.approx(
        500.0
    )


def test_history_can_reanchor_after_athlete_choice() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.ATHLETE_CHOICE,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.ATHLETE_CHOICE,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.ATHLETE_CHOICE,
            ),
        ),
        current_reference_load=500.0,
    )

    assert result.status is ReconciliationTrendStatus.REANCHOR

    assert result.reanchoring_applied is True


def test_history_can_reanchor_after_repeated_fatigue_underload() -> None:
    result = analyze_reconciliation_history(
        history=(
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.FATIGUE,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.FATIGUE,
            ),
            create_week(
                actual_load=350.0,
                cause=LoadDeviationCause.FATIGUE,
            ),
        ),
        current_reference_load=500.0,
    )

    assert result.status is ReconciliationTrendStatus.REANCHOR

    assert result.reanchoring_applied is True


def test_negative_reference_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="référence",
    ):
        analyze_reconciliation_history(
            history=(),
            current_reference_load=-1.0,
        )


def test_invalid_watch_threshold_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="surveillance",
    ):
        ReconciliationHistoryPolicy(
            watch_consecutive_weeks=0,
        )


def test_reanchor_threshold_cannot_precede_watch_threshold() -> None:
    with pytest.raises(
        ValueError,
        match="réancrage",
    ):
        ReconciliationHistoryPolicy(
            watch_consecutive_weeks=3,
            reanchor_consecutive_weeks=2,
        )


def test_invalid_reanchor_strength_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="force",
    ):
        ReconciliationHistoryPolicy(
            reanchor_strength=1.1,
        )
