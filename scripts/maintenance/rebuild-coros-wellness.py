#!/usr/bin/env python3
"""Reconstruit wellness_daily depuis les snapshots COROS déjà stockés."""

from __future__ import annotations

import argparse
import json
from datetime import date
from uuid import UUID

from sqlalchemy import select

from opencoach.database.models import AthleteProfile
from opencoach.database.session import SessionLocal
from opencoach.integrations.coros.sync import rebuild_wellness_from_snapshots


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Reconstruit les journées Wellness COROS depuis les snapshots locaux. "
            "La simulation sans écriture est le comportement par défaut."
        )
    )
    parser.add_argument(
        "--start-date",
        required=True,
        type=date.fromisoformat,
        help="Première date métier à reconstruire (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--end-date",
        required=True,
        type=date.fromisoformat,
        help="Dernière date métier à reconstruire (YYYY-MM-DD).",
    )
    parser.add_argument(
        "--profile-id",
        type=UUID,
        help=(
            "UUID du profil athlète. Si absent, le script exige qu'un seul "
            "profil existe dans la base."
        ),
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Applique les créations et compléments. Sans cette option : dry-run.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.start_date > args.end_date:
        raise SystemExit("--start-date doit être antérieure ou égale à --end-date.")

    db = SessionLocal()
    try:
        profile_id = args.profile_id
        if profile_id is None:
            profile_ids = db.scalars(
                select(AthleteProfile.id).order_by(AthleteProfile.id.asc())
            ).all()
            if len(profile_ids) != 1:
                raise SystemExit(
                    "Plusieurs profils ou aucun profil trouvé. "
                    "Relancez avec --profile-id UUID."
                )
            profile_id = profile_ids[0]

        result = rebuild_wellness_from_snapshots(
            db,
            profile_id,
            args.start_date,
            args.end_date,
            dry_run=not args.apply,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        if args.apply:
            print("Reconstruction COROS appliquée.")
        else:
            print("Simulation uniquement : aucune donnée n'a été modifiée.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
