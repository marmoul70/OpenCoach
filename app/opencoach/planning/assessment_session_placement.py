from datetime import date

from opencoach.models import (
    TrainingSession,
)

from .assessment_session import (
    AssessmentSessionSpec,
)
from .placement_result import (
    SessionPlacementResult,
    build_session_placement_result,
)
from .placement_scoring import (
    rank_session_placement_candidates,
)
from .session_placement import (
    build_session_placement_context,
)
from .weekly_availability import (
    WeeklyAvailability,
)


def place_assessment_session(
    *,
    spec: AssessmentSessionSpec,
    target_date: date,
    week: WeeklyAvailability,
    existing_sessions: tuple[
        TrainingSession,
        ...
    ],
) -> SessionPlacementResult:
    """Cherche le meilleur jour pour placer une séance de calibration."""

    provisional_session = (
        _build_provisional_training_session(
            spec=spec,
            target_date=target_date,
        )
    )

    context = build_session_placement_context(
        session=provisional_session,
        week=week,
        existing_sessions=existing_sessions,
        include_original_date=True,
    )

    candidates = (
        rank_session_placement_candidates(
            context=context
        )
    )

    return build_session_placement_result(
        candidates
    )


def build_assessment_training_session(
    *,
    spec: AssessmentSessionSpec,
    session_date: date,
) -> TrainingSession:
    """Matérialise une spécification placée en TrainingSession."""

    return TrainingSession(
        id=None,
        date=session_date,
        type="assessment",
        sport_type=spec.sport_type,
        title=spec.title,
        description=spec.description,
        duration_minutes=spec.duration_minutes,
        intensity=_training_intensity(
            spec
        ),
        status="planned",
    )


def _build_provisional_training_session(
    *,
    spec: AssessmentSessionSpec,
    target_date: date,
) -> TrainingSession:
    return build_assessment_training_session(
        spec=spec,
        session_date=target_date,
    )


def _training_intensity(
    spec: AssessmentSessionSpec,
) -> str:
    if spec.requires_maximal_effort:
        return "very_hard"

    return "moderate"
