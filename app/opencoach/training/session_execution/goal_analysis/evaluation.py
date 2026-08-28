"""Évaluation coaching des métriques selon l'objectif."""

from __future__ import annotations

from dataclasses import fields

from opencoach.models import (
    Activity,
    ActivityDetail,
    TrainingSession,
)

from ..metric import NumericMetricAssessment
from ..models import (
    SessionExecutionIntensityAssessment,
    SessionExecutionLoadAssessment,
    SessionExecutionStructureAssessment,
    SessionExecutionVolumeAssessment,
)
from ..status import AssessmentStatus
from .feedback import (
    build_metric_message,
    build_session_debriefing,
)
from .half_cooper import (
    analyze_half_cooper,
    is_half_cooper_session,
)
from .models import (
    GoalComplianceStatus,
    GoalMetricAssessment,
    MetricImportance,
    SessionGoalAnalysis,
)
from .resolver import (
    resolve_goal_analysis_plan,
)


def evaluate_session_goal(
    *,
    session: TrainingSession,
    volume: SessionExecutionVolumeAssessment,
    intensity: SessionExecutionIntensityAssessment,
    load: SessionExecutionLoadAssessment,
    structure: SessionExecutionStructureAssessment,
    activity: Activity | None = None,
    activity_detail: ActivityDetail | None = None,
) -> SessionGoalAnalysis:
    """Analyse une séance en fonction de son objectif réel."""

    plan = resolve_goal_analysis_plan(
        session
    )

    # --------------------------------------------------------
    # REPOS
    # --------------------------------------------------------

    if session.type == "rest":
        if activity is None:
            return SessionGoalAnalysis(
                goal_type=plan.goal_type,
                objective=plan.objective,
                overall_status=GoalComplianceStatus.OK,
                metrics=(),
                strengths=(
                    "Le repos prescrit a été respecté.",
                ),
                attention_points=(),
                debriefing=(
                    "La récupération prévue a été respectée "
                    "sans ajout de charge d'entraînement."
                ),
            )

        return SessionGoalAnalysis(
            goal_type=plan.goal_type,
            objective=plan.objective,
            overall_status=(
                GoalComplianceStatus.NON_COMPLIANT
            ),
            metrics=(),
            strengths=(),
            attention_points=(
                "Une activité a été réalisée alors qu'un "
                "repos était prescrit.",
            ),
            debriefing=(
                "Le repos prévu n'a pas été respecté. "
                "Cette charge supplémentaire doit être prise "
                "en compte dans la suite de la planification."
            ),
        )

    # --------------------------------------------------------
    # DEMI-COOPER
    # --------------------------------------------------------

    if is_half_cooper_session(
        session
    ):
        return _evaluate_half_cooper_goal(
            session=session,
            activity=activity,
            activity_detail=activity_detail,
            plan=plan,
        )

    # --------------------------------------------------------
    # AUTRES OBJECTIFS
    # --------------------------------------------------------

    available_metrics = _collect_metrics(
        volume=volume,
        intensity=intensity,
        load=load,
        structure=structure,
    )

    assessments = []

    for definition in plan.metrics:
        source = available_metrics.get(
            definition.key
        )

        assessment = _build_goal_metric(
            definition=definition,
            source=source,
        )

        assessments.append(
            assessment
        )

    overall_status = _resolve_goal_status(
        tuple(assessments)
    )

    strengths = tuple(
        metric.message
        for metric in assessments
        if (
            metric.status
            is GoalComplianceStatus.OK
            and metric.importance
            is not MetricImportance.INFORMATIONAL
            and metric.message
        )
    )

    attention_points = tuple(
        metric.message
        for metric in assessments
        if (
            metric.status
            in {
                GoalComplianceStatus.ATTENTION,
                GoalComplianceStatus.NON_COMPLIANT,
            }
            and metric.importance
            is not MetricImportance.INFORMATIONAL
            and metric.message
        )
    )

    debriefing = build_session_debriefing(
        goal_type=plan.goal_type,
        overall_status=overall_status,
        strengths=strengths,
        attention_points=attention_points,
        metrics=tuple(
            assessments
        ),
    )

    return SessionGoalAnalysis(
        goal_type=plan.goal_type,
        objective=plan.objective,
        overall_status=overall_status,
        metrics=tuple(
            assessments
        ),
        strengths=strengths,
        attention_points=attention_points,
        debriefing=debriefing,
    )


