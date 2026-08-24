"""Orchestration complète de la génération hebdomadaire OpenCoach.

Ce service constitue la façade métier de génération d'une semaine.

Il :
- récupère le profil athlète ;
- consolide les mesures physiologiques ;
- construit le snapshot physiologique courant ;
- transmet ce contexte au moteur hebdomadaire ;
- retourne une semaine de séances concrètes.

Il ne décide pas de la trajectoire ou du placement des séances :
ces responsabilités restent dans ``planning``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.database.repositories.profile import (
    ProfileRepository,
)
from opencoach.planning.physiology.snapshot_service import (
    PhysiologicalCalibrationSnapshotService,
)
from opencoach.planning.weekly.training_envelope import (
    WeeklyTrainingEnvelope,
)

from .models import (
    GeneratedTrainingWeek,
)
from .service import (
    WeeklyTrainingGenerationService,
)


@dataclass(slots=True)
class AthleteWeeklyTrainingGenerationService:
    """Génère une semaine personnalisée pour un athlète."""

    profile_repository: ProfileRepository

    physiology_service: (
        PhysiologicalCalibrationSnapshotService
    )

    generation_service: (
        WeeklyTrainingGenerationService
    )

    def generate(
        self,
        *,
        athlete_profile_id: UUID,
        envelope: WeeklyTrainingEnvelope,
        reference_date: date | None = None,
        additional_context: tuple[
            str,
            ...,
        ] = (),
    ) -> GeneratedTrainingWeek:
        """Génère une semaine avec la physiologie réelle de l'athlète."""

        athlete = (
            self.profile_repository
            .get_profile()
        )

        physiological_reference_date = (
            reference_date
            if reference_date is not None
            else envelope.week_start
        )

        physiology = (
            self.physiology_service
            .build(
                athlete_profile_id=(
                    athlete_profile_id
                ),
                athlete=athlete,
                reference_date=(
                    physiological_reference_date
                ),
            )
        )

        return (
            self.generation_service
            .generate(
                envelope=envelope,
                physiology=physiology,
                additional_context=(
                    additional_context
                ),
            )
        )
