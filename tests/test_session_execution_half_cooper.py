from datetime import date, datetime
from uuid import uuid4

from opencoach.models import (
    Activity,
    ActivityDetail,
    ActivityStream,
    ActivityStreams,
    TrainingSession,
)
from opencoach.training.session_execution.goal_analysis import (
    GoalComplianceStatus,
    analyze_half_cooper,
    is_half_cooper_session,
)


def session() -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=date(2026, 8, 28),
        type="physiological_test",
        sport_type="Run",
        title="Demi-Cooper",
        description="Test VMA 6 minutes",
        duration_minutes=44,
        intensity="maximal",
        prescription={
            "test": {
                "type": "half_cooper",
            },
        },
    )


def activity() -> Activity:
    # Activité complète volontairement beaucoup plus longue
    # que les 6 minutes du test.
    #
    # Ces valeurs globales ne doivent jamais servir
    # directement au calcul de la VMA.
    return Activity(
        id=uuid4(),
        provider="intervals_icu",
        provider_activity_id="test",
        start_at=datetime(
            2026,
            8,
            28,
            10,
            0,
        ),
        sport_type="Run",
        name="Demi-Cooper complet",
        moving_time_seconds=1200,
        elapsed_time_seconds=1200,
        distance_m=4200.0,
    )


def detail(
    *,
    test_speed: float = 4.1666666667,
    stop_start: int | None = None,
    stop_end: int | None = None,
    include_distance: bool = True,
) -> ActivityDetail:
    """Construit :

    0 -> 300 s
        échauffement

    300 -> 660 s
        vrai segment Demi-Cooper de 6 min

    660 -> 1200 s
        retour au calme
    """

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
        in_test = (
            300 <= second < 660
        )

        stopped = (
            stop_start is not None
            and stop_end is not None
            and stop_start <= second < stop_end
        )

        if stopped:
            speed = 0.0
            power = 0.0
            cad = 0.0

        elif in_test:
            speed = test_speed
            power = 360.0
            cad = 96.0

        else:
            speed = 2.0
            power = 180.0
            cad = 82.0

        if in_test:
            # La FC est volontairement haute sur le segment,
            # mais elle n'est pas utilisée pour imposer
            # les frontières.
            hr = 175.0
        else:
            hr = 140.0

        speeds.append(speed)
        watts.append(power)
        cadence.append(cad)
        heart_rate.append(hr)

        if second > 0:
            cumulative_distance += (
                speeds[second - 1]
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
            watts=ActivityStream(
                stream_type="watts",
                data=tuple(watts),
            ),
            cadence=ActivityStream(
                stream_type="cadence",
                data=tuple(cadence),
            ),
            heartrate=ActivityStream(
                stream_type="heartrate",
                data=tuple(heart_rate),
            ),
        ),
    )


def test_detects_explicit_half_cooper_session() -> None:
    assert (
        is_half_cooper_session(
            session()
        )
        is True
    )


def test_uses_only_real_six_minute_test_window() -> None:
    result = analyze_half_cooper(
        session=session(),
        activity=activity(),
        activity_detail=detail(),
    )

    assert (
        result.status
        is GoalComplianceStatus.OK
    )

    assert (
        result.protocol_duration_seconds
        == 360.0
    )

    assert result.distance_m is not None

    assert (
        1495.0
        <= result.distance_m
        <= 1505.0
    )

    assert result.vma_kmh is not None

    assert (
        14.95
        <= result.vma_kmh
        <= 15.05
    )


def test_total_activity_distance_never_drives_vma() -> None:
    value = activity()

    # Valeur volontairement absurde.
    value.distance_m = 9999.0

    result = analyze_half_cooper(
        session=session(),
        activity=value,
        activity_detail=detail(),
    )

    assert result.distance_m is not None
    assert result.vma_kmh is not None

    assert (
        1495.0
        <= result.distance_m
        <= 1505.0
    )

    assert (
        14.95
        <= result.vma_kmh
        <= 15.05
    )


def test_total_activity_duration_never_drives_protocol() -> None:
    value = activity()

    value.moving_time_seconds = 9999
    value.elapsed_time_seconds = 9999

    result = analyze_half_cooper(
        session=session(),
        activity=value,
        activity_detail=detail(),
    )

    assert (
        result.protocol_duration_seconds
        == 360.0
    )

    assert result.vma_kmh is not None

    assert (
        14.95
        <= result.vma_kmh
        <= 15.05
    )


def test_long_interruption_invalidates_test() -> None:
    result = analyze_half_cooper(
        session=session(),
        activity=activity(),
        activity_detail=detail(
            stop_start=400,
            stop_end=430,
        ),
    )

    assert (
        result.status
        is GoalComplianceStatus.NON_COMPLIANT
    )

    assert result.vma_kmh is None


def test_short_interruption_does_not_silently_invalidate_result() -> None:
    result = analyze_half_cooper(
        session=session(),
        activity=activity(),
        activity_detail=detail(
            stop_start=400,
            stop_end=405,
        ),
    )

    assert (
        result.status
        in {
            GoalComplianceStatus.OK,
            GoalComplianceStatus.ATTENTION,
        }
    )

    assert result.vma_kmh is not None


def test_missing_distance_does_not_invent_vma() -> None:
    result = analyze_half_cooper(
        session=session(),
        activity=activity(),
        activity_detail=detail(
            include_distance=False,
        ),
    )

    assert (
        result.status
        is GoalComplianceStatus.NOT_USED
    )

    assert result.distance_m is None
    assert result.vma_kmh is None


def test_missing_activity_detail_is_not_exploitable() -> None:
    result = analyze_half_cooper(
        session=session(),
        activity=activity(),
        activity_detail=None,
    )

    assert (
        result.status
        is GoalComplianceStatus.NOT_USED
    )

    assert result.vma_kmh is None


def test_missing_activity_is_non_compliant() -> None:
    result = analyze_half_cooper(
        session=session(),
        activity=None,
        activity_detail=detail(),
    )

    assert (
        result.status
        is GoalComplianceStatus.NON_COMPLIANT
    )

    assert result.vma_kmh is None
