"""Orchestration de la trajectoire hebdomadaire OpenCoach.

Ce module relie la trajectoire multi-semaines et les adaptations
déterministes du jour afin de produire l'enveloppe hebdomadaire.

La trajectoire multi-semaines constitue le plan de référence.
Les événements et l'état réel de l'athlète peuvent ensuite adapter
la semaine courante.

Il ne génère aucune séance concrète.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .coaching_phase_allocation import (
    CoachingPhaseAllocation,
    allocate_coaching_phases,
)
from .contextual_stimulus_prescription import (
    build_contextual_stimulus_prescription,
)
from .load_recovery_cycle import (
    LoadRecoveryDecision,
    RecoveryTrigger,
    decide_load_recovery,
)
from .multi_week_trajectory import (
    TrajectoryWeek,
    TrajectoryWeekType,
)
from .race_demand_profile import (
    RaceDemandProfile,
    build_race_demand_profile,
)
from .return_to_training_clearance import (
    ReturnToTrainingReadiness,
)
from .return_to_training_resolver import (
    ResolvedReturnToTraining,
    resolve_return_to_training,
)
from .trajectory_adjustment import (
    LoadAdjustment,
)
from .trajectory_event import (
    TrajectoryEvent,
)
from .trajectory_event_resolver import (
    resolve_trajectory_events,
)
from .weekly_load_progression import (
    ADJUSTMENT_FACTORS,
    WeeklyLoadTarget,
    calculate_weekly_load_target,
)
from .weekly_stimulus_slot import (
    Weekday,
)
from .weekly_training_envelope import (
    TrainingPhase,
    WeeklyTrainingEnvelope,
)
from .weekly_training_envelope_builder import (
    WeeklyTrainingEnvelopeInput,
    build_weekly_training_envelope,
)


@dataclass(frozen=True, slots=True)
class CoachingTrajectoryInput:
    """Données nécessaires au calcul de la semaine suivante."""

    planning_date: date

    target_race_date: date
    target_distance_km: float
    target_elevation_gain_m: float

    previous_load: float

    loading_weeks_since_recovery: int

    available_days: tuple[
        Weekday,
        ...
    ]

    trajectory_week: TrajectoryWeek | None = None

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


@dataclass(frozen=True, slots=True)
class CoachingTrajectoryResult:
    """Résultat complet du calcul de trajectoire."""

    phase_allocation: CoachingPhaseAllocation | None

    planned_phase: TrainingPhase
    effective_phase: TrainingPhase

    race_profile: RaceDemandProfile

    load_target: WeeklyLoadTarget

    recovery: LoadRecoveryDecision

    envelope: WeeklyTrainingEnvelope

    return_to_training: ResolvedReturnToTraining

    trajectory_week: TrajectoryWeek | None


def build_coaching_trajectory(
    *,
    input_data: CoachingTrajectoryInput,
) -> CoachingTrajectoryResult:
    """Calcule la trajectoire et l'enveloppe hebdomadaire."""

    if input_data.trajectory_week is not None:
        _validate_trajectory_week(
            trajectory_week=input_data.trajectory_week,
            planning_date=input_data.planning_date,
        )

        allocation = None

        planned_phase = (
            input_data.trajectory_week.phase
        )

    else:
        allocation = allocate_coaching_phases(
            planning_date=input_data.planning_date,
            target_race_date=input_data.target_race_date,
        )

        planned_phase = allocation.phase_on(
            input_data.planning_date
        )

        if planned_phase is None:
            raise ValueError(
                "Aucune phase active à la date de planification."
            )

    resolved_events = resolve_trajectory_events(
        events=input_data.events,
    )

    return_to_training = resolve_return_to_training(
        planning_date=input_data.planning_date,
        events=input_data.events,
        readiness=input_data.return_to_training_readiness,
    )

    effective_phase = (
        TrainingPhase.RETURN_TO_TRAINING
        if return_to_training.active
        else planned_phase
    )

    race_profile = build_race_demand_profile(
        distance_km=input_data.target_distance_km,
        elevation_gain_m=input_data.target_elevation_gain_m,
    )

    effective_adjustment = (
        resolved_events.load_adjustment
        if input_data.events
        else input_data.load_adjustment
    )

    use_trajectory_week = (
        input_data.trajectory_week is not None
        and effective_phase is planned_phase
    )

    if use_trajectory_week:
        trajectory_week = input_data.trajectory_week

        assert trajectory_week is not None

        load_target = _build_load_target_from_trajectory_week(
            trajectory_week=trajectory_week,
            adjustment=effective_adjustment,
        )

        recovery = _resolve_trajectory_week_recovery(
            trajectory_week=trajectory_week,
            effective_phase=effective_phase,
            fatigue_requires_recovery=(
                input_data.fatigue_requires_recovery
            ),
            event_requires_recovery=(
                input_data.event_requires_recovery
                or resolved_events.event_requires_recovery
            ),
            phase_transition_requires_recovery=(
                input_data.phase_transition_requires_recovery
            ),
        )

    else:
        load_target = calculate_weekly_load_target(
            previous_load=input_data.previous_load,
            phase=effective_phase,
            adjustment=effective_adjustment,
        )

        recovery = decide_load_recovery(
            phase=effective_phase,
            loading_weeks_since_recovery=(
                input_data.loading_weeks_since_recovery
            ),
            fatigue_requires_recovery=(
                input_data.fatigue_requires_recovery
            ),
            event_requires_recovery=(
                input_data.event_requires_recovery
                or resolved_events.event_requires_recovery
            ),
            phase_transition_requires_recovery=(
                input_data.phase_transition_requires_recovery
            ),
        )

    prescription = build_contextual_stimulus_prescription(
        phase=effective_phase,
        race_profile=race_profile,
    )

    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=input_data.planning_date,
            phase=effective_phase,
            load_target=load_target,
            recovery=recovery,
            prescription=prescription,
            available_days=input_data.available_days,
            athlete_schedule_constrained=(
                input_data.athlete_schedule_constrained
                or resolved_events.athlete_schedule_constrained
            ),
        )
    )

    return CoachingTrajectoryResult(
        phase_allocation=allocation,
        planned_phase=planned_phase,
        effective_phase=effective_phase,
        race_profile=race_profile,
        load_target=load_target,
        recovery=recovery,
        envelope=envelope,
        return_to_training=return_to_training,
        trajectory_week=input_data.trajectory_week,
    )


