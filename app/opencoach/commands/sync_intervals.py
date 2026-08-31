"""Synchronisation incrémentale Intervals.icu en ligne de commande."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import (
    AthleteProfile,
    User,
)
from opencoach.database.repositories import (
    SqlActivityDetailRepository,
    SqlActivityRepository,
    SqlIntegrationConnectionRepository,
    SqlWellnessRepository,
)
from opencoach.database.session import SessionLocal
from opencoach.integrations.intervals import (
    IntervalsClient,
    IntervalsSyncService,
)
from opencoach.security import SecretCipher
from opencoach.services import (
    DEFAULT_INCREMENTAL_LOOKBACK_DAYS,
    DEFAULT_SYNC_DAYS,
    IntegrationConnectionService,
    IntervalsApplicationService,
)


LOCAL_USER_EMAIL = "local@opencoach.local"


def build_parser() -> argparse.ArgumentParser:
    """Construit le parser de la commande."""

    parser = argparse.ArgumentParser(
        description=(
            "Synchronise OpenCoach avec Intervals.icu."
        ),
    )

    parser.add_argument(
        "--initial-days",
        type=_positive_integer,
        default=DEFAULT_SYNC_DAYS,
    )

    parser.add_argument(
        "--lookback-days",
        type=_non_negative_integer,
        default=DEFAULT_INCREMENTAL_LOOKBACK_DAYS,
    )

    return parser


def _positive_integer(
    raw_value: str,
) -> int:
    value = int(raw_value)

    if value <= 0:
        raise argparse.ArgumentTypeError(
            "la valeur doit être strictement positive"
        )

    return value


def _non_negative_integer(
    raw_value: str,
) -> int:
    value = int(raw_value)

    if value < 0:
        raise argparse.ArgumentTypeError(
            "la valeur ne peut pas être négative"
        )

    return value


def get_local_athlete_profile_id(
    session: Session,
) -> UUID:
    """Retourne le profil sportif de l'utilisateur local."""

    statement = (
        select(AthleteProfile.id)
        .join(AthleteProfile.user)
        .where(
            User.email == LOCAL_USER_EMAIL
        )
    )

    profile_id = session.scalar(
        statement
    )

    if profile_id is None:
        raise RuntimeError(
            "Le profil sportif local est introuvable."
        )

    return profile_id


def build_service(
    session: Session,
) -> IntervalsApplicationService:
    """Construit le service réel de synchronisation."""

    connection_repository = (
        SqlIntegrationConnectionRepository(
            session
        )
    )

    connection_service = (
        IntegrationConnectionService(
            repository=connection_repository,
            cipher=SecretCipher.from_env(),
        )
    )

    profile_id = get_local_athlete_profile_id(
        session
    )

    credentials = (
        connection_service.get_credentials(
            profile_id,
            "intervals",
        )
    )

    client = IntervalsClient(
        api_key=credentials.secret,
        athlete_id=credentials.athlete_id,
    )

    sync_service = IntervalsSyncService(
        client=client,
        repository=SqlActivityRepository(
            session
        ),
        activity_detail_repository=(
            SqlActivityDetailRepository(
                session
            )
        ),
        wellness_repository=SqlWellnessRepository(
            session
        ),
    )

    return IntervalsApplicationService(
        sync_service=sync_service,
        connection_service=connection_service,
    )


def main(
    argv: Sequence[str] | None = None,
    *,
    service: IntervalsApplicationService | None = None,
    athlete_profile_id: UUID | None = None,
) -> int:
    """Exécute une synchronisation incrémentale."""

    args = build_parser().parse_args(
        argv
    )

    if (
        service is not None
        and athlete_profile_id is not None
    ):
        result = service.sync_incremental(
            athlete_profile_id,
            initial_days=args.initial_days,
            lookback_days=args.lookback_days,
        )

        _print_result(
            result
        )

        return 0

    if (
        service is not None
        or athlete_profile_id is not None
    ):
        raise RuntimeError(
            "service et athlete_profile_id doivent "
            "être fournis ensemble."
        )

    with SessionLocal() as session:
        resolved_profile_id = (
            get_local_athlete_profile_id(
                session
            )
        )

        resolved_service = build_service(
            session
        )

        result = (
            resolved_service.sync_incremental(
                resolved_profile_id,
                initial_days=args.initial_days,
                lookback_days=args.lookback_days,
            )
        )

    _print_result(
        result
    )

    return 0


def _print_result(
    result,
) -> None:
    print(
        "Intervals.icu — synchronisation réussie"
    )

    print(
        f"{result.synced_activities} "
        f"activité(s) synchronisée(s)"
    )

    print(
        f"{result.synced_wellness_days} "
        f"jour(s) Wellness synchronisé(s)"
    )

    print(
        f"Période : "
        f"{result.oldest.isoformat()} "
        f"→ {result.newest.isoformat()}"
    )

    print(
        f"Synchronisé à : "
        f"{result.synced_at.isoformat()}"
    )


if __name__ == "__main__":
    try:
        raise SystemExit(
            main()
        )

    except Exception as exc:
        print(
            f"[ERREUR] {exc}",
            file=sys.stderr,
        )

        raise SystemExit(1)
