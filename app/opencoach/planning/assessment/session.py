from dataclasses import dataclass

from opencoach.planning.assessment.recommendation import (
    AssessmentPlanRecommendation,
)


@dataclass(frozen=True)
class AssessmentSessionSpec:
    """Séance de calibration prête à être placée dans le planning."""

    assessment_type: str
    protocol_id: str

    title: str
    description: str

    sport_type: str
    intensity: str

    duration_minutes: int

    priority: str

    requires_maximal_effort: bool

    covered_metrics: tuple[str, ...]


def build_assessment_session_spec(
    recommendation: AssessmentPlanRecommendation,
) -> AssessmentSessionSpec | None:
    """Transforme une recommandation admissible en séance planifiable."""

    if not recommendation.ready_to_schedule:
        return None

    protocol = recommendation.protocol

    if protocol is None:
        return None

    need = recommendation.need

    return AssessmentSessionSpec(
        assessment_type=need.assessment_type,
        protocol_id=protocol.protocol_id,
        title=_build_title(
            protocol_id=protocol.protocol_id,
            protocol_name=protocol.name,
        ),
        description=_build_description(
            recommendation
        ),
        sport_type="run",
        intensity=(
            "maximal"
            if protocol.intensity == "maximal"
            else "submaximal"
        ),
        duration_minutes=(
            protocol.estimated_duration_minutes
        ),
        priority=need.priority,
        requires_maximal_effort=(
            protocol.intensity == "maximal"
        ),
        covered_metrics=tuple(
            sorted(
                protocol.metrics
            )
        ),
    )


def _build_title(
    *,
    protocol_id: str,
    protocol_name: str,
) -> str:
    if protocol_id == "vameval":
        return "Test VAMEVAL"

    if protocol_id == "half_cooper":
        return "Test demi-Cooper"

    if protocol_id == "twenty_minute_threshold":
        return "Test seuil 20 minutes"

    if protocol_id == "laboratory_threshold":
        return "Test physiologique en laboratoire"

    return f"Test physiologique — {protocol_name}"


def _build_description(
    recommendation: AssessmentPlanRecommendation,
) -> str:
    protocol = recommendation.protocol

    if protocol is None:
        return ""

    metrics = ", ".join(
        recommendation.need.metrics
    )

    return (
        f"{protocol.description} "
        f"Objectif de calibration : {metrics}."
    )
