"""Synthèse descriptive de récupération, sans seuils médicaux arbitraires.

Ce module expose les observations physiologiques, la charge et le ressenti
séparément. Il ne transforme pas les mesures en diagnostic ni en score.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import isfinite
from statistics import fmean, median

from opencoach.coaching.daily_checkin import AthleteDailyCheckIn
from opencoach.models import DailyContext, WellnessDay
from opencoach.wellness_aggregation import WellnessAggregation


@dataclass(frozen=True, slots=True)
class RecoveryMetricSummary:
    """Résumé descriptif d'une métrique sur une fenêtre."""

    current: float | None
    average: float | None
    median: float | None
    sample_count: int
    coverage_days: int
    expected_days: int


@dataclass(frozen=True, slots=True)
class RecoveryWindow:
    """Fenêtre temporelle et mesures disponibles."""

    days: int
    start_date: date
    end_date: date
    recorded_days: int
    coverage_ratio: float
    metrics: dict[str, RecoveryMetricSummary]


@dataclass(frozen=True, slots=True)
class RecoveryTimeSeriesMetric:
    """Statistiques descriptives d'une série COROS horodatée."""

    metric: str
    unit: str | None
    current: float
    average: float
    median: float
    minimum: float
    maximum: float
    sample_count: int
    coverage_days: int
    first_measured_at: str
    last_measured_at: str
    statuses: tuple[str, ...]
    source_categories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectiveRecovery:
    """Ressenti saisi par l'athlète, non inféré des capteurs."""

    date: date
    fatigue: int
    pain: int
    illness_status: str
    treatment_impact: str
    motivation: int


@dataclass(frozen=True, slots=True)
class RecoveryAssessment:
    """Synthèse descriptive destinée au tableau de bord et au coach."""

    date: date
    provider: str
    source_date: date | None
    data_age_days: int | None
    data_status: str
    windows: tuple[RecoveryWindow, ...]
    subjective: SubjectiveRecovery | None
    time_series: tuple[RecoveryTimeSeriesMetric, ...] = ()


METRICS: tuple[str, ...] = (
    "hrv",
    "hrv_baseline",
    "resting_hr",
    "avg_hr",
    "min_hr",
    "max_hr",
    "avg_sleeping_hr",
    "stress_avg",
    "sleep_seconds",
    "sleep_score",
    "sleep_quality",
    "spo2",
    "sleep_deep_seconds",
    "sleep_light_seconds",
    "sleep_rem_seconds",
    "sleep_awake_seconds",
    "fatigue_atl",
    "fitness_ctl",
)


def build_recovery_assessment(
    *,
    wellness_days: list[WellnessDay],
    target_date: date,
    provider: str,
    subjective_context: DailyContext | None = None,
    time_series_snapshots: list[dict] | None = None,
    windows: tuple[int, ...] = (7, 14, 30),
) -> RecoveryAssessment:
    """Construit les fenêtres quotidiennes et les séries temporelles COROS."""

    ordered = sorted(
        (
            item for item in wellness_days
            if item.provider == provider and item.date <= target_date
        ),
        key=lambda item: item.date,
    )
    latest = ordered[-1] if ordered else None
    source_date = latest.date if latest is not None else None
    age = (target_date - source_date).days if source_date else None
    status = "unavailable" if age is None else ("fresh" if age == 0 else "stale")

    summaries: list[RecoveryWindow] = []
    for window_days in windows:
        if window_days < 1:
            raise ValueError("Les fenêtres doivent être positives.")
        start = target_date - timedelta(days=window_days - 1)
        selected = [item for item in ordered if start <= item.date <= target_date]
        recorded_days = len({item.date for item in selected})
        metrics: dict[str, RecoveryMetricSummary] = {}
        for metric in METRICS:
            values = [
                (item.date, float(value))
                for item in selected
                if (value := getattr(item, metric)) is not None
            ]
            values.sort(key=lambda pair: pair[0])
            raw = [value for _, value in values]
            metrics[metric] = RecoveryMetricSummary(
                current=raw[-1] if raw else None,
                average=fmean(raw) if raw else None,
                median=float(median(raw)) if raw else None,
                sample_count=len(raw),
                coverage_days=len({day for day, _ in values}),
                expected_days=window_days,
            )
        summaries.append(
            RecoveryWindow(
                days=window_days,
                start_date=start,
                end_date=target_date,
                recorded_days=recorded_days,
                coverage_ratio=recorded_days / window_days,
                metrics=metrics,
            )
        )

    subjective = None
    if subjective_context is not None and subjective_context.date == target_date:
        subjective = SubjectiveRecovery(
            date=subjective_context.date,
            fatigue=subjective_context.fatigue_subjective,
            pain=subjective_context.pain_level,
            illness_status=subjective_context.illness_status,
            treatment_impact=subjective_context.treatment_impact,
            motivation=subjective_context.motivation,
        )

    return RecoveryAssessment(
        date=target_date,
        provider=provider,
        source_date=source_date,
        data_age_days=age,
        data_status=status,
        windows=tuple(summaries),
        subjective=subjective,
        time_series=aggregate_coros_time_series(
            time_series_snapshots or [],
            start_date=target_date - timedelta(days=29),
            end_date=target_date,
        ),
    )


