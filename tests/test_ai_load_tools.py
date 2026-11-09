from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from opencoach.ai.load_tools import (
    TrainingLoadArguments,
    build_training_load_tool,
)
from opencoach.ai.tool_engine import AIToolRegistry
from opencoach.training import RecentTrainingLoad, TrainingLoadComparison


def test_training_load_tool_returns_period_coverage_and_daily_breakdown():
    athlete_id = uuid4()
    reference_date = date(2026, 11, 9)
    calls = []

    class FakeTrainingStatsService:
        def calculate(self, profile_id, start_date, end_date):
            return SimpleNamespace(
                sessions_count=1,
                measured_load_data_count=1,
                manual_sessions_count=0,
            )

    class FakeService:
        def calculate(self, profile_id, target_date, *, days):
            calls.append((profile_id, target_date, days))
            comparisons = (
                TrainingLoadComparison(
                    date=date(2026, 11, 8),
                    planned_duration_minutes=0,
                    actual_duration_minutes=0,
                    planned_load=0.0,
                    actual_load=0.0,
                    measured_load=0.0,
                    estimated_load=0.0,
                    planned_sessions_count=0,
                    actual_sessions_count=0,
                    status="rest_respected",
                ),
                TrainingLoadComparison(
                    date=date(2026, 11, 7),
                    planned_duration_minutes=60,
                    actual_duration_minutes=65,
                    planned_load=40.0,
                    actual_load=45.0,
                    measured_load=45.0,
                    estimated_load=0.0,
                    planned_sessions_count=1,
                    actual_sessions_count=1,
                    status="above_plan",
                ),
            )
            return RecentTrainingLoad(
                days=comparisons,
                analyzed_days=2,
                planned_load_total=40.0,
                actual_load_total=45.0,
                above_plan_days=1,
                below_plan_days=0,
                on_plan_days=0,
                broken_rest_days=0,
                respected_rest_days=1,
                planning_covered_days=2,
                unplanned_days=0,
            )

    registry = AIToolRegistry()
    registry.register(
        build_training_load_tool(
            FakeService(),
            FakeTrainingStatsService(),
            athlete_id,
            reference_date_provider=lambda: reference_date,
        )
    )

    result = registry.execute("training_load", {"nb_days": 2})

    assert result.status == "ok"
    assert calls == [(athlete_id, reference_date, 2)]
    assert result.data["period"] == {
        "start_date": "2026-11-07",
        "end_date": "2026-11-08",
        "nb_days": 2,
        "inclusive": True,
    }
    assert result.data["load"]["actual_total"] == 45.0
    assert result.data["load"]["delta_total"] == 5.0
    assert result.data["planning_coverage"]["ratio"] == 1.0
    assert result.data["daily"][0]["actual_load"] == 45.0
    assert result.data["daily"][1]["actual_load"] is None


def test_training_load_tool_never_reports_missing_actual_load_as_zero():
    class EmptyService:
        def calculate(self, profile_id, target_date, *, days):
            return RecentTrainingLoad(
                days=(
                    TrainingLoadComparison(
                        date=date(2026, 11, 8),
                        planned_duration_minutes=0,
                        actual_duration_minutes=0,
                        planned_load=0.0,
                        actual_load=0.0,
                        measured_load=0.0,
                        estimated_load=0.0,
                        planned_sessions_count=0,
                        actual_sessions_count=0,
                        status="rest_respected",
                    ),
                ),
                analyzed_days=1,
                planned_load_total=0.0,
                actual_load_total=0.0,
                above_plan_days=0,
                below_plan_days=0,
                on_plan_days=0,
                broken_rest_days=0,
                respected_rest_days=1,
                planning_covered_days=1,
                unplanned_days=0,
            )

    class EmptyStatsService:
        def calculate(self, profile_id, start_date, end_date):
            return SimpleNamespace(
                sessions_count=0,
                measured_load_data_count=0,
                manual_sessions_count=0,
            )

    tool = build_training_load_tool(
        EmptyService(),
        EmptyStatsService(),
        uuid4(),
        reference_date_provider=lambda: date(2026, 11, 9),
    )
    result = tool.handler(TrainingLoadArguments(nb_days=1))

    assert result["load"]["actual_total"] is None
    assert result["load"]["delta_total"] is None
    assert result["warnings"] == [
        "Aucune séance réalisée enregistrée : la charge réelle est indisponible, pas égale à zéro."
    ]


def test_training_load_arguments_reject_out_of_range_periods():
    from pydantic import ValidationError

    import pytest

    with pytest.raises(ValidationError):
        TrainingLoadArguments(nb_days=0)
    with pytest.raises(ValidationError):
        TrainingLoadArguments(nb_days=91)


def test_training_load_tool_hides_partial_total_and_marks_daily_status_unreliable():
    class PartialStatsService:
        def calculate(self, profile_id, start_date, end_date):
            return SimpleNamespace(
                sessions_count=2,
                measured_load_data_count=1,
                manual_sessions_count=0,
            )

    class PartialRecentLoadService:
        def calculate(self, profile_id, target_date, *, days):
            comparison = TrainingLoadComparison(
                date=date(2026, 11, 8),
                planned_duration_minutes=45,
                actual_duration_minutes=40,
                planned_load=30.0,
                actual_load=20.0,
                measured_load=20.0,
                estimated_load=0.0,
                planned_sessions_count=1,
                actual_sessions_count=1,
                status="below_plan",
            )
            return RecentTrainingLoad(
                days=(comparison,),
                analyzed_days=1,
                planned_load_total=30.0,
                actual_load_total=20.0,
                above_plan_days=0,
                below_plan_days=1,
                on_plan_days=0,
                broken_rest_days=0,
                respected_rest_days=0,
                planning_covered_days=1,
                unplanned_days=0,
            )

    tool = build_training_load_tool(
        PartialRecentLoadService(),
        PartialStatsService(),
        uuid4(),
        reference_date_provider=lambda: date(2026, 11, 9),
    )
    result = tool.handler(TrainingLoadArguments(nb_days=1))

    assert result["load"]["coverage"]["status"] == "partial"
    assert result["load"]["actual_total"] is None
    assert result["load"]["partial_observed_total"] == 20.0
    assert result["daily"][0]["status"] == "load_data_incomplete"
    assert result["daily"][0]["actual_load"] is None
