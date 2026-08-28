"""Statuts communs aux indicateurs d'exécution d'une séance."""

from enum import StrEnum


class AssessmentStatus(StrEnum):
    """État déterministe d'un indicateur ou d'une évaluation."""

    COMPLIANT = "compliant"
    PARTIAL = "partial"
    NON_COMPLIANT = "non_compliant"

    NOT_APPLICABLE = "not_applicable"
    INSUFFICIENT_DATA = "insufficient_data"
