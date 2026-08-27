from datetime import date, timedelta
from uuid import UUID, uuid4

import pytest

from opencoach.training import (
    RecentTrainingLoadService,
    TrainingLoadComparison,
)


TARGET_DATE = date(
    2026,
    8,
    20,
)


class FakeTrainingLoadComparisonService:
    def __init__(
        self,
        results: dict[
            date,
            TrainingLoadComparison,
        ],
    ) -> None:
        self.results = results
        self.calls: list[date] = []

    def calculate(
        self,
        athlete_profile_id: UUID,
        target_date: date,
    ) -> TrainingLoadComparison:
        self.calls.append(
            target_date,
        )

        return self.results[
            target_date
        ]


def create_comparison(
    *,
    comparison_date: date,
    planned_load: float,
    actual_load: float,
    status: str,
) -> TrainingLoadComparison:
    return TrainingLoadComparison(
        date=comparison_date,
        planned_duration_minutes=60,
        actual_duration_minutes=60,
        planned_load=planned_load,
        actual_load=actual_load,
        measured_load=actual_load,
        estimated_load=0.0,
        planned_sessions_count=(
            0
            if planned_load == 0
            else 1
        ),
        actual_sessions_count=(
            0
            if actual_load == 0
            else 1
        ),
        status=status,
    )


def test_recent_training_load_analyzes_previous_days() -> None:
    results = {}

    for offset in range(
        1,
        4,
    ):
        comparison_date = (
            TARGET_DATE
            - timedelta(
                days=offset,
            )
        )

        results[
            comparison_date
        ] = create_comparison(
            comparison_date=(
                comparison_date
            ),
            planned_load=20.0,
            actual_load=20.0,
            status="on_plan",
        )

    comparison_service = (
        FakeTrainingLoadComparisonService(
            results,
        )
    )

    service = RecentTrainingLoadService(
        comparison_service,
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
        days=3,
    )

    assert result.analyzed_days == 3

    assert result.planned_load_total == 60.0
    assert result.actual_load_total == 60.0

    assert result.load_delta_total == 0.0
    assert result.load_ratio == 1.0

    assert result.on_plan_days == 3
    assert result.above_plan_days == 0
    assert result.broken_rest_days == 0

    assert comparison_service.calls == [
        TARGET_DATE
        - timedelta(days=1),
        TARGET_DATE
        - timedelta(days=2),
        TARGET_DATE
        - timedelta(days=3),
    ]


def test_recent_training_load_counts_statuses() -> None:
    day_1 = (
        TARGET_DATE
        - timedelta(days=1)
    )

    day_2 = (
        TARGET_DATE
        - timedelta(days=2)
    )

    day_3 = (
        TARGET_DATE
        - timedelta(days=3)
    )

    day_4 = (
        TARGET_DATE
        - timedelta(days=4)
    )

    results = {
        day_1: create_comparison(
            comparison_date=day_1,
            planned_load=20.0,
            actual_load=30.0,
            status="above_plan",
        ),
        day_2: create_comparison(
            comparison_date=day_2,
            planned_load=20.0,
            actual_load=10.0,
            status="below_plan",
        ),
        day_3: create_comparison(
            comparison_date=day_3,
            planned_load=0.0,
            actual_load=15.0,
            status="rest_broken",
        ),
        day_4: create_comparison(
            comparison_date=day_4,
            planned_load=0.0,
            actual_load=0.0,
            status="rest_respected",
        ),
    }

    service = RecentTrainingLoadService(
        FakeTrainingLoadComparisonService(
            results,
        )
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
        days=4,
    )

    assert result.above_plan_days == 1
    assert result.below_plan_days == 1
    assert result.on_plan_days == 0

    assert result.broken_rest_days == 1
    assert result.respected_rest_days == 1