def aggregate_coros_time_series(
    snapshots: list[dict],
    *,
    start_date: date,
    end_date: date,
) -> tuple[RecoveryTimeSeriesMetric, ...]:
    """Agrège les échantillons normalisés en dédupliquant les sources qui se recouvrent."""

    samples: dict[tuple[str, str | None], dict[tuple[str, float], dict]] = {}
    allowed_categories = {
        "hrv_timeseries",
        "stress_points",
        "health_check_points",
    }

    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        category = snapshot.get("category")
        payload = snapshot.get("payload")
        if category not in allowed_categories or not isinstance(payload, dict):
            continue
        raw_samples = payload.get("samples")
        if not isinstance(raw_samples, list):
            continue

        for sample in raw_samples:
            if not isinstance(sample, dict):
                continue
            metric = sample.get("metric")
            measured_at_raw = sample.get("measured_at")
            raw_value = sample.get("value")
            if not isinstance(metric, str) or not isinstance(measured_at_raw, str):
                continue
            try:
                measured_at = datetime.fromisoformat(
                    measured_at_raw.replace("Z", "+00:00")
                )
                value = float(raw_value)
            except (TypeError, ValueError):
                continue
            source_date_raw = sample.get("source_date")
            try:
                sample_date = (
                    date.fromisoformat(source_date_raw)
                    if isinstance(source_date_raw, str)
                    else measured_at.date()
                )
            except ValueError:
                sample_date = measured_at.date()
            if not isfinite(value) or not start_date <= sample_date <= end_date:
                continue

            unit = sample.get("unit")
            if not isinstance(unit, str):
                unit = None
            key = (measured_at.isoformat(), value)
            bucket = samples.setdefault((metric, unit), {})
            existing = bucket.get(key)
            if existing is None:
                bucket[key] = {
                    "measured_at": measured_at,
                    "source_date": sample_date,
                    "value": value,
                    "unit": unit,
                    "status": sample.get("status"),
                    "categories": {category},
                }
            else:
                # Une même mesure peut être renvoyée par HRV et Health Check.
                existing["categories"].add(category)

    result: list[RecoveryTimeSeriesMetric] = []
    for (metric, unit), unique_samples in sorted(
        samples.items(),
        key=lambda item: (item[0][0], item[0][1] or ""),
    ):
        values = sorted(
            unique_samples.values(),
            key=lambda item: item["measured_at"],
        )
        if not values:
            continue
        numeric = [item["value"] for item in values]
        statuses = tuple(sorted({
            item["status"]
            for item in values
            if isinstance(item["status"], str) and item["status"]
        }))
        categories = tuple(sorted({
            category
            for item in values
            for category in item["categories"]
        }))
        result.append(
            RecoveryTimeSeriesMetric(
                metric=metric,
                unit=unit,
                current=numeric[-1],
                average=fmean(numeric),
                median=float(median(numeric)),
                minimum=min(numeric),
                maximum=max(numeric),
                sample_count=len(values),
                coverage_days=len({
                    item["source_date"] for item in values
                }),
                first_measured_at=values[0]["measured_at"].isoformat(),
                last_measured_at=values[-1]["measured_at"].isoformat(),
                statuses=statuses,
                source_categories=categories,
            )
        )
    return tuple(result)


