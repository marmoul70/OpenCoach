from dataclasses import dataclass
from typing import Literal

from .season_planning_input import SeasonPlanningInput
from .season_strategy_proposal import SeasonStrategyProposal


ViolationSeverity = Literal[
    "error",
    "warning",
]


@dataclass(frozen=True)
class StrategyViolation:
    """Violation détectée dans une proposition stratégique."""

    rule_id: str
    severity: ViolationSeverity
    message: str

    target: str | None = None


@dataclass(frozen=True)
class SeasonStrategyValidation:
    """Résultat complet de la validation Python."""

    violations: tuple[
        StrategyViolation,
        ...
    ]

    @property
    def errors(
        self,
    ) -> tuple[StrategyViolation, ...]:
        return tuple(
            violation
            for violation in self.violations
            if violation.severity == "error"
        )

    @property
    def warnings(
        self,
    ) -> tuple[StrategyViolation, ...]:
        return tuple(
            violation
            for violation in self.violations
            if violation.severity == "warning"
        )

    @property
    def valid(self) -> bool:
        """Une stratégie reste valide en présence de warnings."""

        return not self.errors


def validate_season_strategy_proposal(
    *,
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
) -> SeasonStrategyValidation:
    """Valide une proposition IA contre les faits détenus par Python."""

    violations: list[StrategyViolation] = []

    violations.extend(
        _validate_fact_references(
            planning_input=planning_input,
            proposal=proposal,
        )
    )

    violations.extend(
        _validate_phases(
            planning_input=planning_input,
            proposal=proposal,
        )
    )

    violations.extend(
        _validate_weeks(
            planning_input=planning_input,
            proposal=proposal,
        )
    )

    violations.extend(
        _validate_revision_contract(
            planning_input=planning_input,
            proposal=proposal,
        )
    )

    return SeasonStrategyValidation(
        violations=tuple(violations),
    )


def _validate_fact_references(
    *,
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
) -> tuple[StrategyViolation, ...]:
    violations: list[StrategyViolation] = []

    for fact in proposal.facts_used:
        if not _path_exists(
            root=planning_input,
            path=fact.source_path,
        ):
            violations.append(
                StrategyViolation(
                    rule_id="fact_reference_exists",
                    severity="error",
                    message=(
                        "La proposition référence un fait "
                        "absent de SeasonPlanningInput."
                    ),
                    target=fact.source_path,
                )
            )

    return tuple(violations)


def _validate_phases(
    *,
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
) -> tuple[StrategyViolation, ...]:
    violations: list[StrategyViolation] = []

    ordered = sorted(
        proposal.phases,
        key=lambda phase: phase.start_date,
    )

    for phase in ordered:
        if phase.start_date < planning_input.planning_date:
            violations.append(
                StrategyViolation(
                    rule_id="phase_not_before_planning",
                    severity="error",
                    message=(
                        "Une phase stratégique commence avant "
                        "la date de planification."
                    ),
                    target=phase.phase_type,
                )
            )

        if phase.end_date > planning_input.goals.primary_race.date:
            violations.append(
                StrategyViolation(
                    rule_id="phase_not_after_primary_race",
                    severity="error",
                    message=(
                        "Une phase stratégique dépasse "
                        "la course principale."
                    ),
                    target=phase.phase_type,
                )
            )

    for previous, current in zip(
        ordered,
        ordered[1:],
    ):
        if current.start_date <= previous.end_date:
            violations.append(
                StrategyViolation(
                    rule_id="phase_no_overlap",
                    severity="error",
                    message=(
                        "Deux phases stratégiques se chevauchent."
                    ),
                    target=(
                        f"{previous.phase_type}"
                        f"->{current.phase_type}"
                    ),
                )
            )

    return tuple(violations)


def _validate_weeks(
    *,
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
) -> tuple[StrategyViolation, ...]:
    violations: list[StrategyViolation] = []

    ordered = sorted(
        proposal.weeks,
        key=lambda week: week.start_date,
    )

    week_numbers = [
        week.week_number
        for week in ordered
    ]

    if len(week_numbers) != len(
        set(week_numbers)
    ):
        violations.append(
            StrategyViolation(
                rule_id="week_number_unique",
                severity="error",
                message=(
                    "Les numéros de semaine "
                    "doivent être uniques."
                ),
            )
        )

    for week in ordered:
        if week.end_date < planning_input.planning_date:
            violations.append(
                StrategyViolation(
                    rule_id="week_not_before_planning",
                    severity="error",
                    message=(
                        "Une semaine stratégique est entièrement "
                        "antérieure à la planification."
                    ),
                    target=str(
                        week.week_number
                    ),
                )
            )

        if week.end_date > planning_input.goals.primary_race.date:
            violations.append(
                StrategyViolation(
                    rule_id="week_not_after_primary_race",
                    severity="error",
                    message=(
                        "Une semaine stratégique dépasse "
                        "la course principale."
                    ),
                    target=str(
                        week.week_number
                    ),
                )
            )

    for previous, current in zip(
        ordered,
        ordered[1:],
    ):
        if current.start_date <= previous.end_date:
            violations.append(
                StrategyViolation(
                    rule_id="week_no_overlap",
                    severity="error",
                    message=(
                        "Deux trajectoires hebdomadaires "
                        "se chevauchent."
                    ),
                    target=(
                        f"{previous.week_number}"
                        f"->{current.week_number}"
                    ),
                )
            )

    return tuple(violations)


def _validate_revision_contract(
    *,
    planning_input: SeasonPlanningInput,
    proposal: SeasonStrategyProposal,
) -> tuple[StrategyViolation, ...]:
    if (
        planning_input.previous_strategy is not None
        and not proposal.revision_changes
    ):
        return (
            StrategyViolation(
                rule_id="revision_changes_required",
                severity="error",
                message=(
                    "Une stratégie précédente existe mais "
                    "la proposition ne décrit aucune révision."
                ),
                target="revision_changes",
            ),
        )

    if (
        planning_input.previous_strategy is None
        and proposal.revision_changes
    ):
        return (
            StrategyViolation(
                rule_id="revision_without_previous_strategy",
                severity="error",
                message=(
                    "La proposition déclare une révision alors "
                    "qu'aucune stratégie précédente n'existe."
                ),
                target="revision_changes",
            ),
        )

    return ()


def _path_exists(
    *,
    root: object,
    path: str,
) -> bool:
    """Résout uniquement des attributs publics simples.

    Aucun index, appel de méthode ou syntaxe dynamique n'est autorisé.
    """

    current = root

    for component in path.split("."):
        if (
            not component
            or component.startswith("_")
            or not component.isidentifier()
        ):
            return False

        try:
            current = getattr(
                current,
                component,
            )
        except AttributeError:
            return False

        if callable(current):
            return False

    return True
