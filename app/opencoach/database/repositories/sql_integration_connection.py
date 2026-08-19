from uuid import UUID
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import (
    IntegrationConnection as IntegrationConnectionModel,
)
from opencoach.database.repositories.integration_connection import (
    IntegrationConnectionRepository,
)
from opencoach.database.repositories.errors import (
    IntegrationConnectionRepositoryError,
)
from opencoach.models import IntegrationConnection


class SqlIntegrationConnectionRepository(
    IntegrationConnectionRepository,
):
    """Persiste les connexions externes dans la base SQL."""

    def __init__(
        self,
        session: Session,
    ) -> None:
        self.session = session

    def get_connection(
        self,
        athlete_profile_id: UUID,
        provider: str,
    ) -> IntegrationConnection | None:
        try:
            database_connection = self._get_database_connection(
                athlete_profile_id=athlete_profile_id,
                provider=provider,
            )

            if database_connection is None:
                return None

            config = database_connection.config or {}

            return IntegrationConnection(
                provider=database_connection.provider,
                enabled=database_connection.enabled,
                athlete_id=config.get("athlete_id"),
                secret_configured=(
                    database_connection.encrypted_secret is not None
                ),
                last_synced_at=database_connection.last_synced_at,
            )

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise IntegrationConnectionRepositoryError(
                "Impossible de charger la connexion."
            ) from exc

    def save_connection(
        self,
        athlete_profile_id: UUID,
        connection: IntegrationConnection,
        encrypted_secret: bytes | None,
    ) -> None:
        try:
            database_connection = self._get_database_connection(
                athlete_profile_id=athlete_profile_id,
                provider=connection.provider,
            )

            if database_connection is None:
                database_connection = IntegrationConnectionModel(
                    athlete_profile_id=athlete_profile_id,
                    provider=connection.provider,
                )

                self.session.add(database_connection)

            database_connection.enabled = connection.enabled
            database_connection.config = {
                "athlete_id": connection.athlete_id,
            }

            if encrypted_secret is not None:
                database_connection.encrypted_secret = (
                    encrypted_secret
                )

            self.session.commit()
            self.session.refresh(database_connection)

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise IntegrationConnectionRepositoryError(
                "Impossible d'enregistrer la connexion."
            ) from exc

    def get_encrypted_secret(
        self,
        athlete_profile_id: UUID,
        provider: str,
    ) -> bytes | None:
        try:
            database_connection = self._get_database_connection(
                athlete_profile_id=athlete_profile_id,
                provider=provider,
            )

            if database_connection is None:
                return None

            return database_connection.encrypted_secret

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise IntegrationConnectionRepositoryError(
                "Impossible de charger le secret."
            ) from exc

    def _get_database_connection(
        self,
        *,
        athlete_profile_id: UUID,
        provider: str,
    ) -> IntegrationConnectionModel | None:
        statement = (
            select(IntegrationConnectionModel)
            .where(
                IntegrationConnectionModel.athlete_profile_id
                == athlete_profile_id,
                IntegrationConnectionModel.provider == provider,
            )
        )

        return self.session.scalar(statement)

    def mark_synced(
        self,
        athlete_profile_id: UUID,
        provider: str,
        synced_at: datetime,
    ) -> None:
        try:
            database_connection = self._get_database_connection(
                athlete_profile_id=athlete_profile_id,
                provider=provider,
            )

            if database_connection is None:
                raise IntegrationConnectionRepositoryError(
                    "La connexion à synchroniser n'existe pas."
                )

            database_connection.last_synced_at = synced_at

            self.session.commit()
            self.session.refresh(database_connection)

        except IntegrationConnectionRepositoryError:
            self.session.rollback()
            raise

        except SQLAlchemyError as exc:
            self.session.rollback()

            raise IntegrationConnectionRepositoryError(
                "Impossible d'enregistrer la date de synchronisation."
            ) from exc