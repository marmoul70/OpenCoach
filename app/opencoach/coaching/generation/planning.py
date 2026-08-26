"""Orchestration du planning hebdomadaire complet OpenCoach.

Ce service relie le moteur de trajectoire déterministe à la
génération concrète et à la persistance des séances.

Pipeline :

CurrentWeekCoachingInput
    -> build_current_week_coaching()
    -> WeeklyTrainingEnvelope
    -> génération personnalisée
    -> persistance des TrainingSession

Aucune règle sportive n'est définie ici.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.planning.trajectory.service import (
    CurrentWeekCoachingInput,
    CurrentWeekCoachingResult,
    build_current_week_coaching,
)

from .application import (
    GenerateAndPersistTrainingWeekResult,
    GenerateAndPersistTrainingWeekService,
)


@dataclass(frozen=True, slots=True)
class GeneratePlannedTrainingWeekResult:
    """Résultat complet du planning hebdomadaire."""

    planning: CurrentWeekCoachingResult

    generation: GenerateAndPersistTrainingWeekResult

    @property
    def session_count(
        self,
    ) -> int:
        """Nombre de séances réellement persistées."""

        return (
            self.generation.session_count
        )


@dataclass(slots=True)
class GeneratePlannedTrainingWeekService:
    """Construit, génère et persiste une semaine complète."""

    generation_service: (
        GenerateAndPersistTrainingWeekService
    )

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        planning_input: CurrentWeekCoachingInput,
        physiological_reference_date: date | None = None,
        reconcile_from_date: date | None = None,
        additional_context: tuple[
            str,
            ...,
        ] = (),
    ) -> GeneratePlannedTrainingWeekResult:
        """Exécute le pipeline complet de coaching hebdomadaire."""

        planning = (
            build_current_week_coaching(
                input_data=planning_input,
            )
        )

        generation = (
            self.generation_service
            .execute(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                envelope=(
                    planning.coaching.envelope
                ),
                reference_date=(
                    physiological_reference_date
                ),
                reconcile_from_date=(
                    reconcile_from_date
                ),
                additional_context=(
                    additional_context
                ),
            )
        )

        return GeneratePlannedTrainingWeekResult(
            planning=planning,
            generation=generation,
        )
