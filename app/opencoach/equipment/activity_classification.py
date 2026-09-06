"""Classification métier des activités pour le matériel OpenCoach.

Ce module appartient au domaine OpenCoach.

Il ne connaît aucun fournisseur externe (Intervals.icu, Suunto,
Garmin, etc.). Les adaptateurs fournisseurs doivent produire une
activité OpenCoach contenant un ``sport_type`` normalisé.

La classification permet ensuite aux services métier de déterminer
le type d'équipement compatible avec une activité.
"""

from __future__ import annotations

from enum import StrEnum

from opencoach.models.activity import Activity


class ActivityEquipmentCategory(StrEnum):
    """Catégorie métier utilisée pour l'affectation du matériel."""

    TRAIL_RUNNING = "trail_running"
    ROAD_RUNNING = "road_running"
    CYCLING = "cycling"
    OTHER = "other"


TRAIL_RUNNING_SPORT_TYPES = frozenset(
    {
        "TrailRun",
    }
)

ROAD_RUNNING_SPORT_TYPES = frozenset(
    {
        "Run",
    }
)

CYCLING_SPORT_TYPES = frozenset(
    {
        "Ride",
        "VirtualRide",
    }
)


def classify_activity(
    activity: Activity,
) -> ActivityEquipmentCategory:
    """Classe une activité selon les besoins matériel d'OpenCoach.

    Règles actuelles :

    - TrailRun -> chaussure Trail ;
    - Run -> chaussure Route ;
    - Ride / VirtualRide -> vélo ;
    - tout autre sport -> aucun équipement kilométrique automatique.

    Le classement est volontairement déterministe et indépendant
    du fournisseur de données.
    """

    return classify_sport_type(
        activity.sport_type,
    )


def classify_sport_type(
    sport_type: str,
) -> ActivityEquipmentCategory:
    """Classe un ``sport_type`` OpenCoach normalisé."""

    normalized = sport_type.strip()

    if normalized in TRAIL_RUNNING_SPORT_TYPES:
        return (
            ActivityEquipmentCategory
            .TRAIL_RUNNING
        )

    if normalized in ROAD_RUNNING_SPORT_TYPES:
        return (
            ActivityEquipmentCategory
            .ROAD_RUNNING
        )

    if normalized in CYCLING_SPORT_TYPES:
        return (
            ActivityEquipmentCategory
            .CYCLING
        )

    return ActivityEquipmentCategory.OTHER
