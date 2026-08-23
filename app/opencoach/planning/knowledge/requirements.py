from dataclasses import dataclass

from opencoach.planning.knowledge.race_classification import (
    RaceClassificationThresholds,
    classify_race_for_knowledge,
)
from opencoach.planning.season.planning_input import (
    SeasonPlanningInput,
)
from opencoach.planning.knowledge.training import (
    KnowledgeApplicability,
    KnowledgeTopic,
)


@dataclass(frozen=True)
class KnowledgeRequirementReason:
    """Explique pourquoi un besoin de connaissance a été retenu."""

    requirement: str
    reason: str


@dataclass(frozen=True)
class TrainingKnowledgeRequirements:
    """Besoins de connaissances déduits du contexte stratégique."""

    topics: tuple[
        KnowledgeTopic,
        ...
    ]

    applicabilities: tuple[
        KnowledgeApplicability,
        ...
    ]

    reasons: tuple[
        KnowledgeRequirementReason,
        ...
    ]


def infer_training_knowledge_requirements(
    *,
    planning_input: SeasonPlanningInput,
    race_thresholds: RaceClassificationThresholds,
) -> TrainingKnowledgeRequirements:
    """Déduit les connaissances utiles à la planification de saison."""

    topics: set[KnowledgeTopic] = {
        "periodization",
        "load_progression",
        "recovery",
        "taper",
        "specificity",
        "race_preparation",
    }

    applicabilities: set[KnowledgeApplicability] = {
        "general_endurance",
    }

    reasons: list[KnowledgeRequirementReason] = [
        KnowledgeRequirementReason(
            requirement="periodization",
            reason=(
                "Toute stratégie de saison nécessite "
                "des connaissances de périodisation."
            ),
        ),
        KnowledgeRequirementReason(
            requirement="load_progression",
            reason=(
                "La trajectoire stratégique doit gérer "
                "l'évolution de la charge."
            ),
        ),
        KnowledgeRequirementReason(
            requirement="recovery",
            reason=(
                "La récupération fait partie de la "
                "construction d'une saison."
            ),
        ),
        KnowledgeRequirementReason(
            requirement="taper",
            reason=(
                "Une course cible nécessite d'évaluer "
                "une stratégie d'affûtage."
            ),
        ),
        KnowledgeRequirementReason(
            requirement="specificity",
            reason=(
                "La préparation doit tenir compte des "
                "caractéristiques des objectifs."
            ),
        ),
        KnowledgeRequirementReason(
            requirement="race_preparation",
            reason=(
                "Le contexte contient au moins une "
                "course cible."
            ),
        ),
        KnowledgeRequirementReason(
            requirement="general_endurance",
            reason=(
                "La planification concerne un sport "
                "d'endurance."
            ),
        ),
    ]

    for race in planning_input.goals.all_races:
        classification = classify_race_for_knowledge(
            race=race,
            thresholds=race_thresholds,
        )

        applicabilities.update(
            classification.applicabilities
        )

        for applicability in classification.applicabilities:
            reasons.append(
                KnowledgeRequirementReason(
                    requirement=applicability,
                    reason=(
                        f"La course '{race.name}' est classée "
                        f"{classification.sport_family}/"
                        f"{classification.distance_family}."
                    ),
                )
            )

    if _physiology_requires_calibration(
        planning_input
    ):
        topics.add(
            "physiological_assessment"
        )

        reasons.append(
            KnowledgeRequirementReason(
                requirement="physiological_assessment",
                reason=(
                    "Au moins une mesure physiologique "
                    "utile nécessite une recalibration."
                ),
            )
        )

    return TrainingKnowledgeRequirements(
        topics=tuple(
            sorted(topics)
        ),
        applicabilities=tuple(
            sorted(applicabilities)
        ),
        reasons=tuple(reasons),
    )


def _physiology_requires_calibration(
    planning_input: SeasonPlanningInput,
) -> bool:
    physiology = (
        planning_input.athlete.physiology
    )

    metrics = (
        physiology.vma,
        physiology.max_heart_rate,
        physiology.resting_heart_rate,
        physiology.threshold_heart_rate_1,
        physiology.threshold_heart_rate_2,
    )

    return any(
        metric.recalibration_recommended
        for metric in metrics
    )
