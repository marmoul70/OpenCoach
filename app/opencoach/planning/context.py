from dataclasses import dataclass
from datetime import date

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    Race,
)
from opencoach.readiness import ReadinessAssessment
from opencoach.training import (
    RecentTrainingLoad,
    TrainingStats,
)


@dataclass(frozen=True)
class PlanningContext:
    """Vue consolidée des données nécessaires à la planification.

    Le contexte ne possède ni ne persiste les données qu'il expose.
    Il assemble les informations métier déjà produites par les autres
    domaines d'OpenCoach afin de fournir une entrée stable au moteur
    de planification.
    """

    planning_date: date

    athlete: AthleteProfile

    primary_race: Race | None
    training_races: tuple[Race, ...]

    readiness: ReadinessAssessment | None

    recent_load: RecentTrainingLoad | None
    recent_stats: TrainingStats | None

    constraints: tuple[AthleteConstraint, ...]
    constraints_end_date: date
