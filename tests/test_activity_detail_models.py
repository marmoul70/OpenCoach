from dataclasses import FrozenInstanceError

import pytest

from opencoach.models import (
    ActivityDetail,
    ActivityInterval,
    ActivityStream,
    ActivityStreams,
)


def test_activity_interval_supports_real_coach_data() -> None:
    interval = ActivityInterval(
        provider_interval_id="5935911",
        interval_type="WORK",
        label=None,
        start_index=0,
        end_index=364,
        start_time_seconds=0,
        end_time_seconds=364,
        distance_m=999.0,
        moving_time_seconds=364,
        elapsed_time_seconds=364,
        average_speed_mps=2.7445054,
        average_heart_rate=114.0,
        max_heart_rate=128.0,
        average_cadence=88.1,
        elevation_gain_m=5.2,
    )

    assert interval.interval_type == "WORK"
    assert interval.distance_m == 999.0


def test_activity_interval_rejects_invalid_indexes() -> None:
    with pytest.raises(
        ValueError,
        match="end_index",
    ):
        ActivityInterval(
            provider_interval_id=None,
            interval_type=None,
            label=None,
            start_index=10,
            end_index=5,
            start_time_seconds=0,
            end_time_seconds=10,
        )


def test_stream_accepts_missing_samples() -> None:
    stream = ActivityStream(
        stream_type="distance",
        data=(
            0.0,
            None,
            None,
            9.0,
        ),
    )

    assert len(stream.data) == 4
    assert stream.data[1] is None


def test_activity_streams_lists_available_types() -> None:
    streams = ActivityStreams(
        time=ActivityStream(
            stream_type="time",
            data=(0, 1, 2),
        ),
        heartrate=ActivityStream(
            stream_type="heartrate",
            data=(120, 125, 130),
        ),
    )

    assert streams.available_types == (
        "time",
        "heartrate",
    )


def test_activity_detail_is_immutable() -> None:
    detail = ActivityDetail(
        provider_activity_id="i123",
    )

    with pytest.raises(
        FrozenInstanceError,
    ):
        detail.provider_activity_id = "i456"



def test_activity_stream_summary_reuses_finite_numeric_sample_rules() -> None:
    stream = ActivityStream(
        stream_type="heartrate",
        data=(120, None, 140.5, True, float("nan"), float("inf")),
    )

    assert stream.summary == {
        "samples": 6,
        "valid_samples": 2,
        "minimum": 120.0,
        "maximum": 140.5,
        "average": 130.25,
    }


def test_empty_activity_stream_summary_keeps_metrics_unavailable() -> None:
    stream = ActivityStream(stream_type="watts", data=())

    assert stream.summary == {
        "samples": 0,
        "valid_samples": 0,
        "minimum": None,
        "maximum": None,
        "average": None,
    }
