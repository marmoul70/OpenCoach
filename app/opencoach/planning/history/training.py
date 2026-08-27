from dataclasses import dataclass
from datetime import date
from uuid import UUID

from opencoach.models import Activity
from opencoach.training import TrainingStats


@dataclass(frozen=True)
class TrainingHistorySnapshot:
    """Photographie multi-fenêtres de l'historique récent d'entraînement."""

    reference_date: date

    last_7_days: TrainingStats
    last_28_days: TrainingStats
    last_42_days: TrainingStats
    last_84_days: TrainingStats

    activities_84_days: tuple[Activity, ...]

    # Fenêtres intermédiaires utilisées par la référence
    # hebdomadaire adaptative.
    #
    # Elles restent optionnelles pour conserver la compatibilité
    # avec les anciens constructeurs de TrainingHistorySnapshot.
    last_14_days: TrainingStats | None = None
    last_21_days: TrainingStats | None = None

    race_activity_ids: frozenset[UUID] = frozenset()

    @property
    def has_training_history(self) -> bool:
        """Indique si l'historique contient au moins un effort réel."""
        return (
            self.last_84_days.sessions_count > 0
        )