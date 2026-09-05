"""Éligibilité déterministe de la clôture hebdomadaire.

La décision est volontairement indépendante de SQL, du scheduler
et des notifications.

La couche d'orchestration fournit les faits temporels observés,
puis ce module décide s'il faut attendre, clôturer normalement ou
forcer la clôture à l'heure limite.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import (
    date,
    datetime,
    time,
    timedelta,
)
from enum import StrEnum


class WeeklyClosureEligibility(StrEnum):
    """Décision de clôture de la semaine."""

    WAIT = "wait"
    CLOSE = "close"
    CUTOFF = "cutoff"


@dataclass(frozen=True, slots=True)
class WeeklyClosureEligibilityResult:
    """Résultat explicable de l'évaluation."""

    decision: WeeklyClosureEligibility
    reason: str


def evaluate_weekly_closure_eligibility(
    *,
    now: datetime,
    week_end: date,
    has_remaining_planned_session: bool,
    last_completed_at: datetime | None = None,
    opening_time: time = time(20, 0),
    cutoff_time: time = time(23, 45),
    sync_grace: timedelta = timedelta(
        minutes=15
    ),
) -> WeeklyClosureEligibilityResult:
    """Décide si le débrief hebdomadaire peut être clôturé.

    ``week_end`` représente le dimanche de la semaine évaluée.

    Avant l'ouverture, le service attend.

    Pendant la fenêtre normale :
    - une séance encore planifiée bloque la clôture ;
    - une séance récemment terminée déclenche une grâce de
      synchronisation ;
    - sinon la semaine peut être clôturée.

    À l'heure limite ou après, le système retourne ``CUTOFF`` :
    l'orchestrateur peut alors clôturer même si une synchronisation
    ou une séance reste imparfaitement reflétée dans les données.
    """

    if now.tzinfo is None:
        raise ValueError(
            "now doit être timezone-aware."
        )

    if (
        last_completed_at is not None
        and last_completed_at.tzinfo is None
    ):
        raise ValueError(
            "last_completed_at doit être timezone-aware."
        )

    if sync_grace < timedelta(0):
        raise ValueError(
            "sync_grace ne peut pas être négatif."
        )

    if cutoff_time <= opening_time:
        raise ValueError(
            "cutoff_time doit être postérieur "
            "à opening_time."
        )

    current_date = now.date()

    if current_date < week_end:
        return WeeklyClosureEligibilityResult(
            decision=WeeklyClosureEligibility.WAIT,
            reason=(
                "La semaine n'est pas encore terminée."
            ),
        )

    if current_date > week_end:
        return WeeklyClosureEligibilityResult(
            decision=WeeklyClosureEligibility.CUTOFF,
            reason=(
                "La date de fin de semaine est dépassée."
            ),
        )

    local_time = now.timetz().replace(
        tzinfo=None
    )

    if local_time < opening_time:
        return WeeklyClosureEligibilityResult(
            decision=WeeklyClosureEligibility.WAIT,
            reason=(
                "La fenêtre de clôture du dimanche "
                "n'est pas encore ouverte."
            ),
        )

    if local_time >= cutoff_time:
        return WeeklyClosureEligibilityResult(
            decision=WeeklyClosureEligibility.CUTOFF,
            reason=(
                "L'heure limite de clôture "
                "hebdomadaire est atteinte."
            ),
        )

    if has_remaining_planned_session:
        return WeeklyClosureEligibilityResult(
            decision=WeeklyClosureEligibility.WAIT,
            reason=(
                "Une séance du dimanche est encore "
                "planifiée."
            ),
        )

    if last_completed_at is not None:
        elapsed = now - last_completed_at

        if elapsed < timedelta(0):
            raise ValueError(
                "last_completed_at ne peut pas être "
                "postérieur à now."
            )

        if elapsed < sync_grace:
            remaining = (
                sync_grace - elapsed
            )

            remaining_minutes = max(
                1,
                int(
                    (
                        remaining.total_seconds()
                        + 59
                    )
                    // 60
                ),
            )

            return WeeklyClosureEligibilityResult(
                decision=WeeklyClosureEligibility.WAIT,
                reason=(
                    "Grâce de synchronisation active "
                    f"({remaining_minutes} min restantes)."
                ),
            )

    return WeeklyClosureEligibilityResult(
        decision=WeeklyClosureEligibility.CLOSE,
        reason=(
            "La semaine est terminée et aucune attente "
            "supplémentaire n'est nécessaire."
        ),
    )
