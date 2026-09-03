"""Synchronisation incrémentale Intervals.icu en ligne de commande."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from opencoach.database.models import (
    AthleteProfile,
    IntegrationConnection,
    User,
)
from opencoach.database.repositories import (
    SqlActivityDetailRepository,
    SqlActivityRepository,
    SqlIntegrationConnectionRepository,
    SqlWellnessRepository,
)
from opencoach.database.session import (
    SessionLocal,
)
from opencoach.integrations.intervals import (
    IntervalsClient,
    IntervalsSyncService,
)
from opencoach.security import (
    SecretCipher,
)
from opencoach.services import (
    DEFAULT_INCREMENTAL_LOOKBACK_DAYS,
    DEFAULT_SYNC_DAYS,
    IntegrationConnectionService,
    IntervalsApplicationService,
)
from opencoach.services.push_notification import (
    PushNotificationService,
)
from opencoach.services.system_notification_state import (
    SystemNotificationState,
)


PROVIDER = "intervals"


@dataclass(
    frozen=True,
    slots=True,
)
class IntervalsSyncTarget:
    """Profil éligible à la synchronisation automatique."""

    user_id: UUID
    athlete_profile_id: UUID


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
    value = int(
        raw_value
    )

    if value <= 0:
        raise argparse.ArgumentTypeError(
            "la valeur doit être strictement positive"
        )

    return value


def _non_negative_integer(
    raw_value: str,
) -> int:
    value = int(
        raw_value
    )

    if value < 0:
        raise argparse.ArgumentTypeError(
            "la valeur ne peut pas être négative"
        )

    return value


def list_intervals_sync_targets(
    session: Session,
) -> list[IntervalsSyncTarget]:
    """Liste les profils ayant une intégration Intervals active.

    Seuls les utilisateurs actifs disposant :
    - d'un profil athlète ;
    - d'une connexion Intervals activée ;
    - d'un secret configuré ;

    sont sélectionnés.
    """

    statement = (
        select(
            User.id,
            AthleteProfile.id,
        )
        .join(
            AthleteProfile,
            AthleteProfile.user_id
            == User.id,
        )
        .join(
            IntegrationConnection,
            IntegrationConnection.athlete_profile_id
            == AthleteProfile.id,
        )
        .where(
            User.active.is_(True),
            IntegrationConnection.provider
            == PROVIDER,
            IntegrationConnection.enabled.is_(True),
            IntegrationConnection.encrypted_secret
            .is_not(None),
        )
        .order_by(
            User.created_at,
        )
    )

    rows = session.execute(
        statement
    ).all()

    return [
        IntervalsSyncTarget(
            user_id=user_id,
            athlete_profile_id=profile_id,
        )
        for user_id, profile_id
        in rows
    ]


def build_service(
    session: Session,
    athlete_profile_id: UUID,
) -> IntervalsApplicationService:
    """Construit le service de synchronisation pour un profil."""

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

    credentials = (
        connection_service.get_credentials(
            athlete_profile_id,
            PROVIDER,
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
        wellness_repository=(
            SqlWellnessRepository(
                session
            )
        ),
    )

    return IntervalsApplicationService(
        sync_service=sync_service,
        connection_service=connection_service,
    )


def _notification_key(
    user_id: UUID,
) -> str:
    """Clé anti-spam spécifique à un utilisateur."""

    return (
        f"intervals_sync:{user_id}"
    )


def _notify_sync_failure(
    session: Session,
    *,
    user_id: UUID,
) -> None:
    """Notifie uniquement l'utilisateur concerné."""

    notification_state = (
        SystemNotificationState()
    )

    key = _notification_key(
        user_id
    )

    if not notification_state.should_notify(
        key
    ):
        return

    try:
        PushNotificationService(
            session
        ).send_system_sync_error(
            user_id=user_id,
            title=(
                "Synchronisation "
                "Intervals.icu"
            ),
            body=(
                "La synchronisation "
                "automatique a échoué."
            ),
            url="/settings",
        )

        notification_state.mark_failed(
            key
        )

    except Exception as exc:
        print(
            "[AVERTISSEMENT] "
            "Impossible d'envoyer "
            "la notification Push : "
            f"{exc}",
            file=sys.stderr,
        )


def _sync_target(
    session: Session,
    *,
    target: IntervalsSyncTarget,
    initial_days: int,
    lookback_days: int,
) -> bool:
    """Synchronise un profil sans interrompre les autres."""

    try:
        service = build_service(
            session,
            target.athlete_profile_id,
        )

        result = (
            service.sync_incremental(
                target.athlete_profile_id,
                initial_days=initial_days,
                lookback_days=lookback_days,
            )
        )

    except Exception as exc:
        session.rollback()

        print(
            "[ERREUR] Intervals.icu "
            f"profil={target.athlete_profile_id} : "
            f"{exc}",
            file=sys.stderr,
        )

        _notify_sync_failure(
            session,
            user_id=target.user_id,
        )

        return False

    SystemNotificationState().mark_success(
        _notification_key(
            target.user_id
        )
    )

    print()
    print(
        "Profil : "
        f"{target.athlete_profile_id}"
    )

    _print_result(
        result
    )

    return True


def main(
    argv: Sequence[str] | None = None,
    *,
    service: IntervalsApplicationService | None = None,
    athlete_profile_id: UUID | None = None,
) -> int:
    """Exécute une synchronisation incrémentale.

    Le mode injecté ``service + athlete_profile_id`` est conservé
    pour les tests et les usages applicatifs explicites.

    Sans injection, tous les profils Intervals éligibles sont
    synchronisés indépendamment.
    """

    args = (
        build_parser()
        .parse_args(
            argv
        )
    )

    # --------------------------------------------------------
    # Mode injecté : contrat historique conservé.
    # --------------------------------------------------------

    if (
        service is not None
        and athlete_profile_id
        is not None
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
        or athlete_profile_id
        is not None
    ):
        raise RuntimeError(
            "service et athlete_profile_id doivent "
            "être fournis ensemble."
        )

    # --------------------------------------------------------
    # Mode automatique multi-utilisateur.
    # --------------------------------------------------------

    with SessionLocal() as session:
        targets = (
            list_intervals_sync_targets(
                session
            )
        )

        if not targets:
            print(
                "[INFO] Aucun profil actif "
                "avec Intervals.icu configuré."
            )

            return 0

        print(
            "[INFO] "
            f"{len(targets)} profil(s) "
            "Intervals.icu à synchroniser."
        )

        success_count = 0
        failure_count = 0

        for target in targets:
            if _sync_target(
                session,
                target=target,
                initial_days=args.initial_days,
                lookback_days=args.lookback_days,
            ):
                success_count += 1
            else:
                failure_count += 1

    print()
    print(
        "Synchronisations réussies :",
        success_count,
    )

    print(
        "Synchronisations échouées :",
        failure_count,
    )

    if failure_count:
        return 1

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
        "Période : "
        f"{result.oldest.isoformat()} "
        "→ "
        f"{result.newest.isoformat()}"
    )

    print(
        "Synchronisé à : "
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
