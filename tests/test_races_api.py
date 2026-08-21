from datetime import date
from uuid import uuid4

from fastapi.testclient import (
    TestClient,
)

from opencoach.api.app import (
    create_app,
)
from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.api.races import (
    get_race_repository,
)
from opencoach.models import Race


TODAY = date(
    2027,
    7,
    10,
)


class FakeRaceRepository:
    def __init__(
        self,
    ) -> None:
        self.races = []
        self.saved = []
        self.deleted = []

    def save_race(
        self,
        athlete_profile_id,
        race,
    ):
        if race.id is None:
            race.id = uuid4()

        self.saved.append(
            (
                athlete_profile_id,
                race,
            )
        )

        existing_index = next(
            (
                index
                for index, item
                in enumerate(
                    self.races
                )
                if item.id == race.id
            ),
            None,
        )

        if existing_index is None:
            self.races.append(
                race
            )
        else:
            self.races[
                existing_index
            ] = race

        return race

    def get_race(
        self,
        athlete_profile_id,
        race_id,
    ):
        del athlete_profile_id

        return next(
            (
                race
                for race in self.races
                if race.id == race_id
            ),
            None,
        )

    def delete_race(
        self,
        athlete_profile_id,
        race_id,
    ):
        self.deleted.append(
            (
                athlete_profile_id,
                race_id,
            )
        )

        for race in self.races:
            if race.id == race_id:
                self.races.remove(
                    race
                )
                return

        from opencoach.database.repositories import (
            RaceRepositoryError,
        )

        raise RaceRepositoryError(
            "Course introuvable."
        )

    def list_races_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        del athlete_profile_id

        return [
            race
            for race in self.races
            if (
                start_date
                <= race.date
                <= end_date
            )
        ]
    def link_activity(
        self,
        athlete_profile_id,
        race_id,
        activity_id,
    ):
        del athlete_profile_id

        race = self.get_race(
            None,
            race_id,
        )

        if race is None:
            from opencoach.database.repositories import (
                RaceRepositoryError,
            )

            raise RaceRepositoryError(
                "Course introuvable."
            )

        race.activity_id = activity_id

        return race

    def list_candidate_activities_for_date(
        self,
        athlete_profile_id,
        race_date,
    ):
        del athlete_profile_id
        del race_date

        return getattr(
            self,
            "activities",
            [],
        )


def create_race(
    *,
    race_id=None,
    name="Ultra objectif",
    priority="primary",
) -> Race:
    return Race(
        id=(
            race_id
            or uuid4()
        ),
        date=TODAY,
        name=name,
        location="Jura",
        race_type="trail",
        priority=priority,
        distance_km=65.0,
        elevation_gain_m=3100.0,
        target_time_minutes=600,
        status="planned",
    )


def create_client(
    repository,
):
    app = create_app()

    profile_id = uuid4()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: profile_id

    app.dependency_overrides[
        get_race_repository
    ] = lambda: repository

    return (
        TestClient(
            app
        ),
        profile_id,
    )


