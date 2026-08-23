"""Services d'orchestration de la trajectoire OpenCoach.

Ce module relie :
- l'historique réel de l'athlète ;
- la baseline de charge ;
- la trajectoire multi-semaines ;
- la semaine correspondant à la date de planification ;
- l'adaptation hebdomadaire ;
- l'enveloppe destinée au coach IA.

Il ne génère aucune séance concrète.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .coaching_trajectory import (
    CoachingTrajectoryInput,
    CoachingTrajectoryResult,
    build_coaching_trajectory,
)
from .multi_week_trajectory import (
    MultiWeekTrajectory,
    TrajectoryWeek,
)
from .multi_week_trajectory_builder import (
    build_multi_week_trajectory,
)
from .return_to_training_clearance import (
    ReturnToTrainingReadiness,
)
from .training_history_metrics import (
    TrainingHistoryMetrics,
)
from .training_load_baseline import (
    TrainingLoadBaseline,
    calculate_training_load_baseline,
)
from .trajectory_adjustment import (
    LoadAdjustment,
)
from .trajectory_event import (
    TrajectoryEvent,
)
from .weekly_stimulus_slot import (
    Weekday,
)


@dataclass(frozen=True, slots=True)
class TrainingTrajectoryResult:
    """Résultat de construction de la trajectoire complète."""

    baseline: TrainingLoadBaseline

    trajectory: MultiWeekTrajectory


@dataclass(frozen=True, slots=True)
class CurrentWeekCoachingInput:
    """Entrée nécessaire à la génération du cadre hebdomadaire.

    trajectory_start_date :
        date à laquelle la trajectoire de préparation a réellement
        commencé.

    planning_date :
        date appartenant à la semaine que nous voulons actuellement
        planifier.
    """

    trajectory_start_date: date
    planning_date: date

    target_race_date: date
    target_distance_km: float
    target_elevation_gain_m: float

    history_metrics: TrainingHistoryMetrics

    available_days: tuple[
        Weekday,
        ...
    ]

    events: tuple[
        TrajectoryEvent,
        ...
    ] = ()

    return_to_training_readiness: (
        ReturnToTrainingReadiness | None
    ) = None

    load_adjustment: LoadAdjustment = (
        LoadAdjustment.MAINTAIN
    )

    fatigue_requires_recovery: bool = False
    event_requires_recovery: bool = False
    phase_transition_requires_recovery: bool = False

    athlete_schedule_constrained: bool = False

    def __post_init__(self) -> None:
        if self.planning_date < self.trajectory_start_date:
            raise ValueError(
                "La date de planification ne peut pas précéder "
                "le début de la trajectoire."
            )

        if self.target_race_date <= self.trajectory_start_date:
            raise ValueError(
                "La course cible doit être postérieure "
                "au début de la trajectoire."
            )

        if self.planning_date >= self.target_race_date:
            raise ValueError(
                "La date de planification doit précéder "
                "la course cible."
            )


@dataclass(frozen=True, slots=True)
class CurrentWeekCoachingResult:
    """Résultat complet pour la semaine demandée."""

    baseline: TrainingLoadBaseline

    trajectory: MultiWeekTrajectory

    trajectory_week: TrajectoryWeek

    coaching: CoachingTrajectoryResult


def build_training_trajectory(
    *,
    planning_date: date,
    target_race_date: date,
    history_metrics: TrainingHistoryMetrics,
) -> TrainingTrajectoryResult:
    """Construit une trajectoire depuis l'historique réel.

    Le paramètre planning_date représente ici la date d'ancrage de la
    trajectoire. Cette fonction est conservée pour compatibilité avec
    les appels existants.

    Pour générer une semaine située plus loin dans une trajectoire,
    utiliser build_current_week_coaching().
    """

    baseline = calculate_training_load_baseline(
        history_metrics
    )

    trajectory = build_multi_week_trajectory(
        planning_date=planning_date,
        target_race_date=target_race_date,
        baseline_load=baseline.baseline_load,
    )

    return TrainingTrajectoryResult(
        baseline=baseline,
        trajectory=trajectory,
    )


def build_current_week_coaching(
    *,
    input_data: CurrentWeekCoachingInput,
) -> CurrentWeekCoachingResult:
    """Construit automatiquement le cadre de la semaine demandée."""

    trajectory_result = build_training_trajectory(
        planning_date=input_data.trajectory_start_date,
        target_race_date=input_data.target_race_date,
        history_metrics=input_data.history_metrics,
    )

    trajectory_week = (
        trajectory_result.trajectory.week_on(
            input_data.planning_date
        )
    )

    if trajectory_week is None:
        raise ValueError(
            "Aucune semaine de trajectoire ne couvre "
            "la date de planification."
        )

    coaching = build_coaching_trajectory(
        input_data=CoachingTrajectoryInput(
            planning_date=input_data.planning_date,
            target_race_date=input_data.target_race_date,
            target_distance_km=input_data.target_distance_km,
            target_elevation_gain_m=(
                input_data.target_elevation_gain_m
            ),
            previous_load=trajectory_week.previous_load,
            loading_weeks_since_recovery=0,
            available_days=input_data.available_days,
            trajectory_week=trajectory_week,
            events=input_data.events,
            return_to_training_readiness=(
                input_data.return_to_training_readiness
            ),
            load_adjustment=input_data.load_adjustment,
            fatigue_requires_recovery=(
                input_data.fatigue_requires_recovery
            ),
            event_requires_recovery=(
                input_data.event_requires_recovery
            ),
            phase_transition_requires_recovery=(
                input_data.phase_transition_requires_recovery
            ),
            athlete_schedule_constrained=(
                input_data.athlete_schedule_constrained
            ),
        )
    )

    return CurrentWeekCoachingResult(
        baseline=trajectory_result.baseline,
        trajectory=trajectory_result.trajectory,
        trajectory_week=trajectory_week,
        coaching=coaching,
    )