def test_recent_training_load_calculates_cumulative_delta() -> None:
    day_1 = (
        TARGET_DATE
        - timedelta(days=1)
    )

    day_2 = (
        TARGET_DATE
        - timedelta(days=2)
    )

    results = {
        day_1: create_comparison(
            comparison_date=day_1,
            planned_load=30.0,
            actual_load=50.0,
            status="above_plan",
        ),
        day_2: create_comparison(
            comparison_date=day_2,
            planned_load=20.0,
            actual_load=30.0,
            status="above_plan",
        ),
    }

    service = RecentTrainingLoadService(
        FakeTrainingLoadComparisonService(
            results,
        )
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
        days=2,
    )

    assert result.planned_load_total == 50.0
    assert result.actual_load_total == 80.0

    assert result.load_delta_total == 30.0
    assert result.load_ratio == 1.6


def test_recent_training_load_has_no_ratio_without_planned_load() -> None:
    day_1 = (
        TARGET_DATE
        - timedelta(days=1)
    )

    results = {
        day_1: create_comparison(
            comparison_date=day_1,
            planned_load=0.0,
            actual_load=20.0,
            status="rest_broken",
        ),
    }

    service = RecentTrainingLoadService(
        FakeTrainingLoadComparisonService(
            results,
        )
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
        days=1,
    )

    assert result.load_ratio is None
    assert result.load_delta_total == 20.0
    assert result.has_training_history is True


def test_recent_training_load_detects_empty_history() -> None:
    day_1 = (
        TARGET_DATE
        - timedelta(days=1)
    )

    results = {
        day_1: create_comparison(
            comparison_date=day_1,
            planned_load=0.0,
            actual_load=0.0,
            status="rest_respected",
        ),
    }

    service = RecentTrainingLoadService(
        FakeTrainingLoadComparisonService(
            results,
        )
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
        days=1,
    )

    assert result.has_training_history is False


def test_recent_training_load_rejects_invalid_period() -> None:
    service = RecentTrainingLoadService(
        FakeTrainingLoadComparisonService(
            {},
        )
    )

    with pytest.raises(
        ValueError,
        match=(
            "au moins un jour"
        ),
    ):
        service.calculate(
            uuid4(),
            TARGET_DATE,
            days=0,
        )

def test_recent_training_load_tracks_planning_coverage() -> None:
    day_1 = (
        TARGET_DATE
        - timedelta(days=1)
    )

    day_2 = (
        TARGET_DATE
        - timedelta(days=2)
    )

    day_3 = (
        TARGET_DATE
        - timedelta(days=3)
    )

    results = {
        day_1: create_comparison(
            comparison_date=day_1,
            planned_load=30.0,
            actual_load=30.0,
            status="on_plan",
        ),
        day_2: create_comparison(
            comparison_date=day_2,
            planned_load=0.0,
            actual_load=25.0,
            status="unplanned",
        ),
        day_3: create_comparison(
            comparison_date=day_3,
            planned_load=0.0,
            actual_load=0.0,
            status="unplanned",
        ),
    }

    service = RecentTrainingLoadService(
        FakeTrainingLoadComparisonService(
            results,
        )
    )

    result = service.calculate(
        uuid4(),
        TARGET_DATE,
        days=3,
    )

    assert result.analyzed_days == 3

    assert (
        result.planning_covered_days
        == 1
    )

    assert (
        result.unplanned_days
        == 2
    )

    assert (
        result.planning_coverage_ratio
        == pytest.approx(
            1 / 3,
            abs=0.001,
        )
    )

    # Les journées sans prescription OpenCoach
    # ne sont pas des écarts au planning.
    assert result.broken_rest_days == 0
    assert result.respected_rest_days == 0
    assert result.above_plan_days == 0
    assert result.below_plan_days == 0

    assert result.on_plan_days == 1

    # Leur charge réelle reste néanmoins
    # comptabilisée dans l'activité observée.
    assert (
        result.actual_load_total
        == 55.0
    )
