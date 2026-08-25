"""Construction de l'enveloppe hebdomadaire OpenCoach.

Ce module assemble les décisions déterministes déjà calculées :
- phase ;
- charge ;
- récupération ;
- disponibilités ;
- capacité temporelle ;
- prescription des stimuli ;
- demande quantitative de stimuli ;
- intentions de séance ;
- placement hebdomadaire.

Il ne génère aucune séance concrète.

Le pipeline repose exclusivement sur les intentions de séance.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.planning.stimulus.contextual_prescription import (
    ContextualStimulusPrescription,
)
from opencoach.planning.trajectory.load_recovery_cycle import (
    LoadRecoveryDecision,
)
from opencoach.planning.trajectory.multi_week import (
    TrajectoryWeekType,
)
from opencoach.planning.sessions.intent_builder import (
    build_session_intent_plan,
    complete_session_intent_frequency,
)
from opencoach.planning.weekly.load_progression import (
    WeeklyLoadTarget,
)
from opencoach.planning.weekly.schedule_capacity import (
    DayScheduleCapacity,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)
from opencoach.planning.weekly.session_intent_scheduler import (
    WeeklySessionIntentSchedule,
    schedule_session_intents,
)
from opencoach.planning.stimulus.weekly_demand import (
    build_weekly_stimulus_demand,
)
from opencoach.planning.weekly.training_envelope import (
    SchedulePressure,
    TrainingPhase,
    WeeklyTrainingEnvelope,
)


@dataclass(frozen=True, slots=True)
class WeeklyTrainingEnvelopeInput:
    """Données nécessaires à la construction d'une enveloppe."""

    week_start: date

    phase: TrainingPhase

    load_target: WeeklyLoadTarget

    recovery: LoadRecoveryDecision

    prescription: ContextualStimulusPrescription

    available_days: tuple[
        Weekday,
        ...
    ]

    phase_week_index: int = 1

    target_session_count: int | None = None

    reference_weekly_duration_minutes: float | None = None

    target_weekly_duration_minutes: float | None = None

    long_endurance_reference_minutes: float | None = None

    day_capacities: tuple[
        DayScheduleCapacity,
        ...
    ] = ()

    athlete_schedule_constrained: bool = False


@dataclass(frozen=True, slots=True)
class _AdjustedLoads:
    """Charges finales transmises à l'enveloppe."""

    target_load: float
    load_min: float
    load_max: float


def build_weekly_training_envelope(
    *,
    input_data: WeeklyTrainingEnvelopeInput,
) -> WeeklyTrainingEnvelope:
    """Construit l'enveloppe hebdomadaire complète."""

    week_end = (
        input_data.week_start
        + timedelta(days=6)
    )

    adjusted_loads = _apply_recovery_factor(
        load_target=input_data.load_target,
        recovery=input_data.recovery,
    )

    week_type = _resolve_week_type(
        phase=input_data.phase,
        recovery=input_data.recovery,
        target_load=adjusted_loads.target_load,
    )

    weekly_demand = (
        build_weekly_stimulus_demand(
            prescription=input_data.prescription,
            week_type=week_type,
            target_load=adjusted_loads.target_load,
            reference_load=(
                input_data.load_target.theoretical_load
            ),
            phase_week_index=(
                input_data.phase_week_index
            ),
        )
    )

    intent_plan = build_session_intent_plan(
        weekly_demand=weekly_demand,
    )

    effective_target_session_count = (
        min(
            input_data.target_session_count,
            len(
                set(
                    input_data.available_days
                )
            ),
        )
        if input_data.target_session_count
        is not None
        else None
    )

    if (
        adjusted_loads.target_load > 0
        and effective_target_session_count
        is not None
    ):
        intent_plan = (
            complete_session_intent_frequency(
                plan=intent_plan,
                target_session_count=(
                    effective_target_session_count
                ),
            )
        )

    session_schedule = (
        schedule_session_intents(
            plan=intent_plan,
            available_days=(
                input_data.available_days
            ),
            day_capacities=(
                input_data.day_capacities
            ),
        )
    )

    schedule_pressure = (
        _classify_schedule_pressure(
            schedule=session_schedule,
            available_days=(
                input_data.available_days
            ),
        )
    )

    notes = _build_notes(
        schedule=session_schedule,
        recovery=input_data.recovery,
    )

    return WeeklyTrainingEnvelope(
        week_start=input_data.week_start,
        week_end=week_end,
        phase=input_data.phase,
        phase_week_index=(
            input_data.phase_week_index
        ),
        target_load=adjusted_loads.target_load,
        reference_duration_minutes=(
            input_data.reference_weekly_duration_minutes
        ),
        target_duration_minutes=(
            input_data.target_weekly_duration_minutes
            if input_data.target_weekly_duration_minutes
            is not None
            else _resolve_target_duration_minutes(
                reference_duration_minutes=(
                    input_data.reference_weekly_duration_minutes
                ),
                recovery=input_data.recovery,
                target_load=(
                    adjusted_loads.target_load
                ),
            )
        ),
        long_endurance_reference_minutes=(
            input_data.long_endurance_reference_minutes
        ),
        load_min=adjusted_loads.load_min,
        load_max=adjusted_loads.load_max,
        available_days=input_data.available_days,
        session_slots=session_schedule.slots,
        schedule_pressure=schedule_pressure,
        athlete_schedule_constrained=(
            input_data.athlete_schedule_constrained
            or session_schedule.constrained
        ),
        notes=notes,
    )


