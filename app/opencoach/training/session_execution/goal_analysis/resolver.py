"""Sélection de la stratégie d'analyse selon la séance prévue."""

from __future__ import annotations

from opencoach.models import TrainingSession

from .endurance import build_endurance_goal_plan
from .generic import build_generic_goal_plan
from .intervals import build_intervals_goal_plan
from .models import GoalAnalysisPlan
from .physiological_test import (
    build_physiological_test_goal_plan,
)
from .rest import build_rest_goal_plan


def resolve_goal_analysis_plan(
    session: TrainingSession,
) -> GoalAnalysisPlan:
    """Détermine l'objectif à partir de la prescription."""

    if session.type == "rest":
        return build_rest_goal_plan()

    if session.type == "physiological_test":
        return build_physiological_test_goal_plan(
            session
        )

    prescription = session.prescription

    if isinstance(
        prescription,
        dict,
    ):
        work_structure = prescription.get(
            "work_structure"
        )

        if isinstance(
            work_structure,
            dict,
        ):
            intervals = work_structure.get(
                "intervals"
            )

            if (
                isinstance(intervals, list)
                and intervals
            ):
                return build_intervals_goal_plan()

        intensity = prescription.get(
            "intensity"
        )

        if isinstance(
            intensity,
            dict,
        ):
            targets = intensity.get(
                "targets"
            )

            if (
                isinstance(targets, list)
                and targets
            ):
                references = {
                    target.get("reference")
                    for target in targets
                    if isinstance(
                        target,
                        dict,
                    )
                }

                if references & {
                    "heart_rate",
                    "vma_percent",
                    "pace",
                    "speed",
                }:
                    return build_endurance_goal_plan()

    return build_generic_goal_plan()
