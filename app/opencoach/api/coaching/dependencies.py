"""Dépendances FastAPI du moteur de coaching hebdomadaire.

Ce module constitue la composition root de la génération
hebdomadaire.

Il assemble les repositories et services techniques mais ne contient
aucune règle métier d'entraînement.
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from opencoach.database.repositories.sql_daily_checkin import (
    SqlDailyCheckInRepository,
)
from opencoach.database.repositories.sql_daily_adaptation import (
    SqlDailyAdaptationRepository,
)


from opencoach.api.readiness import (
    get_readiness_service,
)
from opencoach.api.training_stats import (
    get_training_stats_service,
)
from opencoach.coaching.generation import (
    AthleteWeeklyTrainingGenerationService,
    CurrentWeekPlanningService,
    GenerateAndPersistTrainingWeekService,
    GeneratePlannedTrainingWeekService,
    WeeklyPlanningContextBuilder,
    WeeklyTrainingGenerationService,
    WeeklyTrainingPersistenceService,
)
from opencoach.database.repositories import (
    SqlActivityRepository,
    SqlAthleteConstraintRepository,
    SqlPhysiologicalMeasurementRepository,
    SqlProfileRepository,
    SqlRaceRepository,
    SqlTrainingSessionRepository,
)
from opencoach.database.session import (
    get_db,
)
from opencoach.planning.history.service import (
    TrainingHistorySnapshotService,
)
from opencoach.planning.physiology.snapshot_service import (
    PhysiologicalCalibrationSnapshotService,
)
from opencoach.planning.service import (
    PlanningContextService,
)
from opencoach.planning.sessions.generators import (
    DeterministicSessionGenerator,
)
from opencoach.readiness import (
    ReadinessService,
)
from opencoach.services import (
    ProfileService,
)
from opencoach.training import (
    DailyTrainingLoadService,
    RecentTrainingLoadService,
    TrainingLoadComparisonService,
    TrainingStatsService,
)


def get_planning_context_service(
    db: Session = Depends(
        get_db
    ),
    readiness_service: ReadinessService = Depends(
        get_readiness_service
    ),
    training_stats_service: TrainingStatsService = Depends(
        get_training_stats_service
    ),
) -> PlanningContextService:
    """Construit le service de contexte consolidé du planning."""

    activity_repository = (
        SqlActivityRepository(
            db
        )
    )

    training_repository = (
        SqlTrainingSessionRepository(
            db
        )
    )

    profile_repository = (
        SqlProfileRepository(
            db
        )
    )

    daily_training_load_service = (
        DailyTrainingLoadService(
            activity_repository,
            training_repository,
        )
    )

    load_comparison_service = (
        TrainingLoadComparisonService(
            training_repository,
            daily_training_load_service,
        )
    )

    recent_load_service = (
        RecentTrainingLoadService(
            load_comparison_service
        )
    )

    return PlanningContextService(
        profile_service=ProfileService(
            profile_repository
        ),
        race_repository=SqlRaceRepository(
            db
        ),
        readiness_service=(
            readiness_service
        ),
        recent_load_service=(
            recent_load_service
        ),
        training_stats_service=(
            training_stats_service
        ),
        constraint_repository=(
            SqlAthleteConstraintRepository(
                db
            )
        ),
    )


def get_training_history_snapshot_service(
    db: Session = Depends(
        get_db
    ),
    training_stats_service: TrainingStatsService = Depends(
        get_training_stats_service
    ),
) -> TrainingHistorySnapshotService:
    """Construit le service d'historique multi-fenêtres."""

    return TrainingHistorySnapshotService(
        training_stats_service=(
            training_stats_service
        ),
        activity_repository=(
            SqlActivityRepository(
                db
            )
        ),
        race_repository=(
            SqlRaceRepository(
                db
            )
        ),
    )


def get_weekly_planning_context_builder(
    planning_context_service: PlanningContextService = Depends(
        get_planning_context_service
    ),
    history_service: TrainingHistorySnapshotService = Depends(
        get_training_history_snapshot_service
    ),
) -> WeeklyPlanningContextBuilder:
    """Construit l'adaptateur vers le moteur hebdomadaire."""

    return WeeklyPlanningContextBuilder(
        planning_context_service=(
            planning_context_service
        ),
        history_service=(
            history_service
        ),
    )