def recovery_assessment_to_dict(
    assessment: RecoveryAssessment,
) -> dict:
    """Sérialise le contrat partagé par les API Wellness et Coach."""
    return {
        "date": assessment.date.isoformat(),
        "provider": assessment.provider,
        "source_date": assessment.source_date.isoformat() if assessment.source_date else None,
        "data_age_days": assessment.data_age_days,
        "data_status": assessment.data_status,
        "windows": [
            {
                "days": window.days,
                "start_date": window.start_date.isoformat(),
                "end_date": window.end_date.isoformat(),
                "recorded_days": window.recorded_days,
                "coverage_ratio": window.coverage_ratio,
                "metrics": {
                    name: {
                        "current": metric.current,
                        "average": metric.average,
                        "median": metric.median,
                        "sample_count": metric.sample_count,
                        "coverage_days": metric.coverage_days,
                        "expected_days": metric.expected_days,
                    }
                    for name, metric in window.metrics.items()
                },
            }
            for window in assessment.windows
        ],
        "time_series": [
            {
                "metric": item.metric,
                "unit": item.unit,
                "current": item.current,
                "average": item.average,
                "median": item.median,
                "minimum": item.minimum,
                "maximum": item.maximum,
                "sample_count": item.sample_count,
                "coverage_days": item.coverage_days,
                "first_measured_at": item.first_measured_at,
                "last_measured_at": item.last_measured_at,
                "statuses": list(item.statuses),
                "source_categories": list(item.source_categories),
            }
            for item in assessment.time_series
        ],
        "subjective": (
            {
                "date": assessment.subjective.date.isoformat(),
                "fatigue": assessment.subjective.fatigue,
                "pain": assessment.subjective.pain,
                "illness_status": assessment.subjective.illness_status,
                "treatment_impact": assessment.subjective.treatment_impact,
                "motivation": assessment.subjective.motivation,
            }
            if assessment.subjective is not None
            else None
        ),
    }



