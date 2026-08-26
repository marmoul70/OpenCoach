from datetime import date

from opencoach.models import (
    WellnessDay,
)
from opencoach.wellness_trends import (
    build_wellness_trends,
)


def test_wellness_trend_calculates_average() -> None:
    days = [
        WellnessDay(
            provider="intervals",
            date=date(
                2026,
                8,
                24,
            ),
            hrv=40,
        ),
        WellnessDay(
            provider="intervals",
            date=date(
                2026,
                8,
                25,
            ),
            hrv=50,
        ),
        WellnessDay(
            provider="intervals",
            date=date(
                2026,
                8,
                26,
            ),
            hrv=60,
        ),
    ]

    result = build_wellness_trends(
        wellness_days=days,
        start_date=date(
            2026,
            8,
            20,
        ),
        end_date=date(
            2026,
            8,
            26,
        ),
        days=7,
    )

    assert result.hrv.current == 60
    assert result.hrv.average == 50
    assert result.hrv.sample_count == 3

    assert (
        result.hrv.change_percent
        == 20
    )

    assert (
        result.hrv.direction
        == "up"
    )


def test_missing_values_are_ignored() -> None:
    days = [
        WellnessDay(
            provider="intervals",
            date=date(
                2026,
                8,
                25,
            ),
            resting_hr=None,
        ),
        WellnessDay(
            provider="intervals",
            date=date(
                2026,
                8,
                26,
            ),
            resting_hr=48,
        ),
    ]

    result = build_wellness_trends(
        wellness_days=days,
        start_date=date(
            2026,
            8,
            20,
        ),
        end_date=date(
            2026,
            8,
            26,
        ),
        days=7,
    )

    assert (
        result.resting_hr.current
        == 48
    )

    assert (
        result.resting_hr.average
        == 48
    )

    assert (
        result.resting_hr.sample_count
        == 1
    )

    assert (
        result.resting_hr.direction
        == "stable"
    )


def test_empty_metric_returns_unknown() -> None:
    result = build_wellness_trends(
        wellness_days=[],
        start_date=date(
            2026,
            8,
            20,
        ),
        end_date=date(
            2026,
            8,
            26,
        ),
        days=7,
    )

    assert result.hrv.current is None
    assert result.hrv.average is None
    assert result.hrv.change_percent is None
    assert result.hrv.sample_count == 0

    assert (
        result.hrv.direction
        == "unknown"
    )
