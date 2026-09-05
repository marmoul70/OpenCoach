"""Commande de clôture et adaptation hebdomadaire OpenCoach."""

from __future__ import annotations

import argparse
from datetime import date, datetime
from typing import Protocol, Sequence

from opencoach.api.coaching.dependencies import (
    build_weekly_debrief_application_service,
)
from opencoach.coaching.weekly_debrief_orchestrator import (
    WeeklyDebriefOrchestrationBatch,
)
from opencoach.database.session import (
    SessionLocal,
)


class WeeklyDebriefApplication(
    Protocol,
):
    """Contrat minimal requis par la commande."""

    def execute(
        self,
        *,
        reference_date: date,
        now: datetime,
    ) -> WeeklyDebriefOrchestrationBatch:
        """Exécute la clôture hebdomadaire."""


def _parse_date(
    raw_value: str,
) -> date:
    """Convertit une date CLI ISO-8601."""

    try:
        return date.fromisoformat(
            raw_value
        )

    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Date invalide. "
            "Format attendu : YYYY-MM-DD."
        ) from exc


def build_parser() -> argparse.ArgumentParser:
    """Construit le parseur de la commande."""

    parser = argparse.ArgumentParser(
        description=(
            "Clôture les semaines éligibles "
            "et applique leur adaptation au "
            "planning suivant."
        )
    )

    parser.add_argument(
        "--reference-date",
        type=_parse_date,
        default=None,
        help=(
            "Date de référence au format "
            "YYYY-MM-DD. Par défaut : aujourd'hui."
        ),
    )

    return parser


def execute_application(
    application_service: WeeklyDebriefApplication,
    *,
    reference_date: date,
    now: datetime,
) -> int:
    """Exécute le pipeline et affiche son bilan."""

    batch = application_service.execute(
        reference_date=reference_date,
        now=now,
    )

    print()
    print("=" * 72)
    print(" BILAN DÉBRIEF HEBDOMADAIRE")
    print("=" * 72)

    print(
        "Clôturés          :",
        batch.completed,
    )
    print(
        "Déjà clôturés     :",
        batch.already_completed,
    )
    print(
        "En attente        :",
        batch.waiting,
    )
    print(
        "Sans débrief      :",
        batch.no_debrief,
    )
    print(
        "Échecs            :",
        batch.failed,
    )

    if batch.failed:
        print()
        print(
            "[ERREUR] Débrief hebdomadaire "
            "terminé avec "
            f"{batch.failed} échec(s)."
        )

        return 1

    print()
    print(
        "[OK] Débrief hebdomadaire terminé."
    )

    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    application_service: (
        WeeklyDebriefApplication | None
    ) = None,
    now: datetime | None = None,
) -> int:
    """Point d'entrée CLI."""

    args = (
        build_parser()
        .parse_args(argv)
    )

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

    print(
        "[INFO] Date de référence : "
        f"{reference_date.isoformat()}."
    )

    print(
        "[INFO] Heure d'exécution : "
        f"{execution_time.isoformat()}."
    )

    if application_service is not None:
        return execute_application(
            application_service,
            reference_date=(
                reference_date
            ),
            now=execution_time,
        )

    with SessionLocal() as database:
        service = (
            build_weekly_debrief_application_service(
                database
            )
        )

        return execute_application(
            service,
            reference_date=(
                reference_date
            ),
            now=execution_time,
        )


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
