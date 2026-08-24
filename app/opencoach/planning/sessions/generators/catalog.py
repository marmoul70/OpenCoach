"""Catalogue déterministe des recettes de séance OpenCoach.

Une recette décrit la traduction métier d'un stimulus en contenu
d'entraînement.

Elle ne décide ni du jour, ni de la charge hebdomadaire, ni de la
trajectoire. Ces décisions appartiennent aux couches de planification
situées en amont.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from opencoach.planning.stimulus.training import (
    TrainingModality,
    TrainingStimulus,
)


class SessionStructure(StrEnum):
    """Famille structurelle utilisée pour construire une séance."""

    ENDURANCE = "endurance"
    QUALITY = "quality"
    STRENGTH = "strength"
    RECOVERY = "recovery"


@dataclass(frozen=True, slots=True)
class SessionRecipe:
    """Recette métier associée à un stimulus principal."""

    title: str

    objective: str

    structure: SessionStructure

    default_modality: TrainingModality

    main_block_name: str

    main_block_description: str

    warmup_description: str = (
        "Mise en route progressive en aisance respiratoire."
    )

    cooldown_description: str = (
        "Retour au calme progressif à intensité facile."
    )

    def __post_init__(
        self,
    ) -> None:
        text_values = (
            self.title,
            self.objective,
            self.main_block_name,
            self.main_block_description,
            self.warmup_description,
            self.cooldown_description,
        )

        if any(
            not value.strip()
            for value in text_values
        ):
            raise ValueError(
                "Les textes d'une recette de séance "
                "ne peuvent pas être vides."
            )


SESSION_RECIPES: dict[
    TrainingStimulus,
    SessionRecipe,
] = {
    TrainingStimulus.AEROBIC_EASY: (
        SessionRecipe(
            title="Endurance facile",
            objective=(
                "Développer l'endurance fondamentale "
                "avec une fatigue limitée."
            ),
            structure=SessionStructure.ENDURANCE,
            default_modality=TrainingModality.RUNNING,
            main_block_name="Endurance facile",
            main_block_description=(
                "Course continue confortable, en aisance "
                "respiratoire et sans dérive d'intensité."
            ),
        )
    ),

    TrainingStimulus.AEROBIC_ENDURANCE: (
        SessionRecipe(
            title="Endurance aérobie",
            objective=(
                "Développer la capacité à soutenir un effort "
                "aérobie régulier."
            ),
            structure=SessionStructure.ENDURANCE,
            default_modality=TrainingModality.RUNNING,
            main_block_name="Endurance continue",
            main_block_description=(
                "Course continue régulière à intensité "
                "aérobie maîtrisée."
            ),
        )
    ),

    TrainingStimulus.THRESHOLD: (
        SessionRecipe(
            title="Travail au seuil",
            objective=(
                "Améliorer la capacité à maintenir un effort "
                "soutenu proche du seuil."
            ),
            structure=SessionStructure.QUALITY,
            default_modality=TrainingModality.RUNNING,
            main_block_name="Bloc seuil",
            main_block_description=(
                "Travail soutenu mais contrôlé, réalisé en "
                "fractions suffisamment longues pour accumuler "
                "du temps utile au seuil."
            ),
            warmup_description=(
                "Échauffement progressif avec quelques "
                "accélérations contrôlées avant le travail au seuil."
            ),
        )
    ),

    TrainingStimulus.VO2MAX: (
        SessionRecipe(
            title="Développement VO2max",
            objective=(
                "Stimuler la puissance aérobie et la capacité "
                "à soutenir des efforts intenses."
            ),
            structure=SessionStructure.QUALITY,
            default_modality=TrainingModality.RUNNING,
            main_block_name="Intervalles VO2max",
            main_block_description=(
                "Répétitions courtes à moyennes à intensité élevée, "
                "entrecoupées de récupérations actives."
            ),
            warmup_description=(
                "Échauffement progressif complété par quelques "
                "accélérations avant les intervalles."
            ),
        )
    ),

    TrainingStimulus.UPHILL_STRENGTH: (
        SessionRecipe(
            title="Force en montée",
            objective=(
                "Développer la force spécifique nécessaire "
                "aux montées en trail."
            ),
            structure=SessionStructure.QUALITY,
            default_modality=TrainingModality.TRAIL_RUNNING,
            main_block_name="Répétitions en montée",
            main_block_description=(
                "Montées réalisées avec une foulée dynamique "
                "et une forte qualité gestuelle, récupération "
                "facile entre les répétitions."
            ),
        )
    ),

    TrainingStimulus.UPHILL_THRESHOLD: (
        SessionRecipe(
            title="Seuil en montée",
            objective=(
                "Développer la capacité à soutenir un effort "
                "prolongé en montée."
            ),
            structure=SessionStructure.QUALITY,
            default_modality=TrainingModality.TRAIL_RUNNING,
            main_block_name="Montées soutenues",
            main_block_description=(
                "Efforts prolongés en montée à intensité soutenue "
                "et régulière, avec récupération maîtrisée."
            ),
        )
    ),

    TrainingStimulus.DOWNHILL_SPECIFICITY: (
        SessionRecipe(
            title="Technique de descente",
            objective=(
                "Développer l'efficacité, la confiance et la "
                "résistance musculaire en descente."
            ),
            structure=SessionStructure.QUALITY,
            default_modality=TrainingModality.TRAIL_RUNNING,
            main_block_name="Descentes techniques",
            main_block_description=(
                "Descentes répétées à vitesse contrôlée avec "
                "attention portée aux appuis, à la cadence et "
                "au relâchement."
            ),
        )
    ),

    TrainingStimulus.LONG_ENDURANCE: (
        SessionRecipe(
            title="Sortie longue",
            objective=(
                "Développer l'endurance prolongée et la capacité "
                "à maintenir un effort durable."
            ),
            structure=SessionStructure.ENDURANCE,
            default_modality=TrainingModality.TRAIL_RUNNING,
            main_block_name="Endurance longue",
            main_block_description=(
                "Effort continu majoritairement facile sur terrain "
                "adapté à l'objectif, avec gestion régulière de "
                "l'intensité et de l'alimentation."
            ),
        )
    ),

    TrainingStimulus.RACE_SPECIFIC: (
        SessionRecipe(
            title="Séance spécifique course",
            objective=(
                "Reproduire les principales contraintes de "
                "l'objectif sportif."
            ),
            structure=SessionStructure.QUALITY,
            default_modality=TrainingModality.TRAIL_RUNNING,
            main_block_name="Travail spécifique",
            main_block_description=(
                "Séquence réalisée sur un terrain et à une intensité "
                "proches des contraintes de la course objectif."
            ),
        )
    ),

    TrainingStimulus.STRENGTH_LOWER_BODY: (
        SessionRecipe(
            title="Renforcement membres inférieurs",
            objective=(
                "Développer la force et la robustesse des membres "
                "inférieurs utiles à la course."
            ),
            structure=SessionStructure.STRENGTH,
            default_modality=TrainingModality.STRENGTH,
            main_block_name="Renforcement jambes",
            main_block_description=(
                "Travail contrôlé des principaux groupes musculaires "
                "des membres inférieurs, avec priorité à la qualité "
                "d'exécution."
            ),
            warmup_description=(
                "Mobilité dynamique et activation progressive "
                "des membres inférieurs."
            ),
            cooldown_description=(
                "Retour au calme avec mobilité légère."
            ),
        )
    ),

    TrainingStimulus.STRENGTH_CORE: (
        SessionRecipe(
            title="Renforcement du tronc",
            objective=(
                "Améliorer la stabilité du tronc et le maintien "
                "de la posture pendant l'effort."
            ),
            structure=SessionStructure.STRENGTH,
            default_modality=TrainingModality.STRENGTH,
            main_block_name="Renforcement du tronc",
            main_block_description=(
                "Travail de gainage et de contrôle du tronc, "
                "réalisé avec une exécution propre et maîtrisée."
            ),
            warmup_description=(
                "Mobilité et activation légère du tronc."
            ),
            cooldown_description=(
                "Retour au calme avec mobilité douce."
            ),
        )
    ),

    TrainingStimulus.RECOVERY: (
        SessionRecipe(
            title="Récupération active",
            objective=(
                "Favoriser la récupération tout en maintenant "
                "une activité très légère."
            ),
            structure=SessionStructure.RECOVERY,
            default_modality=TrainingModality.RUNNING,
            main_block_name="Récupération",
            main_block_description=(
                "Effort très facile, relâché et sans objectif "
                "de performance. La séance doit laisser une "
                "sensation de fraîcheur."
            ),
        )
    ),
}


def get_session_recipe(
    stimulus: TrainingStimulus,
) -> SessionRecipe:
    """Retourne la recette associée à un stimulus."""

    try:
        return SESSION_RECIPES[
            stimulus
        ]

    except KeyError as exc:
        raise ValueError(
            "Aucune recette de séance n'est définie "
            f"pour le stimulus '{stimulus.value}'."
        ) from exc


def validate_session_recipe_catalog() -> None:
    """Vérifie que tous les stimuli possèdent une recette."""

    missing = tuple(
        stimulus
        for stimulus in TrainingStimulus
        if stimulus not in SESSION_RECIPES
    )

    if missing:
        values = ", ".join(
            stimulus.value
            for stimulus in missing
        )

        raise RuntimeError(
            "Le catalogue de séances est incomplet : "
            f"{values}."
        )
