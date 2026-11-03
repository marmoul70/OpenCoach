from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from opencoach.api.app import create_app
from opencoach.api import coros as coros_api
from opencoach.api.coros import get_current_athlete_profile_id
from opencoach.database.session import get_db


class FakeConnection:
    enabled = True

    def __init__(self):
        self.config = {"connected": True}


class FakeDatabase:
    def __init__(self):
        self.connection = FakeConnection()
        self.added = []
        self.commits = 0
        self.expirations = 0

    def get(self, model, key):
        return None

    def add(self, value):
        self.added.append(value)

    def commit(self):
        self.commits += 1

    def expire_all(self):
        self.expirations += 1


def make_sync_client(monkeypatch, worker):
    profile_id = uuid4()
    db = FakeDatabase()
    app = create_app()
    app.dependency_overrides[get_current_athlete_profile_id] = lambda: profile_id
    app.dependency_overrides[get_db] = lambda: db
    monkeypatch.setattr(coros_api, "_connection", lambda session, owner: db.connection)
    monkeypatch.setattr(coros_api, "run_coros_sync_job", worker)
    return TestClient(app), db, profile_id


def test_legacy_sync_endpoint_uses_shared_worker_and_returns_result(monkeypatch):
    calls = []

    def worker(*, job_id: UUID, athlete_profile_id: UUID):
        calls.append((job_id, athlete_profile_id))
        db.connection.config["coros_sync_job"] = {
            "job_id": str(job_id),
            "status": "success",
            "result": {"imported_snapshots": {"activities": 2}},
            "error": None,
        }

    client, db, profile_id = make_sync_client(monkeypatch, worker)

    response = client.post("/api/integrations/coros/sync")

    assert response.status_code == 200
    assert response.json() == {
        "status": "completed",
        "imported_snapshots": {"activities": 2},
    }
    assert len(calls) == 1
    assert calls[0][1] == profile_id
    assert db.commits == 1
    assert db.expirations == 1


def test_legacy_sync_endpoint_returns_error_when_shared_worker_fails(monkeypatch):
    def worker(*, job_id: UUID, athlete_profile_id: UUID):
        db.connection.config["coros_sync_job"] = {
            "job_id": str(job_id),
            "status": "error",
            "result": None,
            "error": "Import interrompu.",
        }

    client, db, _ = make_sync_client(monkeypatch, worker)

    response = client.post("/api/integrations/coros/sync")

    assert response.status_code == 502
    assert response.json() == {"detail": "Import interrompu."}
    assert db.expirations == 1



def test_legacy_sync_endpoint_preserves_coros_authentication_error_status(monkeypatch):
    def worker(*, job_id: UUID, athlete_profile_id: UUID):
        db.connection.config["coros_sync_job"] = {
            "job_id": str(job_id),
            "status": "error",
            "http_status": 401,
            "result": None,
            "error": "La connexion COROS a expiré. Reconnecte ton compte.",
        }

    client, db, _ = make_sync_client(monkeypatch, worker)

    response = client.post("/api/integrations/coros/sync")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "La connexion COROS a expiré. Reconnecte ton compte."
    }
    assert db.expirations == 1



def test_orphaned_coros_sync_is_marked_interrupted_and_unlocks_profile():
    from opencoach.api.coros import _recover_interrupted_coros_sync
    from opencoach.database.models import CorosSyncLock

    profile_id = uuid4()
    job_id = str(uuid4())

    class Lock:
        def __init__(self):
            self.job_id = job_id

    class Database:
        def __init__(self):
            self.lock = Lock()
            self.deleted = None
            self.commits = 0

        def get(self, model, key):
            assert model is CorosSyncLock
            assert key == profile_id
            return self.lock

        def delete(self, value):
            self.deleted = value

        def commit(self):
            self.commits += 1

    class Connection:
        config = {
            "coros_sync_job": {
                "job_id": job_id,
                "status": "running",
                "error": None,
            }
        }

    db = Database()
    connection = Connection()

    _recover_interrupted_coros_sync(db, profile_id, connection)

    state = connection.config["coros_sync_job"]
    assert state["status"] == "interrupted"
    assert "Relance-la" in state["error"]
    assert db.deleted is db.lock
    assert db.commits == 1


def test_live_coros_sync_job_is_not_marked_interrupted():
    from opencoach.api.coros import _recover_interrupted_coros_sync
    from opencoach.services.coros_sync_job import COROS_SYNC_JOBS

    profile_id = uuid4()
    job = COROS_SYNC_JOBS.create(profile_id)

    class Database:
        def get(self, model, key):
            raise AssertionError("A live job must not be reconciled")

        def commit(self):
            raise AssertionError("A live job must not be modified")

    class Connection:
        config = {
            "coros_sync_job": {
                "job_id": str(job.id),
                "status": "running",
                "error": None,
            }
        }

    connection = Connection()
    try:
        _recover_interrupted_coros_sync(Database(), profile_id, connection)
        assert connection.config["coros_sync_job"]["status"] == "running"
    finally:
        COROS_SYNC_JOBS.discard(job.id)
