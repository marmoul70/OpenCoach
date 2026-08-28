import pytest

from opencoach.integrations.intervals.activity_detail_mapper import (
    map_intervals_activity_detail,
)
from opencoach.integrations.intervals.errors import (
    IntervalsDataError,
)


def create_detail() -> dict:
    return {
        "id": "i176833684",
        "icu_lap_count": 21,
        "interval_summary": [
            "6x 61s 154bpm",
            "5x 73s 159bpm",
        ],
        "icu_intervals": [
            {
                "id": 5935911,
                "type": "WORK",
                "label": None,
                "start_index": 0,
                "end_index": 364,
                "start_time": 0,
                "end_time": 364,
                "distance": 999.0,
                "moving_time": 364,
                "elapsed_time": 364,
                "average_speed": 2.7445054,
                "average_heartrate": 114,
                "max_heartrate": 128,
                "average_cadence": 88.103935,
                "total_elevation_gain": 5.200012,
                "training_load": None,
            },
        ],
    }


def create_streams() -> list[dict]:
    return [
        {
            "type": "time",
            "data": [
                0,
                1,
                2,
            ],
        },
        {
            "type": "heartrate",
            "data": [
                79,
                80,
                81,
            ],
        },
        {
            "type": "distance",
            "data": [
                0.0,
                None,
                9.0,
            ],
        },
        {
            "type": "velocity_smooth",
            "data": [
                None,
                2.7,
                2.8,
            ],
        },
        {
            "type": "cadence",
            "data": [
                None,
                85,
                86,
            ],
        },
        {
            "type": "watts",
            "data": [
                None,
                152,
                143,
            ],
        },
    ]


def test_mapper_builds_activity_detail() -> None:
    result = map_intervals_activity_detail(
        create_detail(),
        create_streams(),
    )

    assert (
        result.provider_activity_id
        == "i176833684"
    )

    assert result.provider_lap_count == 21

    assert result.interval_summary == (
        "6x 61s 154bpm",
        "5x 73s 159bpm",
    )

    assert len(result.intervals) == 1

    interval = result.intervals[0]

    assert (
        interval.provider_interval_id
        == "5935911"
    )

    assert interval.interval_type == "WORK"
    assert interval.distance_m == 999.0
    assert interval.average_heart_rate == 114.0


def test_mapper_builds_all_supported_streams() -> None:
    result = map_intervals_activity_detail(
        create_detail(),
        create_streams(),
    )

    assert (
        result.streams.available_types
        == (
            "time",
            "distance",
            "heartrate",
            "velocity_smooth",
            "cadence",
            "watts",
        )
    )

    assert result.streams.time is not None
    assert result.streams.time.data == (
        0,
        1,
        2,
    )

    assert result.streams.distance is not None
    assert result.streams.distance.data == (
        0.0,
        None,
        9.0,
    )


def test_mapper_ignores_gps_streams() -> None:
    streams = create_streams()

    streams.append(
        {
            "type": "latlng",
            "data": [
                [47.0, 6.0],
            ],
        }
    )

    result = map_intervals_activity_detail(
        create_detail(),
        streams,
    )

    assert (
        "latlng"
        not in result.streams.available_types
    )


def test_mapper_ignores_altitude_for_now() -> None:
    streams = create_streams()

    streams.append(
        {
            "type": "altitude",
            "data": [
                300.0,
                301.0,
            ],
        }
    )

    result = map_intervals_activity_detail(
        create_detail(),
        streams,
    )

    assert (
        "altitude"
        not in result.streams.available_types
    )


def test_mapper_accepts_missing_optional_streams() -> None:
    result = map_intervals_activity_detail(
        create_detail(),
        [
            {
                "type": "time",
                "data": [
                    0,
                    1,
                ],
            },
        ],
    )

    assert result.streams.time is not None
    assert result.streams.heartrate is None
    assert result.streams.watts is None


def test_mapper_rejects_invalid_intervals() -> None:
    detail = create_detail()

    detail["icu_intervals"] = "invalid"

    with pytest.raises(
        IntervalsDataError,
        match="icu_intervals",
    ):
        map_intervals_activity_detail(
            detail,
            create_streams(),
        )


def test_mapper_rejects_invalid_stream_data() -> None:
    streams = create_streams()

    streams[0]["data"] = "invalid"

    with pytest.raises(
        IntervalsDataError,
        match="stream",
    ):
        map_intervals_activity_detail(
            create_detail(),
            streams,
        )


def test_mapper_rejects_missing_activity_id() -> None:
    detail = create_detail()

    detail.pop("id")

    with pytest.raises(
        IntervalsDataError,
        match="id",
    ):
        map_intervals_activity_detail(
            detail,
            create_streams(),
        )
