from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
)

from .availability import (
    DayAvailability,
    resolve_day_availability,
)


@dataclass(frozen=True)
class WeeklyAvailability:
    """Disponibilité effective de l'athlète sur une semaine."""

    start_date: date
    end_date: date
    days: tuple[DayAvailability, ...]

    def get_day(
        self,
        target_date: date,
    ) -> DayAvailability | None:
        """Retourne la disponibilité d'une date de la semaine."""

        return next(
            (
                day
                for day in self.days
                if day.date == target_date
            ),
            None,
        )

    def training_days(
        self,
    ) -> tuple[DayAvailability, ...]:
        """Retourne tous les jours où un entraînement est possible."""

        return tuple(
            day
            for day in self.days
            if day.training_allowed
        )

    def preferred_training_days(
        self,
    ) -> tuple[DayAvailability, ...]:
        """Retourne les jours préférés actuellement utilisables."""

        return tuple(
            day
            for day in self.days
            if (
                day.training_allowed
                and day.preferred
            )
        )

    def alternative_training_days(
        self,
    ) -> tuple[DayAvailability, ...]:
        """Retourne les jours possibles hors préférences habituelles."""

        return tuple(
            day
            for day in self.days
            if (
                day.training_allowed
                and not day.preferred
            )
        )


def build_weekly_availability(
    *,
    athlete: AthleteProfile,
    week_start: date,
    constraints: tuple[AthleteConstraint, ...] = (),
) -> WeeklyAvailability:
    """Construit les disponibilités effectives de sept jours."""

    days = tuple(
        resolve_day_availability(
            athlete=athlete,
            target_date=(
                week_start
                + timedelta(days=offset)
            ),
            constraints=constraints,
        )
        for offset in range(7)
    )

    return WeeklyAvailability(
        start_date=week_start,
        end_date=(
            week_start
            + timedelta(days=6)
        ),
        days=days,
    )
