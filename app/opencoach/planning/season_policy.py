from dataclasses import dataclass
from datetime import date
from typing import Literal
from .policy_parameters import PolicyParameters

PolicyAuthority = Literal[
    "advisory",
    "warning",
    "hard_limit",
]

PolicyCategory = Literal[
    "load_progression",
    "recovery",
    "taper",
    "specificity",
    "assessment",
    "availability",
    "race_proximity",
    "training_frequency",
    "other",
]

PolicySourceType = Literal[
    "open_coach",
    "scientific_review",
    "scientific_study",
    "consensus",
    "federation",
    "expert_guideline",
    "other",
]


@dataclass(frozen=True)
class PolicySource:
    """Provenance d'une règle ou recommandation."""

    source_id: str

    source_type: PolicySourceType

    title: str

    reference: str | None = None

    publication_year: int | None = None

    notes: str | None = None

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
class SeasonPolicyRule:
    """Règle de planification versionnable et explicable."""

    rule_id: str

    category: PolicyCategory

    authority: PolicyAuthority

    description: str

    rationale: str

    sources: tuple[
        PolicySource,
        ...
    ]

    enabled: bool = True

    parameters: PolicyParameters | None = None

    def __post_init__(self) -> None:
        if not self.rule_id.strip():
            raise ValueError(
                "L'identifiant de règle ne peut pas être vide."
            )

        if not self.description.strip():
            raise ValueError(
                "Une règle doit être décrite."
            )

        if not self.rationale.strip():
            raise ValueError(
                "Une règle doit être justifiée."
            )


@dataclass(frozen=True)
class SeasonPlanningPolicy:
    """Ensemble versionné des règles stratégiques OpenCoach."""

    policy_id: str

    version: str

    effective_from: date

    rules: tuple[
        SeasonPolicyRule,
        ...
    ]

    description: str | None = None

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError(
                "L'identifiant de policy ne peut pas être vide."
            )

        if not self.version.strip():
            raise ValueError(
                "La version de policy ne peut pas être vide."
            )

        _validate_unique_rule_ids(
            self.rules
        )

    @property
    def enabled_rules(
        self,
    ) -> tuple[SeasonPolicyRule, ...]:
        return tuple(
            rule
            for rule in self.rules
            if rule.enabled
        )

    def rules_by_authority(
        self,
        authority: PolicyAuthority,
    ) -> tuple[SeasonPolicyRule, ...]:
        return tuple(
            rule
            for rule in self.enabled_rules
            if rule.authority == authority
        )

    def rules_by_category(
        self,
        category: PolicyCategory,
    ) -> tuple[SeasonPolicyRule, ...]:
        return tuple(
            rule
            for rule in self.enabled_rules
            if rule.category == category
        )

    def get_rule(
        self,
        rule_id: str,
    ) -> SeasonPolicyRule | None:
        normalized = rule_id.strip()

        return next(
            (
                rule
                for rule in self.rules
                if rule.rule_id == normalized
            ),
            None,
        )


def _validate_unique_rule_ids(
    rules: tuple[
        SeasonPolicyRule,
        ...
    ],
) -> None:
    identifiers = [
        rule.rule_id
        for rule in rules
    ]

    if len(identifiers) != len(
        set(identifiers)
    ):
        raise ValueError(
            "Les identifiants de règles "
            "d'une policy doivent être uniques."
        )
