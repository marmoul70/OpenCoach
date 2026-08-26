"""Refresh automatique de la semaine courante OpenCoach.

Ce service constitue le point d'entrée applicatif unique pour
recalculer la semaine en cours lorsqu'une donnée importante change :

- course principale ;
- disponibilités ;
- contrainte temporaire ;
- readiness ;
- activité réellement effectuée ;
- événement affectant la trajectoire.

Il ne définit aucune règle sportive. Il orchestre les composants
existants du moteur de planification.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from .context import (
    WeeklyPlanningContextBuilder,
)
from .planning import (
    GeneratePlannedTrainingWeekResult,
    GeneratePlannedTrainingWeekService,
)


def current_week_start(
    reference_date: date,
) -> date:
    """Retourne le lundi de la semaine contenant la date."""

    return (
        reference_date
        - timedelta(
            days=reference_date.weekday()
        )
    )


@dataclass(slots=True)
class CurrentWeekPlanningService:
    """Recalcule et persiste uniquement la semaine en cours."""

    context_builder: WeeklyPlanningContextBuilder

    generation_service: (
        GeneratePlannedTrainingWeekService
    )

    def refresh(
        self,
        *,
        athlete_profile_id: UUID,
        reference_date: date,
        additional_context: tuple[
            str,
            ...,
        ] = (),
    ) -> GeneratePlannedTrainingWeekResult:
        """Reconstruit la semaine actuelle depuis le contexte courant."""

        week_start = current_week_start(
            reference_date
        )

        prepared = (
            self.context_builder.build(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                planning_date=(
                    reference_date
                ),
                trajectory_start_date=(
                    week_start
                ),
            )
        )

        return self.generation_service.execute(
            athlete_profile_id=(
                athlete_profile_id
            ),
            planning_input=(
                prepared.planning_input
            ),
            physiological_reference_date=(
                reference_date
            ),
            reconcile_from_date=(
                reference_date
            ),
            additional_context=(
                additional_context
            ),
        )
