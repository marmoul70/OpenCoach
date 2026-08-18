from uuid import uuid4

import pytest
from cryptography.fernet import Fernet

from opencoach.models import IntegrationConnection
from opencoach.security import SecretCipher
from opencoach.services import (
    IntegrationConnectionService,
    IntegrationConnectionServiceError,
)


class FakeIntegrationConnectionRepository:
    def __init__(self) -> None:
        self.connection = None
        self.encrypted_secret = None

    def get_connection(
        self,
        athlete_profile_id,
        provider,
    ):
        return self.connection

    def save_connection(
        self,
        athlete_profile_id,
        connection,
        encrypted_secret,
    ) -> None:
        self.connection = connection

        if encrypted_secret is not None:
            self.encrypted_secret = encrypted_secret

    def get_encrypted_secret(
        self,
        athlete_profile_id,
        provider,
    ):
        return self.encrypted_secret


def create_service():
    repository = FakeIntegrationConnectionRepository()

    cipher = SecretCipher(
        Fernet.generate_key()
    )

    service = IntegrationConnectionService(
        repository=repository,
        cipher=cipher,
    )

    return service, repository


def test_service_saves_intervals_connection() -> None:
    service, repository = create_service()

    profile_id = uuid4()

    connection = service.save_intervals_connection(
        profile_id,
        athlete_id=" i651743 ",
        api_key=" secret-api-key ",
    )

    assert connection.provider == "intervals"
    assert connection.athlete_id == "i651743"
    assert connection.secret_configured is True

    assert repository.encrypted_secret is not None
    assert repository.encrypted_secret != b"secret-api-key"


def test_service_preserves_existing_secret() -> None:
    service, repository = create_service()

    profile_id = uuid4()

    service.save_intervals_connection(
        profile_id,
        athlete_id="i651743",
        api_key="secret-api-key",
    )

    encrypted_secret = repository.encrypted_secret

    service.save_intervals_connection(
        profile_id,
        athlete_id="i999999",
        api_key=None,
    )

    assert repository.connection.athlete_id == "i999999"
    assert repository.encrypted_secret == encrypted_secret


def test_service_returns_decrypted_credentials() -> None:
    service, _ = create_service()

    profile_id = uuid4()

    service.save_intervals_connection(
        profile_id,
        athlete_id="i651743",
        api_key="secret-api-key",
    )

    credentials = service.get_credentials(
        profile_id,
        "intervals",
    )

    assert credentials.provider == "intervals"
    assert credentials.athlete_id == "i651743"
    assert credentials.secret == "secret-api-key"


def test_service_requires_api_key_for_new_connection() -> None:
    service, _ = create_service()

    with pytest.raises(
        IntegrationConnectionServiceError,
        match="clé API Intervals.icu est obligatoire",
    ):
        service.save_intervals_connection(
            uuid4(),
            athlete_id="i651743",
            api_key=None,
        )


def test_service_rejects_missing_connection() -> None:
    service, _ = create_service()

    with pytest.raises(
        IntegrationConnectionServiceError,
        match="n'est pas configurée",
    ):
        service.get_credentials(
            uuid4(),
            "intervals",
        )
