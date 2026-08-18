from datetime import date

from opencoach.models import WellnessDay
from opencoach.readiness import (
    MetricBaseline,
    ReadinessBaseline,
    compare_with_baseline,
)


def create_baseline() -> ReadinessBaseline:
    return ReadinessBaseline(
        start_date=date(
            2026,
            8,
            4,
        ),
        end_date=date(
            2026,
            8,
            17,
        ),
        hrv=MetricBaseline(
            median=52.0,
            sample_count=14,
            reliable=True,
        ),
        resting_hr=MetricBaseline(
            median=46.0,
            sample_count=14,
            reliable=True,
        ),
        sleep_seconds=MetricBaseline(
            median=27060.0,
            sample_count=14,
            reliable=True,
        ),
        sleep_score=MetricBaseline(
            median=78.0,
            sample_count=14,
            reliable=True,
        ),
    )


def create_current_day() -> WellnessDay:
    return WellnessDay(
        provider="intervals",
        date=date(
            2026,
            8,
            18,
        ),
        hrv=43.0,
        resting_hr=51,
        sleep_seconds=20520,
        sleep_score=61.0,
    )


def test_comparison_calculates_hrv_delta() -> None:
    result = compare_with_baseline(
        create_current_day(),
        create_baseline(),
    )

    assert result.hrv.current == 43.0
    assert result.hrv.baseline == 52.0
    assert result.hrv.absolute_delta == -9.0
    assert result.hrv.percent_delta == -17.3
    assert result.hrv.reliable is True


def test_comparison_calculates_resting_hr_delta() -> None:
    result = compare_with_baseline(
        create_current_day(),
        create_baseline(),
    )

    assert result.resting_hr.current == 51.0
    assert result.resting_hr.baseline == 46.0
    assert result.resting_hr.absolute_delta == 5.0
    assert result.resting_hr.percent_delta == 10.9


def test_comparison_calculates_sleep_delta() -> None:
    result = compare_with_baseline(
        create_current_day(),
        create_baseline(),
    )

    assert result.sleep_seconds.current == 20520.0
    assert result.sleep_seconds.baseline == 27060.0
    assert result.sleep_seconds.absolute_delta == -6540.0
    assert result.sleep_seconds.percent_delta == -24.2


def test_comparison_handles_missing_current_value() -> None:
    current = create_current_day()
    current.hrv = None

    result = compare_with_baseline(
        current,
        create_baseline(),
    )

    assert result.hrv.current is None
    assert result.hrv.absolute_delta is None
    assert result.hrv.percent_delta is None
    assert result.hrv.reliable is False


def test_comparison_preserves_unreliable_baseline() -> None:
    baseline = create_baseline()

    baseline = ReadinessBaseline(
        start_date=baseline.start_date,
        end_date=baseline.end_date,
        hrv=MetricBaseline(
            median=52.0,
            sample_count=3,
            reliable=False,
        ),
        resting_hr=baseline.resting_hr,
        sleep_seconds=baseline.sleep_seconds,
        sleep_score=baseline.sleep_score,
    )

    result = compare_with_baseline(
        create_current_day(),
        baseline,
    )

    assert result.hrv.percent_delta == -17.3
    assert result.hrv.reliable is False


def test_comparison_handles_missing_baseline() -> None:
    baseline = create_baseline()

    baseline = ReadinessBaseline(
        start_date=baseline.start_date,
        end_date=baseline.end_date,
        hrv=MetricBaseline(
            median=None,
            sample_count=0,
            reliable=False,
        ),
        resting_hr=baseline.resting_hr,
        sleep_seconds=baseline.sleep_seconds,
        sleep_score=baseline.sleep_score,
    )

    result = compare_with_baseline(
        create_current_day(),
        baseline,
    )

    assert result.hrv.baseline is None
    assert result.hrv.absolute_delta is None
    assert result.hrv.percent_delta is None
    assert result.hrv.reliable is False
