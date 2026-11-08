from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api import coros as coros_api
from opencoach.api.coros import get_current_athlete_profile_id
from opencoach.database.session import get_db
from opencoach.models import TrainingSession
from opencoach.integrations.coros.errors import CorosMcpToolError
from opencoach.integrations.coros.workout_mapper import map_training_session_to_coros


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
        self.on_claim = None

    def get_session(self, profile_id, session_id):
        return deepcopy(self.session) if self.session.id == session_id else None

    def save_session(self, profile_id, session):
        self.session = deepcopy(session)
        self.saved.append(deepcopy(session))
        return deepcopy(session)

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
        if self.on_claim is not None:
            self.on_claim()
        return True


class FakeCorosClient:
    calls = []
    scheduled_names = ["Renforcement"]
    editable = True
    created_id = "new-workout-id"
    create_result_without_id = False
    standalone_marker = True
    schedule_omits_date_context = False
    update_error = False
    on_update = None
    details_available_dates = None
    details_error_dates = set()

    def __init__(self, access_token):
        self.access_token = access_token

    def list_tools(self):
        return [
            {
                "name": "queryTrainingSchedule",
                "inputSchema": {
                    "properties": {
                        "startDate": {"type": "string"},
                        "endDate": {"type": "string"},
                    },
                    "required": ["startDate", "endDate"],
                },
            },
            {
                "name": "createScheduledWorkout",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "course": {"type": "object"},
                    },
                    "required": ["date", "course"],
                },
            },
            {
                "name": "queryScheduledWorkoutDetails",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "idInPlan": {"type": "string"},
                    },
                    "required": ["date", "idInPlan"],
                },
            },
            {
                "name": "updateScheduledWorkout",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string"},
                        "idInPlan": {"type": "string"},
                        "course": {"type": "object"},
                    },
                    "required": ["date", "idInPlan", "course"],
                },
            },
        ]

    def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        if name == "updateScheduledWorkout":
            if type(self).on_update is not None:
                type(self).on_update()
            if self.update_error:
                raise CorosMcpToolError("COROS a refusé la mise à jour.")
        if name == "queryScheduledWorkoutDetails":
            if arguments["date"] in type(self).details_error_dates:
                raise CorosMcpToolError("Séance introuvable à cette date.")
            if (
                type(self).details_available_dates is not None
                and arguments["date"] not in type(self).details_available_dates
            ):
                return {"structuredContent": {}}
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
            # Keep structured data for schedule display assertions, and mirror
            # COROS's real text response so recovery tests identify only
            # explicitly standalone workouts.
            standalone_text = (
                "Training Schedule\n"
                "========================\n\n"
                + "".join(
                    ("" if type(self).schedule_omits_date_context else "2026-11-12\n")
                    + f"{workout_name}\n"
                    + (
                        "Standalone workout (scheduled from the workout library)\n"
                        if type(self).standalone_marker
                        else ""
                    )
                    + f"idInPlan: {100 + index}\n\n"
                    for index, workout_name in enumerate(self.scheduled_names)
                )
            )
            return {
                "structuredContent": {
                    "schedule": {
                        "days": [
                            {
                                **(
                                    {}
                                    if type(self).schedule_omits_date_context
                                    else {"date": "2026-11-12"}
                                ),
                                "courses": [
                                    {
                                        "idInPlan": str(100 + index),
                                        "courseName": workout_name,
                                    }
                                    for index, workout_name in enumerate(
                                        self.scheduled_names
                                    )
                                ],
                            }
                        ]
                    }
                },
                "content": [{"type": "text", "text": standalone_text}],
            }
        if name == "createScheduledWorkout" and self.create_result_without_id:
            workout_name = arguments["course"]["courseName"]
            if workout_name not in type(self).scheduled_names:
                type(self).scheduled_names.append(workout_name)
            return {"content": [{"type": "text", "text": "Workout created successfully."}]}
        return {
            "structuredContent": {
                "idInPlan": (
                    "updated-workout-id"
                    if name == "updateScheduledWorkout"
                    else self.created_id
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
    FakeCorosClient.created_id = "new-workout-id"
    FakeCorosClient.create_result_without_id = False
    FakeCorosClient.standalone_marker = True
    FakeCorosClient.schedule_omits_date_context = False
    FakeCorosClient.update_error = False
    FakeCorosClient.on_update = None
    FakeCorosClient.details_available_dates = None
    FakeCorosClient.details_error_dates = set()
    monkeypatch.setattr(coros_api, "CorosMcpClient", FakeCorosClient)

    return TestClient(app), repository, profile_id


def test_rejects_incompatible_coros_tool_schema_before_sending(monkeypatch):
    session = make_session()
    client, repository, _ = make_client(monkeypatch, session)

    original_list_tools = FakeCorosClient.list_tools

    def incompatible_tools(self):
        tools = original_list_tools(self)
        create_tool = next(
            tool for tool in tools
            if tool["name"] == "createScheduledWorkout"
        )
        create_tool["inputSchema"]["properties"] = {
            "date": {"type": "integer"},
            "course": {"type": "object"},
        }
        return tools

    monkeypatch.setattr(FakeCorosClient, "list_tools", incompatible_tools)
    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 502
    assert "types d'arguments incompatibles" in response.json()["detail"]
    assert FakeCorosClient.calls == []
    assert repository.session.coros_sync_status is None


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
        {"startDate": "20261112", "endDate": "20261112"},
    )

    tool_name, arguments = FakeCorosClient.calls[1]
    assert tool_name == "createScheduledWorkout"
    assert arguments["date"] == "20261112"
    assert arguments["course"]["sportType"] == 1


def test_create_without_returned_id_recovers_id_from_calendar_and_marks_synced(monkeypatch):
    session = make_session()
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.create_result_without_id = True
    FakeCorosClient.scheduled_names = ["Renforcement"]

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "synced"
    assert repository.session.coros_sync_status == "synced"
    assert repository.session.coros_workout_id == "101"
    assert repository.session.coros_scheduled_date == date(2026, 11, 12)
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
        "createScheduledWorkout",
        "queryTrainingSchedule",
    ]


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
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
    ]

    confirmed = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "synced"
    assert repository.session.coros_sync_status == "synced"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
        "queryTrainingSchedule",
        "createScheduledWorkout",
    ]



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
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
    ]

    confirmed = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "synced"
    assert repository.session.coros_sync_status == "synced"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
        "queryTrainingSchedule",
        "createScheduledWorkout",
    ]



