"""Résolution du contexte de planification post-débrief."""

from __future__ import annotations

from datetime import timedelta
from typing import Protocol
from uuid import UUID

from opencoach.coaching.weekly_debrief_application import (
    WeeklyDebriefPlanningContext,
)
from opencoach.coaching.weekly_debrief_runtime_context import (
    WeeklyDebriefRuntimeFacts,
)


class WeeklyPlanningPreparedContext(
    Protocol,
):
    """Résultat minimal attendu du builder de contexte hebdomadaire."""

    planning_input: object
    sport_disciplines: tuple


class WeeklyPlanningContextBuilderProtocol(
    Protocol,
):
    """Contrat minimal du builder de contexte hebdomadaire."""

    def build(
        self,
        *,
        athlete_profile_id: UUID,
        planning_date,
        trajectory_start_date,
    ) -> WeeklyPlanningPreparedContext:
        """Prépare le contexte nécessaire au moteur hebdomadaire."""


class DefaultWeeklyDebriefPlanningContextResolver:
    """Construit le contexte de la semaine suivant le débrief."""

    def __init__(
        self,
        *,
        context_builder: WeeklyPlanningContextBuilderProtocol,
    ) -> None:
        self._context_builder = context_builder

    def resolve(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date,
        runtime_facts: WeeklyDebriefRuntimeFacts,
    ) -> WeeklyDebriefPlanningContext:
        """Prépare la semaine immédiatement postérieure à la clôture."""

        del reference_date

        next_week_start = (
            runtime_facts.week_end
            + timedelta(days=1)
        )

        prepared = self._context_builder.build(
            athlete_profile_id=athlete_profile_id,
            planning_date=next_week_start,
            trajectory_start_date=next_week_start,
        )

        return WeeklyDebriefPlanningContext(
            planning_input=prepared.planning_input,
            physiological_reference_date=(
                next_week_start
            ),
            sport_disciplines=(
                prepared.sport_disciplines
            ),
            reconcile_from_date=(
                next_week_start
            ),
        )
