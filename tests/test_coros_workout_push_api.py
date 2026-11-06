from datetime import date
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api import coros as coros_api
from opencoach.api.coros import get_current_athlete_profile_id
from opencoach.database.session import get_db
from opencoach.models import TrainingSession


class FakeConnection:
    enabled = True
    encrypted_secret = b"encrypted"

    def __init__(self):
        self.config = {"connected": True}


class FakeDatabase:
    def commit(self):
        pass


class FakeRepository:
    def __init__(self, session):
        self.session = session
        self.saved = []

    def get_session(self, profile_id, session_id):
        return self.session if self.session.id == session_id else None

    def save_session(self, profile_id, session):
        self.session = session
        self.saved.append(session)
        return session


class FakeCorosClient:
    calls = []

    def __init__(self, access_token):
        self.access_token = access_token

    def list_tools(self):
        return [
            {
                "name": "createScheduledWorkout",
                "inputSchema": {
                    "required": ["date", "course"],
                },
            }
        ]

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return {
            "structuredContent": {
                "idInPlan": "new-workout-id",
                "otherWorkouts": [
                    {
                        "idInPlan": "existing-workout-id",
                        "courseName": "Renforcement",
                    }
                ],
            }
        }


def make_session():
    return TrainingSession(
        id=uuid4(),
        date=date(2026, 11, 12),
        type="aerobic_easy",
        sport_type="Run",
        title="Footing aérobie",
        description="Sortie facile.",
        duration_minutes=40,
        intensity="easy",
        prescription={
            "version": 1,
            "blocks": [],
            "work_structure": {
                "type": "continuous",
                "continuous_minutes": 40,
            },
            "intensity": {
                "targets": [
                    {
                        "reference": "heart_rate",
                        "minimum": 140,
                        "maximum": 155,
                    }
                ]
            },
        },
        status="planned",
    )


def make_client(monkeypatch, session):
    profile_id = uuid4()
    db = FakeDatabase()
    connection = FakeConnection()
    repository = FakeRepository(session)

    app = create_app()
    app.dependency_overrides[get_current_athlete_profile_id] = lambda: profile_id
    app.dependency_overrides[get_db] = lambda: db

    monkeypatch.setattr(
        coros_api,
        "SqlTrainingSessionRepository",
        lambda database: repository,
    )
    monkeypatch.setattr(
        coros_api,
        "_connection",
        lambda database, owner: connection,
    )
    monkeypatch.setattr(coros_api, "_cipher", lambda: object())
    monkeypatch.setattr(
        coros_api,
        "_read_secret",
        lambda connection, cipher: {
            "status": "connected",
            "access_token": "test-access-token",
        },
    )
    monkeypatch.setattr(
        coros_api,
        "refresh_secret_if_needed",
        lambda secret, oauth, now: secret,
    )
    monkeypatch.setattr(coros_api, "_oauth", lambda: object())
    FakeCorosClient.calls = []
    monkeypatch.setattr(coros_api, "CorosMcpClient", FakeCorosClient)

    return TestClient(app), repository, profile_id


def test_pushes_planned_session_to_coros_and_reports_other_workouts(monkeypatch):
    session = make_session()
    client, repository, _ = make_client(monkeypatch, session)

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "synced"
    assert "calendrier COROS" in body["message"]
    assert "Renforcement" in body["message"]
    assert repository.session.coros_sync_status == "synced"
    assert repository.session.coros_workout_id == "new-workout-id"
    assert len(FakeCorosClient.calls) == 1

    tool_name, arguments = FakeCorosClient.calls[0]
    assert tool_name == "createScheduledWorkout"
    assert arguments["date"] == "20261112"
    assert arguments["course"]["sportType"] == 1


def test_repeated_push_does_not_create_a_duplicate(monkeypatch):
    session = make_session()
    client, repository, _ = make_client(monkeypatch, session)

    first = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )
    second = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "synced"
    assert len(FakeCorosClient.calls) == 1


def test_uncertain_previous_push_requires_explicit_no_duplicate_confirmation(
    monkeypatch,
):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_payload_hash = "previous-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)

    blocked = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )
    assert blocked.status_code == 409
    assert FakeCorosClient.calls == []

    confirmed = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )
    assert confirmed.status_code == 200
    assert repository.session.coros_sync_status == "synced"
    assert len(FakeCorosClient.calls) == 1
