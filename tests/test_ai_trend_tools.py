from datetime import date
from uuid import uuid4

from opencoach.ai.trend_tools import (
    TrainingTrendsArguments,
    build_training_trends_tool,
)
from opencoach.training import TrainingStatsService


def test_training_trends_delegates_periods_and_returns_coach_result():
    calls = []
    expected = {
        "current_period": {
            "start_date": "2026-11-02",
            "end_date": "2026-11-08",
            "nb_days": 7,
            "sessions": 2,
        },
        "comparison_period": {
            "start_date": "2026-10-26",
            "end_date": "2026-11-01",
            "nb_days": 7,
            "sessions": 2,
        },
        "metrics": {
            "distance_km": {
                "trend": {
                    "delta": 2.0,
                    "percent_delta": 11.1,
                    "status": "complete",
                }
            }
        },
        "warnings": [],
    }

    class FakeStatsService:
        def compare_adjacent_periods(
            self,
            profile_id,
            *,
            reference_date,
            current_days,
            comparison_days,
        ):
            calls.append(
                (profile_id, reference_date, current_days, comparison_days)
            )
            return expected

    athlete_id = uuid4()
    tool = build_training_trends_tool(
        FakeStatsService(),
        athlete_id,
        reference_date_provider=lambda: date(2026, 11, 9),
    )
    result = tool.handler(
        TrainingTrendsArguments(nb_days=7, comparison_days=7)
    )

    assert calls == [(athlete_id, date(2026, 11, 9), 7, 7)]
    assert result is expected


def test_training_trends_argument_schema_delegates_limits_to_domain_service():
    import pytest

    arguments = TrainingTrendsArguments(nb_days=0, comparison_days=181)
    assert arguments.nb_days == 0
    assert arguments.comparison_days == 181

    service = TrainingStatsService(object(), object())
    with pytest.raises(ValueError, match="1 et 180 jours"):
        service.compare_adjacent_periods(
            uuid4(),
            reference_date=date(2026, 11, 9),
            current_days=0,
            comparison_days=7,
        )
    with pytest.raises(ValueError, match="180 jours"):
        service.compare_adjacent_periods(
            uuid4(),
            reference_date=date(2026, 11, 9),
            current_days=7,
            comparison_days=181,
        )
