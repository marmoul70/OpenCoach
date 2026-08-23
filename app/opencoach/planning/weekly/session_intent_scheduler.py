"""Placement déterministe des intentions de séance dans une semaine.

Le scheduler reçoit des SessionIntent déjà consolidées et décide
uniquement de leur placement sur les jours disponibles.

Il prend également en compte la capacité temporelle connue de chaque
jour. Une intention n'est jamais placée sur une journée dont la durée
maximale est inférieure à sa durée minimale.

Il ne génère aucun contenu concret de séance.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.sessions.intent import (
    SessionIntent,
    SessionIntentImportance,
)
from opencoach.planning.sessions.intent_builder import (
    SessionIntentPlan,
)
from opencoach.planning.weekly.schedule_capacity import (
    DayScheduleCapacity,
)
from opencoach.planning.weekly.schedule_types import (
    FatigueBudget,
    Weekday,
)
from opencoach.planning.weekly.session_intent_slot import (
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
    day_capacities: tuple[
        DayScheduleCapacity,
        ...
    ] = (),
) -> WeeklySessionIntentSchedule:
    """Place les intentions sur des jours temporellement compatibles."""

    ordered_days = tuple(
        sorted(
            set(available_days),
            key=_WEEKDAY_ORDER.__getitem__,
        )
    )

    capacity_by_day = (
        _build_capacity_map(
            available_days=ordered_days,
            day_capacities=day_capacities,
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

    assignments, omitted = (
        _assign_days(
            intents=ordered_intents,
            available_days=ordered_days,
            capacity_by_day=capacity_by_day,
        )
    )

    slots = tuple(
        _build_slot(
            index=index,
            day=day,
            intent=intent,
            capacity=capacity_by_day[
                day
            ],
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


def _build_capacity_map(
    *,
    available_days: tuple[
        Weekday,
        ...
    ],
    day_capacities: tuple[
        DayScheduleCapacity,
        ...
    ],
) -> dict[
    Weekday,
    DayScheduleCapacity,
]:
    """Construit la capacité effective de chaque jour disponible."""

    provided: dict[
        Weekday,
        DayScheduleCapacity,
    ] = {}

    for capacity in day_capacities:
        if capacity.day in provided:
            raise ValueError(
                "Une seule capacité temporelle peut être définie "
                "par jour."
            )

        provided[
            capacity.day
        ] = capacity

    return {
        day: provided.get(
            day,
            DayScheduleCapacity(
                day=day,
            ),
        )
        for day in available_days
    }


def _intent_sort_key(
    intent: SessionIntent,
) -> tuple[
    int,
    int,
    int,
    str,
]:
    importance_order = {
        SessionIntentImportance.KEY: 0,
        SessionIntentImportance.IMPORTANT: 1,
        SessionIntentImportance.SUPPORT: 2,
    }

    # À importance égale, on place d'abord les intentions difficiles
    # à caser : durée minimale élevée, puis intentions multi-stimuli.
    minimum_duration = (
        intent.duration_min_minutes
        or 0
    )

    return (
        importance_order[
            intent.importance
        ],
        -minimum_duration,
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
    capacity_by_day: dict[
        Weekday,
        DayScheduleCapacity,
    ],
) -> tuple[
    tuple[
        tuple[
            Weekday,
            SessionIntent,
        ],
        ...
    ],
    tuple[
        SessionIntent,
        ...
    ],
]:
    """Répartit les intentions sur les journées compatibles."""

    remaining_days = list(
        available_days
    )

    assignments: list[
        tuple[
            Weekday,
            SessionIntent,
        ]
    ] = []

    omitted: list[
        SessionIntent
    ] = []

    for intent in intents:
        compatible_days = [
            day
            for day in remaining_days
            if capacity_by_day[
                day
            ].can_fit(
                minimum_duration_minutes=(
                    intent.duration_min_minutes
                ),
            )
        ]

        if not compatible_days:
            omitted.append(
                intent
            )
            continue

        day = _choose_day(
            remaining_days=compatible_days,
            assignments=assignments,
            intent=intent,
            capacity_by_day=capacity_by_day,
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

    return (
        tuple(
            assignments
        ),
        tuple(
            omitted
        ),
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
    capacity_by_day: dict[
        Weekday,
        DayScheduleCapacity,
    ],
) -> Weekday:
    """Choisit le meilleur jour compatible.

    Les séances clés restent espacées autant que possible.

    En cas d'égalité, une journée ayant davantage de capacité connue
    est privilégiée pour une intention longue.
    """

    if not assignments:
        return _choose_initial_day(
            remaining_days=remaining_days,
            intent=intent,
            capacity_by_day=capacity_by_day,
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
                    _capacity_score(
                        capacity_by_day[
                            day
                        ]
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
            _capacity_score(
                capacity_by_day[
                    day
                ]
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
    capacity_by_day: dict[
        Weekday,
        DayScheduleCapacity,
    ],
) -> Weekday:
    """Choisit le premier jour compatible.

    Pour une intention ayant une durée minimale connue, on privilégie
    la journée offrant la plus grande capacité.

    Sans contrainte de durée, le comportement historique est conservé :
    premier jour disponible.
    """

    if intent.duration_min_minutes is None:
        return remaining_days[0]

    return max(
        remaining_days,
        key=lambda day: (
            _capacity_score(
                capacity_by_day[
                    day
                ]
            ),
            -_WEEKDAY_ORDER[
                day
            ],
        ),
    )


def _capacity_score(
    capacity: DayScheduleCapacity,
) -> int:
    """Score utilisé uniquement pour départager des jours compatibles."""

    if (
        capacity.max_duration_minutes
        is None
    ):
        # Durée non bornée par les informations actuellement connues.
        return 10_000

    return (
        capacity.max_duration_minutes
    )


def _build_slot(
    *,
    index: int,
    day: Weekday,
    intent: SessionIntent,
    capacity: DayScheduleCapacity,
) -> WeeklySessionIntentSlot:
    """Construit un créneau depuis une intention placée."""

    fatigue_budget = (
        _fatigue_budget(
            intent
        )
    )

    recovery_hours = (
        _recovery_hours(
            intent
        )
    )

    return WeeklySessionIntentSlot(
        slot_id=(
            f"session-{index}-"
            f"{intent.primary_stimulus.value}"
        ),
        day=day,
        intent=intent,
        fatigue_budget=fatigue_budget,
        duration_available_minutes=(
            capacity.max_duration_minutes
        ),
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