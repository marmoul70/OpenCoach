from datetime import date
from uuid import uuid4

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
    TrainingSession,
)
from opencoach.planning import (
    build_session_placement_context,
    build_session_placement_result,
    build_weekly_availability,
    rank_session_placement_candidates,
)


WEEK_START = date(
    2026,
    8,
    24,
)

MONDAY = date(
    2026,
    8,
    24,
)

TUESDAY = date(
    2026,
    8,
    25,
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

FRIDAY = date(
    2026,
    8,
    28,
)

SUNDAY = date(
    2026,
    8,
    30,
)


def create_athlete() -> AthleteProfile:
    athlete = AthleteProfile()

    athlete.training.available_days = [
        0,
        2,
        4,
        6,
    ]

    athlete.training.weekly_sessions = 4
    athlete.training.weekly_duration_minutes = 300

    return athlete


def create_run(
    *,
    session_date: date,
    title: str,
    intensity: str,
    duration_minutes: int,
) -> TrainingSession:
    return TrainingSession(
        id=uuid4(),
        date=session_date,
        type="run",
        sport_type="run",
        title=title,
        description="",
        duration_minutes=duration_minutes,
        intensity=intensity,
    )


def test_reschedules_unavailable_hard_session_to_best_valid_day() -> None:
    athlete = create_athlete()

    monday_easy = create_run(
        session_date=MONDAY,
        title="Endurance fondamentale",
        intensity="easy",
        duration_minutes=50,
    )

    wednesday_hard = create_run(
        session_date=WEDNESDAY,
        title="Séance seuil",
        intensity="hard",
        duration_minutes=60,
    )

    friday_hard = create_run(
        session_date=FRIDAY,
        title="Côtes",
        intensity="hard",
        duration_minutes=60,
    )

    sunday_long = create_run(
        session_date=SUNDAY,
        title="Sortie longue trail",
        intensity="moderate",
        duration_minutes=130,
    )

    wednesday_unavailable = AthleteConstraint(
        id=uuid4(),
        start_date=WEDNESDAY,
        end_date=WEDNESDAY,
        constraint_type="work",
        availability="unavailable",
        running_allowed=False,
        cross_training_allowed=False,
        notes="Indisponible mercredi pour raison professionnelle.",
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(
            wednesday_unavailable,
        ),
    )

    wednesday = week.get_day(
        WEDNESDAY
    )

    assert wednesday is not None
    assert wednesday.status == "unavailable"
    assert wednesday.training_allowed is False

    placement_context = (
        build_session_placement_context(
            session=wednesday_hard,
            week=week,
            existing_sessions=(
                monday_easy,
                wednesday_hard,
                friday_hard,
                sunday_long,
            ),
        )
    )

    ranked_candidates = (
        rank_session_placement_candidates(
            context=placement_context,
        )
    )

    result = build_session_placement_result(
        ranked_candidates
    )

    assert result.has_solution is True
    assert result.best_candidate is not None

    assert result.best_candidate.date == (
        TUESDAY
    )

    assert (
        result.best_candidate.requires_confirmation
        is True
    )

    thursday = next(
        candidate
        for candidate in result.rejected_candidates
        if candidate.date == THURSDAY
    )

    assert thursday.eligible is False

    assert (
        "Séance intense déjà prévue le lendemain."
        in thursday.reasons
    )


def test_confirmed_exception_can_make_tuesday_explicitly_available() -> None:
    athlete = create_athlete()

    tuesday_override = AthleteConstraint(
        id=uuid4(),
        start_date=TUESDAY,
        end_date=TUESDAY,
        constraint_type="personal",
        availability="available_override",
        notes="Disponibilité exceptionnelle confirmée.",
    )

    week = build_weekly_availability(
        athlete=athlete,
        week_start=WEEK_START,
        constraints=(
            tuesday_override,
        ),
    )

    tuesday = week.get_day(
        TUESDAY
    )

    assert tuesday is not None
    assert tuesday.preferred is False

    assert tuesday.status == (
        "available_override"
    )

    assert tuesday.training_allowed is True

    assert (
        tuesday.requires_confirmation
        is False
    )
