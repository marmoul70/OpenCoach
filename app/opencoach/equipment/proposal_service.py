"""Construction des propositions de matériel OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence

from opencoach.equipment.activity_classification import (
    ActivityEquipmentCategory,
    classify_activity,
)
from opencoach.equipment.selection_service import (
    EquipmentSelectionService,
)
from opencoach.models.activity import Activity
from opencoach.models.profile import Shoe


@dataclass(frozen=True)
class ShoeEquipmentProposal:
    """Proposition de chaussure avant validation d'une activité."""

    activity_category: ActivityEquipmentCategory
    selected_shoe_id: str | None
    compatible_shoe_ids: tuple[str, ...]


class EquipmentProposalService:
    """Construit le matériel proposé à l'athlète."""

    def __init__(
        self,
        selection_service: EquipmentSelectionService | None = None,
    ) -> None:
        self.selection_service = (
            selection_service
            or EquipmentSelectionService()
        )

    def propose_shoe(
        self,
        *,
        activity: Activity,
        shoes: Sequence[Shoe],
    ) -> ShoeEquipmentProposal:
        """Construit la proposition de chaussure d'une activité.

        La proposition n'est jamais une affectation définitive.
        L'athlète peut encore modifier son choix avant validation.
        """

        category = classify_activity(
            activity
        )

        compatible = tuple(
            shoe
            for shoe in shoes
            if self._is_compatible(
                shoe=shoe,
                activity_category=category,
            )
        )

        selected = self.selection_service.select_shoe(
            activity_category=category,
            shoes=compatible,
        )

        return ShoeEquipmentProposal(
            activity_category=category,
            selected_shoe_id=(
                selected.id
                if selected is not None
                else None
            ),
            compatible_shoe_ids=tuple(
                shoe.id
                for shoe in compatible
            ),
        )

    @staticmethod
    def _is_compatible(
        *,
        shoe: Shoe,
        activity_category: ActivityEquipmentCategory,
    ) -> bool:
        if not shoe.active:
            return False

        if (
            activity_category
            is ActivityEquipmentCategory.TRAIL_RUNNING
        ):
            return shoe.category in {
                "trail",
                "mixed",
            }

        if (
            activity_category
            is ActivityEquipmentCategory.ROAD_RUNNING
        ):
            return shoe.category in {
                "road",
                "mixed",
            }

        return False