def test_uncertain_retry_recovers_existing_workout_when_same_title_is_on_coros(
    monkeypatch,
):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_payload_hash = "previous-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.scheduled_names = ["Footing aérobie"]
    FakeCorosClient.standalone_marker = False

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 200
    assert repository.session.coros_workout_id == "updated-workout-id"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
        "queryScheduledWorkoutDetails",
        "updateScheduledWorkout",
    ]
    assert all(
        name != "createScheduledWorkout"
        for name, _ in FakeCorosClient.calls
    )


def test_uncertain_create_recovers_existing_coros_id_and_updates_instead_of_duplicating(
    monkeypatch,
):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_payload_hash = "previous-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.scheduled_names = ["Footing aérobie"]

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "synced"
    assert repository.session.coros_sync_status == "synced"
    assert repository.session.coros_workout_id == "updated-workout-id"
    assert repository.session.coros_scheduled_date == date(2026, 11, 12)
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
        "queryScheduledWorkoutDetails",
        "updateScheduledWorkout",
    ]
    update_arguments = FakeCorosClient.calls[-1][1]
    assert update_arguments["idInPlan"] == "100"
    assert all(
        name != "createScheduledWorkout"
        for name, _ in FakeCorosClient.calls
    )


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



def test_moving_session_updates_existing_coros_workout_from_previous_date(monkeypatch):
    session = make_session()
    session.coros_sync_status = "synced"
    session.coros_workout_id = "existing-workout-id"
    session.coros_scheduled_date = date(2026, 11, 12)
    session.coros_payload_hash = map_training_session_to_coros(
        session
    ).payload_hash
    session.date = date(2026, 11, 13)
    client, repository, _ = make_client(monkeypatch, session)

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 200
    assert FakeCorosClient.calls[0] == (
        "queryScheduledWorkoutDetails",
        {"date": "20261112", "idInPlan": "existing-workout-id"},
    )
    assert FakeCorosClient.calls[1][0] == "updateScheduledWorkout"
    assert FakeCorosClient.calls[1][1]["date"] == "20261113"
    assert repository.session.coros_scheduled_date == date(2026, 11, 13)


def test_uncertain_move_reconciles_workout_at_new_date_when_old_date_lookup_misses(monkeypatch):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_workout_id = "existing-workout-id"
    session.coros_scheduled_date = date(2026, 11, 12)
    session.coros_payload_hash = "old-payload-hash"
    session.date = date(2026, 11, 13)
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.details_available_dates = {"20261113"}

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )

    assert response.status_code == 200
    detail_calls = [
        arguments
        for name, arguments in FakeCorosClient.calls
        if name == "queryScheduledWorkoutDetails"
    ]
    assert detail_calls == [
        {"date": "20261112", "idInPlan": "existing-workout-id"},
        {"date": "20261113", "idInPlan": "existing-workout-id"},
    ]
    assert repository.session.coros_scheduled_date == date(2026, 11, 13)



def test_uncertain_move_reconciles_when_coros_errors_on_old_date(monkeypatch):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_workout_id = "existing-workout-id"
    session.coros_scheduled_date = date(2026, 11, 12)
    session.coros_payload_hash = "old-payload-hash"
    session.date = date(2026, 11, 13)
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.details_error_dates = {"20261112"}
    FakeCorosClient.details_available_dates = {"20261113"}

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )

    assert response.status_code == 200
    detail_calls = [
        arguments
        for name, arguments in FakeCorosClient.calls
        if name == "queryScheduledWorkoutDetails"
    ]
    assert [item["date"] for item in detail_calls] == [
        "20261112",
        "20261113",
    ]
    assert repository.session.coros_scheduled_date == date(2026, 11, 13)


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




