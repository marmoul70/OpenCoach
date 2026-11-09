from datetime import date, timedelta
from uuid import uuid4

from opencoach.ai.recovery_tools import (
    RecoveryAnalysisArguments,
    build_recovery_analysis_tool,
)
from opencoach.coaching.daily_checkin import AthleteDailyCheckIn
from opencoach.models import DailyContext, WellnessDay


TARGET = date(2026, 11, 9)


class FakeWellnessRepository:
    def __init__(self, days):
        self.days = days
        self.providers = []

    def list_range(self, profile_id, start_date, end_date, *, provider=None):
        self.providers.append(provider)
        return [
            item for item in self.days
            if (provider is None or item.provider == provider) and start_date <= item.date <= end_date
        ]


class FakeDailyContextRepository:
    def __init__(self, context=None):
        self.context = context

    def get_by_date(self, profile_id, context_date):
        return self.context if self.context and self.context.date == context_date else None


class FakeTimeSeriesRepository:
    def __init__(self, snapshots=None):
        self.snapshots = snapshots or []
        self.calls = 0

    def list_time_series_snapshots(self, profile_id, start_date, end_date):
        self.calls += 1
        return self.snapshots


class FakeDailyCheckInRepository:
    def __init__(self, checkin=None):
        self.checkin = checkin

    def get_for_date(self, profile_id, checkin_date):
        return self.checkin if self.checkin and self.checkin.date == checkin_date else None


def test_recovery_analysis_returns_7_14_30_day_sleep_and_fatigue_data():
    profile_id = uuid4()
    wellness = FakeWellnessRepository([
        WellnessDay(
            provider="coros",
            date=TARGET - timedelta(days=offset),
            hrv=55.0 + offset,
            resting_hr=48 + offset % 2,
            stress_avg=20.0 + offset,
            sleep_seconds=7 * 3600 + offset * 60,
            sleep_score=80.0 - offset,
            sleep_quality=4,
            spo2=97.0,
            fatigue_atl=65.0 + offset,
            fitness_ctl=72.0,
        )
        for offset in range(10)
    ])
    context = FakeDailyContextRepository(DailyContext(
        date=TARGET,
        fatigue_subjective=4,
        pain_level=1,
        illness_status="none",
        treatment_impact="none",
        motivation=3,
    ))
    checkin = FakeDailyCheckInRepository(AthleteDailyCheckIn(
        date=TARGET,
        energy_rating=2,
        pain_wellness_rating=4,
    ))
    time_series = FakeTimeSeriesRepository()

    tool = build_recovery_analysis_tool(
        wellness, context, time_series, checkin, profile_id
    )
    result = tool.handler(RecoveryAnalysisArguments(target_date=TARGET))

    assert result["provider"] == "opencoach"
    assert result["data_store"] == "OpenCoach"
    assert result["data_status"] == "fresh"
    assert [window["days"] for window in result["windows"]] == [7, 14, 30]
    assert result["windows"][0]["recorded_days"] == 7
    assert result["windows"][0]["metrics"]["sleep_seconds"]["sample_count"] == 7
    assert result["windows"][0]["metrics"]["sleep_quality"]["current"] == 4.0
    assert result["windows"][0]["metrics"]["spo2"]["current"] == 97.0
    assert result["daily_context"]["fatigue"] == 4
    assert result["daily_checkin"]["energy_rating"] == 2
    assert result["daily_checkin"]["pain_wellness_rating"] == 4
    assert time_series.calls == 0


def test_recovery_analysis_uses_intervals_fallback_without_coros_timeseries():
    profile_id = uuid4()
    wellness = FakeWellnessRepository([
        WellnessDay(
            provider="intervals",
            date=TARGET,
            sleep_seconds=6 * 3600,
            hrv=42.0,
        )
    ])
    time_series = FakeTimeSeriesRepository()
    tool = build_recovery_analysis_tool(
        wellness,
        FakeDailyContextRepository(),
        time_series,
        FakeDailyCheckInRepository(),
        profile_id,
    )

    result = tool.handler(RecoveryAnalysisArguments(target_date=TARGET))

    assert result["provider"] == "opencoach"
    assert result["data_store"] == "OpenCoach"
    assert result["windows"][0]["metrics"]["sleep_seconds"]["current"] == 21600
    assert result["time_series"] == []
    assert time_series.calls == 0


def test_recovery_analysis_keeps_missing_data_unknown_and_requests_subjective_followup():
    profile_id = uuid4()
    tool = build_recovery_analysis_tool(
        FakeWellnessRepository([]),
        FakeDailyContextRepository(),
        FakeTimeSeriesRepository(),
        FakeDailyCheckInRepository(),
        profile_id,
    )

    result = tool.handler(RecoveryAnalysisArguments(target_date=TARGET))

    assert result["provider"] is None
    assert result["data_status"] == "unavailable"
    assert result["windows"][0]["metrics"]["hrv"]["current"] is None
    assert result["windows"][0]["metrics"]["sleep_seconds"]["current"] is None
    assert result["daily_context"] is None
    assert result["daily_checkin"] is None
    assert any("ressenti subjectif" in warning for warning in result["warnings"])


def test_recovery_analysis_merges_complementary_metrics_from_all_opencoach_imports():
    profile_id = uuid4()
    wellness = FakeWellnessRepository([
        WellnessDay(
            provider="coros",
            date=TARGET,
            hrv=52.0,
            sleep_seconds=7 * 3600,
        ),
        WellnessDay(
            provider="intervals",
            date=TARGET,
            resting_hr=47,
            stress_avg=18.0,
        ),
        WellnessDay(
            provider="garmin",
            date=TARGET - timedelta(days=1),
            hrv=49.0,
            sleep_seconds=6 * 3600,
        ),
    ])
    tool = build_recovery_analysis_tool(
        wellness,
        FakeDailyContextRepository(),
        FakeTimeSeriesRepository(),
        FakeDailyCheckInRepository(),
        profile_id,
    )

    result = tool.handler(RecoveryAnalysisArguments(target_date=TARGET))

    current = result["windows"][0]["metrics"]
    assert result["provider"] == "opencoach"
    assert current["hrv"]["current"] == 52.0
    assert current["resting_hr"]["current"] == 47.0
    assert current["stress_avg"]["current"] == 18.0
    assert current["sleep_seconds"]["current"] == 7 * 3600
    assert result["metric_sources"][TARGET.isoformat()]["hrv"] == ("coros",)
    assert result["metric_sources"][TARGET.isoformat()]["resting_hr"] == ("intervals",)
    assert result["windows"][0]["recorded_days"] == 2
