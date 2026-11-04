"""Synthèse descriptive de récupération, sans seuils médicaux arbitraires.

Ce module expose les observations physiologiques, la charge et le ressenti
séparément. Il ne transforme pas les mesures en diagnostic ni en score.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from statistics import fmean, median

from opencoach.models import DailyContext, WellnessDay


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


METRICS: tuple[str, ...] = (
    "hrv",
    "hrv_baseline",
    "resting_hr",
    "avg_sleeping_hr",
    "stress_avg",
    "sleep_seconds",
    "sleep_score",
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
    windows: tuple[int, ...] = (7, 14, 30),
) -> RecoveryAssessment:
    """Construit des fenêtres 7/14/30 j, en conservant la provenance."""

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
    )



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
