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
