"""Services d'orchestration de la trajectoire OpenCoach.

Ce module relie :
- l'historique réel de l'athlète ;
- la baseline de charge ;
- la trajectoire multi-semaines ;
- la réconciliation prévu / réalisé ;
- l'analyse des dérives multi-semaines ;
- le réancrage éventuel de la trajectoire future ;
- l'adaptation hebdomadaire ;
- l'enveloppe destinée au coach IA.

La trajectoire originale reste disponible pour l'audit.
Un réancrage ne réécrit jamais les semaines passées.

Il ne génère aucune séance concrète.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.planning.trajectory.coaching import (
    CoachingTrajectoryInput,
    CoachingTrajectoryResult,
    build_coaching_trajectory,
)
from opencoach.planning.history.load_reconciliation import (
    ReconciliationTrend,
    analyze_reconciliation_history,
)
from opencoach.planning.trajectory.multi_week import (
    MultiWeekTrajectory,
    TrajectoryWeek,
)
from opencoach.planning.trajectory.multi_week_builder import (
    build_multi_week_trajectory,
)
from opencoach.planning.trajectory.reanchoring import (
    reanchor_multi_week_trajectory,
)
from opencoach.planning.return_to_training.clearance import (
    ReturnToTrainingReadiness,
)
from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
)
from opencoach.planning.physiology.training_load_baseline import (
    TrainingLoadBaseline,
    calculate_training_load_baseline,
)
from opencoach.planning.trajectory.adjustment import (
    LoadAdjustment,
    TrajectoryAdjustment,
)
from opencoach.planning.trajectory.event import (
    TrajectoryEvent,
)
from opencoach.planning.weekly.load_reconciliation import (
    WeeklyLoadReconciliation,
    reconcile_weekly_load,
)
from opencoach.planning.weekly.load_reconciliation_context import (
    ContextualWeeklyLoadReconciliation,
    LoadDeviationCause,
    contextualize_weekly_load_reconciliation,
)
from opencoach.planning.weekly.load_reconciliation_policy import (
    build_reconciliation_adjustment,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)


@dataclass(frozen=True, slots=True)
class TrainingTrajectoryResult:
    """Résultat de construction de la trajectoire complète."""

    baseline: TrainingLoadBaseline

    trajectory: MultiWeekTrajectory


@dataclass(frozen=True, slots=True)
class CurrentWeekCoachingInput:
    """Entrée nécessaire à la génération du cadre hebdomadaire."""

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

    reconciliation_history: tuple[
        ContextualWeeklyLoadReconciliation,
        ...
    ] = ()

    previous_week_actual_load: float | None = None

    previous_week_deviation_cause: (
        LoadDeviationCause | None
    ) = None

    previous_week_athlete_imposed: bool = False

    previous_week_note: str | None = None

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

        if (
            self.previous_week_actual_load is not None
            and self.previous_week_actual_load < 0
        ):
            raise ValueError(
                "La charge réalisée de la semaine précédente "
                "ne peut pas être négative."
            )


@dataclass(frozen=True, slots=True)
class CurrentWeekCoachingResult:
    """Résultat complet pour la semaine demandée."""

    baseline: TrainingLoadBaseline

    original_trajectory: MultiWeekTrajectory

    trajectory: MultiWeekTrajectory

    trajectory_week: TrajectoryWeek

    previous_trajectory_week: TrajectoryWeek | None

    reconciliation: WeeklyLoadReconciliation | None

    reconciliation_context: (
        ContextualWeeklyLoadReconciliation | None
    )

    reconciliation_adjustment: TrajectoryAdjustment | None

    reconciliation_trend: ReconciliationTrend

    coaching: CoachingTrajectoryResult


def build_training_trajectory(
    *,
    planning_date: date,
    target_race_date: date,
    history_metrics: TrainingHistoryMetrics,
) -> TrainingTrajectoryResult:
    """Construit une trajectoire depuis l'historique réel."""

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

    original_trajectory = (
        trajectory_result.trajectory
    )

    original_current_week = (
        original_trajectory.week_on(
            input_data.planning_date
        )
    )

    if original_current_week is None:
        raise ValueError(
            "Aucune semaine de trajectoire ne couvre "
            "la date de planification."
        )

    previous_trajectory_week = (
        original_trajectory.week_on(
            input_data.planning_date
            - timedelta(days=7)
        )
    )

    (
        reconciliation,
        reconciliation_context,
        reconciliation_adjustment,
    ) = _build_previous_week_reconciliation(
        previous_trajectory_week=previous_trajectory_week,
        actual_load=input_data.previous_week_actual_load,
        cause=input_data.previous_week_deviation_cause,
        athlete_imposed=(
            input_data.previous_week_athlete_imposed
        ),
        note=input_data.previous_week_note,
    )

    complete_history = (
        input_data.reconciliation_history
        + (
            ()
            if reconciliation_context is None
            else (
                reconciliation_context,
            )
        )
    )

    reconciliation_trend = (
        analyze_reconciliation_history(
            history=complete_history,
            current_reference_load=(
                original_current_week.progression_reference_before
            ),
        )
    )

    trajectory = original_trajectory

    if reconciliation_trend.reanchoring_applied:
        trajectory = reanchor_multi_week_trajectory(
            trajectory=original_trajectory,
            from_date=original_current_week.week_start,
            new_reference_load=(
                reconciliation_trend.recommended_reference_load
            ),
            previous_load=(
                input_data.previous_week_actual_load
                if input_data.previous_week_actual_load
                is not None
                else original_current_week.previous_load
            ),
        )

    trajectory_week = trajectory.week_on(
        input_data.planning_date
    )

    if trajectory_week is None:
        raise ValueError(
            "Aucune semaine effective ne couvre "
            "la date de planification."
        )

    additional_adjustments = (
        ()
        if reconciliation_adjustment is None
        else (
            reconciliation_adjustment,
        )
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
            additional_adjustments=(
                additional_adjustments
            ),
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
        original_trajectory=original_trajectory,
        trajectory=trajectory,
        trajectory_week=trajectory_week,
        previous_trajectory_week=(
            previous_trajectory_week
        ),
        reconciliation=reconciliation,
        reconciliation_context=(
            reconciliation_context
        ),
        reconciliation_adjustment=(
            reconciliation_adjustment
        ),
        reconciliation_trend=(
            reconciliation_trend
        ),
        coaching=coaching,
    )


def _build_previous_week_reconciliation(
    *,
    previous_trajectory_week: TrajectoryWeek | None,
    actual_load: float | None,
    cause: LoadDeviationCause | None,
    athlete_imposed: bool,
    note: str | None,
) -> tuple[
    WeeklyLoadReconciliation | None,
    ContextualWeeklyLoadReconciliation | None,
    TrajectoryAdjustment | None,
]:
    """Réconcilie la semaine précédente lorsqu'elle est disponible."""

    if (
        previous_trajectory_week is None
        or actual_load is None
    ):
        return (
            None,
            None,
            None,
        )

    reconciliation = reconcile_weekly_load(
        planned_load=previous_trajectory_week.target_load,
        actual_load=actual_load,
    )

    context = contextualize_weekly_load_reconciliation(
        reconciliation=reconciliation,
        cause=cause,
        athlete_imposed=athlete_imposed,
        note=note,
    )

    adjustment = build_reconciliation_adjustment(
        context
    )

    return (
        reconciliation,
        context,
        adjustment,
    )