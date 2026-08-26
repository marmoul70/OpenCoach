"""Capacité temporelle des jours d'entraînement.

Ce module adapte les disponibilités détaillées de l'athlète vers
un contrat minimal utilisable par le scheduler hebdomadaire.

La disponibilité reste la source de vérité :
- training_allowed détermine si le jour peut être utilisé ;
- max_duration_minutes limite éventuellement la durée d'une séance.

Une durée ``None`` signifie simplement qu'aucune limite temporelle
n'est connue par le moteur.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.planning.athlete.weekly_availability import (
    WeeklyAvailability,
)
from opencoach.planning.stimulus.training import (
    StimulusLoadCategory,
)
from opencoach.planning.weekly.schedule_types import (
    Weekday,
)


_PYTHON_WEEKDAY_TO_OPENCOACH = {
    0: Weekday.MONDAY,
    1: Weekday.TUESDAY,
    2: Weekday.WEDNESDAY,
    3: Weekday.THURSDAY,
    4: Weekday.FRIDAY,
    5: Weekday.SATURDAY,
    6: Weekday.SUNDAY,
}


@dataclass(frozen=True, slots=True)
class DayScheduleCapacity:
    """Capacité temporelle utilisable pour un jour."""

    day: Weekday

    max_duration_minutes: int | None = None

    blocked_load_categories: frozenset[
        StimulusLoadCategory
    ] = frozenset()

    def __post_init__(self) -> None:
        if (
            self.max_duration_minutes is not None
            and self.max_duration_minutes <= 0
        ):
            raise ValueError(
                "La durée maximale disponible doit être "
                "strictement positive."
            )

    def allows_load_category(
        self,
        category: StimulusLoadCategory,
    ) -> bool:
        """Indique si cette nature de charge est autorisée."""

        return (
            category
            not in self.blocked_load_categories
        )

    def can_fit(
        self,
        *,
        minimum_duration_minutes: int | None,
    ) -> bool:
        """Indique si une intention peut tenir dans ce créneau."""

        if minimum_duration_minutes is None:
            return True

        if self.max_duration_minutes is None:
            return True

        return (
            minimum_duration_minutes
            <= self.max_duration_minutes
        )


def build_day_schedule_capacities(
    *,
    weekly_availability: WeeklyAvailability,
) -> tuple[
    DayScheduleCapacity,
    ...
]:
    """Traduit une WeeklyAvailability en capacités de scheduling.

    Les journées totalement indisponibles sont volontairement exclues.
    """

    result: list[
        DayScheduleCapacity
    ] = []

    for availability in (
        weekly_availability.days
    ):
        if not availability.training_allowed:
            continue

        day = _PYTHON_WEEKDAY_TO_OPENCOACH[
            availability.date.weekday()
        ]

        result.append(
            DayScheduleCapacity(
                day=day,
                max_duration_minutes=(
                    availability.max_duration_minutes
                ),
            )
        )

    return tuple(
        result
    )
