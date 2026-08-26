"""Impact des courses préparatoires sur la trajectoire OpenCoach.

Une course `training` ne pilote pas le pic de forme principal.
Elle constitue néanmoins un événement physiologique pouvant modifier
localement la trajectoire avant, pendant et après la compétition.

L'impact est évalué relativement à l'historique récent de l'athlète.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

from opencoach.models import Race
from opencoach.planning.history.metrics import (
    TrainingHistoryMetrics,
)
from opencoach.planning.trajectory.event import (
    EventImpact,
    RacePriority,
    TrajectoryEvent,
    TrajectoryEventType,
)


@dataclass(frozen=True, slots=True)
class TrainingRaceImpact:
    """Impact physiologique estimé d'une course préparatoire."""

    impact: EventImpact

    distance_ratio: float | None
    elevation_ratio: float | None

    preparation_days: int
    recovery_days: int

    race_priority: RacePriority


def _safe_ratio(
    value: float | None,
    reference: float | None,
) -> float | None:
    if (
        value is None
        or reference is None
        or reference <= 0
    ):
        return None

    return value / reference


def _absolute_fallback_impact(
    race: Race,
) -> EventImpact:
    """Politique conservatrice lorsque l'historique est insuffisant."""

    elevation = (
        race.elevation_gain_m
        or 0.0
    )

    if (
        race.distance_km >= 42.0
        or elevation >= 2000.0
    ):
        return EventImpact.CRITICAL

    if (
        race.distance_km >= 25.0
        or elevation >= 1000.0
    ):
        return EventImpact.HIGH

    if (
        race.distance_km >= 10.0
        or elevation >= 400.0
    ):
        return EventImpact.MODERATE

    return EventImpact.LOW


def evaluate_training_race_impact(
    *,
    race: Race,
    history_metrics: TrainingHistoryMetrics,
) -> TrainingRaceImpact:
    """Évalue une course préparatoire relativement à l'athlète."""

    if race.priority != "training":
        raise ValueError(
            "L'évaluation concerne uniquement les courses training."
        )

    weekly_distance = (
        history_metrics
        .last_28_days
        .distance_km
    )

    weekly_elevation = (
        history_metrics
        .last_28_days
        .elevation_gain_m
    )

    distance_ratio = _safe_ratio(
        race.distance_km,
        weekly_distance,
    )

    elevation_ratio = _safe_ratio(
        race.elevation_gain_m,
        weekly_elevation,
    )

    ratios = tuple(
        value
        for value in (
            distance_ratio,
            elevation_ratio,
        )
        if value is not None
    )

    if ratios:
        relative_demand = max(
            ratios
        )

        if relative_demand >= 0.80:
            impact = EventImpact.CRITICAL

        elif relative_demand >= 0.50:
            impact = EventImpact.HIGH

        elif relative_demand >= 0.25:
            impact = EventImpact.MODERATE

        else:
            impact = EventImpact.LOW

    else:
        impact = (
            _absolute_fallback_impact(
                race
            )
        )

    if impact is EventImpact.CRITICAL:
        preparation_days = 6
        recovery_days = 6
        priority = RacePriority.B

    elif impact is EventImpact.HIGH:
        preparation_days = 4
        recovery_days = 3
        priority = RacePriority.B

    elif impact is EventImpact.MODERATE:
        preparation_days = 2
        recovery_days = 1
        priority = RacePriority.C

    else:
        preparation_days = 0
        recovery_days = 0
        priority = RacePriority.C

    return TrainingRaceImpact(
        impact=impact,
        distance_ratio=distance_ratio,
        elevation_ratio=elevation_ratio,
        preparation_days=(
            preparation_days
        ),
        recovery_days=(
            recovery_days
        ),
        race_priority=priority,
    )


def build_training_race_event(
    *,
    race: Race,
    history_metrics: TrainingHistoryMetrics,
) -> TrajectoryEvent:
    """Transforme une course training en événement de trajectoire."""

    assessment = (
        evaluate_training_race_impact(
            race=race,
            history_metrics=(
                history_metrics
            ),
        )
    )

    event_id = (
        f"training-race:"
        f"{race.id or race.date.isoformat()}"
    )

    return TrajectoryEvent(
        event_id=event_id,
        event_type=(
            TrajectoryEventType.RACE
        ),
        start_date=(
            race.date
            - timedelta(
                days=assessment.preparation_days
            )
        ),
        end_date=(
            race.date
            + timedelta(
                days=assessment.recovery_days
            )
        ),
        impact=assessment.impact,
        race_priority=(
            assessment.race_priority
        ),
        athlete_imposed=True,
        notes=(
            f"Course préparatoire : {race.name}."
        ),
    )


def build_training_race_events(
    *,
    races: tuple[Race, ...],
    history_metrics: TrainingHistoryMetrics,
) -> tuple[TrajectoryEvent, ...]:
    """Construit les événements des courses préparatoires connues."""

    return tuple(
        build_training_race_event(
            race=race,
            history_metrics=(
                history_metrics
            ),
        )
        for race in races
        if (
            race.priority == "training"
            and race.status in {
                "planned",
                "completed",
            }
        )
    )


def build_training_race_protection_dates(
    *,
    race: Race,
    history_metrics: TrainingHistoryMetrics,
) -> tuple[
    date,
    ...,
]:
    """Retourne les jours à protéger avant une course préparatoire.

    Le jour de course n'est pas inclus ici : il est réservé
    séparément par le calendrier.
    """

    assessment = (
        evaluate_training_race_impact(
            race=race,
            history_metrics=(
                history_metrics
            ),
        )
    )

    return tuple(
        race.date
        - timedelta(days=offset)
        for offset in range(
            assessment.preparation_days,
            0,
            -1,
        )
    )


def build_training_race_protection_dates_for_races(
    *,
    races: tuple[Race, ...],
    history_metrics: TrainingHistoryMetrics,
) -> tuple[
    date,
    ...,
]:
    """Agrège les fenêtres de protection des courses préparatoires."""

    protected_dates: set[
        date
    ] = set()

    for race in races:
        if (
            race.priority != "training"
            or race.status != "planned"
        ):
            continue

        protected_dates.update(
            build_training_race_protection_dates(
                race=race,
                history_metrics=(
                    history_metrics
                ),
            )
        )

    return tuple(
        sorted(
            protected_dates
        )
    )


def build_training_race_recovery_dates(
    *,
    race: Race,
    history_metrics: TrainingHistoryMetrics,
) -> tuple[
    date,
    ...,
]:
    """Retourne les jours protégés après une course préparatoire."""

    assessment = (
        evaluate_training_race_impact(
            race=race,
            history_metrics=(
                history_metrics
            ),
        )
    )

    return tuple(
        race.date
        + timedelta(days=offset)
        for offset in range(
            1,
            assessment.recovery_days + 1,
        )
    )


def build_training_race_recovery_dates_for_races(
    *,
    races: tuple[Race, ...],
    history_metrics: TrainingHistoryMetrics,
) -> tuple[
    date,
    ...,
]:
    """Agrège les fenêtres de récupération post-course."""

    recovery_dates: set[
        date
    ] = set()

    for race in races:
        if (
            race.priority != "training"
            or race.status
            not in {
                "planned",
                "completed",
            }
        ):
            continue

        recovery_dates.update(
            build_training_race_recovery_dates(
                race=race,
                history_metrics=(
                    history_metrics
                ),
            )
        )

    return tuple(
        sorted(
            recovery_dates
        )
    )
