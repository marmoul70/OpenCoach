from dataclasses import dataclass
from datetime import date

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

    @property
    def has_training_history(self) -> bool:
        """Indique si l'historique contient au moins un effort réel."""
        return (
            self.last_84_days.sessions_count > 0
        )
