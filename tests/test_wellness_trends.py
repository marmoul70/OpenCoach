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


def test_wellness_trends_include_coros_recovery_metrics() -> None:
    days = [
        WellnessDay(
            provider="coros",
            date=date(2026, 11, 3),
            hrv=42,
            hrv_baseline=40,
            stress_avg=31,
            sleep_deep_seconds=5400,
            sleep_light_seconds=14400,
            sleep_rem_seconds=6000,
            sleep_awake_seconds=900,
        ),
        WellnessDay(
            provider="coros",
            date=date(2026, 11, 4),
            hrv=46,
            hrv_baseline=41,
            stress_avg=24,
            sleep_deep_seconds=7200,
            sleep_light_seconds=16200,
            sleep_rem_seconds=6300,
            sleep_awake_seconds=600,
        ),
    ]

    result = build_wellness_trends(
        wellness_days=days,
        start_date=date(2026, 11, 3),
        end_date=date(2026, 11, 4),
        days=2,
    )

    assert result.hrv_baseline.current == 41
    assert result.stress_avg.current == 24
    assert result.sleep_deep_seconds.current == 7200
    assert result.sleep_light_seconds.current == 16200
    assert result.sleep_rem_seconds.current == 6300
    assert result.sleep_awake_seconds.current == 600
