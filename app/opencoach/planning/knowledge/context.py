from dataclasses import dataclass

from opencoach.planning.knowledge.training import (
    KnowledgeApplicability,
    KnowledgeTopic,
    TrainingKnowledgeItem,
    TrainingKnowledgeSource,
)
from opencoach.planning.knowledge.requirements import (
    KnowledgeRequirementReason,
    TrainingKnowledgeRequirements,
)
from opencoach.planning.knowledge.selection import (
    TrainingKnowledgeSelection,
)


@dataclass(frozen=True)
class TrainingKnowledgeContext:
    """Contexte de connaissances remis au moteur de stratégie.

    Ce contexte contient uniquement des connaissances sélectionnées
    et leur provenance. Il ne contient aucune policy Python ni
    aucun garde-fou d'exécution.
    """

    knowledge_base_id: str
    knowledge_version: str

    topics: tuple[
        KnowledgeTopic,
        ...
    ]

    applicabilities: tuple[
        KnowledgeApplicability,
        ...
    ]

    items: tuple[
        TrainingKnowledgeItem,
        ...
    ]

    selection_reasons: tuple[
        KnowledgeRequirementReason,
        ...
    ]

    @property
    def empty(self) -> bool:
        return not self.items

    @property
    def knowledge_ids(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            item.knowledge_id
            for item in self.items
        )

    @property
    def sources(
        self,
    ) -> tuple[TrainingKnowledgeSource, ...]:
        """Retourne les sources uniques utilisées par le contexte."""

        seen: set[str] = set()
        sources: list[
            TrainingKnowledgeSource
        ] = []

        for item in self.items:
            for source in item.sources:
                if source.source_id in seen:
                    continue

                seen.add(
                    source.source_id
                )

                sources.append(
                    source
                )

        return tuple(sources)


def build_training_knowledge_context(
    *,
    requirements: TrainingKnowledgeRequirements,
    selection: TrainingKnowledgeSelection,
) -> TrainingKnowledgeContext:
    """Construit le contexte final remis au moteur de stratégie."""

    _validate_selection_matches_requirements(
        requirements=requirements,
        selection=selection,
    )

    return TrainingKnowledgeContext(
        knowledge_base_id=(
            selection.knowledge_base_id
        ),
        knowledge_version=(
            selection.knowledge_version
        ),
        topics=requirements.topics,
        applicabilities=(
            requirements.applicabilities
        ),
        items=selection.items,
        selection_reasons=(
            requirements.reasons
        ),
    )


def _validate_selection_matches_requirements(
    *,
    requirements: TrainingKnowledgeRequirements,
    selection: TrainingKnowledgeSelection,
) -> None:
    expected_topics = set(
        requirements.topics
    )

    selected_topics = set(
        selection.requested_topics
    )

    if expected_topics != selected_topics:
        raise ValueError(
            "La sélection de connaissances ne correspond pas "
            "aux topics demandés."
        )

    expected_applicabilities = set(
        requirements.applicabilities
    )

    selected_applicabilities = set(
        selection.requested_applicabilities
    )

    if (
        expected_applicabilities
        != selected_applicabilities
    ):
        raise ValueError(
            "La sélection de connaissances ne correspond pas "
            "aux applicabilités demandées."
        )
