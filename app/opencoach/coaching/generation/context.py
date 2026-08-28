"""Construction des entrées du planning hebdomadaire.

Ce module transforme les données consolidées du contexte OpenCoach
en entrée du moteur de trajectoire.

Il ne contient aucune règle de génération de séance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.coaching.replanning.goal_resolution import (
    resolve_coaching_goal,
)
from opencoach.coaching.replanning.preparation_horizon import (
    resolve_preparation_horizon,
)

from opencoach.coaching.constraint_impact import (
    evaluate_constraint_return_to_training,
    constraints_require_weekly_recovery,
)

from opencoach.planning.history.metrics import (
    calculate_training_history_metrics,
    resolve_weekly_duration_reference,
)
from opencoach.planning.history.service import (
    TrainingHistorySnapshotService,
)
from opencoach.planning.service import (
    PlanningContextService,
)
from opencoach.planning.return_to_training.clearance import (
    ReadinessAnswer,
    ReturnToTrainingReadiness,
)
from opencoach.planning.trajectory.event import (
    EventImpact,
    TrajectoryEvent,
    TrajectoryEventType,
)
from opencoach.planning.trajectory.service import (
    CurrentWeekCoachingInput,
)
from opencoach.planning.trajectory.race_impact import (
    build_training_race_events,
    build_training_race_protection_dates_for_races,
    build_training_race_recovery_dates_for_races,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)

from opencoach.physiology.testing.models import (
    SportDiscipline,
)


class WeeklyPlanningContextError(RuntimeError):
    """Erreur de préparation du contexte hebdomadaire."""


@dataclass(frozen=True, slots=True)
class PreparedWeeklyPlanningContext:
    """Contexte prêt à être transmis au moteur de trajectoire."""

    athlete_profile_id: UUID

    planning_input: CurrentWeekCoachingInput

    sport_disciplines: tuple[
        SportDiscipline,
        ...,
    ]


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

        goal_resolution = resolve_coaching_goal(
            planning_date=planning_date,
            primary_race=context.primary_race,
        )

        primary_race = (
            goal_resolution.target_race
        )

        effective_trajectory_start_date = (
            trajectory_start_date
        )

        if primary_race is not None:
            preparation_horizon = (
                resolve_preparation_horizon(
                    planning_date=planning_date,
                    target_race_date=(
                        primary_race.date
                    ),
                )
            )

            effective_trajectory_start_date = max(
                trajectory_start_date,
                preparation_horizon
                .preparation_week_start_date,
            )

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

        today = date.today()

        trajectory_history_reference_date = min(
            effective_trajectory_start_date,
            today,
        )

        history_reference_date = min(
            planning_date,
            today,
        )

        trajectory_history_snapshot = (
            self.history_service.build(
                athlete_profile_id,
                trajectory_history_reference_date,
            )
        )

        trajectory_history_metrics = (
            calculate_training_history_metrics(
                trajectory_history_snapshot
            )
        )

        if (
            history_reference_date
            == trajectory_history_reference_date
        ):
            history_snapshot = (
                trajectory_history_snapshot
            )

            history_metrics = (
                trajectory_history_metrics
            )

        else:
            history_snapshot = (
                self.history_service.build(
                    athlete_profile_id,
                    history_reference_date,
                )
            )

            history_metrics = (
                calculate_training_history_metrics(
                    history_snapshot
                )
            )

        training_race_events = (
            build_training_race_events(
                races=(
                    context.training_races
                ),
                history_metrics=(
                    history_metrics
                ),
            )
        )

        reserved_race_dates = tuple(
            race.date
            for race in context.training_races
            if race.status == "planned"
        )

        race_protection_dates = (
            build_training_race_protection_dates_for_races(
                races=(
                    context.training_races
                ),
                history_metrics=(
                    history_metrics
                ),
            )
        )

        race_recovery_dates = (
            build_training_race_recovery_dates_for_races(
                races=(
                    context.training_races
                ),
                history_metrics=(
                    history_metrics
                ),
            )
        )

        constraint_return_events = (
            self._constraint_return_events(
                context
            )
        )

        return PreparedWeeklyPlanningContext(
            athlete_profile_id=(
                athlete_profile_id
            ),
            sport_disciplines=(
                self._sport_disciplines(
                    context.athlete.training.sport_disciplines
                )
            ),
            planning_input=(
                CurrentWeekCoachingInput(
                    trajectory_start_date=(
                        effective_trajectory_start_date
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
                    trajectory_history_metrics=(
                        trajectory_history_metrics
                    ),
                    history_metrics=(
                        history_metrics
                    ),
                    events=(
                        training_race_events
                        + constraint_return_events
                    ),
                    reserved_race_dates=(
                        reserved_race_dates
                    ),
                    race_protection_dates=(
                        race_protection_dates
                    ),
                    race_recovery_dates=(
                        race_recovery_dates
                    ),
                    available_days=(
                        available_days
                    ),
                    target_session_count=(
                        context.athlete.training.weekly_sessions
                    ),
                    reference_weekly_duration_minutes=(
                        resolve_weekly_duration_reference(
                            history_metrics
                        )
                    ),
                    long_endurance_reference_minutes=(
                        history_metrics.long_endurance_reference_minutes
                    ),
                    return_to_training_readiness=(
                        self._return_to_training_readiness(
                            context
                        )
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
    def _sport_disciplines(
        values: list[str],
    ) -> tuple[
        SportDiscipline,
        ...,
    ]:
        """Convertit les préférences profil vers le domaine tests."""

        disciplines: list[
            SportDiscipline
        ] = []

        for value in values:
            try:
                discipline = (
                    SportDiscipline(
                        value
                    )
                )
            except ValueError as exc:
                raise WeeklyPlanningContextError(
                    "Le profil contient une discipline "
                    f"sportive invalide : {value}."
                ) from exc

            if discipline not in disciplines:
                disciplines.append(
                    discipline
                )

        return tuple(
            disciplines
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
    def _constraint_return_events(
        context,
    ) -> tuple[
        TrajectoryEvent,
        ...,
    ]:
        """Convertit les interruptions physiologiques en événements.

        Une maladie ou blessure prolongée récemment terminée est
        transmise au resolver RETURN_TO_TRAINING existant.

        Les contraintes logistiques ne deviennent jamais des
        événements physiologiques.
        """

        planning_date = getattr(
            context,
            "planning_date",
            None,
        )

        if planning_date is None:
            return ()

        events: list[
            TrajectoryEvent
        ] = []

        for constraint in tuple(
            getattr(
                context,
                "constraints",
                (),
            )
        ):
            impact = (
                evaluate_constraint_return_to_training(
                    constraint=constraint,
                    reference_date=planning_date,
                )
            )

            if not impact.requires_return_to_training:
                continue

            if constraint.constraint_type == "illness":
                event_type = (
                    TrajectoryEventType.ILLNESS
                )
            elif constraint.constraint_type == "injury":
                event_type = (
                    TrajectoryEventType.INJURY
                )
            else:
                continue

            event_impact = (
                EventImpact.HIGH
                if impact.disruption_days >= 7
                else EventImpact.MODERATE
            )

            events.append(
                TrajectoryEvent(
                    event_id=(
                        "constraint:"
                        f"{constraint.id}"
                    ),
                    event_type=event_type,
                    start_date=constraint.start_date,
                    end_date=constraint.end_date,
                    impact=event_impact,
                )
            )

        return tuple(
            events
        )

    @staticmethod
    def _return_to_training_readiness(
        context,
    ) -> ReturnToTrainingReadiness:
        """Construit l'état de reprise à partir du Readiness objectif.

        Les données physiologiques peuvent empêcher une reprise lorsque
        la récupération paraît insuffisante.

        Elles ne peuvent jamais confirmer seules que l'athlète est
        suffisamment récupéré ou qu'il ne présente plus de symptômes.
        Ces confirmations restent déclaratives.
        """

        assessment = getattr(
            context,
            "readiness",
            None,
        )

        if assessment is None:
            return ReturnToTrainingReadiness()

        readiness = assessment.readiness

        recovery_insufficient = (
            readiness.level
            in {
                "very_low",
                "low",
            }
            or readiness.critical_count > 0
            or (
                "prefer_recovery_or_rest"
                in readiness.training_constraints
            )
        )

        recovery_sufficient = (
            ReadinessAnswer.NO
            if recovery_insufficient
            else ReadinessAnswer.UNKNOWN
        )

        return ReturnToTrainingReadiness(
            blocking_symptoms=(
                ReadinessAnswer.UNKNOWN
            ),
            recovery_sufficient=(
                recovery_sufficient
            ),
            clearance_confirmed=(
                ReadinessAnswer.UNKNOWN
            ),
        )

    @staticmethod
    def _fatigue_requires_recovery(
        context,
    ) -> bool:
        """Détermine si la fatigue justifie une décharge hebdomadaire.

        La décision s'appuie exclusivement sur le DailyReadiness déjà
        calculé. Elle ne remplace pas l'adaptation quotidienne des
        séances : elle indique seulement au moteur de trajectoire qu'une
        réduction structurelle de la charge hebdomadaire est nécessaire.
        """

        constraints = tuple(
            getattr(
                context,
                "constraints",
                (),
            )
        )

        planning_date = getattr(
            context,
            "planning_date",
            None,
        )

        if (
            constraints
            and planning_date is not None
            and constraints_require_weekly_recovery(
                constraints=constraints,
                reference_date=planning_date,
            )
        ):
            return True

        assessment = context.readiness

        if assessment is None:
            return False

        readiness = assessment.readiness

        if (
            "prefer_recovery_or_rest"
            in readiness.training_constraints
        ):
            return True

        if readiness.critical_count > 0:
            return True

        return readiness.level in {
            "very_low",
            "low",
        }
