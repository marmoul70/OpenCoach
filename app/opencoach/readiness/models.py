from dataclasses import dataclass
from datetime import date
from typing import Literal

@dataclass(frozen=True)
class MetricBaseline:
    """Baseline personnelle d'une métrique physiologique."""

    median: float | None
    sample_count: int
    reliable: bool


@dataclass(frozen=True)
class ReadinessBaseline:
    """Baselines personnelles utilisées par le moteur Readiness."""

    start_date: date
    end_date: date

    hrv: MetricBaseline
    resting_hr: MetricBaseline
    sleep_seconds: MetricBaseline
    sleep_score: MetricBaseline

ReadinessLevel = Literal[
    "very_low",
    "low",
    "moderate",
    "good",
    "high",
]

SignalLevel = Literal[
    "normal",
    "warning",
    "critical",
    "unavailable",
]


@dataclass(frozen=True)
class ReadinessSignal:
    """Évaluation d'un signal individuel de récupération."""

    metric: str
    level: SignalLevel

    reason: str

    current_value: float | None = None
    reference_value: float | None = None


@dataclass(frozen=True)
class DailyReadiness:
    """État global de disponibilité à l'entraînement."""

    score: float
    level: ReadinessLevel

    signals: tuple[ReadinessSignal, ...]

    warning_count: int
    critical_count: int

    training_constraints: tuple[str, ...]

    fitness_ctl: float | None
    fatigue_atl: float | None
    training_balance: float | None