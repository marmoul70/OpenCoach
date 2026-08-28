"""Analyse déterministe de la charge prévue et réalisée."""

from __future__ import annotations

from opencoach.models import Activity, TrainingSession
from opencoach.training.load_comparison import (
    classify_training_load,
)
from opencoach.training.load_estimation import (
    estimate_prescribed_load,
)

from .metric import (
    NumericMetricAssessment,
    NumericTarget,
)
from .models import SessionExecutionLoadAssessment
from .status import AssessmentStatus


def assess_session_load(
    session: TrainingSession,
    activity: Activity | None,
) -> SessionExecutionLoadAssessment:
    """Compare la charge prescrite à la charge mesurée.

    La charge prévue utilise le moteur déterministe OpenCoach
    déjà existant.

    La charge réelle utilise uniquement ``training_load``.
    ``hr_load`` n'est pas utilisé comme substitution car ces deux
    métriques ne sont pas nécessairement interchangeables.
    """

    planned_load = estimate_prescribed_load(
        session,
    )

    metric = _assess_training_load(
        session=session,
        activity=activity,
        planned_load=planned_load,
    )

    return SessionExecutionLoadAssessment(
        training_load=metric,
    )


def _assess_training_load(
    *,
    session: TrainingSession,
    activity: Activity | None,
    planned_load: float,
) -> NumericMetricAssessment:
    target = NumericTarget.exact(
        planned_load,
        "load",
    )

    if session.type == "rest":
        if activity is None:
            return NumericMetricAssessment(
                key="training_load",
                label="Charge d'entraînement",
                status=AssessmentStatus.COMPLIANT,
                target=target,
                actual_value=0.0,
                delta=0.0,
                delta_percent=None,
                details="Repos prescrit et respecté.",
            )

        if (
            activity.training_load is None
        ):
            return NumericMetricAssessment(
                key="training_load",
                label="Charge d'entraînement",
                status=(
                    AssessmentStatus.INSUFFICIENT_DATA
                ),
                target=target,
                details=(
                    "Une activité est associée au repos, "
                    "mais sa charge n'est pas disponible."
                ),
            )

        actual_load = float(
            activity.training_load
        )

        status = (
            AssessmentStatus.COMPLIANT
            if actual_load <= 0
            else AssessmentStatus.NON_COMPLIANT
        )

        return NumericMetricAssessment(
            key="training_load",
            label="Charge d'entraînement",
            status=status,
            target=target,
            actual_value=round(
                actual_load,
                2,
            ),
            delta=round(
                actual_load,
                2,
            ),
            delta_percent=None,
            details=(
                "Repos respecté."
                if status is AssessmentStatus.COMPLIANT
                else "Une charge a été réalisée pendant "
                "une journée de repos prescrite."
            ),
        )

    if planned_load <= 0:
        return NumericMetricAssessment(
            key="training_load",
            label="Charge d'entraînement",
            status=AssessmentStatus.NOT_APPLICABLE,
            details=(
                "La séance ne possède pas de charge "
                "prescrite exploitable."
            ),
        )

    if activity is None:
        return NumericMetricAssessment(
            key="training_load",
            label="Charge d'entraînement",
            status=AssessmentStatus.INSUFFICIENT_DATA,
            target=target,
            details="Aucune activité associée à la séance.",
        )

    if activity.training_load is None:
        return NumericMetricAssessment(
            key="training_load",
            label="Charge d'entraînement",
            status=AssessmentStatus.INSUFFICIENT_DATA,
            target=target,
            details=(
                "La charge mesurée de l'activité "
                "n'est pas disponible."
            ),
        )

    actual_load = float(
        activity.training_load
    )

    load_status = classify_training_load(
        planned_load=planned_load,
        actual_load=actual_load,
        has_prescription=True,
        has_planned_rest=False,
    )

    status = _map_load_status(
        load_status,
    )

    delta = (
        actual_load
        - planned_load
    )

    delta_percent = (
        delta
        / planned_load
        * 100.0
    )

    return NumericMetricAssessment(
        key="training_load",
        label="Charge d'entraînement",
        status=status,
        target=target,
        actual_value=round(
            actual_load,
            2,
        ),
        delta=round(
            delta,
            2,
        ),
        delta_percent=round(
            delta_percent,
            2,
        ),
        details=_load_details(
            load_status,
        ),
    )


def _map_load_status(
    status: str,
) -> AssessmentStatus:
    if status in {
        "on_plan",
        "rest_respected",
    }:
        return AssessmentStatus.COMPLIANT

    if status in {
        "below_plan",
        "above_plan",
        "rest_broken",
    }:
        return AssessmentStatus.NON_COMPLIANT

    return AssessmentStatus.NOT_APPLICABLE


def _load_details(
    status: str,
) -> str:
    labels = {
        "on_plan": (
            "La charge réalisée est conforme "
            "à la charge prescrite."
        ),
        "below_plan": (
            "La charge réalisée est inférieure "
            "à la charge prescrite."
        ),
        "above_plan": (
            "La charge réalisée est supérieure "
            "à la charge prescrite."
        ),
        "rest_respected": (
            "Le repos prescrit a été respecté."
        ),
        "rest_broken": (
            "Une activité a été réalisée pendant "
            "un repos prescrit."
        ),
        "unplanned": (
            "Aucune charge prescrite comparable."
        ),
    }

    return labels.get(
        status,
        "État de charge non classifié.",
    )
