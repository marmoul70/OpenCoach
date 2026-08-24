"""Génération hebdomadaire des séances OpenCoach."""

from .models import (
    GeneratedTrainingSession,
    GeneratedTrainingWeek,
)
from .orchestrator import (
    AthleteWeeklyTrainingGenerationService,
)
from .service import (
    WeeklyTrainingGenerationError,
    WeeklyTrainingGenerationService,
)
from .mapper import (
    generated_session_to_training_session,
)
from .persistence import (
    ExistingTrainingSessionConflictError,
    WeeklyTrainingPersistenceError,
    WeeklyTrainingPersistenceService,
)
from .application import (
    GenerateAndPersistTrainingWeekResult,
    GenerateAndPersistTrainingWeekService,
)
from .planning import (
    GeneratePlannedTrainingWeekResult,
    GeneratePlannedTrainingWeekService,
)
from .context import (
    PreparedWeeklyPlanningContext,
    WeeklyPlanningContextBuilder,
    WeeklyPlanningContextError,
)

__all__ = [
    "AthleteWeeklyTrainingGenerationService",
    "GeneratedTrainingSession",
    "GeneratedTrainingWeek",
    "WeeklyTrainingGenerationError",
    "WeeklyTrainingGenerationService",
    "ExistingTrainingSessionConflictError",
    "WeeklyTrainingPersistenceError",
    "WeeklyTrainingPersistenceService",
    "generated_session_to_training_session",
    "GenerateAndPersistTrainingWeekResult",
    "GenerateAndPersistTrainingWeekService",
    "GeneratePlannedTrainingWeekResult",
    "GeneratePlannedTrainingWeekService",
    "PreparedWeeklyPlanningContext",
    "WeeklyPlanningContextBuilder",
    "WeeklyPlanningContextError",
]