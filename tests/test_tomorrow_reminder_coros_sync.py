from types import SimpleNamespace
from uuid import uuid4

from fastapi import HTTPException

from opencoach.commands import send_tomorrow_training_reminder as reminder_command


class FakeDatabase:
    def __init__(self, connection):
        self.connection = connection

    def scalar(self, _statement):
        return self.connection


def test_day_before_sync_uses_existing_coros_push_flow(monkeypatch):
    profile_id = uuid4()
    session_id = uuid4()
    connection = SimpleNamespace(enabled=True)
    database = FakeDatabase(connection)
    calls = []

    def fake_push(**kwargs):
        calls.append(kwargs)
        return {
            "status": "synced",
            "message": "La séance a été ajoutée au calendrier COROS.",
        }

    monkeypatch.setattr(
        reminder_command,
        "push_training_session_to_coros",
        fake_push,
    )

    message = reminder_command._sync_session_to_coros(
        database,
        athlete_profile_id=profile_id,
        session_id=session_id,
    )

    assert message == "COROS : La séance a été ajoutée au calendrier COROS."
    assert len(calls) == 1
    assert calls[0]["session_id"] == session_id
    assert calls[0]["athlete_profile_id"] == profile_id
    assert calls[0]["payload"].confirmed_no_duplicate is False


def test_day_before_sync_skips_when_coros_is_disabled(monkeypatch):
    database = FakeDatabase(SimpleNamespace(enabled=False))

    def unexpected_push(**_kwargs):
        raise AssertionError("COROS must not be called when disabled")

    monkeypatch.setattr(
        reminder_command,
        "push_training_session_to_coros",
        unexpected_push,
    )

    assert reminder_command._sync_session_to_coros(
        database,
        athlete_profile_id=uuid4(),
        session_id=uuid4(),
    ) is None


def test_day_before_sync_reports_coros_errors_without_raising(monkeypatch):
    database = FakeDatabase(SimpleNamespace(enabled=True))

    def failed_push(**_kwargs):
        raise HTTPException(
            status_code=409,
            detail="Séance déjà en cours de synchronisation.",
        )

    monkeypatch.setattr(
        reminder_command,
        "push_training_session_to_coros",
        failed_push,
    )

    message = reminder_command._sync_session_to_coros(
        database,
        athlete_profile_id=uuid4(),
        session_id=uuid4(),
    )

    assert message == (
        "Synchronisation COROS non effectuée : "
        "Séance déjà en cours de synchronisation."
    )
