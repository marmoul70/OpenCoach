from datetime import date

from opencoach.integrations.coros.wellness_mapper import (
    map_coros_wellness,
)


def test_maps_common_coros_wellness_fields() -> None:
    wellness = map_coros_wellness(
        "daily_health",
        {
            "restingHeartRate": 48,
            "hrv": 72.5,
            "sleepDurationSeconds": 27_000,
            "sleepScore": 86,
            "averageSleepingHeartRate": 43,
            "spo2": 97,
            "stepCount": 8_250,
            "fitnessCtl": 54.2,
            "fatigueAtl": 61.8,
            "rampRate": 4.1,
            "updatedAt": "2026-11-04T04:30:00Z",
        },
        date(2026, 11, 4),
    )

    assert wellness.provider == "coros"
    assert wellness.date == date(2026, 11, 4)
    assert wellness.resting_hr == 48
    assert wellness.hrv == 72.5
    assert wellness.sleep_seconds == 27_000
    assert wellness.sleep_score == 86
    assert wellness.avg_sleeping_hr == 43
    assert wellness.spo2 == 97
    assert wellness.steps == 8_250
    assert wellness.fitness_ctl == 54.2
    assert wellness.fatigue_atl == 61.8
    assert wellness.ramp_rate == 4.1
    assert wellness.provider_updated_at is not None


def test_maps_nested_fields_and_sleep_minutes() -> None:
    wellness = map_coros_wellness(
        "sleep",
        {
            "sleep": {
                "sleepDurationMinutes": 450,
                "sleepQualityScore": 91,
            },
        },
        date(2026, 11, 3),
    )

    assert wellness.sleep_seconds == 27_000
    assert wellness.sleep_score == 91


def test_missing_or_invalid_metrics_remain_none() -> None:
    wellness = map_coros_wellness(
        "hrv",
        {
            "hrv": "not-a-number",
            "restingHeartRate": True,
            "spo2": float("nan"),
            "steps": -2,
        },
        date(2026, 11, 4),
    )

    assert wellness.hrv is None
    assert wellness.resting_hr is None
    assert wellness.spo2 is None
    assert wellness.steps is None


def test_mapper_does_not_invent_metrics_from_empty_payload() -> None:
    wellness = map_coros_wellness(
        "stress",
        {"stressLevel": "high"},
        date(2026, 11, 4),
    )

    assert wellness.provider == "coros"
    assert wellness.date == date(2026, 11, 4)
    assert wellness.resting_hr is None
    assert wellness.hrv is None
    assert wellness.sleep_seconds is None
    assert wellness.sleep_score is None



def test_parses_coros_sleep_report_using_wake_up_date() -> None:
    from opencoach.integrations.coros.wellness_mapper import map_coros_wellness_report

    report = """Sleep Overview
========================
Note: each record below is dated by its wake-up day.

2026-11-02
Sleep Score: 90
Daily Sleep: 9h 55min (incl. naps)
Main Sleep (asleep): 9h 55min
Main Sleep Period (incl. awake): 10h 11min
Deep Sleep Ratio: 22%
Light Sleep Ratio: 56%
REM Ratio: 19%
Awake Ratio: 3%
"""
    days = map_coros_wellness_report(
        "sleep", {"data": report}, date(2026, 11, 3)
    )

    assert len(days) == 1
    assert days[0].date == date(2026, 11, 2)
    assert days[0].sleep_score == 90
    assert days[0].sleep_seconds == 35_700


def test_parses_coros_hrv_assessment_and_training_load_reports() -> None:
    from opencoach.integrations.coros.wellness_mapper import map_coros_wellness_report

    hrv = """Sleep HRV — Last 2 days
2026-11-02:
  HRV Avg: 43 ms — Normal
  Normal Range: 34 - 48 ms
  Baseline: 41 ms
2026-11-03:
  HRV Avg: 46 ms — Normal
  Normal Range: 35 - 49 ms
  Baseline: 42 ms
"""
    hrv_days = map_coros_wellness_report("hrv", {"data": hrv}, date(2026, 11, 3))
    assert [(item.date, item.hrv) for item in hrv_days] == [
        (date(2026, 11, 2), 43.0),
        (date(2026, 11, 3), 46.0),
    ]

    load = """Training Load Assessment
2026-11-03
Comment: Optimized
Short-Term Load: 55
Long-Term Load: 55
Load Ratio: 1.00
"""
    load_days = map_coros_wellness_report("training_load", {"data": load}, date(2026, 11, 3))
    assert len(load_days) == 1
    assert load_days[0].fatigue_atl == 55
    assert load_days[0].fitness_ctl == 55
    assert load_days[0].ramp_rate is None


def test_parses_daily_health_steps_sleep_hr_and_latest_resting_hr() -> None:
    from opencoach.integrations.coros.wellness_mapper import map_coros_wellness_report

    report = """Daily Health Data — Last 2 days | Resting HR: 54 bpm | HRV Baseline: 42 ms
--- 20261102 ---
Steps: 5,266 | Calories: 291 kcal | Exercise: 2 min
Stress: Avg 19
Sleep Summary:
  Total: 10h 11min | Deep: 2h 14min | Light: 5h 44min | REM: 1h 57min | Awake: 16 min
  Sleep HR: Avg 49 bpm | Min 42 bpm | Max 74 bpm

--- 20261103 ---
Steps: 10,148 | Calories: 838 kcal | Exercise: 33 min
Stress: Avg 33
Sleep Summary:
  Total: 7h 24min | Deep: 51 min | Light: 4h 30min | REM: 1h 46min | Awake: 17 min
  Sleep HR: Avg 50 bpm | Min 44 bpm | Max 73 bpm
"""
    days = map_coros_wellness_report("daily_health", {"data": report}, date(2026, 11, 3))
    assert len(days) == 2
    assert days[0].date == date(2026, 11, 2)
    assert days[0].steps == 5_266
    assert days[0].avg_sleeping_hr == 49
    assert days[0].resting_hr is None
    assert days[1].date == date(2026, 11, 3)
    assert days[1].sleep_seconds == 26_640
    assert days[1].resting_hr == 54
