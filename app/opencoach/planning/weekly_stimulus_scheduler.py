"""Placement déterministe des stimuli dans une semaine.

Le scheduler transforme des besoins physiologiques en créneaux
hebdomadaires compatibles avec les disponibilités réelles de l'athlète.

Il ne génère aucune séance concrète.

Les préférences de récupération servent à guider le coach IA et à
décrire les compromis. Elles ne rendent pas automatiquement invalide
une organisation imposée par l'athlète.
"""

from __future__ import annotations

from dataclasses import dataclass

from .training_stimulus import (
    StimulusPriority,
    TrainingStimulusRequirement,
)
from .weekly_stimulus_slot import (
    FatigueBudget,
    SlotImportance,
    Weekday,
    WeeklyStimulusSlot,
)


_WEEKDAY_ORDER = {
    Weekday.MONDAY: 0,
    Weekday.TUESDAY: 1,
    Weekday.WEDNESDAY: 2,
    Weekday.THURSDAY: 3,
    Weekday.FRIDAY: 4,
    Weekday.SATURDAY: 5,
    Weekday.SUNDAY: 6,
}


@dataclass(frozen=True, slots=True)
class WeeklyStimulusSchedule:
    """Résultat du placement des stimuli."""

    slots: tuple[WeeklyStimulusSlot, ...]
    available_days: tuple[Weekday, ...]
    constrained: bool
    omitted_requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ] = ()


def schedule_weekly_stimuli(
    *,
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
    available_days: tuple[Weekday, ...],
) -> WeeklyStimulusSchedule:
    """Place les stimuli prioritaires sur les jours disponibles."""

    ordered_days = tuple(
        sorted(
            set(available_days),
            key=_WEEKDAY_ORDER.__getitem__,
        )
    )

    if not ordered_days:
        return WeeklyStimulusSchedule(
            slots=(),
            available_days=(),
            constrained=bool(requirements),
            omitted_requirements=requirements,
        )

    ordered_requirements = tuple(
        sorted(
            requirements,
            key=_requirement_sort_key,
        )
    )

    selected = ordered_requirements[
        : len(ordered_days)
    ]

    omitted = ordered_requirements[
        len(ordered_days) :
    ]

    assignments = _assign_days(
        requirements=selected,
        available_days=ordered_days,
    )

    slots = tuple(
        _build_slot(
            index=index,
            day=day,
            requirement=requirement,
        )
        for index, (day, requirement)
        in enumerate(assignments, start=1)
    )

    return WeeklyStimulusSchedule(
        slots=slots,
        available_days=ordered_days,
        constrained=bool(omitted),
        omitted_requirements=omitted,
    )


def _requirement_sort_key(
    requirement: TrainingStimulusRequirement,
) -> tuple[int, str]:
    priority_order = {
        StimulusPriority.KEY: 0,
        StimulusPriority.IMPORTANT: 1,
        StimulusPriority.SUPPORT: 2,
    }

    return (
        priority_order[requirement.priority],
        requirement.stimulus.value,
    )


def _assign_days(
    *,
    requirements: tuple[
        TrainingStimulusRequirement,
        ...
    ],
    available_days: tuple[Weekday, ...],
) -> tuple[
    tuple[
        Weekday,
        TrainingStimulusRequirement,
    ],
    ...
]:
    """Répartit les besoins sur toute la fenêtre disponible.

    Lorsque plusieurs jours sont disponibles, les besoins les plus
    prioritaires sont répartis autant que possible dans la semaine.
    """

    if not requirements:
        return ()

    remaining_days = list(
        available_days
    )

    assignments: list[
        tuple[
            Weekday,
            TrainingStimulusRequirement,
        ]
    ] = []

    for requirement in requirements:
        day = _choose_day(
            remaining_days=remaining_days,
            assignments=assignments,
        )

        assignments.append(
            (
                day,
                requirement,
            )
        )

        remaining_days.remove(day)

    assignments.sort(
        key=lambda assignment: (
            _WEEKDAY_ORDER[
                assignment[0]
            ]
        )
    )

    return tuple(assignments)


def _choose_day(
    *,
    remaining_days: list[Weekday],
    assignments: list[
        tuple[
            Weekday,
            TrainingStimulusRequirement,
        ]
    ],
) -> Weekday:
    if not assignments:
        return remaining_days[0]

    used_indexes = tuple(
        _WEEKDAY_ORDER[day]
        for day, _ in assignments
    )

    return max(
        remaining_days,
        key=lambda day: min(
            abs(
                _WEEKDAY_ORDER[day]
                - used_index
            )
            for used_index in used_indexes
        ),
    )


def _build_slot(
    *,
    index: int,
    day: Weekday,
    requirement: TrainingStimulusRequirement,
) -> WeeklyStimulusSlot:
    importance = _slot_importance(
        requirement
    )

    fatigue_budget = _fatigue_budget(
        requirement
    )

    recovery_hours = (
        36
        if importance is SlotImportance.KEY
        else 24
        if importance is SlotImportance.SUPPORT
        else None
    )

    return WeeklyStimulusSlot(
        slot_id=(
            f"stimulus-{index}-"
            f"{requirement.stimulus.value}"
        ),
        day=day,
        requirement=requirement,
        importance=importance,
        fatigue_budget=fatigue_budget,
        preserve_next_key_session=(
            importance is SlotImportance.SUPPORT
        ),
        preferred_recovery_before_hours=(
            recovery_hours
        ),
        preferred_recovery_after_hours=(
            recovery_hours
        ),
    )


def _slot_importance(
    requirement: TrainingStimulusRequirement,
) -> SlotImportance:
    if requirement.priority is StimulusPriority.KEY:
        return SlotImportance.KEY

    if requirement.priority is StimulusPriority.IMPORTANT:
        return SlotImportance.KEY

    return SlotImportance.SUPPORT


def _fatigue_budget(
    requirement: TrainingStimulusRequirement,
) -> FatigueBudget:
    if requirement.priority is StimulusPriority.KEY:
        return FatigueBudget.HIGH

    if requirement.priority is StimulusPriority.IMPORTANT:
        return FatigueBudget.MODERATE

    return FatigueBudget.LOW
