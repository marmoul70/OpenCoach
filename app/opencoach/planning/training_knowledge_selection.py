from dataclasses import dataclass

from .season_planning_input import (
    SeasonPlanningInput,
)
from .training_knowledge import (
    KnowledgeApplicability,
    KnowledgeEvidenceLevel,
    KnowledgeTopic,
    TrainingKnowledgeBase,
    TrainingKnowledgeItem,
)


_EVIDENCE_ORDER: dict[
    KnowledgeEvidenceLevel,
    int,
] = {
    "very_low": 0,
    "low": 1,
    "moderate": 2,
    "high": 3,
}


@dataclass(frozen=True)
class TrainingKnowledgeSelection:
    """Sous-ensemble de connaissances pertinent pour une stratégie."""

    knowledge_base_id: str
    knowledge_version: str

    items: tuple[
        TrainingKnowledgeItem,
        ...
    ]

    requested_topics: tuple[
        KnowledgeTopic,
        ...
    ]

    requested_applicabilities: tuple[
        KnowledgeApplicability,
        ...
    ]

    minimum_evidence_level: KnowledgeEvidenceLevel | None

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


def select_training_knowledge(
    *,
    planning_input: SeasonPlanningInput,
    knowledge_base: TrainingKnowledgeBase,
    topics: tuple[
        KnowledgeTopic,
        ...
    ] = (),
    applicabilities: tuple[
        KnowledgeApplicability,
        ...
    ] = (),
    minimum_evidence_level: KnowledgeEvidenceLevel | None = None,
) -> TrainingKnowledgeSelection:
    """Sélectionne les connaissances utiles au contexte stratégique."""

    items = knowledge_base.active_items(
        on_date=planning_input.planning_date,
    )

    if topics:
        requested_topics = set(
            topics
        )

        items = tuple(
            item
            for item in items
            if item.topic in requested_topics
        )

    if applicabilities:
        requested_applicabilities = set(
            applicabilities
        )

        items = tuple(
            item
            for item in items
            if (
                requested_applicabilities
                & set(item.applicability)
            )
        )

    if minimum_evidence_level is not None:
        minimum_rank = _EVIDENCE_ORDER[
            minimum_evidence_level
        ]

        items = tuple(
            item
            for item in items
            if (
                _EVIDENCE_ORDER[
                    item.evidence_level
                ]
                >= minimum_rank
            )
        )

    return TrainingKnowledgeSelection(
        knowledge_base_id=(
            knowledge_base.knowledge_base_id
        ),
        knowledge_version=(
            knowledge_base.version
        ),
        items=items,
        requested_topics=topics,
        requested_applicabilities=applicabilities,
        minimum_evidence_level=(
            minimum_evidence_level
        ),
    )