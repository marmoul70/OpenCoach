from dataclasses import dataclass

from .context import PlanningContext


@dataclass(frozen=True)
class AssessmentSafetyContext:
    """Évalue si un test physiologique maximal est acceptable."""

    maximal_testing_allowed: bool

    blocking_reasons: tuple[str, ...]
    warnings: tuple[str, ...]

    days_to_primary_race: int | None

    @property
    def has_blockers(self) -> bool:
        return bool(
            self.blocking_reasons
        )


def build_assessment_safety_context(
    context: PlanningContext,
) -> AssessmentSafetyContext:
    """Construit les garde-fous applicables aux tests maximaux."""

    blocking_reasons: list[str] = []
    warnings: list[str] = []

    _evaluate_readiness(
        context=context,
        blocking_reasons=blocking_reasons,
        warnings=warnings,
    )

    _evaluate_constraints(
        context=context,
        blocking_reasons=blocking_reasons,
    )

    days_to_primary_race = (
        _evaluate_primary_race(
            context=context,
            blocking_reasons=blocking_reasons,
        )
    )

    return AssessmentSafetyContext(
        maximal_testing_allowed=(
            not blocking_reasons
        ),
        blocking_reasons=tuple(
            blocking_reasons
        ),
        warnings=tuple(
            warnings
        ),
        days_to_primary_race=(
            days_to_primary_race
        ),
    )


def _evaluate_readiness(
    *,
    context: PlanningContext,
    blocking_reasons: list[str],
    warnings: list[str],
) -> None:
    readiness = context.readiness

    if readiness is None:
        warnings.append(
            "Aucune évaluation readiness n'est disponible."
        )
        return

    daily = readiness.readiness

    if daily.level in {
        "very_low",
        "low",
    }:
        blocking_reasons.append(
            "Le niveau de readiness est insuffisant "
            "pour programmer un test maximal."
        )

    if daily.critical_count > 0:
        blocking_reasons.append(
            "Le readiness contient au moins un signal critique."
        )

    if (
        daily.warning_count > 0
        and daily.critical_count == 0
    ):
        warnings.append(
            "Le readiness contient un ou plusieurs signaux "
            "nécessitant de la prudence."
        )

    if daily.training_constraints:
        warnings.extend(
            f"Contrainte readiness : {constraint}"
            for constraint in daily.training_constraints
        )


def _evaluate_constraints(
    *,
    context: PlanningContext,
    blocking_reasons: list[str],
) -> None:
    planning_date = context.planning_date

    for constraint in context.constraints:
        if not (
            constraint.start_date
            <= planning_date
            <= constraint.end_date
        ):
            continue

        if not constraint.running_allowed:
            blocking_reasons.append(
                "Une contrainte active interdit actuellement "
                "la course à pied."
            )
            continue

        if constraint.availability == "unavailable":
            blocking_reasons.append(
                "L'athlète est indisponible à la date évaluée."
            )


def _evaluate_primary_race(
    *,
    context: PlanningContext,
    blocking_reasons: list[str],
) -> int | None:
    race = context.primary_race

    if race is None:
        return None

    if race.status != "planned":
        return None

    days_to_race = (
        race.date
        - context.planning_date
    ).days

    if 0 <= days_to_race <= 7:
        blocking_reasons.append(
            "Une course principale est prévue dans les "
            "sept prochains jours."
        )

    return days_to_race