def _apply_recovery_factor(
    *,
    load_target: WeeklyLoadTarget,
    recovery: LoadRecoveryDecision,
) -> _AdjustedLoads:
    factor = recovery.load_factor

    return _AdjustedLoads(
        target_load=(
            load_target.target_load
            * factor
        ),
        load_min=(
            load_target.load_min
            * factor
        ),
        load_max=(
            load_target.load_max
            * factor
        ),
    )


def _resolve_week_type(
    *,
    phase: TrainingPhase,
    recovery: LoadRecoveryDecision,
    target_load: float,
) -> TrajectoryWeekType:
    """Déduit le rôle qualitatif de la semaine."""

    if target_load == 0:
        return (
            TrajectoryWeekType.SUSPENDED
        )

    if (
        phase
        is TrainingPhase.RETURN_TO_TRAINING
    ):
        return (
            TrajectoryWeekType.RETURN_TO_TRAINING
        )

    if recovery.recovery_week:
        return (
            TrajectoryWeekType.RECOVERY
        )

    if phase is TrainingPhase.TAPER:
        return TrajectoryWeekType.TAPER

    return TrajectoryWeekType.LOADING


def _classify_schedule_pressure(
    *,
    schedule: WeeklySessionIntentSchedule,
    available_days: tuple[
        Weekday,
        ...
    ],
) -> SchedulePressure:
    unique_available_days = len(
        set(available_days)
    )

    if schedule.constrained:
        return SchedulePressure.HIGH

    if unique_available_days <= 2:
        return SchedulePressure.HIGH

    if unique_available_days <= 4:
        return SchedulePressure.MODERATE

    return SchedulePressure.LOW


def _build_notes(
    *,
    schedule: WeeklySessionIntentSchedule,
    recovery: LoadRecoveryDecision,
) -> tuple[
    str,
    ...
]:
    notes: list[
        str
    ] = []

    if recovery.recovery_week:
        notes.append(
            "Semaine de récupération : la charge globale "
            "et la densité qualitative ont été réduites "
            "par le moteur."
        )

    if schedule.constrained:
        notes.append(
            "Les disponibilités ou capacités temporelles "
            "ne permettent pas de positionner toutes les "
            "intentions de séance souhaitées."
        )

    if schedule.omitted_intents:
        required_omitted = tuple(
            intent
            for intent in schedule.omitted_intents
            if intent.required
        )

        optional_omitted = tuple(
            intent
            for intent in schedule.omitted_intents
            if not intent.required
        )

        if required_omitted:
            omitted = ", ".join(
                intent.primary_stimulus.value
                for intent in required_omitted
            )

            notes.append(
                "Intentions obligatoires non positionnées : "
                f"{omitted}."
            )

        if optional_omitted:
            omitted = ", ".join(
                intent.primary_stimulus.value
                for intent in optional_omitted
            )

            notes.append(
                "Intentions optionnelles non positionnées : "
                f"{omitted}."
            )

    return tuple(
        notes
    )

def _resolve_target_duration_minutes(
    *,
    reference_duration_minutes: float | None,
    recovery: LoadRecoveryDecision,
    target_load: float,
) -> float | None:
    """Calcule le budget temporel hebdomadaire.

    La fréquence est conservée ; une récupération planifiée réduit
    principalement le volume total et la densité qualitative.

    Les règles propres au taper seront affinées séparément.
    """

    if reference_duration_minutes is None:
        return None

    if target_load <= 0:
        return None

    factor = (
        recovery.load_factor
        if recovery.recovery_week
        else 1.0
    )

    return round(
        reference_duration_minutes
        * factor,
        1,
    )
