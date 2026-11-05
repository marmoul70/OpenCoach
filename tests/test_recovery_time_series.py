from datetime import date

from opencoach.recovery_assessment import (
    aggregate_coros_time_series,
    build_recovery_assessment,
)


def test_time_series_aggregation_deduplicates_overlapping_coros_sources():
    snapshots = [
        {
            "category": "hrv_timeseries",
            "payload": {
                "samples": [
                    {
                        "metric": "sleep_hrv",
                        "measured_at": "2026-11-02T23:00:00+00:00",
                        "source_date": "2026-11-03",
                        "value": 48,
                        "unit": "ms",
                        "status": "normal",
                    },
                    {
                        "metric": "sleep_hrv",
                        "measured_at": "2026-11-02T23:05:00+00:00",
                        "source_date": "2026-11-03",
                        "value": 52,
                        "unit": "ms",
                        "status": "normal",
                    },
                ],
            },
        },
        {
            "category": "health_check_points",
            "payload": {
                "samples": [
                    {
                        "metric": "sleep_hrv",
                        "measured_at": "2026-11-02T23:00:00+00:00",
                        "source_date": "2026-11-03",
                        "value": 48,
                        "unit": "ms",
                        "status": "normal",
                    },
                    {
                        "metric": "heart_rate",
                        "measured_at": "2026-11-02T23:00:00+00:00",
                        "source_date": "2026-11-03",
                        "value": 44,
                        "unit": "bpm",
                    },
                ],
            },
        },
        {
            "category": "stress_points",
            "payload": {
                "samples": [
                    {
                        "metric": "stress",
                        "measured_at": "2026-10-30T10:00:00+00:00",
                        "source_date": "2026-10-30",
                        "value": 32,
                        "unit": "score",
                    },
                    {
                        "metric": "stress",
                        "measured_at": "2026-11-04T10:00:00+00:00",
                        "value": float("nan"),
                        "unit": "score",
                    },
                    {
                        "metric": "stress",
                        "measured_at": "2026-10-01T10:00:00+00:00",
                        "value": 99,
                        "unit": "score",
                    },
                ],
            },
        },
    ]

    result = aggregate_coros_time_series(
        snapshots,
        start_date=date(2026, 10, 29),
        end_date=date(2026, 11, 4),
    )

    by_metric = {item.metric: item for item in result}
    hrv = by_metric["sleep_hrv"]
    assert hrv.sample_count == 2
    assert hrv.average == 50
    assert hrv.minimum == 48
    assert hrv.maximum == 52
    assert hrv.unit == "ms"
    assert hrv.coverage_days == 1
    assert hrv.source_categories == (
        "health_check_points",
        "hrv_timeseries",
    )

    stress = by_metric["stress"]
    assert stress.sample_count == 1
    assert stress.current == 32
    assert "heart_rate" in by_metric


def test_recovery_assessment_serializes_time_series_without_changing_readiness():
    assessment = build_recovery_assessment(
        wellness_days=[],
        target_date=date(2026, 11, 4),
        provider="coros",
        time_series_snapshots=[
            {
                "category": "stress_points",
                "payload": {
                    "samples": [
                        {
                            "metric": "stress",
                            "measured_at": "2026-11-04T08:00:00+00:00",
                            "value": 27,
                            "unit": "score",
                        },
                    ],
                },
            },
        ],
    )

    from opencoach.recovery_assessment import recovery_assessment_to_dict

    payload = recovery_assessment_to_dict(assessment)
    assert assessment.data_status == "unavailable"
    assert payload["time_series"][0]["metric"] == "stress"
    assert payload["time_series"][0]["sample_count"] == 1
    assert payload["time_series"][0]["current"] == 27
