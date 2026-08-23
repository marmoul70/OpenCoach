"""Construction de l'enveloppe hebdomadaire OpenCoach.

Ce module assemble les décisions déterministes déjà calculées :
- phase ;
- charge ;
- récupération ;
- disponibilités ;
- prescription des stimuli ;
- demande quantitative de stimuli ;
- intentions de séance ;
- placement hebdomadaire.

Il ne génère aucune séance concrète.

Le pipeline historique basé directement sur les stimuli n'est plus
utilisé comme source de planification. Une représentation compatible
est toutefois conservée temporairement dans l'enveloppe.
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
from .multi_week_trajectory import (
    TrajectoryWeekType,
)
from .session_intent import (
    SessionIntentImportance,
)
from .session_intent_builder import (
    build_session_intent_plan,
)
from .weekly_load_progression import (
    WeeklyLoadTarget,
)
from .weekly_session_intent_scheduler import (
    WeeklySessionIntentSchedule,
    schedule_session_intents,
)
from .weekly_session_intent_slot import (
    WeeklySessionIntentSlot,
)
from .weekly_stimulus_demand import (
    build_weekly_stimulus_demand,
)
from .weekly_stimulus_slot import (
    FatigueBudget,
    SlotImportance,
    Weekday,
    WeeklyStimulusSlot,
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
        )
    )

    intent_plan = build_session_intent_plan(
        weekly_demand=weekly_demand,
    )

    session_schedule = (
        schedule_session_intents(
            plan=intent_plan,
            available_days=(
                input_data.available_days
            ),
        )
    )

    legacy_slots = (
        _build_legacy_slots(
            session_slots=session_schedule.slots,
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
        target_load=adjusted_loads.target_load,
        load_min=adjusted_loads.load_min,
        load_max=adjusted_loads.load_max,
        available_days=input_data.available_days,
        slots=legacy_slots,
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
    """Déduit le rôle qualitatif de la semaine.

    La suspension de charge domine toutes les autres décisions.
    Ensuite viennent le retour à l'entraînement, la récupération
    et l'affûtage.
    """

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


def _build_legacy_slots(
    *,
    session_slots: tuple[
        WeeklySessionIntentSlot,
        ...
    ],
) -> tuple[
    WeeklyStimulusSlot,
    ...
]:
    """Produit la vue historique compatible de l'enveloppe.

    Le stimulus principal de chaque SessionIntent est utilisé comme
    requirement historique.

    Les stimuli secondaires restent accessibles uniquement via
    ``session_slots`` et constituent désormais la représentation
    métier complète.
    """

    result: list[
        WeeklyStimulusSlot
    ] = []

    for session_slot in session_slots:
        intent = session_slot.intent

        primary_requirement = next(
            requirement
            for requirement
            in intent.source_requirements
            if (
                requirement.stimulus
                is intent.primary_stimulus
            )
        )

        result.append(
            WeeklyStimulusSlot(
                slot_id=session_slot.slot_id,
                day=session_slot.day,
                requirement=primary_requirement,
                importance=_legacy_importance(
                    intent.importance
                ),
                fatigue_budget=(
                    session_slot.fatigue_budget
                ),
                duration_available_minutes=(
                    session_slot.duration_available_minutes
                ),
                preserve_next_key_session=(
                    session_slot.preserve_next_key_session
                ),
                preferred_recovery_before_hours=(
                    session_slot
                    .preferred_recovery_before_hours
                ),
                preferred_recovery_after_hours=(
                    session_slot
                    .preferred_recovery_after_hours
                ),
                notes=session_slot.notes,
            )
        )

    return tuple(
        result
    )


def _legacy_importance(
    importance: SessionIntentImportance,
) -> SlotImportance:
    """Convertit l'importance vers le vieux contrat.

    SlotImportance ne possède pas encore de niveau IMPORTANT.
    On conserve donc temporairement son ancien comportement.
    """

    if (
        importance
        is SessionIntentImportance.KEY
    ):
        return SlotImportance.KEY

    if (
        importance
        is SessionIntentImportance.IMPORTANT
    ):
        return SlotImportance.KEY

    return SlotImportance.SUPPORT


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
            "Les disponibilités ne permettent pas de positionner "
            "toutes les intentions de séance souhaitées."
        )

    if schedule.omitted_intents:
        omitted = ", ".join(
            intent.primary_stimulus.value
            for intent
            in schedule.omitted_intents
        )

        notes.append(
            "Intentions non positionnées : "
            f"{omitted}."
        )

    return tuple(
        notes
    )