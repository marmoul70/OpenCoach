from datetime import date
from uuid import uuid4

from opencoach.coaching.daily_session_replanning import (
    DailyReplanningAction,
    DailyReplanningRisk,
    DailySessionReplanningOption,
    DailySessionReplanningProposal,
)
from opencoach.coaching.daily_week_replanning import (
    coordinate_daily_week_replanning,
)
from opencoach.models import TrainingSession


THURSDAY = date(2026, 8, 27)
SATURDAY = date(2026, 8, 29)


def _session(
    *,
    session_type: str,
    sport_type: str,
    title: str,
    duration: int,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=THURSDAY,
        type=session_type,
        sport_type=sport_type,
        title=title,
        description="",
        duration_minutes=duration,
        intensity="easy",
        status="skipped",
    )


def _proposal(
    session: TrainingSession,
) -> DailySessionReplanningProposal:
    moved = TrainingSession(
        id=None,
        date=SATURDAY,
        type=session.type,
        sport_type=session.sport_type,
        title=session.title,
        description=session.description,
        duration_minutes=(
            session.duration_minutes
        ),
        intensity=session.intensity,
        status="planned",
    )

    return DailySessionReplanningProposal(
        original_session=session,
        options=(
            DailySessionReplanningOption(
                action=(
                    DailyReplanningAction.CANCEL
                ),
                target_date=None,
                session=None,
                risk=DailyReplanningRisk.LOW,
                recommended=False,
                requires_confirmation=False,
                reasons=(
                    "La séance reste annulée.",
                ),
            ),
            DailySessionReplanningOption(
                action=(
                    DailyReplanningAction
                    .MOVE_UNCHANGED
                ),
                target_date=SATURDAY,
                session=moved,
                risk=(
                    DailyReplanningRisk.MODERATE
                ),
                recommended=True,
                requires_confirmation=True,
                reasons=(
                    "Déplacement samedi.",
                ),
            ),
        ),
    )


def test_two_sessions_are_not_both_recommended_on_same_day() -> None:
    strength = _session(
        session_type="strength_lower_body",
        sport_type="Strength",
        title="Renforcement membres inférieurs",
        duration=15,
    )

    endurance = _session(
        session_type="aerobic_easy",
        sport_type="Run",
        title="Endurance facile",
        duration=45,
    )

    plan = (
        coordinate_daily_week_replanning(
            proposals=(
                _proposal(strength),
                _proposal(endurance),
            ),
        )
    )

    moved = tuple(
        decision
        for decision in plan.decisions
        if (
            decision
            .recommended_option
            .target_date
            == SATURDAY
        )
    )

    assert len(moved) == 1


def test_running_is_preferred_over_strength_on_collision() -> None:
    strength = _session(
        session_type="strength_lower_body",
        sport_type="Strength",
        title="Renforcement membres inférieurs",
        duration=15,
    )

    endurance = _session(
        session_type="aerobic_easy",
        sport_type="Run",
        title="Endurance facile",
        duration=45,
    )

    plan = (
        coordinate_daily_week_replanning(
            proposals=(
                _proposal(strength),
                _proposal(endurance),
            ),
        )
    )

    endurance_decision = next(
        decision
        for decision in plan.decisions
        if (
            decision
            .proposal
            .original_session
            .id
            == endurance.id
        )
    )

    strength_decision = next(
        decision
        for decision in plan.decisions
        if (
            decision
            .proposal
            .original_session
            .id
            == strength.id
        )
    )

    assert (
        endurance_decision
        .recommended_option
        .action
        is DailyReplanningAction
        .MOVE_UNCHANGED
    )

    assert (
        endurance_decision
        .recommended_option
        .target_date
        == SATURDAY
    )

    assert (
        strength_decision
        .recommended_option
        .action
        is DailyReplanningAction.CANCEL
    )


def test_single_proposal_keeps_individual_recommendation() -> None:
    endurance = _session(
        session_type="aerobic_easy",
        sport_type="Run",
        title="Endurance facile",
        duration=45,
    )

    proposal = _proposal(
        endurance
    )

    plan = (
        coordinate_daily_week_replanning(
            proposals=(
                proposal,
            ),
        )
    )

    assert len(
        plan.decisions
    ) == 1

    assert (
        plan.decisions[0]
        .recommended_option
        .action
        is DailyReplanningAction
        .MOVE_UNCHANGED
    )

    assert (
        plan.decisions[0]
        .recommended_option
        .target_date
        == SATURDAY
    )


def test_empty_input_returns_empty_plan() -> None:
    plan = (
        coordinate_daily_week_replanning(
            proposals=(),
        )
    )

    assert plan.decisions == ()
    assert plan.reasons == ()
