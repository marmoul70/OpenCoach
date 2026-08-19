from uuid import UUID
from datetime import date, datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from opencoach.database.models import AthleteProfile, User
from opencoach.database.repositories import (
    ActivityRepositoryError,
    IntegrationConnectionRepositoryError,
    SqlActivityRepository,
    SqlIntegrationConnectionRepository,
    SqlWellnessRepository,
    WellnessRepositoryError,
)
from opencoach.database.session import get_db
from opencoach.integrations.intervals import (
    IntervalsApiError,
    IntervalsAuthenticationError,
    IntervalsClient,
    IntervalsDataError,
    IntervalsSyncService,
)
from opencoach.services import (
    DEFAULT_SYNC_DAYS,
    IntegrationConnectionService,
    IntegrationConnectionServiceError,
    IntervalsApplicationService,
)
from opencoach.schemas.integration import (
    IntervalsConnectionResponse,
    IntervalsConnectionTest,
    IntervalsConnectionTestResponse,
    IntervalsConnectionUpdate,
)
from opencoach.security import (
    SecretCipher,
    SecretCipherError,
)


LOCAL_USER_EMAIL = "local@opencoach.local"


router = APIRouter(
    prefix="/api/integrations/intervals",
    tags=["integrations"],
)


def get_local_athlete_profile_id(
    db: Session = Depends(get_db),
) -> UUID:
    """Retourne l'identifiant du profil sportif local."""

    try:
        statement = (
            select(AthleteProfile.id)
            .join(AthleteProfile.user)
            .where(User.email == LOCAL_USER_EMAIL)
        )

        profile_id = db.scalar(statement)

    except SQLAlchemyError as exc:
        db.rollback()

        raise HTTPException(
            status_code=503,
            detail="Le stockage OpenCoach est temporairement indisponible.",
        ) from exc

    if profile_id is None:
        raise HTTPException(
            status_code=404,
            detail="Le profil sportif local est introuvable.",
        )

    return profile_id

def get_integration_connection_service(
    db: Session = Depends(get_db),
) -> IntegrationConnectionService:
    """Construit le service de gestion des connexions."""

    try:
        cipher = SecretCipher.from_env()

    except SecretCipherError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "La clé de chiffrement OpenCoach "
                "n'est pas configurée."
            ),
        ) from exc

    repository = SqlIntegrationConnectionRepository(
        db,
    )

    return IntegrationConnectionService(
        repository=repository,
        cipher=cipher,
    )

def get_intervals_application_service(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    db: Session = Depends(get_db),
    connection_service: IntegrationConnectionService = Depends(
        get_integration_connection_service,
    ),
) -> IntervalsApplicationService:
    """Construit le service applicatif Intervals.icu."""

    try:
        credentials = connection_service.get_credentials(
            athlete_profile_id,
            "intervals",
        )

    except IntegrationConnectionServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "L'intégration Intervals.icu "
                "n'est pas configurée."
            ),
        ) from exc

    except IntegrationConnectionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de charger la connexion "
                "Intervals.icu."
            ),
        ) from exc

    except SecretCipherError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Impossible de déchiffrer les identifiants "
                "Intervals.icu."
            ),
        ) from exc

    client = IntervalsClient(
        api_key=credentials.secret,
        athlete_id=credentials.athlete_id,
    )

    activity_repository = SqlActivityRepository(db)
    wellness_repository = SqlWellnessRepository(db)

    sync_service = IntervalsSyncService(
        client=client,
        repository=activity_repository,
        wellness_repository=wellness_repository,
    )

    return IntervalsApplicationService(
        sync_service=sync_service,
    )

@router.get(
    "/connection",
    response_model=IntervalsConnectionResponse,
)
def get_intervals_connection(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    service: IntegrationConnectionService = Depends(
        get_integration_connection_service,
    ),
) -> IntervalsConnectionResponse:
    """Retourne l'état de configuration Intervals.icu."""

    try:
        connection = service.get_connection(
            athlete_profile_id,
            "intervals",
        )

    except IntegrationConnectionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de charger la connexion Intervals.icu.",
        ) from exc

    if connection is None:
        return IntervalsConnectionResponse(
            configured=False,
            enabled=False,
            athlete_id=None,
            api_key_configured=False,
            last_synced_at=None,
        )

    return IntervalsConnectionResponse(
        configured=True,
        enabled=connection.enabled,
        athlete_id=connection.athlete_id,
        api_key_configured=connection.secret_configured,
        last_synced_at=connection.last_synced_at,
    )

