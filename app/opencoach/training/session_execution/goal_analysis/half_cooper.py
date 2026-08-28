"""Analyse déterministe d'un test demi-Cooper."""

from __future__ import annotations

from dataclasses import dataclass

from opencoach.models import (
    Activity,
    ActivityDetail,
    TrainingSession,
)

from ..continuous_effort_detection import (
    ContinuousEffortWindow,
    locate_continuous_effort_window,
)

from .models import (
    GoalComplianceStatus,
)


HALF_COOPER_TARGET_SECONDS = 360.0

HALF_COOPER_DURATION_OK_SECONDS = 10.0
HALF_COOPER_DURATION_ATTENTION_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class HalfCooperAnalysis:
    """Résultat d'analyse d'un demi-Cooper."""

    status: GoalComplianceStatus

    protocol_duration_seconds: float | None
    distance_m: float | None

    vma_kmh: float | None

    message: str


def analyze_half_cooper(
    *,
    session: TrainingSession,
    activity: Activity | None,
    activity_detail: ActivityDetail | None,
) -> HalfCooperAnalysis:
    """Valide le segment réel de 6 minutes et estime la VMA.

    La séance complète peut contenir échauffement et retour au calme.
    Seule la fenêtre d'effort continu de 360 secondes reconstruite
    dans les streams est utilisée pour le calcul.
    """

    if activity is None:
        return HalfCooperAnalysis(
            status=GoalComplianceStatus.NON_COMPLIANT,
            protocol_duration_seconds=None,
            distance_m=None,
            vma_kmh=None,
            message=(
                "Aucune activité n'est associée "
                "au test demi-Cooper."
            ),
        )

    if activity_detail is None:
        return HalfCooperAnalysis(
            status=GoalComplianceStatus.NOT_USED,
            protocol_duration_seconds=None,
            distance_m=None,
            vma_kmh=None,
            message=(
                "Les streams nécessaires à l'analyse "
                "du demi-Cooper ne sont pas disponibles."
            ),
        )

    window = locate_continuous_effort_window(
        activity_detail,
        target_duration_seconds=(
            HALF_COOPER_TARGET_SECONDS
        ),
    )

    if window is None:
        return HalfCooperAnalysis(
            status=GoalComplianceStatus.NON_COMPLIANT,
            protocol_duration_seconds=None,
            distance_m=None,
            vma_kmh=None,
            message=(
                "OpenCoach n'a pas pu reconstruire "
                "une fenêtre continue de 6 minutes "
                "suffisamment exploitable."
            ),
        )

    distance = window.distance_m

    if (
        distance is None
        or distance <= 0
    ):
        return HalfCooperAnalysis(
            status=GoalComplianceStatus.NOT_USED,
            protocol_duration_seconds=(
                window.duration_seconds
            ),
            distance_m=None,
            vma_kmh=None,
            message=(
                "La fenêtre de test a été retrouvée, "
                "mais la distance n'est pas exploitable. "
                "La VMA n'est pas calculée."
            ),
        )

    continuity_status = _window_continuity_status(
        window
    )

    if (
        continuity_status
        is GoalComplianceStatus.NON_COMPLIANT
    ):
        return HalfCooperAnalysis(
            status=GoalComplianceStatus.NON_COMPLIANT,
            protocol_duration_seconds=(
                window.duration_seconds
            ),
            distance_m=round(
                distance,
                1,
            ),
            vma_kmh=None,
            message=(
                "La fenêtre de 6 minutes présente trop "
                "d'interruptions pour produire une VMA fiable."
            ),
        )

    confidence_status = _window_confidence_status(
        window
    )

    if (
        confidence_status
        is GoalComplianceStatus.NON_COMPLIANT
    ):
        return HalfCooperAnalysis(
            status=GoalComplianceStatus.NON_COMPLIANT,
            protocol_duration_seconds=(
                window.duration_seconds
            ),
            distance_m=round(
                distance,
                1,
            ),
            vma_kmh=None,
            message=(
                "La fenêtre de test retrouvée n'est pas "
                "suffisamment fiable pour calculer la VMA."
            ),
        )

    status = GoalComplianceStatus.OK

    if (
        continuity_status
        is GoalComplianceStatus.ATTENTION
        or confidence_status
        is GoalComplianceStatus.ATTENTION
    ):
        status = GoalComplianceStatus.ATTENTION

    vma = (
        distance
        / 100.0
    )

    return HalfCooperAnalysis(
        status=status,
        protocol_duration_seconds=round(
            window.duration_seconds,
            1,
        ),
        distance_m=round(
            distance,
            1,
        ),
        vma_kmh=round(
            vma,
            2,
        ),
        message=(
            f"Test demi-Cooper exploitable : "
            f"{distance:.0f} m parcourus sur les "
            f"{window.duration_seconds:.0f} s du segment test. "
            f"VMA estimée à {vma:.2f} km/h."
        ),
    )


def _window_continuity_status(
    window: ContinuousEffortWindow,
) -> GoalComplianceStatus:
    ratio = window.continuity_ratio

    if ratio is None:
        return GoalComplianceStatus.ATTENTION

    if ratio >= 0.985:
        return GoalComplianceStatus.OK

    if ratio >= 0.95:
        return GoalComplianceStatus.ATTENTION

    return GoalComplianceStatus.NON_COMPLIANT


def _window_confidence_status(
    window: ContinuousEffortWindow,
) -> GoalComplianceStatus:
    if window.confidence >= 0.85:
        return GoalComplianceStatus.OK

    if window.confidence >= 0.70:
        return GoalComplianceStatus.ATTENTION

    return GoalComplianceStatus.NON_COMPLIANT

def is_half_cooper_session(
    session: TrainingSession,
) -> bool:
    """Identifie explicitement un demi-Cooper."""

    if session.type != "physiological_test":
        return False

    prescription = session.prescription

    if not isinstance(
        prescription,
        dict,
    ):
        return False

    test = prescription.get(
        "test"
    )

    if isinstance(
        test,
        dict,
    ):
        kind = test.get(
            "type"
        )

        if kind in {
            "half_cooper",
            "demi_cooper",
        }:
            return True

    protocol = prescription.get(
        "protocol"
    )

    if isinstance(
        protocol,
        dict,
    ):
        kind = protocol.get(
            "type"
        )

        if kind in {
            "half_cooper",
            "demi_cooper",
        }:
            return True


    return False
