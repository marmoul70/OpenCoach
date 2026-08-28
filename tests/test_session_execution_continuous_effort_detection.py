from opencoach.models import (
    ActivityDetail,
    ActivityStream,
    ActivityStreams,
)
from opencoach.training.session_execution import (
    locate_continuous_effort_window,
)


def build_activity(
    *,
    include_distance=True,
    include_watts=True,
    include_cadence=True,
):
    times = tuple(
        float(second)
        for second in range(1201)
    )

    speeds = []
    watts = []
    cadence = []
    heart_rate = []
    distance = []

    cumulative_distance = 0.0

    for second in range(1201):
        # 5 min échauffement
        # 6 min test
        # puis retour au calme.
        in_test = (
            300 <= second < 660
        )

        speed = (
            4.1666666667
            if in_test
            else 2.0
        )

        power = (
            360.0
            if in_test
            else 180.0
        )

        cad = (
            96.0
            if in_test
            else 82.0
        )

        hr = (
            175.0
            if in_test
            else 140.0
        )

        speeds.append(speed)
        watts.append(power)
        cadence.append(cad)
        heart_rate.append(hr)

        if second > 0:
            previous_speed = speeds[
                second - 1
            ]

            cumulative_distance += (
                previous_speed
            )

        distance.append(
            cumulative_distance
        )

    return ActivityDetail(
        provider_activity_id="test",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=times,
            ),
            distance=(
                ActivityStream(
                    stream_type="distance",
                    data=tuple(distance),
                )
                if include_distance
                else None
            ),
            velocity_smooth=ActivityStream(
                stream_type="velocity_smooth",
                data=tuple(speeds),
            ),
            watts=(
                ActivityStream(
                    stream_type="watts",
                    data=tuple(watts),
                )
                if include_watts
                else None
            ),
            cadence=(
                ActivityStream(
                    stream_type="cadence",
                    data=tuple(cadence),
                )
                if include_cadence
                else None
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=tuple(heart_rate),
            ),
        ),
    )


def test_locates_six_minute_maximal_segment() -> None:
    result = locate_continuous_effort_window(
        build_activity(),
        target_duration_seconds=360.0,
    )

    assert result is not None

    assert (
        299.0
        <= result.start_time_seconds
        <= 301.0
    )

    assert (
        result.end_time_seconds
        == result.start_time_seconds
        + 360.0
    )


def test_measures_1500_meters_over_six_minutes() -> None:
    result = locate_continuous_effort_window(
        build_activity(),
        target_duration_seconds=360.0,
    )

    assert result is not None
    assert result.distance_m is not None

    assert (
        1495.0
        <= result.distance_m
        <= 1505.0
    )

    assert result.average_speed_mps is not None

    assert (
        4.15
        <= result.average_speed_mps
        <= 4.18
    )


def test_missing_watts_and_cadence_do_not_block_detection() -> None:
    result = locate_continuous_effort_window(
        build_activity(
            include_watts=False,
            include_cadence=False,
        ),
        target_duration_seconds=360.0,
    )

    assert result is not None

    assert (
        299.0
        <= result.start_time_seconds
        <= 301.0
    )


def test_missing_distance_falls_back_to_speed() -> None:
    result = locate_continuous_effort_window(
        build_activity(
            include_distance=False,
        ),
        target_duration_seconds=360.0,
    )

    assert result is not None

    assert result.distance_m is None
    assert result.average_speed_mps is not None

    assert (
        result.average_speed_mps
        > 4.1
    )


def test_missing_time_stream_returns_none() -> None:
    detail = ActivityDetail(
        provider_activity_id="test",
        streams=ActivityStreams(),
    )

    assert (
        locate_continuous_effort_window(
            detail,
            target_duration_seconds=360.0,
        )
        is None
    )


def test_activity_shorter_than_target_returns_none() -> None:
    detail = ActivityDetail(
        provider_activity_id="test",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=tuple(
                    range(100)
                ),
            ),
            velocity_smooth=ActivityStream(
                stream_type="velocity_smooth",
                data=tuple(
                    3.0
                    for _ in range(100)
                ),
            ),
        ),
    )

    assert (
        locate_continuous_effort_window(
            detail,
            target_duration_seconds=360.0,
        )
        is None
    )
