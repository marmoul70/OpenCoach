"""Décision d'entrée dans une préparation orientée course."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.planning.trajectory.coaching_phase_allocation import (
    calculate_preparation_start_date,
)


@dataclass(frozen=True, slots=True)
class PreparationHorizonDecision:
    """Position d'une date de planification par rapport à la préparation."""

    target_race_date: date
    preparation_start_date: date
    planning_date: date

    @property
    def preparation_week_start_date(
        self,
    ) -> date:
        """Retourne le premier lundi de préparation hebdomadaire."""

        days_until_monday = (
            7
            - self.preparation_start_date.weekday()
        ) % 7

        return (
            self.preparation_start_date
            + timedelta(
                days=days_until_monday,
            )
        )

    @property
    def preparation_started(self) -> bool:
        return (
            self.planning_date
            >= self.preparation_start_date
        )


def resolve_preparation_horizon(
    *,
    planning_date: date,
    target_race_date: date,
) -> PreparationHorizonDecision:
    """Détermine si la préparation orientée course doit avoir commencé."""

    if target_race_date <= planning_date:
        raise ValueError(
            "La course cible doit être postérieure "
            "à la date de planification."
        )

    preparation_start_date = (
        calculate_preparation_start_date(
            target_race_date=target_race_date,
        )
    )

    return PreparationHorizonDecision(
        target_race_date=target_race_date,
        preparation_start_date=(
            preparation_start_date
        ),
        planning_date=planning_date,
    )
