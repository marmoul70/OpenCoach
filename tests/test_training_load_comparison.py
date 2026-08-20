from datetime import date

import pytest

from opencoach.training.load_comparison import (
    TrainingLoadComparison,
    classify_training_load,
)


@pytest.mark.parametrize(
    (
        "planned_load",
        "actual_load",
        "expected",
    ),
    [
        (
            0.0,
            0.0,
            "rest_respected",
        ),
        (
            0.0,
            20.0,
            "rest_broken",
        ),
        (
            50.0,
            30.0,
            "below_plan",
        ),
        (
            50.0,
            40.0,
            "on_plan",
        ),
        (
            50.0,
            50.0,
            "on_plan",
        ),
        (
            50.0,
            60.0,
            "on_plan",
        ),
        (
            50.0,
            61.0,
            "above_plan",
        ),
    ],
)
def test_classify_training_load(
    planned_load: float,
    actual_load: float,
    expected: str,
) -> None:
    assert (
        classify_training_load(
            planned_load=planned_load,
            actual_load=actual_load,
        )
        == expected
    )


def test_training_load_comparison_calculates_deltas() -> None:
    comparison = TrainingLoadComparison(
        date=date(
            2026,
            8,
            20,
        ),
        planned_duration_minutes=60,
        actual_duration_minutes=130,
        planned_load=27.0,
        actual_load=68.0,
        measured_load=50.0,
        estimated_load=18.0,
        planned_sessions_count=1,
        actual_sessions_count=3,
        status="above_plan",
    )

    assert comparison.load_delta == 41.0
    assert comparison.duration_delta_minutes == 70
    assert comparison.load_ratio == 2.519


def test_training_load_comparison_has_no_ratio_for_rest() -> None:
    comparison = TrainingLoadComparison(
        date=date(
            2026,
            8,
            20,
        ),
        planned_duration_minutes=0,
        actual_duration_minutes=55,
        planned_load=0.0,
        actual_load=25.0,
        measured_load=25.0,
        estimated_load=0.0,
        planned_sessions_count=0,
        actual_sessions_count=2,
        status="rest_broken",
    )

    assert comparison.load_delta == 25.0
    assert comparison.duration_delta_minutes == 55
    assert comparison.load_ratio is None