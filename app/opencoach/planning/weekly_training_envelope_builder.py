"""Construction de l'enveloppe hebdomadaire OpenCoach.

Ce module assemble les décisions déterministes déjà calculées :
- phase ;
- charge ;
- récupération ;
- disponibilités ;
- prescription des stimuli ;
- placement des stimuli.

Il ne génère aucune séance concrète.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from .contextual_stimulus_prescription import (
    ContextualStimulusPrescription,
)
from .load_recovery_cycle import (
    LoadRecoveryDecision,
)
from .weekly_load_progression import (
    WeeklyLoadTarget,
)
from .weekly_stimulus_scheduler import (
    WeeklyStimulusSchedule,
    schedule_weekly_stimuli,
)
from .weekly_stimulus_slot import (
    Weekday,
)
from .weekly_training_envelope import (
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

    athlete_schedule_constrained: bool = False


def build_weekly_training_envelope(
    *,
    input_data: WeeklyTrainingEnvelopeInput,
) -> WeeklyTrainingEnvelope:
    """Construit l'enveloppe hebdomadaire complète."""

    week_end = (
        input_data.week_start
        + timedelta(days=6)
    )

    schedule = schedule_weekly_stimuli(
        requirements=(
            input_data.prescription.requirements
        ),
        available_days=input_data.available_days,
    )

    adjusted_loads = _apply_recovery_factor(
        load_target=input_data.load_target,
        recovery=input_data.recovery,
    )

    schedule_pressure = _classify_schedule_pressure(
        schedule=schedule,
        available_days=input_data.available_days,
    )

    notes = _build_notes(
        schedule=schedule,
        recovery=input_data.recovery,
    )

    return WeeklyTrainingEnvelope(
        week_start=input_data.week_start,
        week_end=week_end,
        phase=input_data.phase,
        target_load=adjusted_loads.target_load,
        load_min=adjusted_loads.load_min,
        load_max=adjusted_loads.load_max,
        available_days=input_data.available_days,
        slots=schedule.slots,
        schedule_pressure=schedule_pressure,
        athlete_schedule_constrained=(
            input_data.athlete_schedule_constrained
            or schedule.constrained
        ),
        notes=notes,
    )


@dataclass(frozen=True, slots=True)
class _AdjustedLoads:
    target_load: float
    load_min: float
    load_max: float


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


def _classify_schedule_pressure(
    *,
    schedule: WeeklyStimulusSchedule,
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
    schedule: WeeklyStimulusSchedule,
    recovery: LoadRecoveryDecision,
) -> tuple[str, ...]:
    notes: list[str] = []

    if recovery.recovery_week:
        notes.append(
            "Semaine de récupération : la charge globale "
            "a été réduite par le moteur."
        )

    if schedule.constrained:
        notes.append(
            "Les disponibilités ne permettent pas de représenter "
            "séparément tous les stimuli souhaités."
        )

    if schedule.omitted_requirements:
        omitted = ", ".join(
            requirement.stimulus.value
            for requirement
            in schedule.omitted_requirements
        )

        notes.append(
            "Stimuli non positionnés explicitement : "
            f"{omitted}."
        )

    return tuple(
        notes
    )
