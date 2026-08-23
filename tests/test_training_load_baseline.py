import pytest

from opencoach.planning.training_history_metrics import (
    TrainingHistoryMetrics,
    WeeklyTrainingAverages,
)
from opencoach.planning.training_load_baseline import (
    TrainingLoadBaseline,
    calculate_training_load_baseline,
)


def create_weekly_average(
    load: float,
) -> WeeklyTrainingAverages:
    return WeeklyTrainingAverages(
        weeks=1.0,
        sessions=4.0,
        duration_minutes=300.0,
        distance_km=40.0,
        elevation_gain_m=1000.0,
        training_load=load,
    )


def create_metrics(
    *,
    load_7: float,
    load_28: float,
    load_42: float,
    load_84: float,
) -> TrainingHistoryMetrics:
    return TrainingHistoryMetrics(
        last_7_days=create_weekly_average(
            load_7
        ),
        last_28_days=create_weekly_average(
            load_28
        ),
        last_42_days=create_weekly_average(
            load_42
        ),
        last_84_days=create_weekly_average(
            load_84
        ),
        longest_activity=None,
        longest_duration_minutes=None,
        longest_distance_km=None,
        highest_elevation_activity=None,
        highest_elevation_gain_m=None,
    )


def test_stable_history_produces_stable_baseline() -> None:
    metrics = create_metrics(
        load_7=400.0,
        load_28=400.0,
        load_42=400.0,
        load_84=400.0,
    )

    baseline = calculate_training_load_baseline(
        metrics
    )

    assert baseline.baseline_load == pytest.approx(
        400.0
    )

    assert baseline.confidence == pytest.approx(
        1.0
    )


def test_low_last_week_does_not_collapse_baseline() -> None:
    metrics = create_metrics(
        load_7=100.0,
        load_28=400.0,
        load_42=390.0,
        load_84=380.0,
    )

    baseline = calculate_training_load_baseline(
        metrics
    )

    assert baseline.baseline_load > 300.0
    assert baseline.baseline_load < 400.0


def test_high_last_week_does_not_dominate_baseline() -> None:
    metrics = create_metrics(
        load_7=800.0,
        load_28=400.0,
        load_42=390.0,
        load_84=380.0,
    )

    baseline = calculate_training_load_baseline(
        metrics
    )

    assert baseline.baseline_load < 500.0


def test_medium_term_combines_28_and_42_days() -> None:
    metrics = create_metrics(
        load_7=400.0,
        load_28=500.0,
        load_42=300.0,
        load_84=400.0,
    )

    baseline = calculate_training_load_baseline(
        metrics
    )

    assert baseline.medium_term_load == pytest.approx(
        420.0
    )


def test_empty_history_has_zero_baseline_and_confidence() -> None:
    metrics = create_metrics(
        load_7=0.0,
        load_28=0.0,
        load_42=0.0,
        load_84=0.0,
    )

    baseline = calculate_training_load_baseline(
        metrics
    )

    assert baseline.baseline_load == 0.0
    assert baseline.confidence == 0.0


def test_variable_history_reduces_confidence() -> None:
    metrics = create_metrics(
        load_7=100.0,
        load_28=400.0,
        load_42=420.0,
        load_84=390.0,
    )

    baseline = calculate_training_load_baseline(
        metrics
    )

    assert baseline.confidence < 1.0


def test_baseline_rejects_invalid_confidence() -> None:
    with pytest.raises(
        ValueError,
        match="confiance",
    ):
        TrainingLoadBaseline(
            baseline_load=400.0,
            short_term_load=400.0,
            medium_term_load=400.0,
            long_term_load=400.0,
            confidence=1.5,
        )
