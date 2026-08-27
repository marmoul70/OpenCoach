"""Orchestration de l'évaluation hebdomadaire du Coach."""

from __future__ import annotations

from datetime import date
from uuid import UUID

from opencoach.planning.history.metrics import (
    calculate_training_history_metrics,
)
from opencoach.planning.history.service import (
    TrainingHistorySnapshotService,
)
from opencoach.planning.physiology.training_load_baseline import (
    calculate_training_load_baseline,
)
from opencoach.training import (
    WeeklyLoadProjectionService,
)

from .weekly_assessment import (
    CoachWeeklyAssessment,
    build_coach_weekly_assessment,
)


class CoachWeeklyAssessmentService:
    """Construit l'analyse hebdomadaire complète du Coach."""

    def __init__(
        self,
        *,
        weekly_load_projection_service: WeeklyLoadProjectionService,
        training_history_service: TrainingHistorySnapshotService,
    ) -> None:
        self.weekly_load_projection_service = (
            weekly_load_projection_service
        )

        self.training_history_service = (
            training_history_service
        )

    def calculate(
        self,
        athlete_profile_id: UUID,
        reference_date: date,
    ) -> CoachWeeklyAssessment:
        """Évalue la trajectoire de la semaine à la date demandée."""

        projection = (
            self.weekly_load_projection_service.calculate(
                athlete_profile_id,
                reference_date,
            )
        )

        history_snapshot = (
            self.training_history_service.build(
                athlete_profile_id,
                reference_date,
            )
        )

        history_metrics = (
            calculate_training_history_metrics(
                history_snapshot
            )
        )

        baseline = (
            calculate_training_load_baseline(
                history_metrics
            )
        )

        return build_coach_weekly_assessment(
            projection=projection,
            history_window_days=(
                history_metrics.adaptive_window_days
            ),
            history_confidence=(
                baseline.confidence
            ),
        )
