"""Contrat métier de l'analyse orientée objectif."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GoalType(StrEnum):
    """Famille d'objectif poursuivi par la séance."""

    ENDURANCE = "endurance"
    INTERVALS = "intervals"
    PHYSIOLOGICAL_TEST = "physiological_test"
    REST = "rest"
    GENERIC = "generic"


class MetricImportance(StrEnum):
    """Importance d'un indicateur pour l'objectif."""

    PRIMARY = "primary"
    SECONDARY = "secondary"
    INFORMATIONAL = "informational"


class GoalComplianceStatus(StrEnum):
    """Statuts destinés au débriefing utilisateur."""

    OK = "ok"
    ATTENTION = "attention"
    NON_COMPLIANT = "non_compliant"
    NOT_USED = "not_used"


@dataclass(frozen=True, slots=True)
class GoalMetricDefinition:
    """Rôle d'une métrique dans l'analyse de la séance."""

    key: str
    label: str
    importance: MetricImportance
    reason: str


@dataclass(frozen=True, slots=True)
class GoalAnalysisPlan:
    """Plan d'analyse déduit de l'objectif de la séance."""

    goal_type: GoalType
    objective: str

    metrics: tuple[
        GoalMetricDefinition,
        ...,
    ]

    expected_derived_results: tuple[
        str,
        ...,
    ] = ()

    @property
    def primary_metrics(
        self,
    ) -> tuple[
        GoalMetricDefinition,
        ...,
    ]:
        return tuple(
            metric
            for metric in self.metrics
            if (
                metric.importance
                is MetricImportance.PRIMARY
            )
        )

    @property
    def secondary_metrics(
        self,
    ) -> tuple[
        GoalMetricDefinition,
        ...,
    ]:
        return tuple(
            metric
            for metric in self.metrics
            if (
                metric.importance
                is MetricImportance.SECONDARY
            )
        )

    @property
    def informational_metrics(
        self,
    ) -> tuple[
        GoalMetricDefinition,
        ...,
    ]:
        return tuple(
            metric
            for metric in self.metrics
            if (
                metric.importance
                is MetricImportance.INFORMATIONAL
            )
        )

@dataclass(frozen=True, slots=True)
class GoalMetricAssessment:
    """Interprétation coaching d'un indicateur existant."""

    key: str
    label: str

    importance: MetricImportance
    status: GoalComplianceStatus

    target_minimum: float | None = None
    target_maximum: float | None = None
    unit: str | None = None

    actual_value: float | None = None
    delta: float | None = None
    delta_percent: float | None = None

    message: str | None = None


@dataclass(frozen=True, slots=True)
class SessionGoalAnalysis:
    """Débriefing d'une séance par rapport à son objectif."""

    goal_type: GoalType
    objective: str

    overall_status: GoalComplianceStatus

    metrics: tuple[
        GoalMetricAssessment,
        ...,
    ]

    strengths: tuple[str, ...]
    attention_points: tuple[str, ...]

    debriefing: str

    derived_results: tuple[
        tuple[str, float],
        ...,
    ] = ()

    @property
    def primary_metrics(
        self,
    ) -> tuple[
        GoalMetricAssessment,
        ...,
    ]:
        return tuple(
            metric
            for metric in self.metrics
            if (
                metric.importance
                is MetricImportance.PRIMARY
            )
        )
