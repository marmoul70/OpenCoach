"""Primitives génériques des indicateurs d'exécution."""

from __future__ import annotations

from dataclasses import dataclass

from .status import AssessmentStatus


@dataclass(frozen=True, slots=True)
class NumericTarget:
    """Cible numérique prévue pour un indicateur."""

    minimum: float
    maximum: float
    unit: str

    def __post_init__(self) -> None:
        if self.maximum < self.minimum:
            raise ValueError(
                "La borne maximale d'une cible ne peut pas "
                "être inférieure à sa borne minimale."
            )

        if not self.unit.strip():
            raise ValueError(
                "L'unité d'une cible numérique "
                "ne peut pas être vide."
            )

    @classmethod
    def exact(
        cls,
        value: float,
        unit: str,
    ) -> "NumericTarget":
        """Construit une cible à valeur exacte."""

        return cls(
            minimum=value,
            maximum=value,
            unit=unit,
        )

    @property
    def is_exact(self) -> bool:
        """Indique si la cible représente une valeur exacte."""

        return self.minimum == self.maximum


@dataclass(frozen=True, slots=True)
class NumericMetricAssessment:
    """Résultat d'un indicateur numérique prévu/réalisé."""

    key: str
    label: str

    status: AssessmentStatus

    target: NumericTarget | None = None
    actual_value: float | None = None

    delta: float | None = None
    delta_percent: float | None = None

    details: str | None = None

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError(
                "La clé d'un indicateur "
                "ne peut pas être vide."
            )

        if not self.label.strip():
            raise ValueError(
                "Le libellé d'un indicateur "
                "ne peut pas être vide."
            )

        if (
            self.status
            is AssessmentStatus.INSUFFICIENT_DATA
            and self.actual_value is not None
        ):
            raise ValueError(
                "Un indicateur marqué comme données "
                "insuffisantes ne doit pas avoir "
                "de valeur réalisée."
            )
