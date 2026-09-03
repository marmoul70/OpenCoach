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
    build_service,
    get_local_athlete_profile_id,
)
from opencoach.database.models import (
    AthleteProfile,
    User,
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


LOCAL_USER_EMAIL = (
    "local@opencoach.local"
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
) -> None:
    report = (
        PushNotificationService(
            session
        )
        .send_system_sync_error(
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
        profile_id = (
            get_local_athlete_profile_id(
                session
            )
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
                "déjà disponibles."
            )

            return 0

        print(
            "[INFO] Données santé "
            "du jour absentes."
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
                "Suunto / Intervals.icu."
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
                session
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
                "[ERREUR] Collecte santé : "
                f"{exc}"
            )

            if _is_final_check(
                now
            ):
                try:
                    _send_final_failure_notification(
                        session
                    )

                except Exception as push_exc:
                    print(
                        "[ERREUR] Notification : "
                        f"{push_exc}"
                    )

            return 1

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
                "[OK] Données santé "
                "récupérées."
            )

            return 0

        print(
            "[INFO] Les données santé "
            "ne sont pas encore disponibles."
        )

        if _is_final_check(
            now
        ):
            try:
                _send_final_failure_notification(
                    session
                )

            except Exception as exc:
                print(
                    "[ERREUR] Notification : "
                    f"{exc}"
                )

        return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