def get_physiological_snapshot_service(
    db: Session = Depends(
        get_db
    ),
) -> PhysiologicalCalibrationSnapshotService:
    """Construit le service de calibration physiologique."""

    return PhysiologicalCalibrationSnapshotService(
        measurement_repository=(
            SqlPhysiologicalMeasurementRepository(
                db
            )
        )
    )


def get_training_session_repository(
    db: Session = Depends(
        get_db
    ),
) -> SqlTrainingSessionRepository:
    """Construit le repository SQL des séances."""

    return SqlTrainingSessionRepository(
        db
    )


def get_weekly_training_generation_service(
) -> WeeklyTrainingGenerationService:
    """Construit le générateur déterministe de semaine."""

    return WeeklyTrainingGenerationService(
        session_generator=(
            DeterministicSessionGenerator()
        )
    )


def get_athlete_weekly_training_generation_service(
    db: Session = Depends(
        get_db
    ),
    physiology_service: PhysiologicalCalibrationSnapshotService = Depends(
        get_physiological_snapshot_service
    ),
    generation_service: WeeklyTrainingGenerationService = Depends(
        get_weekly_training_generation_service
    ),
) -> AthleteWeeklyTrainingGenerationService:
    """Construit la génération personnalisée d'un athlète."""

    return AthleteWeeklyTrainingGenerationService(
        profile_repository=(
            SqlProfileRepository(
                db
            )
        ),
        physiology_service=(
            physiology_service
        ),
        generation_service=(
            generation_service
        ),
    )


def get_weekly_training_persistence_service(
    repository: SqlTrainingSessionRepository = Depends(
        get_training_session_repository
    ),
) -> WeeklyTrainingPersistenceService:
    """Construit la persistance d'une semaine générée."""

    return WeeklyTrainingPersistenceService(
        repository=repository
    )


def get_generate_and_persist_training_week_service(
    generation_service: AthleteWeeklyTrainingGenerationService = Depends(
        get_athlete_weekly_training_generation_service
    ),
    persistence_service: WeeklyTrainingPersistenceService = Depends(
        get_weekly_training_persistence_service
    ),
) -> GenerateAndPersistTrainingWeekService:
    """Construit le use case génération + persistance."""

    return GenerateAndPersistTrainingWeekService(
        generation_service=(
            generation_service
        ),
        persistence_service=(
            persistence_service
        ),
    )


def get_generate_planned_training_week_service(
    generation_service: GenerateAndPersistTrainingWeekService = Depends(
        get_generate_and_persist_training_week_service
    ),
) -> GeneratePlannedTrainingWeekService:
    """Construit le pipeline complet du coach hebdomadaire."""

    return GeneratePlannedTrainingWeekService(
        generation_service=(
            generation_service
        )
    )

def get_current_week_planning_service(
    context_builder: WeeklyPlanningContextBuilder = Depends(
        get_weekly_planning_context_builder
    ),
    generation_service: GeneratePlannedTrainingWeekService = Depends(
        get_generate_planned_training_week_service
    ),
) -> CurrentWeekPlanningService:
    """Construit le service de refresh de la semaine courante."""

    return CurrentWeekPlanningService(
        context_builder=context_builder,
        generation_service=generation_service,
    )


def get_athlete_constraint_planning_service(
    db: Session = Depends(
        get_db
    ),
    current_week_planning_service: CurrentWeekPlanningService = Depends(
        get_current_week_planning_service
    ),
):
    """Construit le use case contraintes athlète + refresh du coach."""

    from opencoach.coaching.constraint_planning import (
        AthleteConstraintPlanningService,
    )

    return AthleteConstraintPlanningService(
        repository=(
            SqlAthleteConstraintRepository(
                db
            )
        ),
        current_week_planning_service=(
            current_week_planning_service
        ),
    )

def get_daily_checkin_repository(
    db: Session = Depends(
        get_db
    ),
) -> SqlDailyCheckInRepository:
    """Construit le repository SQL des check-ins quotidiens."""

    return SqlDailyCheckInRepository(
        db
    )


def get_daily_adaptation_repository(
    db: Session = Depends(
        get_db
    ),
) -> SqlDailyAdaptationRepository:
    """Construit le repository SQL des propositions quotidiennes."""

    return SqlDailyAdaptationRepository(
        db
    )
