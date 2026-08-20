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

from opencoach.database.repositories import (
    TrainingSessionRepositoryError,
)

class FakeTrainingSessionRepository:
    def __init__(
        self,
        *,
        save_error: Exception | None = None,
    ) -> None:
        self.save_error = save_error
        self.saved_sessions: list[
            TrainingSession
        ] = []
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

    def save_session(
        self,
        athlete_profile_id,
        session,
    ):
        if self.save_error is not None:
            raise self.save_error

        if session.id is None:
            session.id = uuid4()

        self.saved_sessions.append(
            session,
        )

        return session

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

    def list_unlinked_activities_for_date(
        self,
        athlete_profile_id,
        session_date,
    ):
        return [self.activity]


def create_test_client(
    repository: FakeTrainingSessionRepository | None = None,
):
    app = create_app()

    repository = (
        repository
        or FakeTrainingSessionRepository()
    )

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

def test_training_sessions_api_creates_session() -> None:
    client, repository = create_test_client()

    response = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "StrengthTraining",
            "title": "Renforcement caserne",
            "description": "Séance supplémentaire.",
            "duration_minutes": 40,
            "distance_km": None,
            "elevation_gain_m": None,
            "intensity": "Modérée",
            "heart_rate_zone": None,
            "status": "completed",
            "activity_id": None,
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["date"] == "2026-08-19"
    assert payload["type"] == "supplementary"
    assert payload["sport_type"] == "StrengthTraining"
    assert payload["title"] == "Renforcement caserne"
    assert payload["duration_minutes"] == 40
    assert payload["status"] == "completed"
    assert payload["activity_id"] is None

    assert len(
        repository.saved_sessions,
    ) == 1

def test_training_sessions_api_creates_session_with_activity() -> None:
    client, repository = create_test_client()

    response = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-09",
            "type": "supplementary",
            "sport_type": "Run",
            "title": "Course supplémentaire",
            "description": "",
            "duration_minutes": 60,
            "distance_km": 10.0,
            "elevation_gain_m": 180.0,
            "intensity": "Modérée",
            "heart_rate_zone": None,
            "status": "completed",
            "activity_id": str(
                repository.activity.id,
            ),
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["activity_id"] == str(
        repository.activity.id,
    )

    assert (
        repository
        .saved_sessions[0]
        .activity_id
        == repository.activity.id
    )

def test_training_sessions_api_allows_multiple_sessions_same_day() -> None:
    client, repository = create_test_client()

    first_response = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "Run",
            "title": "Footing",
            "description": "",
            "duration_minutes": 60,
            "distance_km": 10.0,
            "elevation_gain_m": 100.0,
            "intensity": "Facile",
            "heart_rate_zone": "Z2",
            "status": "completed",
            "activity_id": None,
        },
    )

    second_response = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "StrengthTraining",
            "title": "Renforcement",
            "description": "",
            "duration_minutes": 40,
            "distance_km": None,
            "elevation_gain_m": None,
            "intensity": "Modérée",
            "heart_rate_zone": None,
            "status": "completed",
            "activity_id": None,
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    assert len(
        repository.saved_sessions,
    ) == 2

    assert (
        repository.saved_sessions[0].date
        == repository.saved_sessions[1].date
    )

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

def test_training_sessions_api_does_not_mark_weak_candidate_as_best() -> None:
    client, repository = create_test_client()

    weak_activity = Activity(
        id=uuid4(),
        provider="intervals",
        provider_activity_id="i-weak",
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
        moving_time_seconds=4 * 3600,
        distance_m=40000.0,
        elevation_gain_m=2000.0,
        feel=3,
    )

    repository.list_candidate_activities_for_date = (
        lambda athlete_profile_id, session_date: [
            weak_activity,
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

    assert len(payload) == 1

    assert payload[0]["match_score"] < 75.0
    assert payload[0]["best_match"] is False

def test_create_training_session() -> None:
    repository = FakeTrainingSessionRepository()

    client, profile_id = create_test_client(
        repository,
    )

    response = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "StrengthTraining",
            "title": "Renforcement caserne",
            "description": "Séance supplémentaire.",
            "duration_minutes": 40,
            "distance_km": None,
            "elevation_gain_m": None,
            "intensity": "Modérée",
            "heart_rate_zone": None,
            "status": "completed",
            "activity_id": None,
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["date"] == "2026-08-19"
    assert payload["type"] == "supplementary"
    assert payload["sport_type"] == "StrengthTraining"
    assert payload["title"] == "Renforcement caserne"
    assert payload["duration_minutes"] == 40
    assert payload["status"] == "completed"
    assert payload["activity_id"] is None

def test_create_training_session_with_activity() -> None:
    repository = FakeTrainingSessionRepository()

    client, _ = create_test_client(
        repository,
    )

    activity_id = uuid4()

    response = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "Swim",
            "title": "Natation",
            "description": "",
            "duration_minutes": 30,
            "distance_km": 1.2,
            "elevation_gain_m": None,
            "intensity": "Facile",
            "heart_rate_zone": None,
            "status": "completed",
            "activity_id": str(activity_id),
        },
    )

    assert response.status_code == 201

    payload = response.json()

    assert payload["activity_id"] == str(
        activity_id,
    )

