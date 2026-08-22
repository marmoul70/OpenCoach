from dataclasses import dataclass

from .season_planning_input import (
    SeasonPlanningInput,
)
from .training_knowledge_context import (
    TrainingKnowledgeContext,
)


@dataclass(frozen=True)
class SeasonStrategistContext:
    """Contexte complet remis au stratège IA.

    Il contient les faits de planification et les connaissances
    sélectionnées pour la décision stratégique.

    Les policies Python et les garde-fous d'exécution restent
    volontairement hors de ce contrat.
    """

    planning_input: SeasonPlanningInput

    training_knowledge: TrainingKnowledgeContext

    def __post_init__(self) -> None:
        if (
            self.planning_input.knowledge.knowledge_version
            != self.training_knowledge.knowledge_version
        ):
            raise ValueError(
                "La version des connaissances du contexte IA "
                "ne correspond pas à celle déclarée dans "
                "SeasonPlanningInput."
            )

    @property
    def is_revision(self) -> bool:
        """Indique si le stratège révise une stratégie existante."""

        return self.planning_input.is_revision

    @property
    def knowledge_ids(
        self,
    ) -> tuple[str, ...]:
        """Expose les connaissances effectivement disponibles."""

        return self.training_knowledge.knowledge_ids

    @property
    def target_race(self):
        """Retourne la course définissant l'horizon stratégique."""

        return self.planning_input.goals.target_race

    @property
    def priority_races(self):
        """Retourne toutes les courses déclarées prioritaires."""

        return self.planning_input.goals.priority_races


def build_season_strategist_context(
    *,
    planning_input: SeasonPlanningInput,
    training_knowledge: TrainingKnowledgeContext,
) -> SeasonStrategistContext:
    """Construit le contexte final destiné au stratège IA."""

    return SeasonStrategistContext(
        planning_input=planning_input,
        training_knowledge=training_knowledge,
    )