def recovery_coach_summary_to_dict(
    assessment: RecoveryAssessment,
    aggregation: WellnessAggregation,
    daily_checkin: AthleteDailyCheckIn | None = None,
) -> dict:
    """Construit le résumé descriptif de récupération partagé par les interfaces Coach.

    La sélection des métriques, la fenêtre récente, la couverture, la provenance
    et les avertissements sont des règles du domaine, pas de l'adaptateur IA.
    """
    analysis_metrics = {
        "hrv", "resting_hr", "sleep_seconds", "sleep_score", "sleep_quality",
        "stress_avg", "spo2", "sleep_deep_seconds", "sleep_rem_seconds",
        "fatigue_atl", "fitness_ctl",
    }
    duration_metrics = {
        "sleep_seconds", "sleep_deep_seconds", "sleep_rem_seconds",
    }

    def format_duration(value: float | int | None) -> str | None:
        if value is None:
            return None
        total_minutes = round(float(value) / 60)
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours} h {minutes:02d} min"

    windows = []
    for window in assessment.windows:
        if window.days != 7:
            continue
        metrics = {}
        for name, metric in window.metrics.items():
            if name not in analysis_metrics:
                continue
            if metric.sample_count <= 0:
                metrics[name] = {"current": None, "sample_count": 0}
            elif name in duration_metrics:
                metrics[name] = {
                    "current": format_duration(metric.current),
                    "average": format_duration(metric.average),
                    "median": format_duration(metric.median),
                    "unit": "heures et minutes",
                    "sample_count": metric.sample_count,
                    "coverage_days": metric.coverage_days,
                    "expected_days": metric.expected_days,
                }
            else:
                metrics[name] = {
                    "current": metric.current,
                    "average": metric.average,
                    "median": metric.median,
                    "sample_count": metric.sample_count,
                    "coverage_days": metric.coverage_days,
                    "expected_days": metric.expected_days,
                }
        windows.append({
            "days": window.days,
            "start_date": window.start_date.isoformat(),
            "end_date": window.end_date.isoformat(),
            "recorded_days": window.recorded_days,
            "coverage_ratio": round(window.coverage_ratio, 3),
            "metrics": metrics,
        })

    available_metrics = sorted({
        metric
        for day_sources in aggregation.metric_sources.values()
        for metric in day_sources
        if metric in analysis_metrics
    })
    metric_sources = {
        metric: sorted({
            source
            for day_sources in aggregation.metric_sources.values()
            for source in day_sources.get(metric, ())
        })
        for metric in available_metrics
    }
    metric_source_days = {
        metric: sum(
            1 for day_sources in aggregation.metric_sources.values()
            if metric in day_sources
        )
        for metric in available_metrics
    }

    checkin_payload = None
    if daily_checkin is not None:
        checkin_payload = {
            "date": daily_checkin.date.isoformat(),
            "energy_rating": daily_checkin.energy_rating,
            "pain_wellness_rating": daily_checkin.pain_wellness_rating,
            "illness": daily_checkin.illness,
            "unavailable": daily_checkin.unavailable,
            "pain_locations": [
                {"area": item.area.value, "side": item.side.value}
                for item in daily_checkin.pain_locations
            ],
        }

    subjective = None
    if assessment.subjective is not None:
        subjective = {
            "date": assessment.subjective.date.isoformat(),
            "fatigue": assessment.subjective.fatigue,
            "pain": assessment.subjective.pain,
            "illness_status": assessment.subjective.illness_status,
            "treatment_impact": assessment.subjective.treatment_impact,
            "motivation": assessment.subjective.motivation,
        }

    warnings = []
    if aggregation.conflicts:
        warnings.append(
            "Des valeurs concurrentes de fraîcheur identique ont été écartées : "
            + str(aggregation.conflicts)
        )
    if assessment.data_status == "unavailable":
        warnings.append("Aucune donnée Wellness disponible sur la période.")
    elif assessment.data_status == "stale":
        warnings.append(
            f"Dernière donnée Wellness le {assessment.source_date.isoformat()} "
            f"(J-{assessment.data_age_days})."
        )
    if checkin_payload is None and subjective is None:
        warnings.append(
            "Aucun ressenti subjectif enregistré pour cette date. "
            "Demander à l'athlète comment il se sent ; ne rien déduire."
        )
    if windows and windows[0]["coverage_ratio"] < 0.7:
        warnings.append(
            "Couverture Wellness inférieure à 70 % sur 7 jours ; "
            "interpréter les tendances avec prudence."
        )

    metric_definitions = {
        "hrv": {"label": "Variabilité de la fréquence cardiaque", "unit": "ms"},
        "resting_hr": {"label": "Fréquence cardiaque au repos", "unit": "bpm"},
        "stress_avg": {"label": "Stress moyen", "unit": "score COROS"},
        "sleep_seconds": {"label": "Durée totale de sommeil", "unit": "heures et minutes"},
        "sleep_score": {"label": "Score de sommeil", "unit": "score COROS"},
        "sleep_quality": {"label": "Qualité du sommeil", "unit": "score COROS"},
        "spo2": {"label": "Saturation périphérique en oxygène", "unit": "%"},
        "sleep_deep_seconds": {"label": "Sommeil profond", "unit": "heures et minutes"},
        "sleep_rem_seconds": {"label": "Sommeil paradoxal (REM)", "unit": "heures et minutes"},
        "fatigue_atl": {"label": "Charge aiguë COROS (ATL)", "unit": "points COROS"},
        "fitness_ctl": {"label": "Charge chronique COROS (CTL)", "unit": "points COROS"},
    }

    return {
        "target_date": assessment.date.isoformat(),
        "data_store": "OpenCoach",
        "metric_definitions": metric_definitions,
        "provider": "opencoach" if assessment.source_date is not None else None,
        "metric_sources": metric_sources,
        "metric_source_days": metric_source_days,
        "conflicting_metrics": aggregation.conflicts,
        "source_date": (
            assessment.source_date.isoformat()
            if assessment.source_date is not None else None
        ),
        "data_age_days": assessment.data_age_days,
        "data_status": assessment.data_status,
        "windows": windows,
        "daily_context": subjective,
        "daily_checkin": checkin_payload,
        "warnings": warnings,
    }
