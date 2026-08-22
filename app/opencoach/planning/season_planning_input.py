from dataclasses import dataclass
from datetime import date
from uuid import UUID

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

from .physiological_snapshot import (
    PhysiologicalCalibrationSnapshot,
)
from .season_strategy import (
    SeasonStrategy,
)
from .training_baseline import (
    AthleteTrainingBaseline,
)


@dataclass(frozen=True)
class SeasonAthleteContext:
    """Données stables décrivant l'athlète pour la stratégie."""

    profile: AthleteProfile

    baseline: AthleteTrainingBaseline

    physiology: PhysiologicalCalibrationSnapshot


@dataclass(frozen=True)
class SeasonGoalContext:
    """Objectifs sportifs connus au moment de la planification."""

    primary_race: Race

    training_races: tuple[
        Race,
        ...
    ] = ()


@dataclass(frozen=True)
class SeasonTrainingState:
    """État d'entraînement observable au moment de la décision."""

    recent_load: RecentTrainingLoad | None

    recent_stats: TrainingStats | None

    readiness: ReadinessAssessment | None


@dataclass(frozen=True)
class SeasonConstraintContext:
    """Contraintes connues pouvant influencer la stratégie future."""

    constraints: tuple[
        AthleteConstraint,
        ...
    ]

    known_until: date


@dataclass(frozen=True)
class SeasonKnowledgeContext:
    """Versions des connaissances et politiques utilisées."""

    knowledge_version: str

    policy_version: str


@dataclass(frozen=True)
class SeasonPlanningInput:
    """Entrée unique du moteur stratégique OpenCoach.

    Ce contrat contient uniquement des faits, des états calculés
    et éventuellement la stratégie précédente.

    Il ne contient aucune décision cachée de l'IA.
    """

    athlete_profile_id: UUID

    planning_date: date

    athlete: SeasonAthleteContext

    goals: SeasonGoalContext

    training_state: SeasonTrainingState

    constraints: SeasonConstraintContext

    knowledge: SeasonKnowledgeContext

    previous_strategy: SeasonStrategy | None = None

    @property
    def is_revision(self) -> bool:
        """Indique si la demande vise à réviser une stratégie existante."""

        return self.previous_strategy is not None

    @property
    def days_to_primary_race(self) -> int:
        """Nombre de jours avant la course principale."""

        return (
            self.goals.primary_race.date
            - self.planning_date
        ).days

    @property
    def weeks_to_primary_race(self) -> int:
        """Nombre de semaines calendaires avant l'objectif."""

        days = self.days_to_primary_race

        if days <= 0:
            return 0

        return (
            days + 6
        ) // 7

    def __post_init__(self) -> None:
        if (
            self.goals.primary_race.date
            < self.planning_date
        ):
            raise ValueError(
                "La course principale ne peut pas "
                "être antérieure à la date de planification."
            )

        if (
            self.constraints.known_until
            < self.planning_date
        ):
            raise ValueError(
                "L'horizon des contraintes ne peut pas "
                "être antérieur à la date de planification."
            )