def _evaluate_half_cooper_goal(
    *,
    session: TrainingSession,
    activity: Activity | None,
    activity_detail: ActivityDetail | None,
    plan,
) -> SessionGoalAnalysis:
    """Construit le débriefing métier du Demi-Cooper."""

    result = analyze_half_cooper(
        session=session,
        activity=activity,
        activity_detail=activity_detail,
    )

    duration_status = (
        GoalComplianceStatus.OK
        if result.protocol_duration_seconds is not None
        else GoalComplianceStatus.NOT_USED
    )

    distance_status = (
        GoalComplianceStatus.OK
        if (
            result.distance_m is not None
            and result.distance_m > 0
        )
        else GoalComplianceStatus.NOT_USED
    )

    metrics = (
        GoalMetricAssessment(
            key="protocol_validity",
            label="Validité du protocole",
            importance=MetricImportance.PRIMARY,
            status=result.status,
            actual_value=(
                1.0
                if result.vma_kmh is not None
                else 0.0
            ),
            message=result.message,
        ),
        GoalMetricAssessment(
            key="duration",
            label="Durée du segment test",
            importance=MetricImportance.PRIMARY,
            status=duration_status,
            target_minimum=360.0,
            target_maximum=360.0,
            unit="s",
            actual_value=(
                result.protocol_duration_seconds
            ),
            message=(
                "La fenêtre d'analyse correspond aux "
                "6 minutes du protocole."
                if duration_status
                is GoalComplianceStatus.OK
                else (
                    "La fenêtre de 6 minutes n'a pas pu "
                    "être reconstruite."
                )
            ),
        ),
        GoalMetricAssessment(
            key="distance",
            label="Distance du segment test",
            importance=MetricImportance.PRIMARY,
            status=distance_status,
            unit="m",
            actual_value=result.distance_m,
            message=(
                f"{result.distance_m:.0f} m parcourus "
                "pendant le segment test."
                if result.distance_m is not None
                else (
                    "La distance du segment test n'est "
                    "pas exploitable."
                )
            ),
        ),
    )

    strengths = tuple(
        metric.message
        for metric in metrics
        if (
            metric.status
            is GoalComplianceStatus.OK
            and metric.message
        )
    )

    attention_points = tuple(
        metric.message
        for metric in metrics
        if (
            metric.status
            in {
                GoalComplianceStatus.ATTENTION,
                GoalComplianceStatus.NON_COMPLIANT,
            }
            and metric.message
        )
    )

    derived_results = ()

    if result.vma_kmh is not None:
        derived_results = (
            (
                "vma_kmh",
                result.vma_kmh,
            ),
        )

    if result.vma_kmh is not None:
        debriefing = (
            f"{result.message} "
            "Cette estimation peut être transmise au moteur "
            "physiologique pour recalibrer les futures "
            "prescriptions après validation du workflow."
        )
    else:
        debriefing = result.message

    return SessionGoalAnalysis(
        goal_type=plan.goal_type,
        objective=plan.objective,
        overall_status=result.status,
        metrics=metrics,
        strengths=strengths,
        attention_points=attention_points,
        debriefing=debriefing,
        derived_results=derived_results,
    )

def _collect_metrics(
    *,
    volume: SessionExecutionVolumeAssessment,
    intensity: SessionExecutionIntensityAssessment,
    load: SessionExecutionLoadAssessment,
    structure: SessionExecutionStructureAssessment,
) -> dict[
    str,
    NumericMetricAssessment,
]:
    result = {}

    for section in (
        volume,
        intensity,
        load,
        structure,
    ):
        for field in fields(
            section
        ):
            metric = getattr(
                section,
                field.name,
            )

            if isinstance(
                metric,
                NumericMetricAssessment,
            ):
                result[
                    metric.key
                ] = metric

    return result