def _validate_trajectory_week(
    *,
    trajectory_week: TrajectoryWeek,
    planning_date: date,
) -> None:
    """Vérifie que la semaine fournie couvre la date demandée."""

    if not (
        trajectory_week.week_start
        <= planning_date
        <= trajectory_week.week_end
    ):
        raise ValueError(
            "La semaine de trajectoire ne couvre pas "
            "la date de planification."
        )


def _build_load_target_from_trajectory_week(
    *,
    trajectory_week: TrajectoryWeek,
    adjustment: LoadAdjustment,
) -> WeeklyLoadTarget:
    """Transforme une semaine planifiée en cible hebdomadaire.

    La progression et les récupérations planifiées sont déjà intégrées
    dans TrajectoryWeek.target_load.

    Seul un ajustement hebdomadaire supplémentaire est appliqué ici.
    """

    factor = ADJUSTMENT_FACTORS[
        adjustment
    ]

    target_load = (
        trajectory_week.target_load
        * factor
    )

    load_min = (
        trajectory_week.load_min
        * factor
    )

    load_max = (
        trajectory_week.load_max
        * factor
    )

    return WeeklyLoadTarget(
        previous_load=trajectory_week.previous_load,
        theoretical_load=trajectory_week.target_load,
        target_load=target_load,
        load_min=load_min,
        load_max=load_max,
        phase=trajectory_week.phase,
        adjustment=adjustment,
    )


def _resolve_trajectory_week_recovery(
    *,
    trajectory_week: TrajectoryWeek,
    effective_phase: TrainingPhase,
    fatigue_requires_recovery: bool,
    event_requires_recovery: bool,
    phase_transition_requires_recovery: bool,
) -> LoadRecoveryDecision:
    """Résout la récupération sans appliquer deux fois une décharge."""

    exceptional_recovery = (
        fatigue_requires_recovery
        or event_requires_recovery
        or phase_transition_requires_recovery
    )

    if exceptional_recovery:
        return decide_load_recovery(
            phase=effective_phase,
            loading_weeks_since_recovery=0,
            fatigue_requires_recovery=(
                fatigue_requires_recovery
            ),
            event_requires_recovery=(
                event_requires_recovery
            ),
            phase_transition_requires_recovery=(
                phase_transition_requires_recovery
            ),
        )

    if (
        trajectory_week.week_type
        is TrajectoryWeekType.RECOVERY
    ):
        if (
            trajectory_week.recovery_trigger
            is RecoveryTrigger.NONE
        ):
            raise ValueError(
                "Une semaine de récupération planifiée doit "
                "définir un déclencheur."
            )

        return LoadRecoveryDecision(
            recovery_week=True,
            trigger=trajectory_week.recovery_trigger,
            load_factor=1.0,
            loading_weeks_since_recovery=0,
        )

    return LoadRecoveryDecision(
        recovery_week=False,
        trigger=RecoveryTrigger.NONE,
        load_factor=1.0,
        loading_weeks_since_recovery=0,
    )