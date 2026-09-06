"""Sélection automatique du matériel OpenCoach.

La sélection appartient au domaine OpenCoach et ne dépend d'aucun
fournisseur de données externe.

Une sélection automatique est seulement une proposition. Le matériel
réellement utilisé sera confirmé par l'athlète lors de la validation
de la séance.
"""

from __future__ import annotations

from collections.abc import Sequence

from opencoach.equipment.activity_classification import (
    ActivityEquipmentCategory,
)
from opencoach.models.profile import Shoe


class EquipmentSelectionService:
    """Détermine le matériel à proposer pour une activité."""

    def select_shoe(
        self,
        *,
        activity_category: ActivityEquipmentCategory,
        shoes: Sequence[Shoe],
    ) -> Shoe | None:
        """Retourne la chaussure à présélectionner.

        Trail :
        - Trail préférée ;
        - Mixte préférée ;
        - unique Trail active ;
        - unique Mixte active.

        Route :
        - Route préférée ;
        - Mixte préférée ;
        - unique Route active ;
        - unique Mixte active.

        Les autres catégories d'activité ne sélectionnent aucune
        chaussure automatiquement.
        """

        if (
            activity_category
            is ActivityEquipmentCategory.TRAIL_RUNNING
        ):
            return self._select_by_categories(
                shoes=shoes,
                primary_category="trail",
                fallback_category="mixed",
            )

        if (
            activity_category
            is ActivityEquipmentCategory.ROAD_RUNNING
        ):
            return self._select_by_categories(
                shoes=shoes,
                primary_category="road",
                fallback_category="mixed",
            )

        return None

    @staticmethod
    def _select_by_categories(
        *,
        shoes: Sequence[Shoe],
        primary_category: str,
        fallback_category: str,
    ) -> Shoe | None:
        active_shoes = [
            shoe
            for shoe in shoes
            if shoe.active
        ]

        primary = [
            shoe
            for shoe in active_shoes
            if shoe.category == primary_category
        ]

        fallback = [
            shoe
            for shoe in active_shoes
            if shoe.category == fallback_category
        ]

        preferred_primary = [
            shoe
            for shoe in primary
            if shoe.preferred
        ]

        if len(preferred_primary) == 1:
            return preferred_primary[0]

        preferred_fallback = [
            shoe
            for shoe in fallback
            if shoe.preferred
        ]

        if len(preferred_fallback) == 1:
            return preferred_fallback[0]

        if len(primary) == 1:
            return primary[0]

        if len(fallback) == 1:
            return fallback[0]

        return None
