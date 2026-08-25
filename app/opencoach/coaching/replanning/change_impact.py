"""Classification déterministe des changements de configuration.

Cette brique ne régénère aucun planning.

Elle répond uniquement à la question :

    jusqu'où le changement observé invalide-t-il
    la planification actuelle ?

Les niveaux sont ordonnés du moins au plus structurant.
"""

from __future__ import annotations

from enum import IntEnum

from opencoach.models import (
    AthleteProfile,
    Race,
)


class PlanningChangeImpact(IntEnum):
    """Niveau maximal de recalcul requis."""

    NONE = 0
    PRESCRIPTION = 1
    WEEK = 2
    TRAJECTORY = 3


def assess_profile_change(
    before: AthleteProfile,
    after: AthleteProfile,
) -> PlanningChangeImpact:
    """Évalue l'impact d'une modification du profil."""

    impact = PlanningChangeImpact.NONE

    if _physiology_changed(
        before,
        after,
    ):
        impact = max(
            impact,
            PlanningChangeImpact.PRESCRIPTION,
        )

    if _weekly_planning_changed(
        before,
        after,
    ):
        impact = max(
            impact,
            PlanningChangeImpact.WEEK,
        )

    return PlanningChangeImpact(
        impact
    )


def assess_race_change(
    before: Race,
    after: Race,
) -> PlanningChangeImpact:
    """Évalue l'impact d'une modification de course."""

    trajectory_fields = (
        "date",
        "race_type",
        "priority",
        "distance_km",
        "elevation_gain_m",
        "target_time_minutes",
        "status",
    )

    if any(
        getattr(before, field)
        != getattr(after, field)
        for field in trajectory_fields
    ):
        return (
            PlanningChangeImpact.TRAJECTORY
        )

    return PlanningChangeImpact.NONE


def _physiology_changed(
    before: AthleteProfile,
    after: AthleteProfile,
) -> bool:
    """Détecte un changement modifiant la prescription d'intensité."""

    fields = (
        "max_heart_rate",
        "resting_heart_rate",
        "vma",
        "threshold_heart_rate_1",
        "threshold_heart_rate_2",
    )

    return any(
        getattr(
            before.physiology,
            field,
        )
        != getattr(
            after.physiology,
            field,
        )
        for field in fields
    )


def _weekly_planning_changed(
    before: AthleteProfile,
    after: AthleteProfile,
) -> bool:
    """Détecte un changement structurant la semaine."""

    fields = (
        "weekly_sessions",
        "weekly_duration_minutes",
        "weekly_distance_km",
        "available_days",
        "fatigue_threshold",
        "experience",
    )

    return any(
        getattr(
            before.training,
            field,
        )
        != getattr(
            after.training,
            field,
        )
        for field in fields
    )
