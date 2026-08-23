"""Placement déterministe des intentions de séance dans une semaine.

Ce scheduler reçoit des SessionIntent déjà consolidées et décide
uniquement de leur placement sur les jours disponibles.

Il ne génère aucun contenu concret de séance.
"""

from __future__ import annotations

from dataclasses import dataclass

from .session_intent import (
    SessionIntent,
    SessionIntentImportance,
)
from .session_intent_builder import (
    SessionIntentPlan,
)
from .weekly_schedule_types import (
    FatigueBudget,
    Weekday,
)
from .weekly_session_intent_slot import (
    WeeklySessionIntentSlot,
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
class WeeklySessionIntentSchedule:
    """Résultat du placement des intentions de séance."""

    slots: tuple[
        WeeklySessionIntentSlot,
        ...
    ]

    available_days: tuple[
        Weekday,
        ...
    ]

    constrained: bool

    omitted_intents: tuple[
        SessionIntent,
        ...
    ] = ()

    @property
    def session_count(
        self,
    ) -> int:
        return len(
            self.slots
        )


def schedule_session_intents(
    *,
    plan: SessionIntentPlan,
    available_days: tuple[
        Weekday,
        ...
    ],
) -> WeeklySessionIntentSchedule:
    """Place les intentions les plus importantes sur la semaine."""

    ordered_days = tuple(
        sorted(
            set(available_days),
            key=_WEEKDAY_ORDER.__getitem__,
        )
    )

    ordered_intents = tuple(
        sorted(
            plan.intents,
            key=_intent_sort_key,
        )
    )

    if not ordered_days:
        return WeeklySessionIntentSchedule(
            slots=(),
            available_days=(),
            constrained=bool(
                ordered_intents
            ),
            omitted_intents=(
                ordered_intents
            ),
        )

    selected = ordered_intents[
        : len(ordered_days)
    ]

    omitted = ordered_intents[
        len(ordered_days) :
    ]

    assignments = _assign_days(
        intents=selected,
        available_days=ordered_days,
    )

    slots = tuple(
        _build_slot(
            index=index,
            day=day,
            intent=intent,
        )
        for index, (
            day,
            intent,
        )
        in enumerate(
            assignments,
            start=1,
        )
    )

    return WeeklySessionIntentSchedule(
        slots=slots,
        available_days=ordered_days,
        constrained=bool(
            omitted
        ),
        omitted_intents=(
            omitted
        ),
    )


def _intent_sort_key(
    intent: SessionIntent,
) -> tuple[
    int,
    int,
    str,
]:
    importance_order = {
        SessionIntentImportance.KEY: 0,
        SessionIntentImportance.IMPORTANT: 1,
        SessionIntentImportance.SUPPORT: 2,
    }

    return (
        importance_order[
            intent.importance
        ],
        -len(
            intent.stimuli
        ),
        intent.primary_stimulus.value,
    )


def _assign_days(
    *,
    intents: tuple[
        SessionIntent,
        ...
    ],
    available_days: tuple[
        Weekday,
        ...
    ],
) -> tuple[
    tuple[
        Weekday,
        SessionIntent,
    ],
    ...
]:
    """Répartit les intentions sur toute la fenêtre disponible."""

    if not intents:
        return ()

    remaining_days = list(
        available_days
    )

    assignments: list[
        tuple[
            Weekday,
            SessionIntent,
        ]
    ] = []

    for intent in intents:
        day = _choose_day(
            remaining_days=remaining_days,
            assignments=assignments,
            intent=intent,
        )

        assignments.append(
            (
                day,
                intent,
            )
        )

        remaining_days.remove(
            day
        )

    assignments.sort(
        key=lambda assignment: (
            _WEEKDAY_ORDER[
                assignment[0]
            ]
        )
    )

    return tuple(
        assignments
    )


def _choose_day(
    *,
    remaining_days: list[
        Weekday
    ],
    assignments: list[
        tuple[
            Weekday,
            SessionIntent,
        ]
    ],
    intent: SessionIntent,
) -> Weekday:
    """Choisit un jour en privilégiant l'espacement des séances clés."""

    if not assignments:
        return _choose_initial_day(
            remaining_days=remaining_days,
            intent=intent,
        )

    if (
        intent.importance
        is SessionIntentImportance.KEY
    ):
        used_key_indexes = tuple(
            _WEEKDAY_ORDER[day]
            for day, existing_intent
            in assignments
            if (
                existing_intent.importance
                is SessionIntentImportance.KEY
            )
        )

        if used_key_indexes:
            return max(
                remaining_days,
                key=lambda day: (
                    min(
                        abs(
                            _WEEKDAY_ORDER[day]
                            - used_index
                        )
                        for used_index
                        in used_key_indexes
                    ),
                    _WEEKDAY_ORDER[day],
                ),
            )

    used_indexes = tuple(
        _WEEKDAY_ORDER[day]
        for day, _ in assignments
    )

    return max(
        remaining_days,
        key=lambda day: (
            min(
                abs(
                    _WEEKDAY_ORDER[day]
                    - used_index
                )
                for used_index
                in used_indexes
            ),
            _WEEKDAY_ORDER[day],
        ),
    )


def _choose_initial_day(
    *,
    remaining_days: list[
        Weekday
    ],
    intent: SessionIntent,
) -> Weekday:
    """Choisit le premier jour disponible."""

    return remaining_days[0]


def _build_slot(
    *,
    index: int,
    day: Weekday,
    intent: SessionIntent,
) -> WeeklySessionIntentSlot:
    """Construit un créneau depuis une intention."""

    fatigue_budget = _fatigue_budget(
        intent
    )

    recovery_hours = _recovery_hours(
        intent
    )

    return WeeklySessionIntentSlot(
        slot_id=(
            f"session-{index}-"
            f"{intent.primary_stimulus.value}"
        ),
        day=day,
        intent=intent,
        fatigue_budget=fatigue_budget,
        preserve_next_key_session=(
            intent.importance
            is SessionIntentImportance.SUPPORT
        ),
        preferred_recovery_before_hours=(
            recovery_hours
        ),
        preferred_recovery_after_hours=(
            recovery_hours
        ),
    )


def _fatigue_budget(
    intent: SessionIntent,
) -> FatigueBudget:
    if (
        intent.importance
        is SessionIntentImportance.KEY
    ):
        return FatigueBudget.HIGH

    if (
        intent.importance
        is SessionIntentImportance.IMPORTANT
    ):
        return FatigueBudget.MODERATE

    return FatigueBudget.LOW


def _recovery_hours(
    intent: SessionIntent,
) -> int:
    if (
        intent.importance
        is SessionIntentImportance.KEY
    ):
        return 36

    return 24