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
            "1 et 90 jours"
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



def test_recent_training_load_analysis_summary_preserves_partial_load_semantics():
    from opencoach.training import RecentTrainingLoad, TrainingLoadComparison, TrainingStats

    comparison = TrainingLoadComparison(
        date=TARGET_DATE - timedelta(days=1),
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
    recent = RecentTrainingLoad(
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
    stats = TrainingStats(
        start_date=TARGET_DATE - timedelta(days=1),
        end_date=TARGET_DATE - timedelta(days=1),
        activities_count=2,
        manual_sessions_count=0,
        total_duration_minutes=80,
        total_distance_km=10.0,
        total_elevation_gain_m=100.0,
        measured_load=20.0,
        estimated_load=0.0,
        duration_data_count=2,
        distance_data_count=1,
        elevation_data_count=2,
        measured_load_data_count=1,
    )

    summary = recent.analysis_summary(stats)

    assert summary["load"]["actual_total"] is None
    assert summary["load"]["partial_observed_total"] == 20.0
    assert summary["load"]["coverage"]["status"] == "partial"
    assert summary["volume"]["distance_km"] is None
    assert summary["volume"]["partial_distance_km"] == 10.0
    assert summary["daily"][0]["status"] == "load_data_incomplete"
    assert summary["daily"][0]["actual_load"] is None
    assert summary["warnings"] == [
        "Charge partielle : 1/2 séances disposent d'une charge exploitable. Le total complet est masqué."
    ]



def test_recent_training_load_enforces_the_domain_maximum_window():
    service = RecentTrainingLoadService(FakeTrainingLoadComparisonService({}))
    with pytest.raises(ValueError, match="90 jours"):
        service.calculate(
            uuid4(),
            TARGET_DATE,
            days=91,
        )



def test_recent_training_load_service_owns_combined_load_and_volume_summary():
    from opencoach.training import TrainingStats

    comparison_date = TARGET_DATE - timedelta(days=1)
    comparison = create_comparison(
        comparison_date=comparison_date,
        planned_load=35.0,
        actual_load=42.0,
        status="above_plan",
    )
    comparison_service = FakeTrainingLoadComparisonService({
        comparison_date: comparison,
    })
    stats_calls = []

    class FakeTrainingStatsService:
        def calculate_days(
            self,
            athlete_profile_id,
            reference_date,
            *,
            days=7,
            include_reference_day=True,
        ):
            stats_calls.append(
                (athlete_profile_id, reference_date, days, include_reference_day)
            )
            end_date = reference_date if include_reference_day else reference_date - timedelta(days=1)
            start_date = end_date - timedelta(days=days - 1)
            return TrainingStats(
                start_date=start_date,
                end_date=end_date,
                activities_count=1,
                manual_sessions_count=0,
                total_duration_minutes=60,
                total_distance_km=10.0,
                total_elevation_gain_m=250.0,
                measured_load=42.0,
                estimated_load=0.0,
                duration_data_count=1,
                distance_data_count=1,
                elevation_data_count=1,
                measured_load_data_count=1,
                estimated_load_data_count=0,
            )

    athlete_id = uuid4()
    service = RecentTrainingLoadService(
        comparison_service,
        reference_date_provider=lambda: TARGET_DATE,
        training_stats_service=FakeTrainingStatsService(),
    )

    result = service.analysis_summary(athlete_id, days=1)

    assert result["period"] == {
        "start_date": comparison_date.isoformat(),
        "end_date": comparison_date.isoformat(),
        "nb_days": 1,
        "inclusive": True,
    }
    assert result["load"]["planned_total"] == 35.0
    assert result["load"]["actual_total"] == 42.0
    assert result["volume"]["duration_minutes"] == 60
    assert result["volume"]["distance_km"] == 10.0
    assert comparison_service.calls == [comparison_date]
    assert stats_calls == [(athlete_id, TARGET_DATE, 1, False)]
