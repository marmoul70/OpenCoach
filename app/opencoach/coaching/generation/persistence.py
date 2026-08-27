"""Persistance des semaines générées par le coach OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.database.repositories.training_session import (
    TrainingSessionRepository,
)
from opencoach.database.repositories.weekly_training_plan import (
    WeeklyTrainingPlanRepository,
)
from opencoach.models import (
    WeeklyTrainingPlan,
)
from opencoach.models import (
    TrainingSession,
)

from .mapper import (
    generated_session_to_training_session,
)
from .models import (
    GeneratedTrainingWeek,
)
from .identity import (
    build_planning_key,
)

class WeeklyTrainingPersistenceError(
    RuntimeError
):
    """Erreur métier de persistance d'une semaine générée."""


class ExistingTrainingSessionConflictError(
    WeeklyTrainingPersistenceError
):
    """Une séance existante ne peut pas être remplacée automatiquement."""


@dataclass(slots=True)
class WeeklyTrainingPersistenceService:
    """Persiste une semaine générée sans créer de doublons."""

    repository: TrainingSessionRepository
    weekly_plan_repository: WeeklyTrainingPlanRepository

    def persist(
        self,
        *,
        athlete_profile_id: UUID,
        week: GeneratedTrainingWeek,
        envelope,
        reconcile_from_date: date | None = None,
    ) -> tuple[
        TrainingSession,
        ...,
    ]:
        """Crée ou actualise les séances planifiées de la semaine."""

        self.weekly_plan_repository.save_plan(
            WeeklyTrainingPlan(
                id=None,
                athlete_profile_id=(
                    athlete_profile_id
                ),
                week_start=envelope.week_start,
                week_end=envelope.week_end,
                phase=str(
                    envelope.phase.value
                    if hasattr(
                        envelope.phase,
                        "value",
                    )
                    else envelope.phase
                ),
                phase_week_index=(
                    envelope.phase_week_index
                ),
                target_load=(
                    envelope.target_load
                ),
                load_min=(
                    envelope.load_min
                ),
                load_max=(
                    envelope.load_max
                ),
                reference_duration_minutes=(
                    envelope.reference_duration_minutes
                ),
                target_duration_minutes=(
                    envelope.target_duration_minutes
                ),
                long_endurance_reference_minutes=(
                    envelope.long_endurance_reference_minutes
                ),
                schedule_pressure=str(
                    envelope.schedule_pressure.value
                    if hasattr(
                        envelope.schedule_pressure,
                        "value",
                    )
                    else envelope.schedule_pressure
                ),
                athlete_schedule_constrained=(
                    envelope.athlete_schedule_constrained
                ),
            )
        )

        existing_sessions = (
            self.repository
            .list_sessions_between(
                athlete_profile_id,
                week.week_start,
                week.week_end,
            )
        )

        generated_planning_keys = {
            build_planning_key(
                week_start=week.week_start,
                slot_id=generated.slot_id,
            )
            for generated in week.sessions
        }

        _remove_obsolete_generated_sessions(
            repository=self.repository,
            athlete_profile_id=(
                athlete_profile_id
            ),
            existing_sessions=(
                existing_sessions
            ),
            generated_planning_keys=(
                generated_planning_keys
            ),
            reconcile_from_date=(
                reconcile_from_date
            ),
        )

        persisted: list[
            TrainingSession
        ] = []

        for generated in week.sessions:
            if (
                reconcile_from_date is not None
                and generated.date
                < reconcile_from_date
            ):
                continue

            planning_key = build_planning_key(
                week_start=week.week_start,
                slot_id=generated.slot_id,
            )

            existing = _find_existing_session(
                sessions=existing_sessions,
                planning_key=planning_key,
            )

            if (
                existing is not None
                and reconcile_from_date is not None
                and existing.date
                < reconcile_from_date
            ):
                continue

            if (
                existing is not None
                and existing.status != "planned"
            ):
                raise (
                    ExistingTrainingSessionConflictError(
                        (
                            "Une séance existe déjà le "
                            f"{generated.date.isoformat()} "
                            f"avec le statut "
                            f"'{existing.status}'."
                        )
                    )
                )

            mapped = (
                generated_session_to_training_session(
                    generated,
                    planning_key=planning_key,
                    existing_id=(
                        existing.id
                        if existing is not None
                        else None
                    ),
                )
            )

            saved = (
                self.repository
                .save_session(
                    athlete_profile_id,
                    mapped,
                )
            )

            persisted.append(
                saved
            )

        return tuple(
            persisted
        )


def _find_existing_session(
    *,
    sessions: list[
        TrainingSession
    ],
    planning_key: str,
) -> TrainingSession | None:
    """Recherche une séance générée par son identité stable."""

    matching = [
        session
        for session in sessions
        if (
            session.planning_key
            == planning_key
        )
    ]

    if len(
        matching
    ) > 1:
        raise WeeklyTrainingPersistenceError(
            (
                "Plusieurs séances utilisent la clé "
                f"'{planning_key}'."
            )
        )

    if not matching:
        return None

    return matching[0]

def _remove_obsolete_generated_sessions(
    *,
    repository: TrainingSessionRepository,
    athlete_profile_id: UUID,
    existing_sessions: list[
        TrainingSession
    ],
    generated_planning_keys: set[str],
    reconcile_from_date: date | None = None,
) -> None:
    """Supprime les anciennes séances générées devenues obsolètes.

    Seules les séances encore planifiées, sans activité liée et
    possédant une identité OpenCoach peuvent être supprimées
    automatiquement.

    Les séances manuelles, réalisées ou liées à une activité sont
    toujours conservées.
    """

    for session in existing_sessions:
        if (
            reconcile_from_date is not None
            and session.date
            < reconcile_from_date
        ):
            continue

        if session.planning_key is None:
            continue

        if session.status != "planned":
            continue

        if session.activity_id is not None:
            continue

        if (
            session.planning_key
            in generated_planning_keys
        ):
            continue

        if session.id is None:
            raise WeeklyTrainingPersistenceError(
                "Une séance existante sans identifiant "
                "ne peut pas être réconciliée."
            )

        repository.delete_session(
            athlete_profile_id,
            session.id,
        )
