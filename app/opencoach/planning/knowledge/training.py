from dataclasses import dataclass
from datetime import date
from typing import Literal


KnowledgeEvidenceLevel = Literal[
    "very_low",
    "low",
    "moderate",
    "high",
]

KnowledgeSourceType = Literal[
    "systematic_review",
    "meta_analysis",
    "randomized_trial",
    "observational_study",
    "consensus",
    "federation_guideline",
    "expert_guideline",
    "open_coach",
    "other",
]

KnowledgeTopic = Literal[
    "load_progression",
    "intensity_distribution",
    "recovery",
    "taper",
    "periodization",
    "specificity",
    "strength",
    "physiological_assessment",
    "race_preparation",
    "training_frequency",
    "other",
]

KnowledgeApplicability = Literal[
    "general_endurance",
    "road_running",
    "trail_running",
    "ultra_running",
    "10k",
    "half_marathon",
    "marathon",
    "short_trail",
    "long_trail",
    "ultra_trail",
]


@dataclass(frozen=True)
class TrainingKnowledgeSource:
    """Source vérifiable associée à une connaissance."""

    source_id: str

    source_type: KnowledgeSourceType

    title: str

    authors: str | None = None
    publication_year: int | None = None

    reference: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError(
                "L'identifiant de source ne peut pas être vide."
            )

        if not self.title.strip():
            raise ValueError(
                "Le titre de la source ne peut pas être vide."
            )


@dataclass(frozen=True)
class TrainingKnowledgeItem:
    """Connaissance consultable par le moteur de stratégie.

    Une connaissance informe la décision.
    Elle ne constitue pas automatiquement un garde-fou Python.
    """

    knowledge_id: str

    topic: KnowledgeTopic

    statement: str

    rationale: str

    evidence_level: KnowledgeEvidenceLevel

    applicability: tuple[
        KnowledgeApplicability,
        ...
    ]

    sources: tuple[
        TrainingKnowledgeSource,
        ...
    ]

    valid_from: date

    valid_until: date | None = None

    supersedes: tuple[
        str,
        ...
    ] = ()

    tags: tuple[
        str,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if not self.knowledge_id.strip():
            raise ValueError(
                "L'identifiant de connaissance ne peut pas être vide."
            )

        if not self.statement.strip():
            raise ValueError(
                "Une connaissance doit contenir une affirmation."
            )

        if not self.rationale.strip():
            raise ValueError(
                "Une connaissance doit être justifiée."
            )

        if (
            self.valid_until is not None
            and self.valid_until < self.valid_from
        ):
            raise ValueError(
                "La fin de validité ne peut pas précéder "
                "le début de validité."
            )


@dataclass(frozen=True)
class TrainingKnowledgeBase:
    """Version immuable des connaissances utilisables par OpenCoach."""

    knowledge_base_id: str

    version: str

    effective_from: date

    items: tuple[
        TrainingKnowledgeItem,
        ...
    ]

    def __post_init__(self) -> None:
        if not self.knowledge_base_id.strip():
            raise ValueError(
                "L'identifiant de la base de connaissances "
                "ne peut pas être vide."
            )

        if not self.version.strip():
            raise ValueError(
                "La version de la base de connaissances "
                "ne peut pas être vide."
            )

        identifiers = [
            item.knowledge_id
            for item in self.items
        ]

        if len(identifiers) != len(
            set(identifiers)
        ):
            raise ValueError(
                "Les identifiants de connaissances "
                "doivent être uniques."
            )

    def active_items(
        self,
        *,
        on_date: date,
    ) -> tuple[TrainingKnowledgeItem, ...]:
        """Retourne uniquement les connaissances valides à une date."""

        return tuple(
            item
            for item in self.items
            if (
                item.valid_from <= on_date
                and (
                    item.valid_until is None
                    or on_date <= item.valid_until
                )
            )
        )

    def items_for_topic(
        self,
        topic: KnowledgeTopic,
        *,
        on_date: date,
    ) -> tuple[TrainingKnowledgeItem, ...]:
        return tuple(
            item
            for item in self.active_items(
                on_date=on_date
            )
            if item.topic == topic
        )

    def items_for_applicability(
        self,
        applicability: KnowledgeApplicability,
        *,
        on_date: date,
    ) -> tuple[TrainingKnowledgeItem, ...]:
        return tuple(
            item
            for item in self.active_items(
                on_date=on_date
            )
            if applicability in item.applicability
        )