def test_session_changed_between_mapping_and_claim_is_not_sent_to_coros(monkeypatch):
    session = make_session()
    client, repository, _ = make_client(monkeypatch, session)
    repository.on_claim = lambda: setattr(
        repository.session,
        "title",
        "Footing modifié avant envoi",
    )

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 409
    assert "modifiée pendant la préparation" in response.json()["detail"]
    assert repository.session.coros_sync_status == "failed"
    assert repository.session.title == "Footing modifié avant envoi"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule"
    ]


def test_definitive_update_error_keeps_existing_coros_identity_and_old_hash(monkeypatch):
    session = make_session()
    session.coros_sync_status = "synced"
    session.coros_workout_id = "existing-workout-id"
    session.coros_payload_hash = "old-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.update_error = True

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 422
    assert repository.session.coros_sync_status == "synced"
    assert repository.session.coros_workout_id == "existing-workout-id"
    assert repository.session.coros_payload_hash == "old-payload-hash"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryScheduledWorkoutDetails",
        "updateScheduledWorkout",
    ]



def test_update_error_does_not_overwrite_opencoach_edit_made_while_pending(monkeypatch):
    session = make_session()
    session.coros_sync_status = "synced"
    session.coros_workout_id = "existing-workout-id"
    session.coros_payload_hash = "old-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.update_error = True
    FakeCorosClient.on_update = lambda: setattr(
        repository.session,
        "title",
        "Titre modifié pendant erreur COROS",
    )

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 422
    assert repository.session.title == "Titre modifié pendant erreur COROS"
    assert repository.session.coros_sync_status == "synced"
    assert repository.session.coros_workout_id == "existing-workout-id"
    assert repository.session.coros_payload_hash == "old-payload-hash"


def test_session_changed_during_update_is_not_reported_as_synced_and_retries_as_update(monkeypatch):
    session = make_session()
    session.coros_sync_status = "synced"
    session.coros_workout_id = "existing-workout-id"
    session.coros_payload_hash = "old-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.on_update = lambda: setattr(
        repository.session,
        "title",
        "Footing modifié pendant l'envoi",
    )

    interrupted = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert interrupted.status_code == 409
    assert "modifiée pendant l'envoi" in interrupted.json()["detail"]
    assert repository.session.coros_sync_status == "failed"
    assert repository.session.coros_workout_id == "updated-workout-id"
    assert FakeCorosClient.calls[1][1]["course"]["courseName"] == "Footing aérobie"

    FakeCorosClient.on_update = None
    retried = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert retried.status_code == 200
    assert repository.session.coros_sync_status == "synced"
    assert repository.session.title == "Footing modifié pendant l'envoi"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryScheduledWorkoutDetails",
        "updateScheduledWorkout",
        "queryScheduledWorkoutDetails",
        "updateScheduledWorkout",
    ]
    assert FakeCorosClient.calls[-1][1]["course"]["courseName"] == (
        "Footing modifié pendant l'envoi"
    )


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


def test_uncertain_retry_fails_closed_when_schedule_has_no_parseable_records(monkeypatch):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_payload_hash = "previous-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.scheduled_names = []

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={"confirmed_no_duplicate": True},
    )

    assert response.status_code == 502
    assert "ne reconnaît aucun enregistrement" in response.json()["detail"]
    assert repository.session.coros_sync_status == "unknown"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
    ]
    assert all(name != "createScheduledWorkout" for name, _ in FakeCorosClient.calls)


def test_uncertain_retry_uses_date_scoped_schedule_without_date_fields(monkeypatch):
    session = make_session()
    session.coros_sync_status = "unknown"
    session.coros_payload_hash = "previous-payload-hash"
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.scheduled_names = ["Footing aérobie"]
    FakeCorosClient.standalone_marker = False
    FakeCorosClient.schedule_omits_date_context = True

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "synced"
    assert repository.session.coros_sync_status == "synced"
    assert repository.session.coros_workout_id == "updated-workout-id"
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
        "queryScheduledWorkoutDetails",
        "updateScheduledWorkout",
    ]


def test_create_without_coros_id_is_reconciled_from_new_calendar_record(monkeypatch):
    session = make_session()
    client, repository, _ = make_client(monkeypatch, session)
    FakeCorosClient.created_id = None
    FakeCorosClient.create_result_without_id = True
    FakeCorosClient.standalone_marker = False

    response = client.post(
        f"/api/integrations/coros/workouts/{session.id}/push",
        json={},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "synced"
    assert repository.session.coros_sync_status == "synced"
    assert repository.session.coros_workout_id == "101"
    assert repository.session.coros_last_synced_at is not None
    assert [name for name, _ in FakeCorosClient.calls] == [
        "queryTrainingSchedule",
        "createScheduledWorkout",
        "queryTrainingSchedule",
    ]
