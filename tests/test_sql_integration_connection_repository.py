from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from opencoach.database.base import Base
from opencoach.database.models import (
    AthleteProfile,
    IntegrationConnection as IntegrationConnectionModel,
    User,
)
from opencoach.database.repositories import (
    SqlIntegrationConnectionRepository,
)
from opencoach.models import IntegrationConnection


def create_session():
    engine = create_engine(
        "sqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )

    return SessionLocal()


def create_profile(
    db,
) -> AthleteProfile:
    user = User(
        email="local@opencoach.local",
    )

    profile = AthleteProfile(
        user=user,
        first_name="Test",
        last_name="Athlete",
    )

    db.add(profile)
    db.commit()

    return profile


def create_connection() -> IntegrationConnection:
    return IntegrationConnection(
        provider="intervals",
        enabled=True,
        athlete_id="i651743",
        secret_configured=True,
    )


def test_sql_integration_repository_inserts_connection() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlIntegrationConnectionRepository(
            db,
        )

        repository.save_connection(
            profile.id,
            create_connection(),
            b"encrypted-api-key",
        )

        saved = db.query(
            IntegrationConnectionModel,
        ).one()

        assert saved.athlete_profile_id == profile.id
        assert saved.provider == "intervals"
        assert saved.enabled is True

        assert saved.config == {
            "athlete_id": "i651743",
        }

        assert saved.encrypted_secret == (
            b"encrypted-api-key"
        )

    finally:
        db.close()


def test_sql_integration_repository_returns_connection() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlIntegrationConnectionRepository(
            db,
        )

        repository.save_connection(
            profile.id,
            create_connection(),
            b"encrypted-api-key",
        )

        result = repository.get_connection(
            profile.id,
            "intervals",
        )

        assert result is not None
        assert result.provider == "intervals"
        assert result.enabled is True
        assert result.athlete_id == "i651743"
        assert result.secret_configured is True

    finally:
        db.close()


def test_sql_integration_repository_preserves_existing_secret() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlIntegrationConnectionRepository(
            db,
        )

        connection = create_connection()

        repository.save_connection(
            profile.id,
            connection,
            b"original-secret",
        )

        connection.athlete_id = "i999999"

        repository.save_connection(
            profile.id,
            connection,
            None,
        )

        rows = db.query(
            IntegrationConnectionModel,
        ).all()

        assert len(rows) == 1

        assert rows[0].config == {
            "athlete_id": "i999999",
        }

        assert rows[0].encrypted_secret == (
            b"original-secret"
        )

    finally:
        db.close()


def test_sql_integration_repository_returns_encrypted_secret() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlIntegrationConnectionRepository(
            db,
        )

        repository.save_connection(
            profile.id,
            create_connection(),
            b"encrypted-api-key",
        )

        secret = repository.get_encrypted_secret(
            profile.id,
            "intervals",
        )

        assert secret == b"encrypted-api-key"

    finally:
        db.close()


def test_sql_integration_repository_returns_none_when_missing() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlIntegrationConnectionRepository(
            db,
        )

        connection = repository.get_connection(
            profile.id,
            "intervals",
        )

        secret = repository.get_encrypted_secret(
            profile.id,
            "intervals",
        )

        assert connection is None
        assert secret is None

    finally:
        db.close()

def test_marks_integration_as_synced() -> None:
    db = create_session()

    try:
        profile = create_profile(db)

        repository = SqlIntegrationConnectionRepository(
            db,
        )

        repository.save_connection(
            profile.id,
            IntegrationConnection(
                provider="intervals",
                enabled=True,
                athlete_id="i123456",
                secret_configured=True,
            ),
            b"encrypted-secret",
        )

        synced_at = datetime(
            2026,
            8,
            19,
            21,
            0,
        )

        repository.mark_synced(
            profile.id,
            "intervals",
            synced_at,
        )

        connection = repository.get_connection(
            profile.id,
            "intervals",
        )

        assert connection is not None
        assert connection.last_synced_at == synced_at

    finally:
        db.close()