from dataclasses import dataclass
from typing import Literal

from opencoach.planning.season.strategy import (
    MacrocyclePhase,
    WeekTrajectory,
)


StrategyDecisionType = Literal[
    "phase_structure",
    "load_progression",
    "recovery_strategy",
    "specificity_progression",
    "taper_strategy",
    "race_integration",
    "assessment_strategy",
    "other",
]


AssumptionImpact = Literal[
    "low",
    "medium",
    "high",
]


UncertaintyLevel = Literal[
    "low",
    "medium",
    "high",
]


StrategyChangeAction = Literal[
    "keep",
    "modify",
    "add",
    "remove",
]


@dataclass(frozen=True)
class StrategyFactReference:
    """Référence à un fait présent dans SeasonPlanningInput.

    La valeur n'est volontairement pas recopiée ici.
    Le futur validateur résoudra source_path dans l'entrée réelle.
    """

    source_path: str

    purpose: str

    def __post_init__(self) -> None:
        if not self.source_path.strip():
            raise ValueError(
                "Le chemin d'un fait utilisé ne peut pas être vide."
            )

        if not self.purpose.strip():
            raise ValueError(
                "L'utilisation d'un fait doit être explicitée."
            )


@dataclass(frozen=True)
class StrategyAssumption:
    """Hypothèse formulée par l'IA faute de donnée suffisante."""

    assumption_id: str

    description: str

    impact: AssumptionImpact

    affected_area: str

    def __post_init__(self) -> None:
        if not self.assumption_id.strip():
            raise ValueError(
                "L'identifiant d'une hypothèse ne peut pas être vide."
            )

        if not self.description.strip():
            raise ValueError(
                "Une hypothèse doit être décrite."
            )


@dataclass(frozen=True)
class StrategyDecision:
    """Décision stratégique explicitement prise par l'IA."""

    decision_type: StrategyDecisionType

    description: str

    rationale: str

    based_on_facts: tuple[
        str,
        ...
    ] = ()

    based_on_assumptions: tuple[
        str,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError(
                "Une décision stratégique doit être décrite."
            )

        if not self.rationale.strip():
            raise ValueError(
                "Une décision stratégique doit être justifiée."
            )


@dataclass(frozen=True)
class StrategyUncertainty:
    """Limite connue pouvant affecter la qualité de la stratégie."""

    level: UncertaintyLevel

    description: str

    affected_area: str

    resolution_hint: str | None = None

    def __post_init__(self) -> None:
        if not self.description.strip():
            raise ValueError(
                "Une incertitude doit être décrite."
            )


@dataclass(frozen=True)
class StrategyRevisionChange:
    """Modification proposée par rapport à une stratégie précédente."""

    action: StrategyChangeAction

    target: str

    description: str

    reason: str

    def __post_init__(self) -> None:
        if not self.target.strip():
            raise ValueError(
                "La cible d'une révision ne peut pas être vide."
            )

        if not self.description.strip():
            raise ValueError(
                "Une modification doit être décrite."
            )

        if not self.reason.strip():
            raise ValueError(
                "Une modification doit être justifiée."
            )


@dataclass(frozen=True)
class SeasonStrategyProposal:
    """Proposition stratégique produite par l'IA.

    Elle ne constitue pas encore une stratégie OpenCoach valide.
    Elle doit être contrôlée par Python avant matérialisation.
    """

    summary: str

    facts_used: tuple[
        StrategyFactReference,
        ...
    ]

    assumptions: tuple[
        StrategyAssumption,
        ...
    ]

    decisions: tuple[
        StrategyDecision,
        ...
    ]

    uncertainties: tuple[
        StrategyUncertainty,
        ...
    ]

    phases: tuple[
        MacrocyclePhase,
        ...
    ]

    weeks: tuple[
        WeekTrajectory,
        ...
    ]

    revision_changes: tuple[
        StrategyRevisionChange,
        ...
    ] = ()

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise ValueError(
                "La proposition stratégique doit contenir un résumé."
            )

        _validate_unique_assumption_ids(
            self.assumptions
        )

        _validate_decision_references(
            decisions=self.decisions,
            facts=self.facts_used,
            assumptions=self.assumptions,
        )

    @property
    def has_assumptions(self) -> bool:
        return bool(
            self.assumptions
        )

    @property
    def has_high_uncertainty(self) -> bool:
        return any(
            uncertainty.level == "high"
            for uncertainty in self.uncertainties
        )

    @property
    def is_revision(self) -> bool:
        return bool(
            self.revision_changes
        )


def _validate_unique_assumption_ids(
    assumptions: tuple[
        StrategyAssumption,
        ...
    ],
) -> None:
    identifiers = [
        assumption.assumption_id
        for assumption in assumptions
    ]

    if len(identifiers) != len(
        set(identifiers)
    ):
        raise ValueError(
            "Les identifiants d'hypothèses doivent être uniques."
        )


def _validate_decision_references(
    *,
    decisions: tuple[
        StrategyDecision,
        ...
    ],
    facts: tuple[
        StrategyFactReference,
        ...
    ],
    assumptions: tuple[
        StrategyAssumption,
        ...
    ],
) -> None:
    known_fact_paths = {
        fact.source_path
        for fact in facts
    }

    known_assumption_ids = {
        assumption.assumption_id
        for assumption in assumptions
    }

    for decision in decisions:
        unknown_facts = (
            set(
                decision.based_on_facts
            )
            - known_fact_paths
        )

        if unknown_facts:
            raise ValueError(
                "Une décision référence un fait non déclaré."
            )

        unknown_assumptions = (
            set(
                decision.based_on_assumptions
            )
            - known_assumption_ids
        )

        if unknown_assumptions:
            raise ValueError(
                "Une décision référence une hypothèse non déclarée."
            )
