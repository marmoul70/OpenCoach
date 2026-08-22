from datetime import date, timedelta
from uuid import uuid4

from opencoach.models import (
    AthleteProfile,
    Race,
)
from opencoach.planning import (
    AssessmentNeed,
    PlanningContext,
    build_assessment_safety_context,
    build_assessment_selection_context,
    select_assessment_protocol,
)


PLANNING_DATE = date(
    2026,
    8,
    22,
)


def create_context(
    *,
    primary_race=None,
):
    return PlanningContext(
        planning_date=PLANNING_DATE,
        athlete=AthleteProfile(),
        primary_race=primary_race,
        training_races=(),
        readiness=None,
        recent_load=None,
        recent_stats=None,
        constraints=(),
        constraints_end_date=(
            PLANNING_DATE
            + timedelta(days=14)
        ),
    )


def create_vma_need() -> AssessmentNeed:
    return AssessmentNeed(
        assessment_type="vma_calibration",
        priority="high",
        metrics=("vma",),
        reason="VMA à recalibrer.",
    )


def test_vma_protocol_is_selected_when_safety_allows_it() -> None:
    planning_context = create_context()

    safety = build_assessment_safety_context(
        planning_context
    )

    selection_context = (
        build_assessment_selection_context(
            safety=safety,
            track_available=True,
            flat_route_available=True,
        )
    )

    selection = select_assessment_protocol(
        need=create_vma_need(),
        context=selection_context,
    )

    assert selection.has_solution is True

    assert selection.best_candidate is not None

    assert (
        selection.best_candidate.protocol.protocol_id
        == "vameval"
    )


def test_primary_race_blocks_maximal_vma_protocols() -> None:
    race = Race(
        id=uuid4(),
        date=(
            PLANNING_DATE
            + timedelta(days=5)
        ),
        name="Trail objectif",
        location="Test",
        race_type="trail",
        priority="primary",
        distance_km=50.0,
        elevation_gain_m=2500.0,
        status="planned",
    )

    planning_context = create_context(
        primary_race=race
    )

    safety = build_assessment_safety_context(
        planning_context
    )

    selection_context = (
        build_assessment_selection_context(
            safety=safety,
            track_available=True,
            flat_route_available=True,
        )
    )

    selection = select_assessment_protocol(
        need=create_vma_need(),
        context=selection_context,
    )

    assert (
        safety.maximal_testing_allowed
        is False
    )

    assert selection.has_solution is False
