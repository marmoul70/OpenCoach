from datetime import date, timedelta

from opencoach.models import WellnessDay
from opencoach.readiness import (
    calculate_readiness_baseline,
)


CURRENT_DATE = date(
    2026,
    8,
    18,
)

WINDOW_DAYS = 14
MINIMUM_SAMPLES = 7

def create_wellness_day(
    days_before: int,
    *,
    hrv: float | None = 50.0,
    resting_hr: int | None = 45,
    sleep_seconds: int | None = 28800,
    sleep_score: float | None = 80.0,
) -> WellnessDay:
    return WellnessDay(
        provider="intervals",
        date=(
            CURRENT_DATE
            - timedelta(
                days=days_before,
            )
        ),
        hrv=hrv,
        resting_hr=resting_hr,
        sleep_seconds=sleep_seconds,
        sleep_score=sleep_score,
    )


def test_baseline_uses_previous_14_days() -> None:
    wellness_days = [
        create_wellness_day(
            day,
            hrv=float(40 + day),
        )
        for day in range(
            1,
            15,
        )
    ]

    result = calculate_readiness_baseline(
        wellness_days,
        current_date=CURRENT_DATE,
        window_days=WINDOW_DAYS,
        minimum_samples=MINIMUM_SAMPLES,
    )

    assert result.start_date == date(
        2026,
        8,
        4,
    )

    assert result.end_date == date(
        2026,
        8,
        17,
    )

    assert result.hrv.sample_count == 14
    assert result.hrv.reliable is True


def test_baseline_excludes_current_day() -> None:
    wellness_days = [
        create_wellness_day(
            day,
            hrv=50.0,
        )
        for day in range(
            1,
            15,
        )
    ]

    wellness_days.append(
        WellnessDay(
            provider="intervals",
            date=CURRENT_DATE,
            hrv=200.0,
        )
    )

    result = calculate_readiness_baseline(
        wellness_days,
        current_date=CURRENT_DATE,
        window_days=WINDOW_DAYS,
        minimum_samples=MINIMUM_SAMPLES,
    )

    assert result.hrv.median == 50.0


def test_baseline_uses_median() -> None:
    wellness_days = [
        create_wellness_day(
            day,
            hrv=50.0,
        )
        for day in range(
            1,
            14,
        )
    ]

    wellness_days.append(
        create_wellness_day(
            14,
            hrv=200.0,
        )
    )

    result = calculate_readiness_baseline(
        wellness_days,
        current_date=CURRENT_DATE,
        window_days=WINDOW_DAYS,
        minimum_samples=MINIMUM_SAMPLES,
    )

    assert result.hrv.median == 50.0


def test_baseline_is_unreliable_with_too_few_samples() -> None:
    wellness_days = [
        create_wellness_day(day)
        for day in range(
            1,
            5,
        )
    ]

    result = calculate_readiness_baseline(
        wellness_days,
        current_date=CURRENT_DATE,
        window_days=WINDOW_DAYS,
        minimum_samples=MINIMUM_SAMPLES,
    )

    assert result.hrv.sample_count == 4
    assert result.hrv.reliable is False


def test_baseline_handles_missing_metric_values() -> None:
    wellness_days = [
        create_wellness_day(
            day,
            hrv=(
                50.0
                if day <= 8
                else None
            ),
        )
        for day in range(
            1,
            15,
        )
    ]

    result = calculate_readiness_baseline(
        wellness_days,
        current_date=CURRENT_DATE,
        window_days=WINDOW_DAYS,
        minimum_samples=MINIMUM_SAMPLES,
    )

    assert result.hrv.sample_count == 8
    assert result.hrv.median == 50.0
    assert result.hrv.reliable is True


def test_baseline_returns_empty_metric_when_no_data() -> None:
    wellness_days = [
        create_wellness_day(
            day,
            hrv=None,
        )
        for day in range(
            1,
            15,
        )
    ]

    result = calculate_readiness_baseline(
        wellness_days,
        current_date=CURRENT_DATE,
        window_days=WINDOW_DAYS,
        minimum_samples=MINIMUM_SAMPLES,
    )

    assert result.hrv.median is None
    assert result.hrv.sample_count == 0
    assert result.hrv.reliable is False


def test_baseline_calculates_all_supported_metrics() -> None:
    wellness_days = [
        create_wellness_day(
            day,
            hrv=52.0,
            resting_hr=46,
            sleep_seconds=27000,
            sleep_score=78.0,
        )
        for day in range(
            1,
            15,
        )
    ]

    result = calculate_readiness_baseline(
        wellness_days,
        current_date=CURRENT_DATE,
        window_days=WINDOW_DAYS,
        minimum_samples=MINIMUM_SAMPLES,
    )

    assert result.hrv.median == 52.0
    assert result.resting_hr.median == 46.0
    assert result.sleep_seconds.median == 27000.0
    assert result.sleep_score.median == 78.0
