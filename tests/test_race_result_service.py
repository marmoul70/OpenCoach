from datetime import (
    date,
    datetime,
)
from uuid import uuid4

from opencoach.models import (
    Activity,
    Race,
)
from opencoach.races import (
    RaceResultService,
)


class FakeActivityRepository:
    def __init__(
        self,
        activity=None,
    ) -> None:
        self.activity = activity
        self.calls = []

    def get_activity(
        self,
        athlete_profile_id,
        activity_id,
    ):
        self.calls.append(
            (
                athlete_profile_id,
                activity_id,
            )
        )

        if (
            self.activity is not None
            and self.activity.id
            == activity_id
        ):
            return self.activity

        return None


def create_race(
    *,
    status="completed",
    activity_id=None,
    actual_distance_km=42.0,
    actual_elevation_gain_m=1800.0,
    actual_time_minutes=300,
) -> Race:
    return Race(
        id=uuid4(),
        date=date(
            2027,
            7,
            10,
        ),
        name="Trail objectif",
        location="Jura",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2200.0,
        target_time_minutes=360,
        status=status,
        actual_distance_km=(
            actual_distance_km
        ),
        actual_elevation_gain_m=(
            actual_elevation_gain_m
        ),
        actual_time_minutes=(
            actual_time_minutes
        ),
        activity_id=activity_id,
    )


def create_activity(
    *,
    activity_id,
) -> Activity:
    return Activity(
        id=activity_id,
        provider="intervals",
        provider_activity_id=(
            "i-race-result"
        ),
        name="Trail compétition",
        sport_type="Run",
        start_at=datetime(
            2027,
            7,
            10,
            7,
            0,
        ),
        start_at_local=datetime(
            2027,
            7,
            10,
            9,
            0,
        ),
        distance_m=43150.0,
        moving_time_seconds=(
            6 * 3600
            + 22 * 60
        ),
        elevation_gain_m=2150.0,
        training_load=325.0,
    )


def test_race_result_prefers_activity() -> None:
    profile_id = uuid4()
    activity_id = uuid4()

    activity = create_activity(
        activity_id=activity_id,
    )

    repository = FakeActivityRepository(
        activity
    )

    service = RaceResultService(
        repository
    )

    race = create_race(
        activity_id=activity_id,
        actual_distance_km=42.8,
        actual_elevation_gain_m=2100.0,
        actual_time_minutes=390,
    )

    result = service.calculate(
        profile_id,
        race,
    )

    assert result.source == "activity"

    assert (
        result.activity_id
        == activity_id
    )

    assert (
        result.distance_km
        == 43.15
    )

    assert (
        result.elevation_gain_m
        == 2150.0
    )

    assert (
        result.duration_minutes
        == 382.0
    )

    assert (
        result.training_load
        == 325.0
    )


def test_race_result_uses_manual_completed_result() -> None:
    service = RaceResultService(
        FakeActivityRepository()
    )

    race = create_race(
        status="completed",
        actual_distance_km=50.2,
        actual_elevation_gain_m=2250.0,
        actual_time_minutes=355,
    )

    result = service.calculate(
        uuid4(),
        race,
    )

    assert result.source == "manual"
    assert result.activity_id is None

    assert result.distance_km == 50.2
    assert (
        result.elevation_gain_m
        == 2250.0
    )
    assert (
        result.duration_minutes
        == 355.0
    )

    assert result.training_load is None


def test_race_result_uses_partial_manual_abandon_result() -> None:
    service = RaceResultService(
        FakeActivityRepository()
    )

    race = create_race(
        status="abandoned",
        actual_distance_km=31.7,
        actual_elevation_gain_m=1600.0,
        actual_time_minutes=280,
    )

    result = service.calculate(
        uuid4(),
        race,
    )

    assert result.source == "manual"
    assert result.distance_km == 31.7
    assert (
        result.elevation_gain_m
        == 1600.0
    )
    assert (
        result.duration_minutes
        == 280.0
    )


def test_race_result_returns_zero_when_not_participated() -> None:
    service = RaceResultService(
        FakeActivityRepository()
    )

    race = create_race(
        status="not_participated",
        actual_distance_km=None,
        actual_elevation_gain_m=None,
        actual_time_minutes=None,
    )

    result = service.calculate(
        uuid4(),
        race,
    )

    assert result.source == "none"

    assert result.distance_km == 0.0
    assert result.elevation_gain_m == 0.0
    assert result.duration_minutes == 0.0
    assert result.training_load == 0.0


def test_race_result_has_no_result_when_planned() -> None:
    service = RaceResultService(
        FakeActivityRepository()
    )

    race = create_race(
        status="planned",
        actual_distance_km=None,
        actual_elevation_gain_m=None,
        actual_time_minutes=None,
    )

    result = service.calculate(
        uuid4(),
        race,
    )

    assert result.source == "none"

    assert result.distance_km is None
    assert result.elevation_gain_m is None
    assert result.duration_minutes is None
    assert result.training_load is None


def test_race_result_falls_back_to_manual_when_activity_missing() -> None:
    missing_activity_id = uuid4()

    service = RaceResultService(
        FakeActivityRepository()
    )

    race = create_race(
        status="abandoned",
        activity_id=(
            missing_activity_id
        ),
        actual_distance_km=28.4,
        actual_elevation_gain_m=1400.0,
        actual_time_minutes=245,
    )

    result = service.calculate(
        uuid4(),
        race,
    )

    assert result.source == "manual"
    assert result.activity_id is None

    assert result.distance_km == 28.4
