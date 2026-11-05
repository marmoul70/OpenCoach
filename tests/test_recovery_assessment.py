from datetime import date, timedelta

from opencoach.models import DailyContext, WellnessDay
from opencoach.recovery_assessment import build_recovery_assessment


TARGET = date(2026, 11, 4)


def test_recovery_assessment_builds_7_14_30_day_windows() -> None:
    days = [
        WellnessDay(
            provider="coros",
            date=TARGET - timedelta(days=offset),
            hrv=40 + offset,
            stress_avg=20 + offset,
            sleep_seconds=7 * 3600,
        )
        for offset in range(10)
    ]

    result = build_recovery_assessment(
        wellness_days=days,
        target_date=TARGET,
        provider="coros",
    )

    assert [window.days for window in result.windows] == [7, 14, 30]
    assert result.windows[0].recorded_days == 7
    assert result.windows[0].coverage_ratio == 1.0
    assert result.windows[0].metrics["hrv"].current == 40.0
    assert result.windows[1].recorded_days == 10
    assert result.windows[1].coverage_ratio == 10 / 14
    assert result.windows[2].recorded_days == 10


def test_recovery_assessment_does_not_mix_providers_or_future_data() -> None:
    days = [
        WellnessDay(provider="coros", date=TARGET, hrv=45),
        WellnessDay(provider="intervals", date=TARGET, hrv=99),
        WellnessDay(provider="coros", date=TARGET + timedelta(days=1), hrv=100),
    ]

    result = build_recovery_assessment(
        wellness_days=days,
        target_date=TARGET,
        provider="coros",
    )

    assert result.windows[0].metrics["hrv"].current == 45.0
    assert result.source_date == TARGET
    assert result.data_status == "fresh"


def test_recovery_assessment_keeps_missing_metrics_unknown() -> None:
    result = build_recovery_assessment(
        wellness_days=[
            WellnessDay(provider="coros", date=TARGET, hrv=None)
        ],
        target_date=TARGET,
        provider="coros",
    )

    metric = result.windows[0].metrics["hrv"]
    assert metric.current is None
    assert metric.average is None
    assert metric.sample_count == 0
    assert metric.coverage_days == 0


def test_recovery_assessment_separates_subjective_fatigue() -> None:
    context = DailyContext(
        date=TARGET,
        fatigue_subjective=4,
        pain_level=2,
        illness_status="mild",
        treatment_impact="none",
        motivation=3,
    )

    result = build_recovery_assessment(
        wellness_days=[],
        target_date=TARGET,
        provider="coros",
        subjective_context=context,
    )

    assert result.data_status == "unavailable"
    assert result.subjective is not None
    assert result.subjective.fatigue == 4
    assert result.subjective.pain == 2


def test_recovery_assessment_ignores_subjective_context_from_another_day() -> None:
    context = DailyContext(
        date=TARGET - timedelta(days=1),
        fatigue_subjective=5,
        pain_level=0,
    )

    result = build_recovery_assessment(
        wellness_days=[],
        target_date=TARGET,
        provider="coros",
        subjective_context=context,
    )

    assert result.subjective is None