def test_races_api_lists_races() -> None:
    repository = FakeRaceRepository()

    repository.races = [
        create_race(
            name="Préparation",
            priority="training",
        ),
        create_race(),
    ]

    client, _ = create_client(
        repository
    )

    response = client.get(
        (
            "/api/races"
            "?start=2027-01-01"
            "&end=2027-12-31"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 2

    assert (
        payload[0]["name"]
        == "Préparation"
    )

    assert (
        payload[1]["priority"]
        == "primary"
    )


def test_races_api_gets_race() -> None:
    repository = FakeRaceRepository()

    race = create_race()

    repository.races = [
        race
    ]

    client, _ = create_client(
        repository
    )

    response = client.get(
        f"/api/races/{race.id}"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(
        race.id
    )

    assert payload["name"] == (
        "Ultra objectif"
    )

    assert payload["priority"] == (
        "primary"
    )


def test_races_api_returns_404_for_unknown_race() -> None:
    repository = FakeRaceRepository()

    client, _ = create_client(
        repository
    )

    response = client.get(
        f"/api/races/{uuid4()}"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail":
            "Course introuvable."
    }


def test_races_api_creates_race() -> None:
    repository = FakeRaceRepository()

    client, profile_id = create_client(
        repository
    )

    response = client.post(
        "/api/races",
        json={
            "date": "2027-07-10",
            "name": "Ultra objectif",
            "location": "Jura",
            "race_type": "trail",
            "priority": "primary",
            "distance_km": 65.0,
            "elevation_gain_m": 3100.0,
            "target_time_minutes": 600,
            "status": "planned",
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["name"] == (
        "Ultra objectif"
    )

    assert payload["priority"] == (
        "primary"
    )

    assert len(
        repository.saved
    ) == 1

    assert (
        repository.saved[0][0]
        == profile_id
    )


def test_races_api_updates_race() -> None:
    repository = FakeRaceRepository()

    race = create_race()

    repository.races = [
        race
    ]

    client, _ = create_client(
        repository
    )

    response = client.put(
        f"/api/races/{race.id}",
        json={
            "date": "2027-07-10",
            "name": "Ultra objectif modifié",
            "location": "Jura",
            "race_type": "ultra",
            "priority": "primary",
            "distance_km": 70.0,
            "elevation_gain_m": 3500.0,
            "target_time_minutes": 660,
            "status": "planned",
            "notes": "Nouvel objectif.",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["name"] == (
        "Ultra objectif modifié"
    )

    assert payload["distance_km"] == (
        70.0
    )

    assert payload["notes"] == (
        "Nouvel objectif."
    )


def test_races_api_deletes_race() -> None:
    repository = FakeRaceRepository()

    race = create_race()

    repository.races = [
        race
    ]

    client, profile_id = create_client(
        repository
    )

    response = client.delete(
        f"/api/races/{race.id}"
    )

    assert response.status_code == 204

    assert repository.deleted == [
        (
            profile_id,
            race.id,
        )
    ]


def test_races_api_rejects_invalid_priority() -> None:
    repository = FakeRaceRepository()

    client, _ = create_client(
        repository
    )

    response = client.post(
        "/api/races",
        json={
            "date": "2027-07-10",
            "name": "Ultra",
            "location": "Jura",
            "race_type": "trail",
            "priority": "super-important",
            "distance_km": 65.0,
        },
    )

    assert response.status_code == 422


def test_races_api_rejects_partial_date_range() -> None:
    repository = FakeRaceRepository()

    client, _ = create_client(
        repository
    )

    response = client.get(
        "/api/races?start=2027-01-01"
    )

    assert response.status_code == 422


def test_races_api_rejects_invalid_date_range() -> None:
    repository = FakeRaceRepository()

    client, _ = create_client(
        repository
    )

    response = client.get(
        (
            "/api/races"
            "?start=2027-12-31"
            "&end=2027-01-01"
        )
    )

    assert response.status_code == 422


def test_races_api_rejects_result_for_non_participant() -> None:
    repository = FakeRaceRepository()

    client, _ = create_client(
        repository
    )

    response = client.post(
        "/api/races",
        json={
            "date": "2027-07-10",
            "name": "Ultra",
            "location": "Jura",
            "race_type": "trail",
            "priority": "training",
            "distance_km": 65.0,
            "status":
                "not_participated",
            "actual_distance_km":
                12.0,
        },
    )

    assert response.status_code == 422
def test_races_api_links_activity() -> None:
    repository = FakeRaceRepository()

    race = create_race()

    repository.races = [
        race
    ]

    client, _ = create_client(
        repository
    )

    activity_id = uuid4()

    response = client.patch(
        f"/api/races/{race.id}/activity",
        json={
            "activity_id":
                str(activity_id),
        },
    )

    assert response.status_code == 200

    assert (
        response.json()["activity_id"]
        == str(activity_id)
    )
def test_races_api_unlinks_activity() -> None:
    repository = FakeRaceRepository()

    race = create_race()
    race.activity_id = uuid4()

    repository.races = [
        race
    ]

    client, _ = create_client(
        repository
    )

    response = client.patch(
        f"/api/races/{race.id}/activity",
        json={
            "activity_id": None,
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["activity_id"]
        is None
    )