@router.put(
    "/connection",
    response_model=IntervalsConnectionResponse,
)
def save_intervals_connection(
    payload: IntervalsConnectionUpdate,
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    service: IntegrationConnectionService = Depends(
        get_integration_connection_service,
    ),
) -> IntervalsConnectionResponse:
    """Crée ou met à jour la connexion Intervals.icu."""

    try:
        connection = service.save_intervals_connection(
            athlete_profile_id=athlete_profile_id,
            athlete_id=payload.athlete_id,
            api_key=payload.api_key,
            enabled=payload.enabled,
        )

    except IntegrationConnectionServiceError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except IntegrationConnectionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible d'enregistrer la connexion Intervals.icu.",
        ) from exc

    return IntervalsConnectionResponse(
        configured=True,
        enabled=connection.enabled,
        athlete_id=connection.athlete_id,
        api_key_configured=connection.secret_configured,
        last_synced_at=connection.last_synced_at,
    )

@router.post("/sync")
def sync_intervals(
    days: int = Query(
        default=DEFAULT_SYNC_DAYS,
        ge=1,
        le=3650,
    ),
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    service: IntervalsApplicationService = Depends(
        get_intervals_application_service,
    ),
    connection_service: IntegrationConnectionService = Depends(
        get_integration_connection_service,
    ),
) -> dict[str, str | int]:
    """Synchronise activités et Wellness Intervals.icu."""

    try:
        (
            synced_activities,
            synced_wellness_days,
        ) = service.sync_all(
            athlete_profile_id,
            days=days,
        )

    except IntervalsAuthenticationError as exc:
        raise HTTPException(
            status_code=502,
            detail="L'authentification auprès d'Intervals.icu a échoué.",
        ) from exc

    except IntervalsApiError as exc:
        raise HTTPException(
            status_code=502,
            detail="Intervals.icu est temporairement indisponible.",
        ) from exc

    except IntervalsDataError as exc:
        raise HTTPException(
            status_code=502,
            detail="Intervals.icu a retourné des données invalides.",
        ) from exc

    except ActivityRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible d'enregistrer les activités.",
        ) from exc

    except WellnessRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible d'enregistrer les données Wellness.",
        ) from exc

    synced_at = datetime.now(
        timezone.utc,
    )

    try:
        connection_service.mark_synced(
            athlete_profile_id,
            "intervals",
            synced_at,
        )

    except IntegrationConnectionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "La synchronisation a réussi, "
                "mais sa date n'a pas pu être enregistrée."
            ),
        ) from exc

    return {
        "provider": "intervals",
        "synced_activities": synced_activities,
        "synced_wellness_days": synced_wellness_days,
        "days": days,
        "synced_at": synced_at.isoformat(),
    }



@router.post(
    "/connection/test",
    response_model=IntervalsConnectionTestResponse,
)
def test_intervals_connection(
    payload: IntervalsConnectionTest,
) -> IntervalsConnectionTestResponse:
    """Teste des credentials Intervals.icu sans les enregistrer."""

    client = IntervalsClient(
        api_key=payload.api_key.strip(),
        athlete_id=payload.athlete_id.strip(),
    )

    today = date.today()

    try:
        client.get_wellness(
            oldest=today,
            newest=today,
        )

    except IntervalsAuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail="Identifiants Intervals.icu refusés.",
        ) from exc

    except IntervalsApiError as exc:
        raise HTTPException(
            status_code=502,
            detail="Impossible de contacter Intervals.icu.",
        ) from exc

    return IntervalsConnectionTestResponse(
        connected=True,
        athlete_id=payload.athlete_id.strip(),
    )

@router.post(
    "/connection/test-saved",
    response_model=IntervalsConnectionTestResponse,
)
def test_saved_intervals_connection(
    athlete_profile_id: UUID = Depends(
        get_local_athlete_profile_id,
    ),
    service: IntegrationConnectionService = Depends(
        get_integration_connection_service,
    ),
) -> IntervalsConnectionTestResponse:
    """Teste la connexion Intervals.icu enregistrée."""

    try:
        credentials = service.get_credentials(
            athlete_profile_id,
            "intervals",
        )

    except IntegrationConnectionServiceError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except IntegrationConnectionRepositoryError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de charger la connexion Intervals.icu.",
        ) from exc

    except SecretCipherError as exc:
        raise HTTPException(
            status_code=503,
            detail="Impossible de déchiffrer les identifiants Intervals.icu.",
        ) from exc

    client = IntervalsClient(
        api_key=credentials.secret,
        athlete_id=credentials.athlete_id,
    )

    today = date.today()

    try:
        client.get_wellness(
            oldest=today,
            newest=today,
        )

    except IntervalsAuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail="Identifiants Intervals.icu refusés.",
        ) from exc

    except IntervalsApiError as exc:
        raise HTTPException(
            status_code=502,
            detail="Impossible de contacter Intervals.icu.",
        ) from exc

    return IntervalsConnectionTestResponse(
        connected=True,
        athlete_id=credentials.athlete_id,
    )