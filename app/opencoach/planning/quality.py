from dataclasses import dataclass
from typing import Literal

from .context import PlanningContext


PlanningCapability = Literal[
    "general_planning",
    "race_planning",
    "daily_adaptation",
]


@dataclass(frozen=True)
class PlanningContextAssessment:
    """Évalue les usages possibles d'un contexte de planification."""

    general_planning: bool
    race_planning: bool
    daily_adaptation: bool

    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def has_blockers(self) -> bool:
        """Indique si le contexte présente au moins un blocage."""
        return bool(self.blockers)


def assess_planning_context(
    context: PlanningContext,
) -> PlanningContextAssessment:
    """Évalue la qualité des données disponibles pour planifier."""

    blockers: list[str] = []
    warnings: list[str] = []

    training = context.athlete.training
    physiology = context.athlete.physiology

    has_training_frequency = (
        training.weekly_sessions is not None
        and training.weekly_sessions > 0
    )

    has_training_volume = (
        (
            training.weekly_duration_minutes is not None
            and training.weekly_duration_minutes > 0
        )
        or (
            training.weekly_distance_km is not None
            and training.weekly_distance_km > 0
        )
    )

    has_availability = bool(
        training.available_days
    )

    has_intensity_reference = any(
        value is not None
        for value in (
            physiology.max_heart_rate,
            physiology.vma,
            physiology.threshold_heart_rate_1,
            physiology.threshold_heart_rate_2,
        )
    )

    if not has_training_frequency:
        blockers.append(
            "Nombre de séances hebdomadaires non renseigné."
        )

    if not has_training_volume:
        blockers.append(
            "Volume hebdomadaire de référence non renseigné."
        )

    if not has_availability:
        blockers.append(
            "Jours disponibles pour l'entraînement non renseignés."
        )

    if not has_intensity_reference:
        warnings.append(
            "Aucune référence physiologique d'intensité disponible."
        )

    if context.recent_stats is None:
        warnings.append(
            "Historique récent d'entraînement indisponible."
        )

    if context.recent_load is None:
        warnings.append(
            "Charge récente indisponible."
        )

    if context.readiness is None:
        warnings.append(
            "Readiness indisponible pour l'adaptation quotidienne."
        )

    general_planning = (
        has_training_frequency
        and has_training_volume
        and has_availability
    )

    race_planning = (
        general_planning
        and context.primary_race is not None
    )

    daily_adaptation = (
        general_planning
        and context.readiness is not None
    )

    return PlanningContextAssessment(
        general_planning=general_planning,
        race_planning=race_planning,
        daily_adaptation=daily_adaptation,
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )
