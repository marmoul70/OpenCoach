from datetime import date, timedelta

from opencoach.training import (
    RecentTrainingLoad,
    TrainingLoadComparison,
    assess_recent_training_load,
)


TARGET_DATE = date(
    2026,
    8,
    20,
)


def create_comparison(
    *,
    offset: int,
    status: str,
    planned_load: float,
    actual_load: float,
) -> TrainingLoadComparison:
    return TrainingLoadComparison(
        date=(
            TARGET_DATE
            - timedelta(
                days=offset,
            )
        ),
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


def create_recent_load(
    days: tuple[
        TrainingLoadComparison,
        ...,
    ],
) -> RecentTrainingLoad:
    return RecentTrainingLoad(
        days=days,
        analyzed_days=len(
            days,
        ),
        planned_load_total=sum(
            day.planned_load
            for day in days
        ),
        actual_load_total=sum(
            day.actual_load
            for day in days
        ),
        above_plan_days=sum(
            day.status == "above_plan"
            for day in days
        ),
        below_plan_days=sum(
            day.status == "below_plan"
            for day in days
        ),
        on_plan_days=sum(
            day.status == "on_plan"
            for day in days
        ),
        broken_rest_days=sum(
            day.status == "rest_broken"
            for day in days
        ),
        respected_rest_days=sum(
            day.status == "rest_respected"
            for day in days
        ),
    )


def test_recent_load_signals_empty_history() -> None:
    assessment = assess_recent_training_load(
        create_recent_load(
            (),
        )
    )

    assert assessment.signals == ()
    assert assessment.has_warning is False
    assert assessment.has_critical is False


def test_recent_load_signals_detects_yesterday_overload() -> None:
    recent_load = create_recent_load(
        (
            create_comparison(
                offset=1,
                status="above_plan",
                planned_load=30.0,
                actual_load=50.0,
            ),
        )
    )

    assessment = (
        assess_recent_training_load(
            recent_load,
        )
    )

    assert len(
        assessment.signals,
    ) == 1

    signal = (
        assessment.signals[0]
    )

    assert signal.kind == "recent_overload"
    assert signal.level == "warning"

    assert assessment.has_overload is True


def test_recent_load_signals_detects_repeated_overload() -> None:
    recent_load = create_recent_load(
        (
            create_comparison(
                offset=1,
                status="above_plan",
                planned_load=30.0,
                actual_load=45.0,
            ),
            create_comparison(
                offset=2,
                status="on_plan",
                planned_load=30.0,
                actual_load=30.0,
            ),
            create_comparison(
                offset=3,
                status="above_plan",
                planned_load=20.0,
                actual_load=35.0,
            ),
        )
    )

    assessment = (
        assess_recent_training_load(
            recent_load,
        )
    )

    kinds = {
        signal.kind
        for signal
        in assessment.signals
    }

    assert "recent_overload" in kinds
    assert "repeated_overload" in kinds

    assert assessment.has_critical is True


def test_recent_load_signals_detects_broken_rest_yesterday() -> None:
    recent_load = create_recent_load(
        (
            create_comparison(
                offset=1,
                status="rest_broken",
                planned_load=0.0,
                actual_load=20.0,
            ),
        )
    )

    assessment = (
        assess_recent_training_load(
            recent_load,
        )
    )

    assert len(
        assessment.signals,
    ) == 1

    assert (
        assessment.signals[0].kind
        == "broken_rest"
    )

    assert assessment.has_broken_rest is True
    assert assessment.has_warning is True


def test_recent_load_signals_detects_repeated_broken_rest() -> None:
    recent_load = create_recent_load(
        (
            create_comparison(
                offset=1,
                status="rest_broken",
                planned_load=0.0,
                actual_load=15.0,
            ),
            create_comparison(
                offset=2,
                status="rest_respected",
                planned_load=0.0,
                actual_load=0.0,
            ),
            create_comparison(
                offset=3,
                status="rest_broken",
                planned_load=0.0,
                actual_load=20.0,
            ),
        )
    )

    assessment = (
        assess_recent_training_load(
            recent_load,
        )
    )

    kinds = {
        signal.kind
        for signal
        in assessment.signals
    }

    assert "broken_rest" in kinds
    assert "repeated_broken_rest" in kinds

    assert assessment.has_critical is True


def test_recent_load_signals_do_not_flag_old_single_overload_as_recent() -> None:
    recent_load = create_recent_load(
        (
            create_comparison(
                offset=1,
                status="on_plan",
                planned_load=30.0,
                actual_load=30.0,
            ),
            create_comparison(
                offset=2,
                status="above_plan",
                planned_load=20.0,
                actual_load=30.0,
            ),
        )
    )

    assessment = (
        assess_recent_training_load(
            recent_load,
        )
    )

    assert assessment.signals == ()
    assert assessment.has_overload is False
