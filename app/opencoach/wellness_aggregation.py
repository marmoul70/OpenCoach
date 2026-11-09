"""Agrégation canonique des données Wellness importées dans OpenCoach.

Les fournisseurs sont des origines d'import, jamais des sources consultées par
les services métier. Chaque métrique est consolidée indépendamment par journée.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from opencoach.models import WellnessDay


WELLNESS_METRIC_FIELDS: tuple[str, ...] = (
    "fitness_ctl", "fatigue_atl", "ramp_rate",
    "resting_hr", "avg_hr", "min_hr", "max_hr",
    "hrv", "hrv_baseline", "stress_avg",
    "sleep_seconds", "sleep_score", "sleep_quality",
    "sleep_deep_seconds", "sleep_light_seconds",
    "sleep_rem_seconds", "sleep_awake_seconds",
    "avg_sleeping_hr", "min_sleeping_hr", "max_sleeping_hr",
    "spo2", "steps",
)


@dataclass(frozen=True, slots=True)
class WellnessAggregation:
    """Journées consolidées et traçabilité des valeurs retenues."""

    days: tuple[WellnessDay, ...]
    metric_sources: dict[str, dict[str, tuple[str, ...]]]
    conflicts: dict[str, tuple[str, ...]]


def _timestamp(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    # Les dates sans fuseau sont traitées comme UTC pour une comparaison stable.
    if value.tzinfo is None:
        from datetime import timezone
        return value.replace(tzinfo=timezone.utc)
    return value


def aggregate_wellness_days(days: list[WellnessDay]) -> WellnessAggregation:
    """Fusionne les lignes de tous les fournisseurs stockées dans OpenCoach.

    Une métrique est choisie indépendamment des autres. La mesure ayant la date
    de mise à jour fournisseur la plus récente est retenue. Si plusieurs valeurs
    concurrentes ont la même fraîcheur (ou aucune date de mise à jour), la
    métrique est laissée inconnue plutôt que choisie arbitrairement.
    """
    grouped: dict[date, list[WellnessDay]] = {}
    for item in days:
        grouped.setdefault(item.date, []).append(item)

    merged_days: list[WellnessDay] = []
    all_sources: dict[str, dict[str, tuple[str, ...]]] = {}
    all_conflicts: dict[str, tuple[str, ...]] = {}

    for day in sorted(grouped):
        rows = grouped[day]
        values: dict[str, Any] = {}
        sources: dict[str, tuple[str, ...]] = {}
        conflicts: list[str] = []
        for field in WELLNESS_METRIC_FIELDS:
            candidates = [row for row in rows if getattr(row, field) is not None]
            if not candidates:
                continue
            dated = [(row, _timestamp(row.provider_updated_at)) for row in candidates]
            freshest = max((stamp for _, stamp in dated if stamp is not None), default=None)
            winners = [
                row for row, stamp in dated
                if stamp == freshest
            ] if freshest is not None else candidates
            distinct = {getattr(row, field) for row in winners}
            if len(distinct) > 1:
                conflicts.append(field)
                continue
            values[field] = getattr(winners[0], field)
            sources[field] = tuple(sorted({row.provider for row in winners}))

        timestamps = [
            stamp for stamp in (_timestamp(row.provider_updated_at) for row in rows)
            if stamp is not None
        ]
        merged_days.append(WellnessDay(
            provider="opencoach",
            date=day,
            provider_updated_at=max(timestamps) if timestamps else None,
            **values,
        ))
        all_sources[day.isoformat()] = sources
        if conflicts:
            all_conflicts[day.isoformat()] = tuple(sorted(conflicts))

    return WellnessAggregation(
        days=tuple(merged_days),
        metric_sources=all_sources,
        conflicts=all_conflicts,
    )
