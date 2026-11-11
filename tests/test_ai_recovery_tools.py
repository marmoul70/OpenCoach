from datetime import date
from types import SimpleNamespace
from uuid import uuid4

from opencoach.ai.recovery_tools import (
    RecoveryStatusArguments,
    build_recovery_status_tool,
)
from opencoach.readiness import ReadinessDataUnavailableError


def _assessment(*, data_age_days=0):
    source_date = date(2026, 11, 9 - data_age_days)
    baseline_metric = SimpleNamespace(
        median=50.0,
        sample_count=20,
        reliable=True,
    )
    comparison_metric = SimpleNamespace(
        current=48.0,
        baseline=50.0,
        absolute_delta=-2.0,
        percent_delta=-4.0,
        reliable=True,
    )
    readiness = SimpleNamespace(
        score=82.0,
        level="good",
        warning_count=1,
        critical_count=0,
        training_constraints=(),
        fitness_ctl=75.0,
        fatigue_atl=68.0,
        training_balance=7.0,
        signals=[
            SimpleNamespace(
                metric="hrv",
                level="normal",
                reason="Dans la plage habituelle.",
                current_value=48.0,
                reference_value=50.0,
            )
        ],
    )
    baseline = SimpleNamespace(
        start_date=date(2026, 10, 10),
        end_date=date(2026, 11, 8),
        hrv=baseline_metric,
        resting_hr=baseline_metric,
        sleep_seconds=baseline_metric,
        sleep_score=baseline_metric,
    )
    comparison = SimpleNamespace(
        hrv=comparison_metric,
        resting_hr=comparison_metric,
        sleep_seconds=comparison_metric,
        sleep_score=comparison_metric,
    )
    return SimpleNamespace(
        date=date(2026, 11, 9),
        provider="opencoach",
        baseline=baseline,
        comparison=comparison,
        readiness=readiness,
        source_date=source_date,
        data_age_days=data_age_days,
        data_status="fresh" if data_age_days == 0 else "stale",
    )


def test_recovery_status_returns_readiness_and_data_freshness():
    class FakeService:
        def calculate(self, profile_id, target_date):
            assert target_date == date(2026, 11, 9)
            return _assessment(data_age_days=1)

    tool = build_recovery_status_tool(FakeService(), uuid4())
    result = tool.handler(
        RecoveryStatusArguments(target_date=date(2026, 11, 9))
    )

    assert result["available"] is True
    assert result["source"] == "opencoach"
    assert result["data"]["freshness"] == "stale"
    assert result["data"]["age_days"] == 1
    assert result["readiness"]["score"] == 82.0
    assert result["metrics"]["hrv"]["baseline_reliable"] is True
    assert result["warnings"]


def test_recovery_status_returns_explicit_unavailable_result():
    class EmptyService:
        def calculate(self, profile_id, target_date):
            raise ReadinessDataUnavailableError("No wellness data")

    tool = build_recovery_status_tool(EmptyService(), uuid4())
    result = tool.handler(
        RecoveryStatusArguments(target_date=date(2026, 11, 9))
    )

    assert result == {
        "available": False,
        "target_date": "2026-11-09",
        "reason": "no_readiness_data",
        "message": "Aucune donnée de récupération exploitable n'est disponible pour cette date.",
    }


def test_recovery_analysis_compacts_per_day_metric_provenance(monkeypatch):
    from datetime import timedelta
    from types import SimpleNamespace

    from opencoach.ai.recovery_tools import (
        RecoveryAnalysisArguments,
        build_recovery_analysis_tool,
    )

    target_date = date(2026, 11, 10)
    metric_sources = {
        (target_date - timedelta(days=offset)).isoformat(): {
            "hrv": ("coros",),
            "sleep_seconds": ("coros",),
        }
        for offset in range(30)
    }
    monkeypatch.setattr(
        "opencoach.wellness_aggregation.aggregate_wellness_days",
        lambda _days: SimpleNamespace(days=(), metric_sources=metric_sources, conflicts={}),
    )

    class EmptyWellnessRepository:
        def list_range(self, *_args):
            return []

    class EmptyDailyContextRepository:
        def get_by_date(self, *_args):
            return None

    class EmptyDailyCheckinRepository:
        def get_for_date(self, *_args):
            return None

    tool = build_recovery_analysis_tool(
        EmptyWellnessRepository(),
        EmptyDailyContextRepository(),
        EmptyDailyCheckinRepository(),
        uuid4(),
    )
    result = tool.handler(RecoveryAnalysisArguments(target_date=target_date))

    assert result["metric_sources"] == {
        "hrv": ["coros"],
        "sleep_seconds": ["coros"],
    }
    assert result["metric_source_days"] == {
        "hrv": 30,
        "sleep_seconds": 30,
    }
    assert len(str(result)) < 8_000
