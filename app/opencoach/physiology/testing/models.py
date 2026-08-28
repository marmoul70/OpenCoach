"""Modèles métier des tests physiologiques OpenCoach.

Ce module décrit les protocoles disponibles sans gérer leur
planification, leur persistance ni l'analyse des activités.

Un protocole définit :
- les disciplines auxquelles il s'applique ;
- les métriques recherchées ;
- son coût physiologique ;
- les données nécessaires à son analyse ;
- son niveau de preuve.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SportDiscipline(StrEnum):
    """Disciplines pratiquées par l'athlète."""

    ROAD_RUNNING = "road_running"
    TRAIL_RUNNING = "trail_running"
    TRACK_RUNNING = "track_running"
    CYCLING = "cycling"


class PhysiologicalMetric(StrEnum):
    """Métriques pouvant être produites par un test."""

    VMA = "vma"
    MAX_HEART_RATE = "max_heart_rate"

    THRESHOLD_PACE = "threshold_pace"
    THRESHOLD_HEART_RATE = (
        "threshold_heart_rate"
    )

    CRITICAL_SPEED = "critical_speed"
    D_PRIME = "d_prime"

    UPHILL_VAM = "uphill_vam"
    UPHILL_SUSTAINED_VAM = (
        "uphill_sustained_vam"
    )

    TRAIL_DURABILITY = "trail_durability"


class PhysiologicalTestType(StrEnum):
    """Protocoles reconnus par OpenCoach."""

    HALF_COOPER = "half_cooper"
    COOPER_12_MIN = "cooper_12_min"
    VAMEVAL = "vameval"

    THRESHOLD_20_MIN = "threshold_20_min"
    THRESHOLD_30_MIN = "threshold_30_min"

    CRITICAL_SPEED_MULTI_EFFORT = (
        "critical_speed_multi_effort"
    )

    UPHILL_6_MIN = "uphill_6_min"
    UPHILL_20_MIN = "uphill_20_min"
    INCREMENTRAIL = "incrementrail"

    TRAIL_DURABILITY = "trail_durability"


class PhysiologicalTestAcquisitionMode(StrEnum):
    """Façon dont le résultat peut être obtenu."""

    SCHEDULED = "scheduled"
    PASSIVE = "passive"
    MANUAL = "manual"


class PhysiologicalTestEffortLevel(StrEnum):
    """Intensité demandée par le protocole."""

    SUBMAXIMAL = "submaximal"
    HARD = "hard"
    MAXIMAL = "maximal"


class PhysiologicalTestFatigueCost(StrEnum):
    """Coût relatif du protocole."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EvidenceLevel(StrEnum):
    """Nature du support du protocole.

    RESEARCH_PROTOCOL :
        protocole directement issu ou fortement adossé
        à une méthode publiée.

    FIELD_STANDARD :
        test terrain couramment utilisé pour l'évaluation.

    OPENCOACH_MONITORING :
        protocole standardisé par OpenCoach pour le suivi
        longitudinal. Il ne doit pas être présenté comme
        une mesure de laboratoire validée.
    """

    RESEARCH_PROTOCOL = "research_protocol"
    FIELD_STANDARD = "field_standard"
    OPENCOACH_MONITORING = (
        "opencoach_monitoring"
    )


class ActivityMetric(StrEnum):
    """Données nécessaires pour analyser un test."""

    DURATION = "duration"
    DISTANCE = "distance"

    PACE = "pace"
    SPEED = "speed"

    HEART_RATE = "heart_rate"
    HEART_RATE_STREAM = "heart_rate_stream"

    ELEVATION_GAIN = "elevation_gain"
    ELEVATION_STREAM = "elevation_stream"

    CADENCE = "cadence"
    POWER = "power"

    INTERVALS = "intervals"


@dataclass(frozen=True, slots=True)
class PhysiologicalTestProtocol:
    """Définition immuable d'un protocole de test."""

    id: PhysiologicalTestType

    name: str
    description: str

    disciplines: tuple[
        SportDiscipline,
        ...,
    ]

    target_metrics: tuple[
        PhysiologicalMetric,
        ...,
    ]

    acquisition_modes: tuple[
        PhysiologicalTestAcquisitionMode,
        ...,
    ]

    effort_level: PhysiologicalTestEffortLevel
    fatigue_cost: PhysiologicalTestFatigueCost

    replaces_quality_session: bool

    minimum_recovery_before_hours: int
    minimum_recovery_after_hours: int

    required_activity_metrics: tuple[
        ActivityMetric,
        ...,
    ]

    evidence_level: EvidenceLevel

    instructions: tuple[
        str,
        ...,
    ]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError(
                "Le nom du protocole est obligatoire."
            )

        if not self.disciplines:
            raise ValueError(
                "Un protocole doit concerner "
                "au moins une discipline."
            )

        if not self.target_metrics:
            raise ValueError(
                "Un protocole doit produire "
                "au moins une métrique."
            )

        if not self.acquisition_modes:
            raise ValueError(
                "Un protocole doit définir "
                "au moins un mode d'acquisition."
            )

        if (
            self.minimum_recovery_before_hours
            < 0
        ):
            raise ValueError(
                "La récupération avant le test "
                "ne peut pas être négative."
            )

        if (
            self.minimum_recovery_after_hours
            < 0
        ):
            raise ValueError(
                "La récupération après le test "
                "ne peut pas être négative."
            )
