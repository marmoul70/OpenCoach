from datetime import date

import pytest

from opencoach.models import (
    TrainingSession,
)
from opencoach.planning import (
    AssessmentNeed,
    AssessmentPlanningError,
    AssessmentPlanningService,
    AssessmentSafetyContext,
    AssessmentSelectionContext,
    WeeklyAvailability,
    build_assessment_recommendation,
    select_assessment_protocol,
)


WEDNESDAY = date(
    2026,
    8,
    26,
)

THURSDAY = date(
    2026,
    8,
    27,
)


class FakeDayAvailability:
    def __init__(
        self,
        *,
        target_date: date,
        training_allowed: bool = True,
        preferred: bool = True,
        requires_confirmation: bool = False,
    ) -> None:
        self.date = target_date
        self.training_allowed = training_allowed

        self.running_allowed = True
        self.cross_training_allowed = True

        self.preferred = preferred

        self.status = (
            "available"
            if training_allowed
            else "unavailable"
        )

        self.requires_confirmation = (
            requires_confirmation
        )

        self.max_duration_minutes = None


def create_week(
    *days,
) -> WeeklyAvailability:
    return WeeklyAvailability(
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2026,
            8,
            30,
        ),
        days=tuple(days),
    )


def create_recommendation(
    *,
    allowed: bool = True,
):
    need = AssessmentNeed(
        assessment_type="vma_calibration",
        priority="high",
        metrics=("vma",),
        reason="VMA à recalibrer.",
    )

    safety = AssessmentSafetyContext(
        maximal_testing_allowed=allowed,
        blocking_reasons=(
            ()
            if allowed
            else (
                "Test maximal temporairement interdit.",
            )
        ),
        warnings=(),
        days_to_primary_race=None,
    )

    selection = select_assessment_protocol(
        need=need,
        context=AssessmentSelectionContext(
            maximal_testing_allowed=allowed,
            track_available=True,
            flat_route_available=True,
        ),
    )

    return build_assessment_recommendation(
        need=need,
        safety=safety,
        selection=selection,
    )


def test_service_proposes_target_day_when_available() -> None:
    service = AssessmentPlanningService()

    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
        ),
    )

    proposal = service.propose(
        recommendation=create_recommendation(),
        target_date=WEDNESDAY,
        week=week,
    )

    assert proposal.status == "proposed"

    assert (
        proposal.proposed_date
        == WEDNESDAY
    )


def test_service_proposes_alternative_with_confirmation() -> None:
    service = AssessmentPlanningService()

    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
            training_allowed=False,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
            preferred=False,
            requires_confirmation=True,
        ),
    )

    proposal = service.propose(
        recommendation=create_recommendation(),
        target_date=WEDNESDAY,
        week=week,
    )

    assert (
        proposal.status
        == "confirmation_required"
    )

    assert (
        proposal.proposed_date
        == THURSDAY
    )


def test_service_applies_confirmed_alternative() -> None:
    service = AssessmentPlanningService()

    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
            training_allowed=False,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
            preferred=False,
            requires_confirmation=True,
        ),
    )

    proposal = service.propose(
        recommendation=create_recommendation(),
        target_date=WEDNESDAY,
        week=week,
    )

    application = service.apply(
        proposal=proposal,
        confirmed=True,
    )

    assert (
        application.session.date
        == THURSDAY
    )

    assert (
        application.session.type
        == "assessment"
    )

    assert (
        application.athlete_confirmation_used
        is True
    )


def test_existing_hard_session_influences_proposal() -> None:
    service = AssessmentPlanningService()

    tuesday = date(
        2026,
        8,
        25,
    )

    hard_session = TrainingSession(
        id=None,
        date=tuesday,
        type="interval",
        sport_type="run",
        title="Fractionné",
        description="Séance intense.",
        duration_minutes=60,
        intensity="hard",
    )

    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
            preferred=False,
            requires_confirmation=True,
        ),
    )

    proposal = service.propose(
        recommendation=create_recommendation(),
        target_date=WEDNESDAY,
        week=week,
        existing_sessions=(
            hard_session,
        ),
    )

    assert (
        proposal.proposed_date
        == THURSDAY
    )

    assert (
        proposal.status
        == "confirmation_required"
    )


def test_non_schedulable_recommendation_is_rejected() -> None:
    service = AssessmentPlanningService()

    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
        ),
    )

    with pytest.raises(
        AssessmentPlanningError,
        match="ne peut pas être planifiée",
    ):
        service.propose(
            recommendation=create_recommendation(
                allowed=False
            ),
            target_date=WEDNESDAY,
            week=week,
        )
