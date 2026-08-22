from dataclasses import dataclass
from datetime import date

from .weekly_availability import (
    WeeklyAvailability,
)


@dataclass(frozen=True)
class TrainingDayCandidate:
    """Jour candidat pour déplacer ou placer une séance."""

    date: date
    score: int

    preferred: bool
    requires_confirmation: bool

    running_allowed: bool
    cross_training_allowed: bool
    max_duration_minutes: int | None

    reasons: tuple[str, ...]


def rank_training_day_candidates(
    *,
    week: WeeklyAvailability,
    original_date: date,
    for_running: bool = True,
) -> tuple[TrainingDayCandidate, ...]:
    """Classe les jours disponibles autour d'une date initiale."""

    candidates: list[TrainingDayCandidate] = []

    for day in week.days:
        if day.date == original_date:
            continue

        if not day.training_allowed:
            continue

        if for_running and not day.running_allowed:
            continue

        if (
            not for_running
            and not day.cross_training_allowed
        ):
            continue

        score = 100
        reasons: list[str] = []

        distance_days = abs(
            (day.date - original_date).days
        )

        score -= distance_days * 25

        reasons.append(
            f"Écart de {distance_days} jour(s) avec la date initiale."
        )

        if day.preferred:
            score += 10

            reasons.append(
                "Jour habituel préféré par l'athlète."
            )

        if day.status == "available_override":
            score += 15

            reasons.append(
                "Disponibilité exceptionnelle confirmée."
            )

        if day.status == "limited":
            score -= 20

            reasons.append(
                "Disponibilité limitée."
            )

        if day.requires_confirmation:
            score -= 10

            reasons.append(
                "Jour non habituel à confirmer avec l'athlète."
            )

        if day.date > original_date:
            score += 2

            reasons.append(
                "Déplacement après la date initiale."
            )

        candidates.append(
            TrainingDayCandidate(
                date=day.date,
                score=score,
                preferred=day.preferred,
                requires_confirmation=(
                    day.requires_confirmation
                ),
                running_allowed=(
                    day.running_allowed
                ),
                cross_training_allowed=(
                    day.cross_training_allowed
                ),
                max_duration_minutes=(
                    day.max_duration_minutes
                ),
                reasons=tuple(reasons),
            )
        )

    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                -candidate.score,
                abs(
                    (
                        candidate.date
                        - original_date
                    ).days
                ),
                candidate.date,
            ),
        )
    )