def _build_goal_metric(
    *,
    definition,
    source: NumericMetricAssessment | None,
) -> GoalMetricAssessment:
    if (
        definition.importance
        is MetricImportance.INFORMATIONAL
    ):
        return GoalMetricAssessment(
            key=definition.key,
            label=definition.label,
            importance=definition.importance,
            status=GoalComplianceStatus.NOT_USED,
            target_minimum=(
                source.target.minimum
                if (
                    source is not None
                    and source.target is not None
                )
                else None
            ),
            target_maximum=(
                source.target.maximum
                if (
                    source is not None
                    and source.target is not None
                )
                else None
            ),
            unit=(
                source.target.unit
                if (
                    source is not None
                    and source.target is not None
                )
                else None
            ),
            actual_value=(
                source.actual_value
                if source is not None
                else None
            ),
            delta=(
                source.delta
                if source is not None
                else None
            ),
            delta_percent=(
                source.delta_percent
                if source is not None
                else None
            ),
            message=(
                f"{definition.label} : indicateur informatif, "
                "non utilisé pour déterminer la conformité "
                "de cette séance."
            ),
        )

    if source is None:
        result = GoalMetricAssessment(
            key=definition.key,
            label=definition.label,
            importance=definition.importance,
            status=GoalComplianceStatus.NOT_USED,
        )

        return _with_message(
            result
        )

    status = _map_status(
        source.status
    )

    target = source.target

    result = GoalMetricAssessment(
        key=definition.key,
        label=definition.label,
        importance=definition.importance,
        status=status,
        target_minimum=(
            target.minimum
            if target is not None
            else None
        ),
        target_maximum=(
            target.maximum
            if target is not None
            else None
        ),
        unit=(
            target.unit
            if target is not None
            else None
        ),
        actual_value=source.actual_value,
        delta=source.delta,
        delta_percent=(
            source.delta_percent
        ),
    )

    return _with_message(
        result
    )


def _with_message(
    metric: GoalMetricAssessment,
) -> GoalMetricAssessment:
    message = build_metric_message(
        metric
    )

    return GoalMetricAssessment(
        key=metric.key,
        label=metric.label,
        importance=metric.importance,
        status=metric.status,
        target_minimum=metric.target_minimum,
        target_maximum=metric.target_maximum,
        unit=metric.unit,
        actual_value=metric.actual_value,
        delta=metric.delta,
        delta_percent=metric.delta_percent,
        message=message,
    )


def _map_status(
    status: AssessmentStatus,
) -> GoalComplianceStatus:
    if status is AssessmentStatus.COMPLIANT:
        return GoalComplianceStatus.OK

    if status is AssessmentStatus.PARTIAL:
        return GoalComplianceStatus.ATTENTION

    if status is AssessmentStatus.NON_COMPLIANT:
        return GoalComplianceStatus.NON_COMPLIANT

    # Le Dashboard utilise volontairement un seul état gris :
    # soit la métrique n'est pas pertinente, soit les données
    # ne sont pas suffisamment exploitables.
    return GoalComplianceStatus.NOT_USED


def _resolve_goal_status(
    metrics: tuple[
        GoalMetricAssessment,
        ...,
    ],
) -> GoalComplianceStatus:
    """Détermine le verdict depuis l'importance des objectifs."""

    primary = tuple(
        metric
        for metric in metrics
        if (
            metric.importance
            is MetricImportance.PRIMARY
            and metric.status
            is not GoalComplianceStatus.NOT_USED
        )
    )

    secondary = tuple(
        metric
        for metric in metrics
        if (
            metric.importance
            is MetricImportance.SECONDARY
            and metric.status
            is not GoalComplianceStatus.NOT_USED
        )
    )

    if not primary:
        if not secondary:
            return GoalComplianceStatus.NOT_USED

        if any(
            metric.status
            is GoalComplianceStatus.NON_COMPLIANT
            for metric in secondary
        ):
            return GoalComplianceStatus.ATTENTION

        if any(
            metric.status
            is GoalComplianceStatus.ATTENTION
            for metric in secondary
        ):
            return GoalComplianceStatus.ATTENTION

        return GoalComplianceStatus.OK

    # Un objectif PRINCIPAL clairement raté signifie que
    # le stimulus demandé n'a pas été respecté.
    if any(
        metric.status
        is GoalComplianceStatus.NON_COMPLIANT
        for metric in primary
    ):
        return GoalComplianceStatus.NON_COMPLIANT

    if any(
        metric.status
        is GoalComplianceStatus.ATTENTION
        for metric in primary
    ):
        return GoalComplianceStatus.ATTENTION

    # Tous les objectifs principaux sont OK.
    # Un écart secondaire entraîne uniquement ATTENTION.
    if any(
        metric.status
        in {
            GoalComplianceStatus.ATTENTION,
            GoalComplianceStatus.NON_COMPLIANT,
        }
        for metric in secondary
    ):
        return GoalComplianceStatus.ATTENTION

    return GoalComplianceStatus.OK
