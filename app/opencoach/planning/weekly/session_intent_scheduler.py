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
from opencoach.planning.stimulus.training import (
    TrainingStimulus,
    stimulus_load_category,
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
            constrained=any(
                intent.required
                for intent in ordered_intents
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

    assignments, omitted = (
        _pair_omitted_strength_with_easy_days(
            assignments=assignments,
            omitted=omitted,
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
        constrained=any(
            intent.required
            for intent in omitted
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


def _intent_allows_day(
    *,
    intent: SessionIntent,
    day: Weekday,
) -> bool:
    """Vérifie les contraintes calendaires dures d'une intention.

    `preferred_days` influence uniquement le classement.

    `allowed_days` constitue en revanche une contrainte stricte :
    lorsqu'il est renseigné, l'intention ne peut être placée sur
    aucun autre jour.
    """

    return (
        not intent.allowed_days
        or day.value in intent.allowed_days
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
            if (
                _intent_allows_day(
                    intent=intent,
                    day=day,
                )
                and capacity_by_day[
                    day
                ].can_fit(
                    minimum_duration_minutes=(
                        intent.duration_min_minutes
                    ),
                )
                and capacity_by_day[
                    day
                ].allows_load_category(
                    stimulus_load_category(
                        intent.primary_stimulus
                    )
                )
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

        if not _intent_allows_day(
            intent=intent,
            day=day,
        ):
            raise RuntimeError(
                "Le scheduler a sélectionné un jour interdit "
                f"pour le stimulus {intent.primary_stimulus.value!r}: "
                f"{day.value!r}."
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


def _pair_omitted_strength_with_easy_days(
    *,
    assignments: tuple[
        tuple[
            Weekday,
            SessionIntent,
        ],
        ...
    ],
    omitted: tuple[
        SessionIntent,
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
    """Rattache un renforcement support à une journée d'EF.

    Cette règle constitue une exception volontaire au principe
    général d'une intention par jour.

    Seul un renforcement SUPPORT omis peut partager une journée
    contenant déjà une endurance facile.

    Les séances qualitatives et les sorties longues ne peuvent
    jamais recevoir ce second slot.
    """

    result = list(
        assignments
    )

    still_omitted: list[
        SessionIntent
    ] = []

    for intent in omitted:
        if not _is_support_strength_intent(
            intent
        ):
            still_omitted.append(
                intent
            )
            continue

        candidates = [
            (
                day,
                existing_intent,
            )
            for (
                day,
                existing_intent,
            )
            in result
            if (
                existing_intent.primary_stimulus
                is TrainingStimulus.AEROBIC_EASY
                and _combined_day_can_fit(
                    day=day,
                    assignments=result,
                    additional_intent=intent,
                    capacity=capacity_by_day[
                        day
                    ],
                )
            )
        ]

        if not candidates:
            still_omitted.append(
                intent
            )
            continue

        day, _ = min(
            candidates,
            key=lambda candidate: (
                _intent_minimum_duration(
                    candidate[1]
                ),
                _WEEKDAY_ORDER[
                    candidate[0]
                ],
            ),
        )

        result.append(
            (
                day,
                intent,
            )
        )

    result.sort(
        key=lambda assignment: (
            _WEEKDAY_ORDER[
                assignment[0]
            ],
            _same_day_order(
                assignment[1]
            ),
        )
    )

    return (
        tuple(result),
        tuple(still_omitted),
    )


def _is_support_strength_intent(
    intent: SessionIntent,
) -> bool:
    """Indique si une intention est un renforcement léger associable."""

    return (
        intent.importance
        is SessionIntentImportance.SUPPORT
        and intent.primary_stimulus
        in {
            TrainingStimulus.STRENGTH_LOWER_BODY,
            TrainingStimulus.STRENGTH_CORE,
        }
    )


def _combined_day_can_fit(
    *,
    day: Weekday,
    assignments: list[
        tuple[
            Weekday,
            SessionIntent,
        ]
    ],
    additional_intent: SessionIntent,
    capacity: DayScheduleCapacity,
) -> bool:
    """Vérifie la capacité minimale cumulée d'une journée."""

    if (
        capacity.max_duration_minutes
        is None
    ):
        return True

    current_minimum = sum(
        _intent_minimum_duration(
            existing_intent
        )
        for (
            existing_day,
            existing_intent,
        )
        in assignments
        if existing_day is day
    )

    return (
        current_minimum
        + _intent_minimum_duration(
            additional_intent
        )
        <= capacity.max_duration_minutes
    )


def _intent_minimum_duration(
    intent: SessionIntent,
) -> int:
    """Durée minimale connue d'une intention."""

    return (
        intent.duration_min_minutes
        or 0
    )


def _same_day_order(
    intent: SessionIntent,
) -> int:
    """Place la course avant le renforcement le même jour."""

    if (
        intent.primary_stimulus
        in {
            TrainingStimulus.STRENGTH_LOWER_BODY,
            TrainingStimulus.STRENGTH_CORE,
        }
    ):
        return 1

    return 0


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
                    _intent_day_preference_score(
                        intent=intent,
                        day=day,
                    ),
                    _weekend_preference_score(
                        intent=intent,
                        day=day,
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
            _intent_day_preference_score(
                intent=intent,
                day=day,
            ),
            _weekend_preference_score(
                intent=intent,
                day=day,
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

    if (
        intent.primary_stimulus
        is TrainingStimulus.LONG_ENDURANCE
    ):
        weekend_days = [
            day
            for day in remaining_days
            if day in {
                Weekday.SATURDAY,
                Weekday.SUNDAY,
            }
        ]

        if weekend_days:
            return max(
                weekend_days,
                key=_WEEKDAY_ORDER.__getitem__,
            )

    if intent.duration_min_minutes is None:
        return remaining_days[0]

    return max(
        remaining_days,
        key=lambda day: (
            _intent_day_preference_score(
                intent=intent,
                day=day,
            ),
            _weekend_preference_score(
                intent=intent,
                day=day,
            ),
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


def _intent_day_preference_score(
    *,
    intent: SessionIntent,
    day: Weekday,
) -> int:
    """Score de préférence explicite d'une intention pour un jour."""

    if not intent.preferred_days:
        return 0

    try:
        index = intent.preferred_days.index(
            day.value
        )
    except ValueError:
        return 0

    return (
        len(intent.preferred_days)
        - index
    )


def _weekend_preference_score(
    *,
    intent: SessionIntent,
    day: Weekday,
) -> int:
    """Privilégie le week-end pour une sortie longue.

    Cette préférence ne remplace jamais les contraintes
    de disponibilité, de capacité ou d'espacement.
    """

    if (
        intent.primary_stimulus
        is not TrainingStimulus.LONG_ENDURANCE
    ):
        return 0

    if day in {
        Weekday.SATURDAY,
        Weekday.SUNDAY,
    }:
        return 1

    return 0


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