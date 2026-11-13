from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from opencoach.ai.trend_tools import (
    TrainingTrendsArguments,
    build_training_trends_tool,
)


def test_training_trends_compares_adjacent_periods_with_complete_coverage():
    calls = []

    class FakeStatsService:
        def calculate(self, profile_id, start_date, end_date):
            calls.append((start_date, end_date))
            is_current = start_date == date(2026, 11, 2)
            return SimpleNamespace(
                start_date=start_date,
                end_date=end_date,
                sessions_count=2,
                duration_data_count=2,
                distance_data_count=2,
                elevation_data_count=2,
                measured_load_data_count=2,
                manual_sessions_count=0,
                total_duration_minutes=120 if is_current else 100,
                total_distance_km=20.0 if is_current else 18.0,
                total_elevation_gain_m=400.0 if is_current else 350.0,
                total_load=80.0 if is_current else 70.0,
            )

    tool = build_training_trends_tool(
        FakeStatsService(),
        uuid4(),
        reference_date_provider=lambda: date(2026, 11, 9),
    )
    result = tool.handler(
        TrainingTrendsArguments(nb_days=7, comparison_days=7)
    )

    assert calls == [
        (date(2026, 11, 2), date(2026, 11, 8)),
        (date(2026, 10, 26), date(2026, 11, 1)),
    ]
    assert result["metrics"]["distance_km"]["trend"] == {
        "delta": 2.0,
        "percent_delta": 11.1,
        "status": "complete",
    }
    assert "trend" not in result
    assert all(
        metric["trend"]["status"] == "complete"
        for metric in result["metrics"].values()
    )


def test_training_trends_suppresses_delta_when_coverage_is_partial():
    class PartialStatsService:
        def calculate(self, profile_id, start_date, end_date):
            return SimpleNamespace(
                start_date=start_date,
                end_date=end_date,
                sessions_count=2,
                duration_data_count=2,
                distance_data_count=1,
                elevation_data_count=2,
                measured_load_data_count=2,
                manual_sessions_count=0,
                total_duration_minutes=120,
                total_distance_km=10.0,
                total_elevation_gain_m=300.0,
                total_load=60.0,
            )

    tool = build_training_trends_tool(
        PartialStatsService(),
        uuid4(),
        reference_date_provider=lambda: date(2026, 11, 9),
    )
    result = tool.handler(
        TrainingTrendsArguments(nb_days=7, comparison_days=7)
    )

    distance = result["metrics"]["distance_km"]
    assert distance["current_period"]["value"] is None
    assert distance["current_period"]["partial_observed_value"] == 10.0
    assert distance["trend"]["delta"] is None
    assert distance["trend"]["status"] == "insufficient_coverage"
    assert "trend" not in result
    assert result["metrics"]["duration_minutes"]["trend"]["status"] == "complete"
