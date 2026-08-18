from datetime import date, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api.intervals import (
    get_local_athlete_profile_id,
)
from opencoach.api.training_sessions import (
    get_training_session_repository,
)
from opencoach.models import Activity, TrainingSession


class FakeTrainingSessionRepository:
    def __init__(self) -> None:
        self.profile_id = uuid4()

        self.session = TrainingSession(
            id=uuid4(),
            date=date(2026, 8, 9),
            type="easy",
            title="Endurance fondamentale",
            sport_type="Run",
            description="Course facile en endurance.",
            duration_minutes=60,
            distance_km=9.0,
            elevation_gain_m=100.0,
            intensity="Facile",
            heart_rate_zone="Z2",
            status="planned",
            activity_id=None,
        )

        self.activity = Activity(
            id=uuid4(),
            provider="intervals",
            provider_activity_id="i-run",
            name="Morning Course à pied",
            sport_type="Run",
            start_at=datetime(
                2026,
                8,
                9,
                5,
                7,
                2,
            ),
            start_at_local=datetime(
                2026,
                8,
                9,
                7,
                7,
                2,
            ),
            moving_time_seconds=3600,
            distance_m=10000.0,
            elevation_gain_m=180.0,
            feel=2,
        )

    def list_sessions_between(
        self,
        athlete_profile_id,
        start_date,
        end_date,
    ):
        return [self.session]

    def get_session(
        self,
        athlete_profile_id,
        session_id,
    ):
        if session_id != self.session.id:
            return None

        return self.session

    def update_status(
        self,
        athlete_profile_id,
        session_id,
        status,
    ):
        self.session.status = status
        return self.session

    def link_activity(
        self,
        athlete_profile_id,
        session_id,
        activity_id,
    ):
        self.session.activity_id = activity_id
        return self.session

    def list_candidate_activities_for_date(
        self,
        athlete_profile_id,
        session_date,
    ):
        return [self.activity]


def create_test_client():
    app = create_app()

    repository = FakeTrainingSessionRepository()

    app.dependency_overrides[
        get_local_athlete_profile_id
    ] = lambda: repository.profile_id

    app.dependency_overrides[
        get_training_session_repository
    ] = lambda: repository

    return TestClient(app), repository


def test_training_sessions_api_lists_period() -> None:
    client, repository = create_test_client()

    response = client.get(
        "/api/training-sessions",
        params={
            "start": "2026-08-03",
            "end": "2026-08-09",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1
    assert payload[0]["id"] == str(repository.session.id)
    assert payload[0]["date"] == "2026-08-09"
    assert payload[0]["title"] == "Endurance fondamentale"
    assert payload[0]["sport_type"] == "Run"
    assert payload[0]["status"] == "planned"
    assert payload[0]["activity_id"] is None


def test_training_sessions_api_returns_session() -> None:
    client, repository = create_test_client()

    response = client.get(
        f"/api/training-sessions/{repository.session.id}"
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["id"] == str(repository.session.id)
    assert payload["title"] == "Endurance fondamentale"
    assert payload["heart_rate_zone"] == "Z2"


def test_training_sessions_api_updates_status() -> None:
    client, repository = create_test_client()

    response = client.patch(
        (
            f"/api/training-sessions/"
            f"{repository.session.id}/status"
        ),
        json={
            "status": "completed",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["status"] == "completed"
    assert repository.session.status == "completed"


def test_training_sessions_api_rejects_invalid_status() -> None:
    client, repository = create_test_client()

    response = client.patch(
        (
            f"/api/training-sessions/"
            f"{repository.session.id}/status"
        ),
        json={
            "status": "invalid",
        },
    )

    assert response.status_code == 422


def test_training_sessions_api_links_activity() -> None:
    client, repository = create_test_client()

    response = client.patch(
        (
            f"/api/training-sessions/"
            f"{repository.session.id}/activity"
        ),
        json={
            "activity_id": str(repository.activity.id),
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["activity_id"] == str(
        repository.activity.id
    )

    assert repository.session.activity_id == (
        repository.activity.id
    )


def test_training_sessions_api_unlinks_activity() -> None:
    client, repository = create_test_client()

    repository.session.activity_id = (
        repository.activity.id
    )

    response = client.patch(
        (
            f"/api/training-sessions/"
            f"{repository.session.id}/activity"
        ),
        json={
            "activity_id": None,
        },
    )

    assert response.status_code == 200
    assert response.json()["activity_id"] is None
    assert repository.session.activity_id is None


def test_training_sessions_api_lists_candidate_activities() -> None:
    client, repository = create_test_client()

    response = client.get(
        (
            f"/api/training-sessions/"
            f"{repository.session.id}/candidate-activities"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1

    activity = payload[0]

    assert activity["id"] == str(
        repository.activity.id
    )

    assert activity["provider"] == "intervals"
    assert activity["name"] == "Morning Course à pied"
    assert activity["sport_type"] == "Run"
    assert activity["distance_m"] == 10000.0
    assert activity["elevation_gain_m"] == 180.0
    assert activity["feel"] == 2

    assert activity["match_score"] == 89.2
    assert activity["best_match"] is True
    assert activity["sport_matches"] is True
    assert activity["sport_score"] == 40.0
    assert activity["distance_score"] == 22.2
    assert activity["duration_score"] == 25.0
    assert activity["elevation_score"] == 2.0

    assert activity["start_at_local"] == (
        "2026-08-09T07:07:02"
    )


def test_training_sessions_api_returns_404_when_missing() -> None:
    client, _ = create_test_client()

    response = client.get(
        f"/api/training-sessions/{uuid4()}"
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Séance introuvable."
    }

def test_training_sessions_api_marks_best_candidate() -> None:
    client, repository = create_test_client()

    better = repository.activity

    worse = Activity(
        id=uuid4(),
        provider="intervals",
        provider_activity_id="i-worse",
        name="Morning Marche",
        sport_type="Walk",
        start_at=datetime(
            2026,
            8,
            9,
            7,
            0,
        ),
        start_at_local=datetime(
            2026,
            8,
            9,
            9,
            0,
        ),
        moving_time_seconds=1800,
        distance_m=3000.0,
        elevation_gain_m=20.0,
        feel=1,
    )

    repository.list_candidate_activities_for_date = (
        lambda athlete_profile_id, session_date: [
            worse,
            better,
        ]
    )

    response = client.get(
        (
            f"/api/training-sessions/"
            f"{repository.session.id}/candidate-activities"
        )
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 2

    assert payload[0]["id"] == str(
        better.id
    )

    assert payload[0]["best_match"] is True
    assert payload[1]["best_match"] is False

    assert (
        payload[0]["match_score"]
        >
        payload[1]["match_score"]
    )
