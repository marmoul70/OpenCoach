"""Orchestration de la trajectoire hebdomadaire OpenCoach.

Ce module relie les briques déterministes du moteur de progression
pour produire l'enveloppe de la semaine suivante.

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
    decide_load_recovery,
)
from .race_demand_profile import (
    RaceDemandProfile,
    build_race_demand_profile,
)
from .trajectory_adjustment import (
    LoadAdjustment,
)
from .weekly_load_progression import (
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
from .trajectory_event import (
    TrajectoryEvent,
)
from .trajectory_event_resolver import (
    resolve_trajectory_events,
)
from .return_to_training_resolver import (
    ResolvedReturnToTraining,
    resolve_return_to_training,
)
from .return_to_training_clearance import (
    ReturnToTrainingReadiness,
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

    phase_allocation: CoachingPhaseAllocation

    planned_phase: TrainingPhase
    effective_phase: TrainingPhase

    race_profile: RaceDemandProfile

    load_target: WeeklyLoadTarget

    recovery: LoadRecoveryDecision

    envelope: WeeklyTrainingEnvelope

    return_to_training: ResolvedReturnToTraining

def build_coaching_trajectory(
    *,
    input_data: CoachingTrajectoryInput,
) -> CoachingTrajectoryResult:
    """Calcule la trajectoire et l'enveloppe hebdomadaire."""

    allocation = allocate_coaching_phases(
        planning_date=input_data.planning_date,
        target_race_date=input_data.target_race_date,
    )

    current_phase = allocation.phase_on(
        input_data.planning_date
    )

    if current_phase is None:
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
        else current_phase
    )

    race_profile = build_race_demand_profile(
        distance_km=input_data.target_distance_km,
        elevation_gain_m=input_data.target_elevation_gain_m,
    )

    load_target = calculate_weekly_load_target(
        previous_load=input_data.previous_load,
        phase=effective_phase,
        adjustment=(
            resolved_events.load_adjustment
            if input_data.events
            else input_data.load_adjustment
        ),
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
        planned_phase=current_phase,
        effective_phase=effective_phase,
        race_profile=race_profile,
        load_target=load_target,
        recovery=recovery,
        envelope=envelope,
        return_to_training=return_to_training,
    )
