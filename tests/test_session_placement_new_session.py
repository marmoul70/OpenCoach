from datetime import date
from types import SimpleNamespace

from opencoach.models import (
    TrainingSession,
)
from opencoach.planning import (
    build_session_placement_context,
    rank_training_day_candidates,
)


TARGET_DATE = date(
    2026,
    8,
    26,
)


def create_day(
    target_date,
):
    return SimpleNamespace(
        date=target_date,
        training_allowed=True,
        running_allowed=True,
        cross_training_allowed=True,
        preferred=True,
        status="available",
        requires_confirmation=False,
        max_duration_minutes=None,
    )


def test_original_date_can_be_included_for_new_placement() -> None:
    week = SimpleNamespace(
        days=(
            create_day(
                TARGET_DATE
            ),
        )
    )

    candidates = rank_training_day_candidates(
        week=week,
        original_date=TARGET_DATE,
        include_original_date=True,
    )

    assert len(candidates) == 1

    assert (
        candidates[0].date
        == TARGET_DATE
    )


def test_original_date_remains_excluded_by_default() -> None:
    week = SimpleNamespace(
        days=(
            create_day(
                TARGET_DATE
            ),
        )
    )

    candidates = rank_training_day_candidates(
        week=week,
        original_date=TARGET_DATE,
    )

    assert candidates == ()


def test_unsaved_existing_sessions_are_not_removed() -> None:
    session = TrainingSession(
        id=None,
        date=TARGET_DATE,
        type="assessment",
        sport_type="run",
        title="Test",
        description="Test",
        duration_minutes=45,
        intensity="very_hard",
    )

    existing = TrainingSession(
        id=None,
        date=date(
            2026,
            8,
            25,
        ),
        type="interval",
        sport_type="run",
        title="Fractionné",
        description="Séance intense",
        duration_minutes=60,
        intensity="hard",
    )

    context = build_session_placement_context(
        session=session,
        week=SimpleNamespace(
            days=()
        ),
        existing_sessions=(
            existing,
        ),
        include_original_date=True,
    )

    assert context.existing_sessions == (
        existing,
    )

    assert context.previous_session is existing

    assert context.previous_day_hard is True
