"""Génération manuelle du planning d'entraînement OpenCoach.

Cette commande utilise exactement le même pipeline que l'API Coach :
contexte athlète complet, trajectoire, courses, historique, contraintes,
physiologie, disponibilité, génération et persistance.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from typing import Sequence
from uuid import UUID

from sqlalchemy import select

from opencoach.api.coaching.dependencies import (
    build_weekly_planning_services_for_user,
)
from opencoach.database.models import AthleteProfile, User
from opencoach.database.repositories import SqlTrainingSessionRepository
from opencoach.database.session import SessionLocal


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Date invalide : format attendu YYYY-MM-DD."
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Génère manuellement le planning Coach avec le moteur "
            "de production et toutes les données disponibles."
        ),
        epilog=(
            "Exemple : python -m opencoach.commands.generate_training_plan "
            "--username mon_compte --weeks 2"
        ),
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument(
        "--username",
        help="Identifiant OpenCoach du compte à planifier.",
    )
    target.add_argument(
        "--all-active",
        action="store_true",
        help="Traite tous les comptes actifs disposant d'un profil athlète.",
    )
    parser.add_argument(
        "--reference-date",
        type=_parse_date,
        default=None,
        help="Date de référence YYYY-MM-DD (défaut : aujourd'hui).",
    )
    parser.add_argument(
        "--weeks",
        type=int,
        choices=range(1, 9),
        default=2,
        metavar="1..8",
        help="Nombre de semaines à examiner (défaut : 2).",
    )
    parser.add_argument(
        "--include-existing",
        action="store_true",
        help=(
            "Ne pas ignorer une semaine qui contient déjà des séances "
            "planifiées. À utiliser avec prudence : le moteur peut signaler "
            "un conflit si des séances existent déjà."
        ),
    )
    return parser


def _resolve_profiles(database, *, username: str | None, all_active: bool):
    statement = (
        select(AthleteProfile, User)
        .join(User, AthleteProfile.user_id == User.id)
        .where(User.active.is_(True))
        .order_by(User.username.asc())
    )
    if username is not None:
        statement = statement.where(User.username == username.strip().lower())
    rows = list(database.execute(statement).all())
    if not rows:
        target = f"'{username}'" if username else "les comptes actifs"
        raise SystemExit(
            f"Aucun profil athlète actif trouvé pour {target}."
        )
    if username is None and not all_active:
        raise SystemExit("Précise --username ou --all-active.")
    return rows


def _generate_for_profile(
    database,
    *,
    profile: AthleteProfile,
    user: User,
    reference_date: date,
    weeks: int,
    include_existing: bool,
) -> tuple[int, int, int]:
    user_id: UUID = user.id
    profile_id: UUID = profile.id
    context_builder, generation_service = (
        build_weekly_planning_services_for_user(
            db=database,
            user_id=user_id,
        )
    )
    repository = SqlTrainingSessionRepository(database)
    monday = reference_date - timedelta(days=reference_date.weekday())

    generated_total = 0
    skipped_total = 0
    failed_total = 0

    print()
    print(f"Profil : {user.username or user.email} ({profile_id})")
    print(f"Date de référence : {reference_date.isoformat()}")

    for offset in range(weeks):
        week_start = monday + timedelta(days=7 * offset)
        week_end = week_start + timedelta(days=6)
        existing = repository.list_sessions_between(
            profile_id,
            week_start,
            week_end,
        )
        planned = [session for session in existing if session.status == "planned"]

        print()
        print(f"Semaine du {week_start.isoformat()} au {week_end.isoformat()}")
        if planned and not include_existing:
            skipped_total += 1
            print(
                f"[IGNORÉE] {len(planned)} séance(s) déjà planifiée(s). "
                "Utilise --include-existing uniquement si tu sais pourquoi."
            )
            continue

        try:
            prepared = context_builder.build(
                athlete_profile_id=profile_id,
                planning_date=week_start,
                trajectory_start_date=monday,
            )
            result = generation_service.execute(
                athlete_profile_id=profile_id,
                planning_input=prepared.planning_input,
                physiological_reference_date=week_start,
                sport_disciplines=prepared.sport_disciplines,
                reconcile_from_date=(
                    reference_date
                    if offset == 0
                    else week_start
                ),
                additional_context=(
                    "Génération manuelle demandée depuis la ligne de commande "
                    "avec le pipeline de production OpenCoach.",
                ),
            )
            count = result.session_count
            generated_total += count
            generated_week = result.generation.generated_week
            print(
                f"[OK] {count} séance(s) persistée(s) | "
                f"phase : {generated_week.phase.value} | "
                f"charge cible : {generated_week.target_load}"
            )
            for session in result.generation.persisted_sessions:
                print(
                    f"  - {session.date.isoformat()} | "
                    f"{session.title} | {session.duration_minutes} min | "
                    f"{session.status}"
                )
        except Exception as exc:
            database.rollback()
            failed_total += 1
            print(f"[ERREUR] Génération impossible : {exc}")

    print()
    print(
        f"Bilan {user.username or user.email} : "
        f"{generated_total} séance(s) créée(s), "
        f"{skipped_total} semaine(s) ignorée(s), "
        f"{failed_total} échec(s)."
    )
    return generated_total, skipped_total, failed_total


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    reference_date = args.reference_date or date.today()

    generated = 0
    skipped = 0
    failed = 0

    with SessionLocal() as database:
        profiles = _resolve_profiles(
            database,
            username=args.username,
            all_active=args.all_active,
        )
        for profile, user in profiles:
            result = _generate_for_profile(
                database,
                profile=profile,
                user=user,
                reference_date=reference_date,
                weeks=args.weeks,
                include_existing=args.include_existing,
            )
            generated += result[0]
            skipped += result[1]
            failed += result[2]

    print()
    print("=" * 72)
    print("BILAN GÉNÉRATION MANUELLE DU PLANNING")
    print("=" * 72)
    print(f"Séances créées       : {generated}")
    print(f"Semaines ignorées    : {skipped}")
    print(f"Échecs               : {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
