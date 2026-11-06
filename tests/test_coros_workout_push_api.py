from datetime import date, datetime, timedelta, timezone
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

    def claim_coros_workout_push(
        self,
        profile_id,
        session_id,
        payload_hash,
        started_at,
        *,
        allow_uncertain=False,
        allow_synced_update=False,
    ):
        status = self.session.coros_sync_status
        eligible = status in {None, "failed"}
        if allow_uncertain and status in {"pending", "unknown"}:
            eligible = True
        if allow_synced_update and status == "synced":
            eligible = True
        if not eligible:
            return False
        self.session.coros_sync_status = "pending"
        self.session.coros_sync_started_at = started_at.replace(tzinfo=None)
        self.session.coros_payload_hash = payload_hash
        self.session.coros_sync_error = None
        return True


class FakeCorosClient:
    calls = []
    scheduled_names = ["Renforcement"]
    editable = True

    def __init__(self, access_token):
        self.access_token = access_token

    def list_tools(self):
        return [
            {
                "name": "queryTrainingSchedule",
                "inputSchema": {
                    "properties": {
                        "startDay": {"type": "string"},
                        "endDay": {"type": "string"},
                    },
                    "required": ["startDay", "endDay"],
                },
            },
            {
                "name": "createScheduledWorkout",
                "inputSchema": {
                    "required": ["date", "course"],
                },
            },
            {
                "name": "queryScheduledWorkoutDetails",
                "inputSchema": {
                    "required": ["date", "idInPlan"],
                },
            },
            {
                "name": "updateScheduledWorkout",
                "inputSchema": {
                    "required": ["date", "idInPlan", "course"],
                },
            },
        ]

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "queryScheduledWorkoutDetails":
            return {
                "structuredContent": {
                    "editable": self.editable,
                    "reason": None if self.editable else "Séance déjà terminée.",
                    "course": {
                        "courseName": "Ancien titre",
                        "courseDescription": "Ancienne description",
                        "sportType": 1,
                        "sections": [],
                    },
                }
            }
        if name == "queryTrainingSchedule":
            return {
                "structuredContent": {
                    "schedule": {
                        "days": [
                            {
                                "date": "2026-11-12",
                                "courses": [
                                    {
                                        "idInPlan": f"existing-{index}",
                                        "courseName": name,
                                    }
                                    for index, name in enumerate(
                                        self.scheduled_names
                                    )
                                ],
                            }
                        ]
                    }
                }
            }
        return {
            "structuredContent": {
                "idInPlan": (
                    "updated-workout-id"
                    if name == "updateScheduledWorkout"
                    else "new-workout-id"
                ),
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
    FakeCorosClient.scheduled_names = ["Renforcement"]
    FakeCorosClient.editable = True
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
    assert len(FakeCorosClient.calls) == 2
    assert FakeCorosClient.calls[0] == (
        "queryTrainingSchedule",
        {"startDay": "20261112", "endDay": "20261112"},
    )

    tool_name, arguments = FakeCorosClient.calls[1]
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
    assert len(FakeCorosClient.calls) == 2


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
    assert len(FakeCorosClient.calls) == 2



def test_pending_push_cannot_be_retried_while_original_request_is_active(
    monkeypatch,
):
    session = make_session()
    session.coros_sync_status = "pending"
    session.coros_sync_started_at = datetime.now(timezone.utc)
    client, _, _ = make_client(monkeypatch, session)

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )

    assert response.status_code == 409
    assert "encore en cours" in response.json()["detail"]
    assert FakeCorosClient.calls == []


def test_stale_pending_push_requires_confirmation_then_can_retry(monkeypatch):
    session = make_session()
    session.coros_sync_status = "pending"
    session.coros_sync_started_at = (
        datetime.now(timezone.utc) - timedelta(minutes=10)
    )
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
    assert repository.session.coros_sync_started_at is None
    assert len(FakeCorosClient.calls) == 2



def test_uncertain_retry_is_blocked_when_same_title_is_already_on_coros(
    monkeypatch,
):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_payload_hash = "previous-payload-hash"
    client, _, _ = make_client(monkeypatch, session)
    FakeCorosClient.scheduled_names = ["Footing aérobie"]

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )

    assert response.status_code == 409
    assert "portant déjà ce titre" in response.json()["detail"]
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule"
    ]


def test_updates_existing_coros_workout_instead_of_creating_a_duplicate(monkeypatch):
    session = make_session()
    session.coros_sync_status = "synced"
    session.coros_workout_id = "existing-workout-id"
    session.coros_payload_hash = "old-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "synced"
    assert "mise à jour" in response.json()["message"]
    assert repository.session.coros_workout_id == "updated-workout-id"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryScheduledWorkoutDetails",
        "updateScheduledWorkout",
    ]
    _, arguments = FakeCorosClient.calls[1]
    assert arguments["idInPlan"] == "existing-workout-id"
    assert arguments["course"]["courseName"] == "Footing aérobie"


def test_refuses_to_update_a_coros_workout_that_is_not_editable(monkeypatch):
    session = make_session()
    session.coros_sync_status = "synced"
    session.coros_workout_id = "completed-workout-id"
    session.coros_payload_hash = "old-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.editable = False

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 409
    assert "déjà terminée" in response.json()["detail"]
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryScheduledWorkoutDetails"
    ]
    assert repository.session.coros_workout_id == "completed-workout-id"


def test_uncertain_update_retry_keeps_existing_coros_identity(monkeypatch):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_workout_id = "existing-workout-id"
    session.coros_payload_hash = "uncertain-new-payload"
    client, repository, _ = make_client(monkeypatch, session)

    blocked = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )
    assert blocked.status_code == 409
    assert FakeCorosClient.calls == []

    retried = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )

    assert retried.status_code == 200
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryScheduledWorkoutDetails",
        "updateScheduledWorkout",
    ]
    assert repository.session.coros_workout_id == "updated-workout-id"


def test_synced_session_without_coros_id_never_falls_back_to_creation(monkeypatch):
    session = make_session()
    session.coros_sync_status = "synced"
    session.coros_payload_hash = "old-payload-hash"
    session.coros_workout_id = None
    client, _, _ = make_client(monkeypatch, session)

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 409
    assert "identifiant COROS est absent" in response.json()["detail"]
    assert FakeCorosClient.calls == []
