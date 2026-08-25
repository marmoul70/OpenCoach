"""Résolution dynamique de l'objectif actif du coach.

Cette brique détermine la cible sportive pertinente à partir
des courses actuellement planifiées.

Elle ne construit pas elle-même la trajectoire d'entraînement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from uuid import UUID

from opencoach.database.repositories import (
    RaceRepository,
)
from opencoach.models import Race


class CoachingGoalMode(StrEnum):
    """Mode stratégique courant du coach."""

    TARGET_RACE = "target_race"
    GENERAL_DEVELOPMENT = "general_development"


@dataclass(
    frozen=True,
    slots=True,
)
class CoachingGoalResolution:
    """Résultat de résolution de l'objectif actif."""

    mode: CoachingGoalMode

    target_race: Race | None

    planning_date: date

    def __post_init__(self) -> None:
        if (
            self.mode
            is CoachingGoalMode.TARGET_RACE
            and self.target_race is None
        ):
            raise ValueError(
                "Une résolution TARGET_RACE "
                "doit posséder une course cible."
            )

        if (
            self.mode
            is CoachingGoalMode.GENERAL_DEVELOPMENT
            and self.target_race is not None
        ):
            raise ValueError(
                "Le mode GENERAL_DEVELOPMENT "
                "ne doit pas posséder de course cible."
            )

        if (
            self.target_race is not None
            and self.target_race.date
            < self.planning_date
        ):
            raise ValueError(
                "La course cible ne peut pas "
                "précéder la date de planification."
            )

    @property
    def days_until_target(
        self,
    ) -> int | None:
        """Nombre de jours restant avant l'objectif."""

        if self.target_race is None:
            return None

        return (
            self.target_race.date
            - self.planning_date
        ).days

    @property
    def weeks_until_target(
        self,
    ) -> float | None:
        """Nombre de semaines restant avant l'objectif."""

        days = self.days_until_target

        if days is None:
            return None

        return days / 7.0


@dataclass(
    frozen=True,
    slots=True,
)
class CoachingGoalResolver:
    """Sélectionne l'objectif actif à partir des courses."""

    race_repository: RaceRepository

    def resolve(
        self,
        *,
        athlete_profile_id: UUID,
        planning_date: date,
    ) -> CoachingGoalResolution:
        """Résout le prochain objectif principal planifié."""

        upcoming = (
            self.race_repository.list_upcoming_races(
                athlete_profile_id,
                planning_date,
            )
        )

        primary_races = tuple(
            race
            for race in upcoming
            if (
                race.priority == "primary"
                and race.status == "planned"
            )
        )

        if not primary_races:
            return CoachingGoalResolution(
                mode=(
                    CoachingGoalMode.GENERAL_DEVELOPMENT
                ),
                target_race=None,
                planning_date=planning_date,
            )

        target_race = min(
            primary_races,
            key=lambda race: (
                race.date,
                str(race.id or ""),
            ),
        )

        return CoachingGoalResolution(
            mode=CoachingGoalMode.TARGET_RACE,
            target_race=target_race,
            planning_date=planning_date,
        )
