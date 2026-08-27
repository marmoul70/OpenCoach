"""Plan d'entraînement hebdomadaire persistant.

Ce modèle conserve l'intention produite par le moteur de planification
pour une semaine donnée.

Les données d'avancement telles que la charge réellement effectuée,
la projection de fin de semaine ou l'écart à la cible ne sont pas
persistées ici : elles sont recalculées dynamiquement.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class WeeklyTrainingPlan:
    """Référence persistante d'une semaine planifiée."""

    id: UUID | None

    athlete_profile_id: UUID

    week_start: date
    week_end: date

    phase: str
    week_type: str | None
    phase_week_index: int

    target_load: float | None
    load_min: float | None
    load_max: float | None

    reference_duration_minutes: float | None
    target_duration_minutes: float | None
    long_endurance_reference_minutes: float | None

    schedule_pressure: str
    athlete_schedule_constrained: bool

    generated_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.week_end < self.week_start:
            raise ValueError(
                "La fin de semaine ne peut pas précéder "
                "le début de semaine."
            )

        if self.phase_week_index < 1:
            raise ValueError(
                "L'indice de semaine dans la phase "
                "doit être supérieur ou égal à 1."
            )

        load_values = (
            self.target_load,
            self.load_min,
            self.load_max,
        )

        if any(
            value is not None
            and value < 0
            for value in load_values
        ):
            raise ValueError(
                "Les charges hebdomadaires "
                "ne peuvent pas être négatives."
            )

        if (
            self.load_min is not None
            and self.load_max is not None
            and self.load_min > self.load_max
        ):
            raise ValueError(
                "La charge minimale ne peut pas "
                "dépasser la charge maximale."
            )

        if (
            self.target_load is not None
            and self.load_min is not None
            and self.target_load < self.load_min
        ):
            raise ValueError(
                "La charge cible doit appartenir "
                "à la plage autorisée."
            )

        if (
            self.target_load is not None
            and self.load_max is not None
            and self.target_load > self.load_max
        ):
            raise ValueError(
                "La charge cible doit appartenir "
                "à la plage autorisée."
            )

        duration_values = (
            self.reference_duration_minutes,
            self.target_duration_minutes,
            self.long_endurance_reference_minutes,
        )

        if any(
            value is not None
            and value <= 0
            for value in duration_values
        ):
            raise ValueError(
                "Les durées hebdomadaires renseignées "
                "doivent être strictement positives."
            )

    @property
    def has_load_target(self) -> bool:
        """Indique si une cible de charge exploitable est disponible."""

        return (
            self.target_load is not None
            and self.target_load > 0
        )
