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

from opencoach.physiology.testing.automatic_proposal import (
    AutomaticPhysiologicalTestProposalRequest,
    AutomaticPhysiologicalTestProposalResult,
    AutomaticPhysiologicalTestProposalService,
)
from opencoach.physiology.testing.models import (
    SportDiscipline,
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

    physiological_test: (
        AutomaticPhysiologicalTestProposalResult
        | None
    ) = None

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

    physiological_test_service: (
        AutomaticPhysiologicalTestProposalService
        | None
    ) = None

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        planning_input: CurrentWeekCoachingInput,
        physiological_reference_date: date | None = None,
        sport_disciplines: tuple[
            SportDiscipline,
            ...,
        ] = (),
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

        physiological_test = None

        if (
            self.physiological_test_service
            is not None
            and sport_disciplines
        ):
            reference_date = (
                physiological_reference_date
                or generation.generated_week.week_start
            )

            physiological_test = (
                self.physiological_test_service
                .evaluate_week(
                    AutomaticPhysiologicalTestProposalRequest(
                        athlete_profile_id=(
                            athlete_profile_id
                        ),
                        reference_date=(
                            reference_date
                        ),
                        week_start=(
                            generation.generated_week.week_start
                        ),
                        week_end=(
                            generation.generated_week.week_end
                        ),
                        phase=(
                            generation.generated_week.phase
                        ),
                        disciplines=(
                            sport_disciplines
                        ),
                    )
                )
            )

        return GeneratePlannedTrainingWeekResult(
            planning=planning,
            generation=generation,
            physiological_test=(
                physiological_test
            ),
        )
