import json
from datetime import datetime
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from opencoach.database.base import Base
from opencoach.database.models import (
    Activity,
    AthleteProfile,
    CorosSyncLock,
    IntegrationConnection,
    User,
)
from opencoach.services import coros_sync_job


def test_coros_sync_worker_persists_success_and_releases_lock(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    profile_id = uuid4()
    job = coros_sync_job.COROS_SYNC_JOBS.create(profile_id)
    job_id = job.id
    secret = {"status": "connected", "access_token": "test-access"}
    initial_checkpoint = {
        "activities": "2026-10-30",
        "_completed": "activities,sleep",
    }

    with TestSession() as setup_db:
        user = User(email=f"{profile_id}@example.test")
        profile = AthleteProfile(id=profile_id, user=user)
        setup_db.add(profile)
        setup_db.flush()
        connection = IntegrationConnection(
            athlete_profile_id=profile_id,
            provider="coros",
            enabled=True,
            config={
                "connected": True,
                "categories": {"activities": True},
                "coros_sync_checkpoint": initial_checkpoint,
            },
            encrypted_secret=b"encrypted-test-secret",
        )
        setup_db.add_all([
            connection,
            CorosSyncLock(
                athlete_profile_id=profile_id,
                job_id=str(job_id),
            ),
        ])
        setup_db.commit()

    monkeypatch.setattr(
        "opencoach.database.session.SessionLocal",
        TestSession,
    )

    class FakeCipher:
        def decrypt(self, _encrypted):
            return json.dumps(secret)

        def encrypt(self, value):
            return value.encode()

    monkeypatch.setattr(
        "opencoach.security.SecretCipher.from_env",
        classmethod(lambda cls: FakeCipher()),
    )
    monkeypatch.setattr(
        "opencoach.integrations.coros.tokens.refresh_secret_if_needed",
        lambda current, _oauth, now: current,
    )

    class FakeOAuth:
        def __init__(self, redirect_uri):
            self.redirect_uri = redirect_uri

    class FakeClient:
        def __init__(self, access_token):
            assert access_token == "test-access"

    class FakeImporter:
        def __init__(self, client, db, owner_id, progress_callback):
            self.db = db
            self.owner_id = owner_id
            self.progress_callback = progress_callback

        def import_history(self, categories, *, months, start_date, checkpoint):
            assert categories == {"activities": True}
            assert months == 6
            assert start_date is None
            assert checkpoint == {
                "activities": "2026-10-30",
                "_completed": "sleep",
            }
            self.progress_callback("activities", "2026-10-23")
            self.progress_callback("activities", None)
            self.db.add(Activity(
                athlete_profile_id=self.owner_id,
                provider="coros",
                provider_activity_id="test-activity-1",
                name="Test trail",
                sport_type="trail_running",
                start_at=datetime(2026, 11, 3, 7, 0),
            ))
            return {"imported_snapshots": {"activities": 1}}

    monkeypatch.setattr(
        "opencoach.integrations.coros.oauth.CorosOAuthClientService",
        FakeOAuth,
    )
    monkeypatch.setattr(
        "opencoach.integrations.coros.client.CorosMcpClient",
        FakeClient,
    )
    monkeypatch.setattr(
        "opencoach.integrations.coros.sync.CorosImportService",
        FakeImporter,
    )

    coros_sync_job.run_coros_sync_job(
        job_id=job_id,
        athlete_profile_id=profile_id,
    )

    with TestSession() as verify_db:
        saved_connection = verify_db.scalar(
            select(IntegrationConnection).where(
                IntegrationConnection.athlete_profile_id == profile_id,
                IntegrationConnection.provider == "coros",
            )
        )
        saved_lock = verify_db.get(CorosSyncLock, profile_id)
        saved_activity = verify_db.scalar(
            select(Activity).where(
                Activity.athlete_profile_id == profile_id,
                Activity.provider == "coros",
            )
        )

        assert saved_lock is None
        assert saved_activity is not None
        assert saved_connection.config["coros_initial_import_completed"] is True
        assert "coros_sync_checkpoint" not in saved_connection.config
        assert saved_connection.config["coros_sync_job"]["status"] == "success"
        assert saved_connection.config["coros_sync_job"]["result"] == {
            "imported_snapshots": {"activities": 1}
        }
        assert saved_connection.last_synced_at is not None

    saved_job = coros_sync_job.COROS_SYNC_JOBS.get(job_id)
    assert saved_job is not None
    assert saved_job.status == "success"
    coros_sync_job.COROS_SYNC_JOBS.discard(job_id)
    engine.dispose()


def _run_coros_sync_failure(monkeypatch, error):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)
    profile_id = uuid4()
    job = coros_sync_job.COROS_SYNC_JOBS.create(profile_id)
    job_id = job.id
    secret = {"status": "connected", "access_token": "test-access"}

    with TestSession() as setup_db:
        user = User(email=f"{profile_id}@example.test")
        profile = AthleteProfile(id=profile_id, user=user)
        setup_db.add(profile)
        setup_db.flush()
        setup_db.add_all([
            IntegrationConnection(
                athlete_profile_id=profile_id,
                provider="coros",
                enabled=True,
                config={
                    "connected": True,
                    "categories": {"activities": True},
                },
                encrypted_secret=b"encrypted-test-secret",
            ),
            CorosSyncLock(
                athlete_profile_id=profile_id,
                job_id=str(job_id),
            ),
        ])
        setup_db.commit()

    monkeypatch.setattr(
        "opencoach.database.session.SessionLocal",
        TestSession,
    )

    class FakeCipher:
        def decrypt(self, _encrypted):
            return json.dumps(secret)

    monkeypatch.setattr(
        "opencoach.security.SecretCipher.from_env",
        classmethod(lambda cls: FakeCipher()),
    )
    monkeypatch.setattr(
        "opencoach.integrations.coros.tokens.refresh_secret_if_needed",
        lambda current, _oauth, now: current,
    )

    class FakeOAuth:
        def __init__(self, redirect_uri):
            self.redirect_uri = redirect_uri

    class FakeClient:
        def __init__(self, access_token):
            assert access_token == "test-access"

    class FakeImporter:
        def __init__(self, client, db, owner_id, progress_callback):
            pass

        def import_history(self, categories, *, months, start_date, checkpoint):
            raise error

    monkeypatch.setattr(
        "opencoach.integrations.coros.oauth.CorosOAuthClientService",
        FakeOAuth,
    )
    monkeypatch.setattr(
        "opencoach.integrations.coros.client.CorosMcpClient",
        FakeClient,
    )
    monkeypatch.setattr(
        "opencoach.integrations.coros.sync.CorosImportService",
        FakeImporter,
    )

    coros_sync_job.run_coros_sync_job(
        job_id=job_id,
        athlete_profile_id=profile_id,
    )

    with TestSession() as verify_db:
        saved_connection = verify_db.scalar(
            select(IntegrationConnection).where(
                IntegrationConnection.athlete_profile_id == profile_id,
                IntegrationConnection.provider == "coros",
            )
        )
        assert verify_db.get(CorosSyncLock, profile_id) is None
        assert saved_connection.config["coros_sync_job"]["status"] == "error"
        assert saved_connection.config["coros_sync_job"]["http_status"] == (
            401 if isinstance(error, CorosMcpAuthenticationError) else 502
        )
        assert saved_connection.enabled is (
            not isinstance(error, CorosMcpAuthenticationError)
        )
        assert saved_connection.config["connected"] is (
            not isinstance(error, CorosMcpAuthenticationError)
        )
        if isinstance(error, CorosMcpAuthenticationError):
            assert saved_connection.config["coros_sync_job"]["error"] == (
                "La connexion COROS a expiré. Reconnecte ton compte."
            )
        else:
            assert saved_connection.config["coros_sync_job"]["error"] == (
                "La synchronisation COROS a échoué. Vérifie la connexion puis consulte les journaux OpenCoach."
            )

    saved_job = coros_sync_job.COROS_SYNC_JOBS.get(job_id)
    assert saved_job is not None
    assert saved_job.status == "error"
    coros_sync_job.COROS_SYNC_JOBS.discard(job_id)
    engine.dispose()


def test_coros_sync_worker_persists_authentication_failure_and_disables_connection(monkeypatch):
    from opencoach.integrations.coros.errors import CorosMcpAuthenticationError

    _run_coros_sync_failure(
        monkeypatch,
        CorosMcpAuthenticationError("sensitive provider response must not leak"),
    )


def test_coros_sync_worker_persists_generic_failure_without_disabling_connection(monkeypatch):
    _run_coros_sync_failure(
        monkeypatch,
        RuntimeError("sensitive internal failure must not leak"),
    )
