"""Construction des entrées du planning hebdomadaire.

Ce module transforme les données consolidées du contexte OpenCoach
en entrée du moteur de trajectoire.

Il ne contient aucune règle de génération de séance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.planning.history.metrics import (
    calculate_training_history_metrics,
)
from opencoach.planning.history.service import (
    TrainingHistorySnapshotService,
)
from opencoach.planning.service import (
    PlanningContextService,
)
from opencoach.planning.trajectory.service import (
    CurrentWeekCoachingInput,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)


class WeeklyPlanningContextError(RuntimeError):
    """Erreur de préparation du contexte hebdomadaire."""


@dataclass(frozen=True, slots=True)
class PreparedWeeklyPlanningContext:
    """Contexte prêt à être transmis au moteur de trajectoire."""

    athlete_profile_id: UUID

    planning_input: CurrentWeekCoachingInput


@dataclass(slots=True)
class WeeklyPlanningContextBuilder:
    """Construit l'entrée complète du moteur hebdomadaire."""

    planning_context_service: PlanningContextService

    history_service: TrainingHistorySnapshotService

    def build(
        self,
        *,
        athlete_profile_id: UUID,
        planning_date: date,
        trajectory_start_date: date,
    ) -> PreparedWeeklyPlanningContext:
        """Prépare toutes les données nécessaires au planning."""

        context = (
            self.planning_context_service.build(
                athlete_profile_id,
                planning_date,
            )
        )

        primary_race = context.primary_race

        if primary_race is None:
            target_race_date = None
            target_distance_km = None
            target_elevation_gain_m = None
        else:
            if primary_race.distance_km is None:
                raise WeeklyPlanningContextError(
                    "La course principale ne possède "
                    "pas de distance."
                )

            target_race_date = primary_race.date
            target_distance_km = (
                primary_race.distance_km
            )
            target_elevation_gain_m = (
                primary_race.elevation_gain_m
                or 0.0
            )

        available_days = self._available_days(
            context.athlete.training.available_days
        )

        if not available_days:
            raise WeeklyPlanningContextError(
                "Aucun jour d'entraînement "
                "n'est disponible dans le profil."
            )

        history_snapshot = (
            self.history_service.build(
                athlete_profile_id,
                planning_date,
            )
        )

        history_metrics = (
            calculate_training_history_metrics(
                history_snapshot
            )
        )

        return PreparedWeeklyPlanningContext(
            athlete_profile_id=(
                athlete_profile_id
            ),
            planning_input=(
                CurrentWeekCoachingInput(
                    trajectory_start_date=(
                        trajectory_start_date
                    ),
                    planning_date=planning_date,
                    target_race_date=(
                        target_race_date
                    ),
                    target_distance_km=(
                        target_distance_km
                    ),
                    target_elevation_gain_m=(
                        target_elevation_gain_m
                    ),
                    history_metrics=(
                        history_metrics
                    ),
                    available_days=(
                        available_days
                    ),
                    target_session_count=(
                        context.athlete.training.weekly_sessions
                    ),
                    reference_weekly_duration_minutes=(
                        history_metrics.last_28_days.duration_minutes
                    ),
                    long_endurance_reference_minutes=(
                        history_metrics.long_endurance_reference_minutes
                    ),
                    fatigue_requires_recovery=(
                        self._fatigue_requires_recovery(
                            context
                        )
                    ),
                    athlete_schedule_constrained=(
                        bool(context.constraints)
                    ),
                )
            ),
        )

    @staticmethod
    def _available_days(
        values: list[int],
    ) -> tuple[Weekday, ...]:
        """Convertit les jours 0..6 du profil vers Weekday."""

        mapping = {
            0: Weekday.MONDAY,
            1: Weekday.TUESDAY,
            2: Weekday.WEDNESDAY,
            3: Weekday.THURSDAY,
            4: Weekday.FRIDAY,
            5: Weekday.SATURDAY,
            6: Weekday.SUNDAY,
        }

        try:
            return tuple(
                mapping[value]
                for value in values
            )

        except KeyError as exc:
            raise WeeklyPlanningContextError(
                "Le profil contient un jour "
                "d'entraînement invalide."
            ) from exc

    @staticmethod
    def _fatigue_requires_recovery(
        context,
    ) -> bool:
        """Détermine si le readiness impose une récupération.

        La décision fine de charge reste dans le moteur de planning.
        Cette méthode ne fait que transmettre l'état disponible.
        """

        readiness = context.readiness

        if readiness is None:
            return False

        return bool(
            getattr(
                readiness,
                "requires_recovery",
                False,
            )
        )
