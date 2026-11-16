"""Tests de contrat de l'historique sportif et de sa couverture."""

from datetime import date, timedelta
from uuid import uuid4

from opencoach.training import TrainingStats

from opencoach.ai.training_tools import (
    TrainingHistoryArguments,
    build_training_history_tool,
)


class FakeTrainingStatsService:
    def __init__(self, stats):
        self.stats = stats
        self.calls = []

    def calculate_days(
        self,
        athlete_profile_id,
        reference_date,
        *,
        days,
        include_reference_day=True,
    ):
        end_date = reference_date if include_reference_day else reference_date - timedelta(days=1)
        start_date = end_date - timedelta(days=days - 1)
        self.calls.append((athlete_profile_id, start_date, end_date))
        return self.stats


def make_stats(**overrides):
    values = {
        "start_date": date(2026, 11, 1),
        "end_date": date(2026, 11, 7),
        "activities_count": 0,
        "manual_sessions_count": 0,
        "duration_data_count": 0,
        "distance_data_count": 0,
        "elevation_data_count": 0,
        "measured_load_data_count": 0,
        "estimated_load_data_count": 0,
        "total_duration_minutes": 0,
        "total_distance_km": 0.0,
        "total_elevation_gain_m": 0.0,
        "measured_load": 0.0,
        "estimated_load": 0.0,
    }
    values.update(overrides)
    return TrainingStats(**values)


def run_history(stats):
    tool = build_training_history_tool(
        FakeTrainingStatsService(stats),
        uuid4(),
        reference_date_provider=lambda: date(2026, 11, 7),
    )
    return tool.handler(TrainingHistoryArguments(nb_days=7))


def test_empty_period_reports_metrics_as_unavailable_not_zero():
    result = run_history(make_stats())

    assert result["sessions"]["total"] == 0
    for metric_name in ("duration_minutes", "distance_km", "elevation_gain_m"):
        metric = result["metrics"][metric_name]
        assert metric["value"] is None
        assert metric["observed_value"] is None
        assert metric["coverage"]["status"] == "no_sessions"

    load = result["metrics"]["training_load"]
    assert load["measured"] is None
    assert load["estimated"] is None
    assert load["total"] is None
    assert load["coverage"]["status"] == "no_sessions"


def test_partial_history_keeps_only_explicit_partial_subtotals():
    result = run_history(make_stats(
        activities_count=2,
        duration_data_count=1,
        distance_data_count=2,
        elevation_data_count=1,
        measured_load_data_count=1,
        total_duration_minutes=45,
        total_distance_km=12.5,
        total_elevation_gain_m=300,
        measured_load=80,
    ))

    duration = result["metrics"]["duration_minutes"]
    assert duration["value"] is None
    assert duration["observed_value"] == 45
    assert duration["coverage"]["status"] == "partial"

    distance = result["metrics"]["distance_km"]
    assert distance["value"] == 12.5
    assert distance["coverage"]["status"] == "complete"

    elevation = result["metrics"]["elevation_gain_m"]
    assert elevation["value"] is None
    assert elevation["observed_value"] == 300
    assert elevation["coverage"]["status"] == "partial"

    load = result["metrics"]["training_load"]
    assert load["total"] is None
    assert load["coverage"]["status"] == "partial"


def test_coaching_history_can_use_the_same_completed_days_as_training_load():
    reference_date = date(2026, 11, 15)
    service = FakeTrainingStatsService(make_stats())
    tool = build_training_history_tool(
        service,
        uuid4(),
        reference_date_provider=lambda: reference_date,
    )

    tool.handler(TrainingHistoryArguments(nb_days=7, exclude_current_day=True))

    _, start_date, end_date = service.calls[0]
    assert (start_date, end_date) == (
        date(2026, 11, 8),
        date(2026, 11, 14),
    )


def test_history_keeps_including_reference_day_by_default():
    reference_date = date(2026, 11, 15)
    service = FakeTrainingStatsService(make_stats())
    tool = build_training_history_tool(
        service,
        uuid4(),
        reference_date_provider=lambda: reference_date,
    )

    tool.handler(TrainingHistoryArguments(nb_days=7))

    _, start_date, end_date = service.calls[0]
    assert (start_date, end_date) == (
        date(2026, 11, 9),
        date(2026, 11, 15),
    )
