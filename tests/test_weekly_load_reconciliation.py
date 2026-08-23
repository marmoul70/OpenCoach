import pytest

from opencoach.planning.weekly_load_reconciliation import (
    LoadReconciliationStatus,
    WeeklyLoadReconciliation,
    reconcile_weekly_load,
)


def test_exact_target_is_on_target() -> None:
    result = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=500.0,
    )

    assert result.status is LoadReconciliationStatus.ON_TARGET

    assert result.absolute_delta == pytest.approx(
        0.0
    )

    assert result.relative_delta == pytest.approx(
        0.0
    )


def test_small_underload_is_still_on_target() -> None:
    result = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=460.0,
    )

    assert result.relative_delta == pytest.approx(
        -0.08
    )

    assert result.status is LoadReconciliationStatus.ON_TARGET


def test_small_overload_is_still_on_target() -> None:
    result = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=540.0,
    )

    assert result.relative_delta == pytest.approx(
        0.08
    )

    assert result.status is LoadReconciliationStatus.ON_TARGET


def test_under_target_is_detected() -> None:
    result = reconcile_weekly_load(
        planned_load=550.0,
        actual_load=430.0,
    )

    assert result.absolute_delta == pytest.approx(
        -120.0
    )

    assert result.relative_delta == pytest.approx(
        -120.0 / 550.0
    )

    assert (
        result.status
        is LoadReconciliationStatus.UNDER_TARGET
    )


def test_strong_under_target_is_detected() -> None:
    result = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=300.0,
    )

    assert result.relative_delta == pytest.approx(
        -0.40
    )

    assert (
        result.status
        is LoadReconciliationStatus.STRONGLY_UNDER_TARGET
    )


def test_over_target_is_detected() -> None:
    result = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=600.0,
    )

    assert result.relative_delta == pytest.approx(
        0.20
    )

    assert (
        result.status
        is LoadReconciliationStatus.OVER_TARGET
    )


def test_strong_over_target_is_detected() -> None:
    result = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=700.0,
    )

    assert result.relative_delta == pytest.approx(
        0.40
    )

    assert (
        result.status
        is LoadReconciliationStatus.STRONGLY_OVER_TARGET
    )


def test_minus_ten_percent_is_on_target() -> None:
    result = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=450.0,
    )

    assert result.relative_delta == pytest.approx(
        -0.10
    )

    assert result.status is LoadReconciliationStatus.ON_TARGET


def test_plus_ten_percent_is_on_target() -> None:
    result = reconcile_weekly_load(
        planned_load=500.0,
        actual_load=550.0,
    )

    assert result.relative_delta == pytest.approx(
        0.10
    )

    assert result.status is LoadReconciliationStatus.ON_TARGET


def test_minus_twenty_five_percent_is_under_target() -> None:
    result = reconcile_weekly_load(
        planned_load=400.0,
        actual_load=300.0,
    )

    assert result.relative_delta == pytest.approx(
        -0.25
    )

    assert (
        result.status
        is LoadReconciliationStatus.UNDER_TARGET
    )


def test_plus_twenty_five_percent_is_over_target() -> None:
    result = reconcile_weekly_load(
        planned_load=400.0,
        actual_load=500.0,
    )

    assert result.relative_delta == pytest.approx(
        0.25
    )

    assert (
        result.status
        is LoadReconciliationStatus.OVER_TARGET
    )


def test_zero_planned_and_zero_actual_is_on_target() -> None:
    result = reconcile_weekly_load(
        planned_load=0.0,
        actual_load=0.0,
    )

    assert result.relative_delta == 0.0

    assert result.status is LoadReconciliationStatus.ON_TARGET


def test_training_when_zero_was_planned_is_strong_overload() -> None:
    result = reconcile_weekly_load(
        planned_load=0.0,
        actual_load=100.0,
    )

    assert (
        result.status
        is LoadReconciliationStatus.STRONGLY_OVER_TARGET
    )

    assert result.absolute_delta == pytest.approx(
        100.0
    )


def test_negative_planned_load_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="planifiée",
    ):
        reconcile_weekly_load(
            planned_load=-1.0,
            actual_load=100.0,
        )


def test_negative_actual_load_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="réalisée",
    ):
        reconcile_weekly_load(
            planned_load=100.0,
            actual_load=-1.0,
        )


def test_reconciliation_model_rejects_negative_planned_load() -> None:
    with pytest.raises(
        ValueError,
        match="planifiée",
    ):
        WeeklyLoadReconciliation(
            planned_load=-1.0,
            actual_load=100.0,
            absolute_delta=101.0,
            relative_delta=1.01,
            status=LoadReconciliationStatus.OVER_TARGET,
        )


def test_reconciliation_model_rejects_negative_actual_load() -> None:
    with pytest.raises(
        ValueError,
        match="réalisée",
    ):
        WeeklyLoadReconciliation(
            planned_load=100.0,
            actual_load=-1.0,
            absolute_delta=-101.0,
            relative_delta=-1.01,
            status=(
                LoadReconciliationStatus.STRONGLY_UNDER_TARGET
            ),
        )
