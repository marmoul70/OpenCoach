from datetime import date, datetime, timezone

from opencoach.models import WellnessDay
from opencoach.wellness_aggregation import aggregate_wellness_days


DAY = date(2026, 11, 9)


def test_aggregator_merges_complementary_metrics_from_multiple_integrations():
    result = aggregate_wellness_days([
        WellnessDay(provider="coros", date=DAY, hrv=52.0, sleep_seconds=25200),
        WellnessDay(provider="intervals", date=DAY, resting_hr=47, stress_avg=18.0),
        WellnessDay(provider="garmin", date=DAY, spo2=97.0),
    ])

    assert len(result.days) == 1
    day = result.days[0]
    assert day.provider == "opencoach"
    assert day.hrv == 52.0
    assert day.sleep_seconds == 25200
    assert day.resting_hr == 47
    assert day.stress_avg == 18.0
    assert day.spo2 == 97.0
    assert result.metric_sources[DAY.isoformat()]["hrv"] == ("coros",)
    assert result.metric_sources[DAY.isoformat()]["resting_hr"] == ("intervals",)
    assert result.conflicts == {}


def test_aggregator_uses_latest_provider_update_per_metric():
    earlier = datetime(2026, 11, 9, 6, tzinfo=timezone.utc)
    later = datetime(2026, 11, 9, 8, tzinfo=timezone.utc)
    result = aggregate_wellness_days([
        WellnessDay(provider="coros", date=DAY, hrv=48.0, provider_updated_at=earlier),
        WellnessDay(provider="garmin", date=DAY, hrv=53.0, provider_updated_at=later),
    ])

    assert result.days[0].hrv == 53.0
    assert result.metric_sources[DAY.isoformat()]["hrv"] == ("garmin",)


def test_aggregator_does_not_guess_when_equally_fresh_values_conflict():
    timestamp = datetime(2026, 11, 9, 8, tzinfo=timezone.utc)
    result = aggregate_wellness_days([
        WellnessDay(provider="coros", date=DAY, hrv=48.0, provider_updated_at=timestamp),
        WellnessDay(provider="intervals", date=DAY, hrv=53.0, provider_updated_at=timestamp),
    ])

    assert result.days[0].hrv is None
    assert result.conflicts[DAY.isoformat()] == ("hrv",)
    assert "hrv" not in result.metric_sources[DAY.isoformat()]


def test_aggregator_does_not_guess_when_conflicting_values_have_no_timestamps():
    result = aggregate_wellness_days([
        WellnessDay(provider="coros", date=DAY, hrv=48.0),
        WellnessDay(provider="intervals", date=DAY, hrv=53.0),
    ])

    assert result.days[0].hrv is None
    assert result.conflicts[DAY.isoformat()] == ("hrv",)


def test_aggregator_does_not_compare_a_timestamped_value_with_an_undated_conflict():
    timestamp = datetime(2026, 11, 9, 8, tzinfo=timezone.utc)
    result = aggregate_wellness_days([
        WellnessDay(provider="coros", date=DAY, hrv=48.0),
        WellnessDay(provider="garmin", date=DAY, hrv=53.0, provider_updated_at=timestamp),
    ])

    assert result.days[0].hrv is None
    assert result.conflicts[DAY.isoformat()] == ("hrv",)


def test_aggregator_uses_opencoach_ingestion_time_when_provider_timestamp_is_missing():
    earlier = datetime(2026, 11, 9, 7, tzinfo=timezone.utc)
    later = datetime(2026, 11, 9, 9, tzinfo=timezone.utc)
    result = aggregate_wellness_days([
        WellnessDay(provider="coros", date=DAY, hrv=48.0, stored_at=earlier),
        WellnessDay(provider="garmin", date=DAY, hrv=53.0, stored_at=later),
    ])

    assert result.days[0].hrv == 53.0
    assert result.metric_sources[DAY.isoformat()]["hrv"] == ("garmin",)
