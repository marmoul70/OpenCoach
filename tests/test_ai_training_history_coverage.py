"""Tests de couverture de l'outil d'historique sportif."""

from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from opencoach.ai.training_tools import (
    TrainingHistoryArguments,
    build_training_history_tool,
)


class FakeTrainingStatsService:
    def __init__(self, stats):
        self.stats = stats

    def calculate(self, athlete_profile_id, start_date, end_date):
        return self.stats


def make_stats(**overrides):
    values = {
        "start_date": date(2026, 11, 1),
        "end_date": date(2026, 11, 7),
        "sessions_count": 0,
        "activities_count": 0,
        "manual_sessions_count": 0,
        "duration_data_count": 0,
        "measured_load_data_count": 0,
        "distance_data_count": 0,
        "elevation_data_count": 0,
        "total_duration_minutes": 0,
        "total_distance_km": 0,
        "total_elevation_gain_m": 0,
        "measured_load": 0,
        "estimated_load": 0,
        "total_load": 0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


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
        sessions_count=2,
        activities_count=2,
        duration_data_count=1,
        distance_data_count=2,
        elevation_data_count=1,
        measured_load_data_count=1,
        total_duration_minutes=45,
        total_distance_km=12.5,
        total_elevation_gain_m=300,
        measured_load=80,
        total_load=80,
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
