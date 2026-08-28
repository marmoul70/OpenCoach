from opencoach.models import (
    ActivityDetail,
    ActivityStream,
    ActivityStreams,
)
from opencoach.training.session_execution import (
    IntervalSetPrescription,
    RepetitionTarget,
    select_evidenced_distance_repetitions,
)


def prescription(
    *,
    repetitions: int = 7,
) -> IntervalSetPrescription:
    return IntervalSetPrescription(
        repetitions=repetitions,
        work_distance_m=300.0,
        recovery_duration_seconds=60.0,
        repetition_target=RepetitionTarget(
            distance_m=300.0,
            target_duration_min_seconds=60.0,
            target_duration_max_seconds=80.0,
        ),
    )


def build_activity(
    work_durations: tuple[float, ...],
    *,
    strong_flags: tuple[bool, ...] | None = None,
) -> ActivityDetail:
    if strong_flags is None:
        strong_flags = tuple(
            True
            for _ in work_durations
        )

    time_values = []
    distance_values = []
    velocity_values = []
    cadence_values = []
    watts_values = []
    hr_values = []

    current_time = 0.0
    current_distance = 0.0
    current_hr = 125.0

    def append_second(
        *,
        speed: float,
        cadence: float,
        watts: float,
        hr_delta: float,
    ) -> None:
        nonlocal current_time
        nonlocal current_distance
        nonlocal current_hr

        time_values.append(
            current_time
        )
        distance_values.append(
            current_distance
        )
        velocity_values.append(
            speed
        )
        cadence_values.append(
            cadence
        )
        watts_values.append(
            watts
        )

        current_hr = min(
            180.0,
            max(
                90.0,
                current_hr + hr_delta,
            ),
        )

        hr_values.append(
            current_hr
        )

        current_distance += speed
        current_time += 1.0

    # Échauffement facile.
    for _ in range(120):
        append_second(
            speed=2.4,
            cadence=78.0,
            watts=180.0,
            hr_delta=0.02,
        )

    for index, duration in enumerate(
        work_durations
    ):
        strong = strong_flags[index]

        work_speed = (
            300.0
            / duration
        )

        steps = int(
            round(duration)
        )

        for _ in range(steps):
            append_second(
                speed=(
                    work_speed
                    if strong
                    else 2.7
                ),
                cadence=(
                    96.0
                    if strong
                    else 80.0
                ),
                watts=(
                    360.0
                    if strong
                    else 195.0
                ),
                hr_delta=(
                    0.35
                    if strong
                    else 0.02
                ),
            )

        # Récupération.
        if index < len(
            work_durations
        ) - 1:
            for _ in range(60):
                append_second(
                    speed=1.8,
                    cadence=70.0,
                    watts=140.0,
                    hr_delta=-0.12,
                )

    return ActivityDetail(
        provider_activity_id="test",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=tuple(time_values),
            ),
            distance=ActivityStream(
                stream_type="distance",
                data=tuple(distance_values),
            ),
            velocity_smooth=ActivityStream(
                stream_type="velocity_smooth",
                data=tuple(velocity_values),
            ),
            cadence=ActivityStream(
                stream_type="cadence",
                data=tuple(cadence_values),
            ),
            watts=ActivityStream(
                stream_type="watts",
                data=tuple(watts_values),
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=tuple(hr_values),
            ),
        ),
    )


def test_seven_strong_repetitions_returns_seven() -> None:
    result = (
        select_evidenced_distance_repetitions(
            build_activity(
                (
                    71.0,
                    70.0,
                    69.0,
                    70.0,
                    65.0,
                    75.0,
                    74.0,
                )
            ),
            prescription(),
        )
    )

    assert len(result) == 7

    assert all(
        item.evidence.confidence
        >= 0.62
        for item in result
    )


def test_only_five_proven_repetitions_returns_five() -> None:
    result = (
        select_evidenced_distance_repetitions(
            build_activity(
                (
                    70.0,
                    70.0,
                    70.0,
                    70.0,
                    70.0,
                    70.0,
                    70.0,
                ),
                strong_flags=(
                    True,
                    True,
                    True,
                    False,
                    True,
                    False,
                    True,
                ),
            ),
            prescription(),
        )
    )

    assert len(result) == 5


def test_prescribed_count_is_only_a_ceiling() -> None:
    result = (
        select_evidenced_distance_repetitions(
            build_activity(
                (
                    70.0,
                    70.0,
                    70.0,
                    70.0,
                    70.0,
                    70.0,
                    70.0,
                )
            ),
            prescription(
                repetitions=5,
            ),
        )
    )

    assert len(result) == 5


def test_flat_continuous_running_is_not_seven_intervals() -> None:
    times = tuple(
        range(1000)
    )

    speed = 4.2

    detail = ActivityDetail(
        provider_activity_id="continuous",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=times,
            ),
            distance=ActivityStream(
                stream_type="distance",
                data=tuple(
                    second * speed
                    for second in times
                ),
            ),
            velocity_smooth=ActivityStream(
                stream_type="velocity_smooth",
                data=tuple(
                    speed
                    for _ in times
                ),
            ),
            cadence=ActivityStream(
                stream_type="cadence",
                data=tuple(
                    90.0
                    for _ in times
                ),
            ),
            watts=ActivityStream(
                stream_type="watts",
                data=tuple(
                    300.0
                    for _ in times
                ),
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=tuple(
                    150.0
                    for _ in times
                ),
            ),
        ),
    )

    result = (
        select_evidenced_distance_repetitions(
            detail,
            prescription(),
        )
    )

    assert result == ()


def test_duration_alone_is_not_enough_evidence() -> None:
    times = tuple(
        range(500)
    )

    speed = (
        300.0 / 70.0
    )

    detail = ActivityDetail(
        provider_activity_id="duration-only",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=times,
            ),
            distance=ActivityStream(
                stream_type="distance",
                data=tuple(
                    second * speed
                    for second in times
                ),
            ),
        ),
    )

    result = (
        select_evidenced_distance_repetitions(
            detail,
            prescription(),
        )
    )

    assert result == ()


def test_production_detection_does_not_force_prescribed_distance() -> None:
    """La distance finale vient des frontières mesurées."""

    from opencoach.training.session_execution import (
        detect_repetitions,
    )

    detail = build_activity(
        (
            70.0,
            70.0,
            70.0,
        )
    )

    result = detect_repetitions(
        detail,
        prescription(
            repetitions=3,
        ),
    )

    assert result.detected_repetitions == 3

    assert all(
        repetition.distance_m is not None
        for repetition in result.repetitions
    )

    assert all(
        repetition.duration_seconds > 0
        for repetition in result.repetitions
    )

    assert all(
        repetition.average_speed_mps is not None
        for repetition in result.repetitions
    )

    assert all(
        repetition.boundary_confidence is not None
        for repetition in result.repetitions
    )

