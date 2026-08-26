"""Orchestration de la trajectoire hebdomadaire OpenCoach.

Ce module relie la trajectoire multi-semaines et les adaptations
déterministes du moment afin de produire l'enveloppe hebdomadaire.

Toutes les adaptations sont consolidées par un resolver commun :
événements actifs, réconciliation du réel et ajustement explicite.

Le lifecycle de retour à l'entraînement reste sous l'autorité du
ReturnToTrainingResolver.

Il ne génère aucune séance concrète.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.planning.trajectory.coaching_phase_allocation import (
    CoachingPhaseAllocation,
    allocate_coaching_phases,
)
from opencoach.planning.stimulus.contextual_prescription import (
    build_contextual_stimulus_prescription,
)
from opencoach.planning.trajectory.load_recovery_cycle import (
    LoadRecoveryDecision,
    RecoveryTrigger,
    decide_load_recovery,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeek,
    TrajectoryWeekType,
)
from opencoach.planning.knowledge.race_demand_profile import (
    RaceDemandProfile,
    build_race_demand_profile,
)
from opencoach.planning.return_to_training.clearance import (
    ReturnToTrainingReadiness,
)
from opencoach.planning.return_to_training.resolver import (
    ResolvedReturnToTraining,
    resolve_return_to_training,
)
from opencoach.planning.trajectory.adjustment import (
    AdjustmentSeverity,
    LoadAdjustment,
    ProgressionAdjustment,
    TrajectoryAdjustment,
)
from opencoach.planning.trajectory.adjustment_resolver import (
    ResolvedTrajectoryAdjustment,
    resolve_trajectory_adjustments,
)
from opencoach.planning.trajectory.event import (
    TrajectoryEvent,
)
from opencoach.planning.trajectory.event_resolver import (
    resolve_trajectory_events,
)
from opencoach.planning.weekly.load_progression import (
    ADJUSTMENT_FACTORS,
    WeeklyLoadTarget,
    calculate_weekly_load_target,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.training_envelope import (
    TrainingPhase,
    WeeklyTrainingEnvelope,
)
from opencoach.planning.weekly.training_envelope_builder import (
    WeeklyTrainingEnvelopeInput,
    build_weekly_training_envelope,
)


@dataclass(frozen=True, slots=True)
class CoachingTrajectoryInput:
    """Données nécessaires au calcul de la semaine suivante."""

    planning_date: date

    target_race_date: date | None
    target_distance_km: float | None
    target_elevation_gain_m: float | None

    previous_load: float

    loading_weeks_since_recovery: int

    available_days: tuple[
        Weekday,
        ...
    ]

    target_session_count: int | None = None

    reference_weekly_duration_minutes: float | None = None

    long_endurance_reference_minutes: float | None = None

    trajectory_week: TrajectoryWeek | None = None

    events: tuple[
        TrajectoryEvent,
        ...
    ] = ()

    reserved_race_dates: tuple[
        date,
        ...
    ] = ()

    race_protection_dates: tuple[
        date,
        ...
    ] = ()

    race_recovery_dates: tuple[
        date,
        ...
    ] = ()

    additional_adjustments: tuple[
        TrajectoryAdjustment,
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
        target_values = (
            self.target_race_date,
            self.target_distance_km,
            self.target_elevation_gain_m,
        )

        has_target = any(
            value is not None
            for value in target_values
        )

        complete_target = all(
            value is not None
            for value in target_values
        )

        if has_target and not complete_target:
            raise ValueError(
                "Une course cible doit fournir ensemble "
                "date, distance et dénivelé."
            )

        if (
            self.target_session_count is not None
            and self.target_session_count < 1
        ):
            raise ValueError(
                "Le nombre cible de séances "
                "doit être strictement positif."
            )


        if (
            self.reference_weekly_duration_minutes
            is not None
            and self.reference_weekly_duration_minutes <= 0
        ):
            raise ValueError(
                "La durée hebdomadaire de référence "
                "doit être strictement positive."
            )

        if (
            self.long_endurance_reference_minutes
            is not None
            and self.long_endurance_reference_minutes <= 0
        ):
            raise ValueError(
                "La durée de référence de sortie longue "
                "doit être strictement positive."
            )


@dataclass(frozen=True, slots=True)
class CoachingTrajectoryResult:
    """Résultat complet du calcul de trajectoire."""

    phase_allocation: CoachingPhaseAllocation | None

    planned_phase: TrainingPhase
    effective_phase: TrainingPhase

    race_profile: RaceDemandProfile | None

    resolved_adjustment: ResolvedTrajectoryAdjustment

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
        if input_data.target_race_date is None:
            raise ValueError(
                "Une trajectoire hebdomadaire doit être fournie "
                "en mode développement général."
            )

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

    active_events = _active_events_on(
        events=input_data.events,
        planning_date=input_data.planning_date,
    )

    resolved_events = resolve_trajectory_events(
        events=active_events,
    )

    manual_adjustment = _build_manual_adjustment(
        input_data.load_adjustment
    )

    all_adjustments = (
        resolved_events.adjustments
        + input_data.additional_adjustments
        + (manual_adjustment,)
    )

    resolved_adjustment = (
        resolve_trajectory_adjustments(
            adjustments=all_adjustments,
        )
    )

    return_to_training = resolve_return_to_training(
        planning_date=input_data.planning_date,
        events=input_data.events,
        readiness=input_data.return_to_training_readiness,
    )

    additional_requires_return_to_training = any(
        adjustment.requires_return_to_training
        for adjustment in input_data.additional_adjustments
    )

    effective_phase = (
        TrainingPhase.RETURN_TO_TRAINING
        if (
            return_to_training.active
            or additional_requires_return_to_training
        )
        else planned_phase
    )

    race_profile: RaceDemandProfile | None = None

    if input_data.target_distance_km is not None:
        assert (
            input_data.target_elevation_gain_m
            is not None
        )

        race_profile = build_race_demand_profile(
            distance_km=(
                input_data.target_distance_km
            ),
            elevation_gain_m=(
                input_data.target_elevation_gain_m
            ),
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
            adjustment=resolved_adjustment.load,
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
            adjustment=resolved_adjustment.load,
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

    phase_week_index = (
        input_data.trajectory_week.phase_week_index
        if (
            use_trajectory_week
            and input_data.trajectory_week is not None
        )
        else 1
    )

    prescription = build_contextual_stimulus_prescription(
        phase=effective_phase,
        race_profile=race_profile,
        phase_week_index=phase_week_index,
    )

    current_week_start = (
        input_data.planning_date
        - timedelta(
            days=input_data.planning_date.weekday()
        )
    )

    envelope = build_weekly_training_envelope(
        input_data=WeeklyTrainingEnvelopeInput(
            week_start=current_week_start,
            phase=effective_phase,
            load_target=load_target,
            recovery=recovery,
            prescription=prescription,
            available_days=input_data.available_days,
            target_race_date=input_data.target_race_date,
            reserved_race_dates=(
                input_data.reserved_race_dates
            ),
            race_protection_dates=(
                input_data.race_protection_dates
            ),
            race_recovery_dates=(
                input_data.race_recovery_dates
            ),
            phase_week_index=phase_week_index,
            target_session_count=(
                input_data.target_session_count
            ),
            reference_weekly_duration_minutes=(
                input_data.reference_weekly_duration_minutes
            ),
            target_weekly_duration_minutes=(
                input_data.trajectory_week.target_duration_minutes
                if (
                    use_trajectory_week
                    and input_data.trajectory_week is not None
                )
                else None
            ),
            long_endurance_reference_minutes=(
                input_data.long_endurance_reference_minutes
            ),
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
        resolved_adjustment=resolved_adjustment,
        load_target=load_target,
        recovery=recovery,
        envelope=envelope,
        return_to_training=return_to_training,
        trajectory_week=input_data.trajectory_week,
    )


def _active_events_on(
    *,
    events: tuple[
        TrajectoryEvent,
        ...
    ],
    planning_date: date,
) -> tuple[
    TrajectoryEvent,
    ...
]:
    """Retourne uniquement les événements actifs à la date demandée.

    Les événements historiques restent disponibles pour le lifecycle
    de retour à l'entraînement, mais ils ne doivent plus modifier
    directement la charge hebdomadaire une fois terminés.
    """

    return tuple(
        event
        for event in events
        if (
            event.start_date
            <= planning_date
            <= event.end_date
        )
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


def _build_manual_adjustment(
    load_adjustment: LoadAdjustment,
) -> TrajectoryAdjustment:
    """Convertit l'ancien ajustement de charge en décision générique."""

    severity = {
        LoadAdjustment.MAINTAIN: AdjustmentSeverity.MINOR,
        LoadAdjustment.REDUCE_SLIGHTLY: AdjustmentSeverity.MINOR,
        LoadAdjustment.REDUCE: AdjustmentSeverity.MODERATE,
        LoadAdjustment.REDUCE_STRONGLY: AdjustmentSeverity.MAJOR,
        LoadAdjustment.SUSPEND: AdjustmentSeverity.MAJOR,
    }[
        load_adjustment
    ]

    progression = (
        ProgressionAdjustment.PAUSE
        if load_adjustment is LoadAdjustment.SUSPEND
        else ProgressionAdjustment.CONTINUE
    )

    return TrajectoryAdjustment(
        reason="Ajustement hebdomadaire explicite.",
        severity=severity,
        load=load_adjustment,
        progression=progression,
        athlete_override_allowed=True,
    )


def _build_load_target_from_trajectory_week(
    *,
    trajectory_week: TrajectoryWeek,
    adjustment: LoadAdjustment,
) -> WeeklyLoadTarget:
    """Transforme une semaine planifiée en cible hebdomadaire."""

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