def test_create_multiple_sessions_same_day() -> None:
    repository = FakeTrainingSessionRepository()

    client, _ = create_test_client(
        repository,
    )

    first = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "Run",
            "title": "Footing",
            "description": "",
            "duration_minutes": 60,
            "distance_km": 10,
            "elevation_gain_m": 100,
            "intensity": "Facile",
            "heart_rate_zone": "Z2",
            "status": "completed",
            "activity_id": None,
        },
    )

    second = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "StrengthTraining",
            "title": "Renforcement",
            "description": "",
            "duration_minutes": 40,
            "distance_km": None,
            "elevation_gain_m": None,
            "intensity": "Modérée",
            "heart_rate_zone": None,
            "status": "completed",
            "activity_id": None,
        },
    )

    assert first.status_code == 201
    assert second.status_code == 201

def test_create_training_session_handles_repository_error() -> None:
    repository = FakeTrainingSessionRepository(
        save_error=TrainingSessionRepositoryError(
            "storage failed",
        ),
    )

    client, _ = create_test_client(
        repository,
    )

    response = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "Run",
            "title": "Footing",
            "description": "",
            "duration_minutes": 30,
            "distance_km": 5,
            "elevation_gain_m": 0,
            "intensity": "Facile",
            "heart_rate_zone": "Z2",
            "status": "completed",
            "activity_id": None,
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "Impossible de créer la séance."
    }

def test_training_sessions_api_handles_create_repository_error() -> None:
    repository = FakeTrainingSessionRepository(
        save_error=TrainingSessionRepositoryError(
            "storage failed",
        ),
    )

    client, _ = create_test_client(
        repository,
    )

    response = client.post(
        "/api/training-sessions",
        json={
            "date": "2026-08-19",
            "type": "supplementary",
            "sport_type": "Run",
            "title": "Footing",
            "description": "",
            "duration_minutes": 30,
            "distance_km": 5.0,
            "elevation_gain_m": 0,
            "intensity": "Facile",
            "heart_rate_zone": "Z2",
            "status": "completed",
            "activity_id": None,
        },
    )

    assert response.status_code == 503

    assert response.json() == {
        "detail": "Impossible de créer la séance."
    }

def test_training_sessions_api_lists_available_activities() -> None:
    client, repository = create_test_client()

    response = client.get(
        "/api/training-sessions/available-activities",
        params={
            "date": "2026-08-09",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert len(payload) == 1

    activity = payload[0]

    assert activity["id"] == str(
        repository.activity.id
    )
    assert activity["provider"] == "intervals"
    assert activity["provider_activity_id"] == "i-run"
    assert activity["name"] == "Morning Course à pied"
    assert activity["sport_type"] == "Run"

    assert (
        activity["start_at_local"]
        == "2026-08-09T07:07:02"
    )

    assert activity["moving_time_seconds"] == 3600
    assert activity["distance_m"] == 10000.0
    assert activity["elevation_gain_m"] == 180.0
    assert activity["feel"] == 2

def test_training_sessions_api_rejects_invalid_available_activity_date() -> None:
    client, _ = create_test_client()

    response = client.get(
        "/api/training-sessions/available-activities",
        params={
            "date": "invalid",
        },
    )

    assert response.status_code == 422