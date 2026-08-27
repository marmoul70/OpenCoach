"""Service applicatif de génération et persistance hebdomadaire OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.models import (
    TrainingSession,
)
from opencoach.planning.weekly.training_envelope import (
    WeeklyTrainingEnvelope,
)

from .models import (
    GeneratedTrainingWeek,
)
from .orchestrator import (
    AthleteWeeklyTrainingGenerationService,
)
from .persistence import (
    WeeklyTrainingPersistenceService,
)


@dataclass(frozen=True, slots=True)
class GenerateAndPersistTrainingWeekResult:
    """Résultat complet d'une génération hebdomadaire persistée."""

    generated_week: GeneratedTrainingWeek

    persisted_sessions: tuple[
        TrainingSession,
        ...,
    ]

    @property
    def session_count(
        self,
    ) -> int:
        """Nombre de séances persistées."""

        return len(
            self.persisted_sessions
        )


@dataclass(slots=True)
class GenerateAndPersistTrainingWeekService:
    """Orchestre la génération puis la persistance d'une semaine."""

    generation_service: (
        AthleteWeeklyTrainingGenerationService
    )

    persistence_service: (
        WeeklyTrainingPersistenceService
    )

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        envelope: WeeklyTrainingEnvelope,
        reference_date: date | None = None,
        reconcile_from_date: date | None = None,
        additional_context: tuple[
            str,
            ...,
        ] = (),
    ) -> GenerateAndPersistTrainingWeekResult:
        """Génère puis persiste une semaine d'entraînement."""

        generated_week = (
            self.generation_service
            .generate(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                envelope=envelope,
                reference_date=(
                    reference_date
                ),
                additional_context=(
                    additional_context
                ),
            )
        )

        persisted_sessions = (
            self.persistence_service
            .persist(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                week=generated_week,
                envelope=envelope,
                reconcile_from_date=(
                    reconcile_from_date
                ),
            )
        )

        return GenerateAndPersistTrainingWeekResult(
            generated_week=(
                generated_week
            ),
            persisted_sessions=(
                persisted_sessions
            ),
        )
