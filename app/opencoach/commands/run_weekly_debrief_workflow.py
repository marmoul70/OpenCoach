"""Exécute le workflow hebdomadaire complet OpenCoach.

Ordre :
1. clôture / débrief ;
2. adaptation et planning N+1 ;
3. synchronisation workout Intervals.icu ;
4. notification Push finale.

Le moteur de débrief reste la source de vérité pour l'éligibilité.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta
from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from opencoach.coaching.weekly_debrief_notification import (
    WeeklyDebriefNotificationService,
    WeeklyDebriefNotificationStatus,
)
from opencoach.commands import run_weekly_debrief
from opencoach.database.models import (
    AthleteProfile,
    User,
)
from opencoach.database.repositories.sql_training_session import (
    SqlTrainingSessionRepository,
)
from opencoach.database.repositories.sql_weekly_debrief import (
    SqlWeeklyDebriefRepository,
)
from opencoach.database.session import SessionLocal
from opencoach.services.push_notification import (
    PushNotificationService,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Exécute le workflow hebdomadaire complet OpenCoach."
        )
    )

    parser.add_argument(
        "--reference-date",
        type=date.fromisoformat,
        default=None,
        help=(
            "Date de référence au format YYYY-MM-DD. "
            "Par défaut : aujourd'hui."
        ),
    )

    return parser


def _active_profiles(database) -> list[AthleteProfile]:
    statement = (
        select(AthleteProfile)
        .join(AthleteProfile.user)
        .where(User.active.is_(True))
        .order_by(AthleteProfile.id.asc())
    )

    return list(database.scalars(statement))


def _resolve_user_id(
    database,
    athlete_profile_id: UUID,
) -> UUID | None:
    profile = database.get(
        AthleteProfile,
        athlete_profile_id,
    )

    if profile is None:
        return None

    return profile.user_id


def _run_notifications(
    *,
    reference_date: date,
) -> int:
    week_start = (
        reference_date
        - timedelta(days=reference_date.weekday())
    )

    sent = 0
    already_sent = 0
    not_ready = 0
    no_debrief = 0
    no_recipient = 0
    failed = 0
    sync_incomplete = 0

    with SessionLocal() as database:
        profiles = _active_profiles(database)

        service = WeeklyDebriefNotificationService(
            debrief_repository=(
                SqlWeeklyDebriefRepository(database)
            ),
            training_session_reader=(
                SqlTrainingSessionRepository(database)
            ),
            push_service=(
                PushNotificationService(database)
            ),
            user_id_resolver=lambda athlete_profile_id: (
                _resolve_user_id(
                    database,
                    athlete_profile_id,
                )
            ),
        )

        for profile in profiles:
            result = service.execute(
                athlete_profile_id=profile.id,
                week_start=week_start,
            )

            if (
                result.status
                is WeeklyDebriefNotificationStatus.SENT
            ):
                sent += 1

            elif (
                result.status
                is WeeklyDebriefNotificationStatus.ALREADY_SENT
            ):
                already_sent += 1

            elif (
                result.status
                is WeeklyDebriefNotificationStatus.NOT_READY
            ):
                not_ready += 1

            elif (
                result.status
                is WeeklyDebriefNotificationStatus.NO_DEBRIEF
            ):
                no_debrief += 1

            elif (
                result.status
                is WeeklyDebriefNotificationStatus.NO_RECIPIENT
            ):
                no_recipient += 1

            else:
                failed += 1
                print(
                    "[ERREUR] Notification profil "
                    f"{profile.id}: {result.error}"
                )

            if result.sync_incomplete:
                sync_incomplete += 1

    print()
    print("=" * 72)
    print(" BILAN NOTIFICATIONS HEBDOMADAIRES")
    print("=" * 72)
    print("Envoyées           :", sent)
    print("Déjà envoyées      :", already_sent)
    print("Planning non prêt  :", not_ready)
    print("Sans débrief       :", no_debrief)
    print("Sans destinataire  :", no_recipient)
    print("Sync incomplète    :", sync_incomplete)
    print("Échecs             :", failed)

    return 1 if failed else 0


def main(
    argv: Sequence[str] | None = None,
    *,
    now: datetime | None = None,
) -> int:
    args = build_parser().parse_args(argv)

    execution_time = (
        now
        if now is not None
        else datetime.now().astimezone()
    )

    reference_date = (
        args.reference_date
        if args.reference_date is not None
        else execution_time.date()
    )

    weekly_rc = run_weekly_debrief.main(
        [
            "--reference-date",
            reference_date.isoformat(),
        ],
        now=execution_time,
    )

    if weekly_rc != 0:
        print(
            "[ERREUR] Le débrief hebdomadaire a échoué ; "
            "notification finale non exécutée."
        )
        return weekly_rc

    return _run_notifications(
        reference_date=reference_date
    )


if __name__ == "__main__":
    raise SystemExit(main())
