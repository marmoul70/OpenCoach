"""Projection de charge de la semaine courante."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class WeeklyLoadProjection:
    """Synthèse de charge de la semaine au jour J."""

    week_start: date
    week_end: date
    as_of_date: date

    actual_load_to_date: float
    remaining_planned_load: float
    projected_week_load: float

    target_load: float | None
    load_min: float | None
    load_max: float | None

    projected_gap: float | None
    projected_gap_percent: float | None

    remaining_days: int

    adaptation_opportunity: bool
    adaptation_direction: str | None

    completed_sessions_count: int
    missed_sessions_count: int
    remaining_sessions_count: int

    planned_sessions_count: int
    supplementary_sessions_count: int

    @property
    def has_week_plan(self) -> bool:
        """Indique si OpenCoach possède une prescription cette semaine."""

        return self.planned_sessions_count > 0
