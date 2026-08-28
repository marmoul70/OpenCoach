"""Fiches détaillées des protocoles de tests physiologiques.

Ces fiches constituent la source de vérité métier utilisée par :
- l'interface athlète ;
- la génération de la séance de test ;
- le futur moteur d'analyse des activités synchronisées.

Elles décrivent la réalisation du test sans effectuer elles-mêmes
l'analyse physiologique.
"""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.physiology.testing.models import (
    PhysiologicalMetric,
    PhysiologicalTestType,
)


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestStep:
    """Étape d'un protocole de test."""

    title: str
    description: str
    duration_minutes: int | None = None


@dataclass(
    frozen=True,
    slots=True,
)
class PhysiologicalTestProtocolDetails:
    """Description complète d'un protocole physiologique."""

    protocol: PhysiologicalTestType

    title: str
    short_description: str

    target_metrics: tuple[
        PhysiologicalMetric,
        ...,
    ]

    total_duration_minutes: int

    terrain_recommendation: str

    preparation: tuple[str, ...]

    warmup: tuple[
        PhysiologicalTestStep,
        ...,
    ]

    test_steps: tuple[
        PhysiologicalTestStep,
        ...,
    ]

    cooldown: tuple[
        PhysiologicalTestStep,
        ...,
    ]

    execution_advice: tuple[str, ...]

    invalidation_reasons: tuple[str, ...]

    required_activity_data: tuple[str, ...]

    useful_activity_data: tuple[str, ...]

    analysis_notes: tuple[str, ...]


_HALF_COOPER = PhysiologicalTestProtocolDetails(
    protocol=(
        PhysiologicalTestType.HALF_COOPER
    ),
    title="Demi-Cooper",
    short_description=(
        "Effort maximal régulier de 6 minutes "
        "permettant d'estimer la VMA."
    ),
    target_metrics=(
        PhysiologicalMetric.VMA,
    ),
    total_duration_minutes=(
        35
    ),
    terrain_recommendation=(
        "Idéalement une piste d'athlétisme ou une portion "
        "plate, régulière, mesurée et sans interruption."
    ),
    preparation=(
        (
            "Éviter une séance très intense ou une compétition "
            "dans les 24 à 48 heures précédentes."
        ),
        (
            "Réaliser le test dans de bonnes conditions de récupération "
            "et sans douleur limitante."
        ),
        (
            "Utiliser de préférence le même matériel et un terrain "
            "comparable lors des futurs retests."
        ),
        (
            "Sur piste, utiliser la distance mesurée plutôt que "
            "la seule distance GPS lorsque cela est possible."
        ),
    ),
    warmup=(
        PhysiologicalTestStep(
            title="Échauffement facile",
            description=(
                "Course facile et progressive. "
                "L'objectif est d'augmenter progressivement "
                "la température corporelle sans créer de fatigue."
            ),
            duration_minutes=15,
        ),
        PhysiologicalTestStep(
            title="Mobilité et préparation",
            description=(
                "Quelques mouvements dynamiques et éducatifs de course."
            ),
            duration_minutes=3,
        ),
        PhysiologicalTestStep(
            title="Accélérations",
            description=(
                "Effectuer 3 accélérations progressives de 15 à 20 secondes "
                "avec récupération facile entre chaque accélération."
            ),
            duration_minutes=4,
        ),
        PhysiologicalTestStep(
            title="Récupération avant test",
            description=(
                "Courir très facilement puis se préparer au départ."
            ),
            duration_minutes=2,
        ),
    ),
    test_steps=(
        PhysiologicalTestStep(
            title="Demi-Cooper",
            description=(
                "Parcourir la plus grande distance possible en 6 minutes "
                "avec un effort maximal mais aussi régulier que possible. "
                "Éviter un départ en sprint qui provoquerait "
                "un ralentissement important en fin de test."
            ),
            duration_minutes=6,
        ),
    ),
    cooldown=(
        PhysiologicalTestStep(
            title="Retour au calme",
            description=(
                "Course très facile ou marche active pour faire "
                "redescendre progressivement l'intensité."
            ),
            duration_minutes=5,
        ),
    ),
    execution_advice=(
        (
            "Chercher une allure élevée mais soutenable pendant "
            "l'intégralité des 6 minutes."
        ),
        (
            "Un léger negative split ou une allure stable est préférable "
            "à un départ beaucoup trop rapide."
        ),
        (
            "Accélérer dans la dernière minute uniquement si l'allure "
            "a été correctement maîtrisée jusque-là."
        ),
        (
            "Ne pas interrompre l'enregistrement de la montre "
            "pendant les 6 minutes."
        ),
    ),
    invalidation_reasons=(
        "Arrêt ou pause pendant les 6 minutes.",
        "Erreur manifeste de distance ou de durée.",
        "Terrain fortement descendant.",
        "Interruption par circulation ou obstacle.",
        (
            "Effort volontairement sous-maximal ne permettant pas "
            "d'interpréter le résultat comme un test."
        ),
    ),
    required_activity_data=(
        "duration",
        "distance",
        "sport_type",
        "start_time",
    ),
    useful_activity_data=(
        "pace",
        "speed",
        "heart_rate",
        "max_heart_rate",
        "elevation_gain",
        "elevation_loss",
        "laps",
        "gps_track",
        "cadence",
    ),
    analysis_notes=(
        (
            "La fenêtre d'analyse principale correspond exactement "
            "aux 6 minutes du test."
        ),
        (
            "Pour un Demi-Cooper correctement exécuté, la vitesse moyenne "
            "sur les 6 minutes constitue l'estimation principale de la VMA."
        ),
        (
            "Une distance de 1 500 m en 6 minutes correspond par exemple "
            "à une vitesse moyenne de 15 km/h."
        ),
        (
            "La fréquence cardiaque n'est pas nécessaire au calcul "
            "de la VMA mais apporte un contexte utile au débriefing."
        ),
        (
            "Le profil d'allure doit être analysé afin de détecter "
            "un départ excessivement rapide ou un effondrement final."
        ),
        (
            "Le dénivelé doit être contrôlé avant d'accepter "
            "automatiquement la mesure comme calibration de référence."
        ),
    ),
)


_PROTOCOL_DETAILS: dict[
    PhysiologicalTestType,
    PhysiologicalTestProtocolDetails,
] = {
    _HALF_COOPER.protocol: (
        _HALF_COOPER
    ),
}


def get_physiological_test_protocol_details(
    protocol: PhysiologicalTestType,
) -> PhysiologicalTestProtocolDetails:
    """Retourne la fiche détaillée d'un protocole connu."""

    try:
        return _PROTOCOL_DETAILS[
            protocol
        ]
    except KeyError as exc:
        raise ValueError(
            "Aucune fiche détaillée disponible "
            f"pour le protocole {protocol.value}."
        ) from exc


def has_physiological_test_protocol_details(
    protocol: PhysiologicalTestType,
) -> bool:
    """Indique si une fiche détaillée est disponible."""

    return (
        protocol
        in _PROTOCOL_DETAILS
    )
