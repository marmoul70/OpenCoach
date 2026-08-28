from opencoach.models import (
    ActivityDetail,
    ActivityStream,
    ActivityStreams,
)
from opencoach.training.session_execution import (
    IntervalSetPrescription,
    RepetitionTarget,
    detect_distance_repetitions_from_streams,
)


def test_reconstructs_seven_300m_repetitions() -> None:
    # Série synthétique construite à partir des chronos
    # réellement observés sur l'activité validée :
    #
    # 71.2, 70.2, 69.2, 69.8, 65.0, 74.7, 74.0 s
    #
    # avec récupérations :
    #
    # 65.8, 59.8, 61.8, 52.3, 71.0, 56.3 s

    work_durations = (
        71.2,
        70.2,
        69.2,
        69.8,
        65.0,
        74.7,
        74.0,
    )

    recoveries = (
        65.8,
        59.8,
        61.8,
        52.3,
        71.0,
        56.3,
    )

    time_values = []
    distance_values = []

    current_time = 0.0
    current_distance = 0.0

    # Échauffement.
    for _ in range(100):
        time_values.append(
            current_time
        )
        distance_values.append(
            current_distance
        )

        current_time += 1.0
        current_distance += 2.5

    for repetition_index, duration in enumerate(
        work_durations
    ):
        speed = (
            300.0
            / duration
        )

        steps = int(
            round(duration)
        )

        for _ in range(steps):
            time_values.append(
                current_time
            )
            distance_values.append(
                current_distance
            )

            current_time += 1.0
            current_distance += speed

        if (
            repetition_index
            < len(recoveries)
        ):
            recovery = recoveries[
                repetition_index
            ]

            steps = int(
                round(recovery)
            )

            for _ in range(steps):
                time_values.append(
                    current_time
                )
                distance_values.append(
                    current_distance
                )

                current_time += 1.0
                current_distance += 1.5

    detail = ActivityDetail(
        provider_activity_id="7x300",
        streams=ActivityStreams(
            time=ActivityStream(
                stream_type="time",
                data=tuple(
                    time_values
                ),
            ),
            distance=ActivityStream(
                stream_type="distance",
                data=tuple(
                    distance_values
                ),
            ),
        ),
    )

    prescription = IntervalSetPrescription(
        repetitions=7,
        work_distance_m=300.0,
        recovery_duration_seconds=60.0,
        repetition_target=RepetitionTarget(
            distance_m=300.0,
            target_duration_min_seconds=60.0,
            target_duration_max_seconds=80.0,
        ),
    )

    result = (
        detect_distance_repetitions_from_streams(
            detail,
            prescription,
        )
    )

    assert len(result) == 7

    durations = [
        repetition.duration_seconds
        for repetition in result
    ]

    assert all(
        60.0
        <= duration
        <= 80.0
        for duration in durations
    )

    for current, following in zip(
        result,
        result[1:],
        strict=False,
    ):
        assert (
            following.start_time_seconds
            > current.end_time_seconds
        )
