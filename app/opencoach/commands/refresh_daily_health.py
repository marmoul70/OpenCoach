"""Collecte automatique des données santé du jour."""

from __future__ import annotations

import argparse
import time

from collections.abc import Sequence
from datetime import (
    date,
    datetime,
)

from sqlalchemy import select

from opencoach.commands.sync_intervals import (
    IntervalsSyncTarget,
    build_service,
    list_intervals_sync_targets,
)
from opencoach.database.repositories import (
    SqlIntegrationConnectionRepository,
    SqlWellnessRepository,
)
from opencoach.database.session import (
    SessionLocal,
)
from opencoach.integrations.intervals import (
    IntervalsClient,
)
from opencoach.security import (
    SecretCipher,
)
from opencoach.services import (
    IntegrationConnectionService,
)
from opencoach.services.push_notification import (
    PushNotificationService,
)


PROVIDER = "intervals"

WAIT_SECONDS = 30


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Actualise les données santé "
            "quotidiennes depuis Intervals.icu."
        ),
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Ignore la fenêtre horaire "
            "08:00-10:00."
        ),
    )

    return parser


def _within_refresh_window(
    now: datetime,
) -> bool:
    return (
        8
        <= now.hour
        <= 10
    )


def _is_final_check(
    now: datetime,
) -> bool:
    return now.hour >= 10


def _health_data_available(
    wellness,
) -> bool:
    if wellness is None:
        return False

    values = (
        wellness.hrv,
        wellness.resting_hr,
        wellness.sleep_seconds,
        wellness.sleep_score,
        wellness.avg_sleeping_hr,
        wellness.spo2,
    )

    return any(
        value is not None
        for value in values
    )


def _build_intervals_client(
    session,
    athlete_profile_id,
) -> IntervalsClient:
    repository = (
        SqlIntegrationConnectionRepository(
            session
        )
    )

    connection_service = (
        IntegrationConnectionService(
            repository=repository,
            cipher=SecretCipher.from_env(),
        )
    )

    credentials = (
        connection_service
        .get_credentials(
            athlete_profile_id,
            "intervals",
        )
    )

    return IntervalsClient(
        api_key=credentials.secret,
        athlete_id=credentials.athlete_id,
    )


def _send_final_failure_notification(
    session,
    *,
    user_id,
) -> None:
    report = (
        PushNotificationService(
            session
        )
        .send_system_sync_error(
            user_id=user_id,
            title=(
                "Données santé indisponibles"
            ),
            body=(
                "Un problème est survenu "
                "pour collecter tes données santé. "
                "Lance une synchronisation manuelle."
            ),
            url="/settings",
        )
    )

    print(
        "[INFO] Notification envoyée : "
        f"{report.sent}"
    )


def _refresh_target(
    session,
    *,
    target: IntervalsSyncTarget,
    today: date,
    now: datetime,
) -> bool:
    """Actualise les données santé d'un profil Intervals."""

    profile_id = (
        target.athlete_profile_id
    )

    wellness_repository = (
        SqlWellnessRepository(
            session
        )
    )

    wellness = (
        wellness_repository
        .get_by_date(
            profile_id,
            today,
            provider=PROVIDER,
        )
    )

    if _health_data_available(
        wellness
    ):
        print(
            "[OK] Données santé du jour "
            f"déjà disponibles pour {profile_id}."
        )

        return True

    print(
        "[INFO] Données santé absentes "
        f"pour {profile_id}."
    )

    try:
        client = (
            _build_intervals_client(
                session,
                profile_id,
            )
        )

        print(
            "[INFO] Déclenchement "
            "de la synchronisation "
            "Suunto / Intervals.icu "
            f"pour {profile_id}."
        )

        try:
            client.trigger_partner_sync()

            print(
                "[INFO] Synchronisation partenaire "
                "Intervals.icu déclenchée."
            )

            print(
                "[INFO] Attente de "
                f"{WAIT_SECONDS} secondes."
            )

            time.sleep(
                WAIT_SECONDS
            )

        except Exception as exc:
            print(
                "[AVERTISSEMENT] Synchronisation partenaire "
                "indisponible : "
                f"{exc}"
            )

        service = build_service(
            session,
            profile_id,
        )

        result = (
            service.sync_incremental(
                profile_id,
            )
        )

        print(
            "[INFO] Synchronisation "
            "OpenCoach terminée : "
            f"{result.synced_wellness_days} "
            "jour(s) Wellness."
        )

    except Exception as exc:
        print(
            "[ERREUR] Collecte santé "
            f"pour {profile_id} : {exc}"
        )

        if _is_final_check(
            now
        ):
            try:
                _send_final_failure_notification(
                    session,
                    user_id=target.user_id,
                )

            except Exception as push_exc:
                print(
                    "[ERREUR] Notification : "
                    f"{push_exc}"
                )

        return False

    wellness = (
        wellness_repository
        .get_by_date(
            profile_id,
            today,
            provider=PROVIDER,
        )
    )

    if _health_data_available(
        wellness
    ):
        print(
            "[OK] Données santé récupérées "
            f"pour {profile_id}."
        )

        return True

    print(
        "[INFO] Les données santé "
        "ne sont pas encore disponibles "
        f"pour {profile_id}."
    )

    if _is_final_check(
        now
    ):
        try:
            _send_final_failure_notification(
                session,
                user_id=target.user_id,
            )

        except Exception as exc:
            print(
                "[ERREUR] Notification : "
                f"{exc}"
            )

    return True


def main(
    argv: Sequence[str] | None = None,
) -> int:
    args = (
        build_parser()
        .parse_args(argv)
    )

    now = datetime.now()

    if (
        not args.force
        and not _within_refresh_window(
            now
        )
    ):
        print(
            "[INFO] Hors fenêtre "
            "de collecte 08:00-10:00."
        )

        return 0

    today = date.today()

    with SessionLocal() as session:
        targets = (
            list_intervals_sync_targets(
                session
            )
        )

        if not targets:
            print(
                "[INFO] Aucun profil Intervals.icu "
                "éligible à la collecte santé."
            )

            return 0

        print(
            "[INFO] Profils Intervals.icu "
            f"à traiter : {len(targets)}."
        )

        failures = 0

        for target in targets:
            print(
                "[INFO] Traitement du profil "
                f"{target.athlete_profile_id}."
            )

            if not _refresh_target(
                session,
                target=target,
                today=today,
                now=now,
            ):
                failures += 1

        if failures:
            print(
                "[ERREUR] Collecte santé terminée "
                f"avec {failures} échec(s)."
            )

            return 1

        print(
            "[OK] Collecte santé terminée "
            "pour tous les profils."
        )

        return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
