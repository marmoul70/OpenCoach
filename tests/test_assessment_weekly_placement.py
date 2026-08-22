from datetime import date

from opencoach.models import (
    TrainingSession,
)
from opencoach.planning import (
    AssessmentSessionSpec,
    WeeklyAvailability,
    place_assessment_session,
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


class FakeDayAvailability:
    def __init__(
        self,
        *,
        target_date: date,
        training_allowed: bool = True,
        running_allowed: bool = True,
        cross_training_allowed: bool = True,
        preferred: bool = False,
        status: str = "available",
        requires_confirmation: bool = False,
        max_duration_minutes: int | None = None,
    ) -> None:
        self.date = target_date

        self.training_allowed = (
            training_allowed
        )

        self.running_allowed = (
            running_allowed
        )

        self.cross_training_allowed = (
            cross_training_allowed
        )

        self.preferred = preferred
        self.status = status

        self.requires_confirmation = (
            requires_confirmation
        )

        self.max_duration_minutes = (
            max_duration_minutes
        )


def create_spec() -> AssessmentSessionSpec:
    return AssessmentSessionSpec(
        assessment_type="vma_calibration",
        protocol_id="vameval",
        title="Test VAMEVAL",
        description="Calibration de la VMA.",
        sport_type="run",
        intensity="maximal",
        duration_minutes=45,
        priority="high",
        requires_maximal_effort=True,
        covered_metrics=(
            "vma",
            "max_heart_rate",
        ),
    )


def create_hard_session(
    *,
    session_date: date,
) -> TrainingSession:
    return TrainingSession(
        id=None,
        date=session_date,
        type="interval",
        sport_type="run",
        title="Fractionné",
        description="Séance intense.",
        duration_minutes=60,
        intensity="hard",
    )


def create_week(
    *days,
) -> WeeklyAvailability:
    return WeeklyAvailability(
        start_date=WEEK_START,
        end_date=SUNDAY,
        days=tuple(days),
    )


def test_target_day_is_selected_when_valid() -> None:
    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
            preferred=True,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
            preferred=False,
            requires_confirmation=True,
        ),
    )

    result = place_assessment_session(
        spec=create_spec(),
        target_date=WEDNESDAY,
        week=week,
        existing_sessions=(),
    )

    assert result.has_solution is True

    assert result.best_candidate is not None

    assert (
        result.best_candidate.date
        == WEDNESDAY
    )

    assert (
        result.best_candidate.preferred
        is True
    )

    assert (
        result.best_candidate.requires_confirmation
        is False
    )


def test_hard_session_previous_day_rejects_target_day() -> None:
    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
            preferred=True,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
            preferred=False,
            requires_confirmation=True,
        ),
    )

    result = place_assessment_session(
        spec=create_spec(),
        target_date=WEDNESDAY,
        week=week,
        existing_sessions=(
            create_hard_session(
                session_date=TUESDAY,
            ),
        ),
    )

    rejected_dates = {
        candidate.date
        for candidate in result.rejected_candidates
    }

    assert WEDNESDAY in rejected_dates

    assert result.best_candidate is not None

    assert (
        result.best_candidate.date
        == THURSDAY
    )


def test_alternative_day_requires_confirmation() -> None:
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

    result = place_assessment_session(
        spec=create_spec(),
        target_date=WEDNESDAY,
        week=week,
        existing_sessions=(),
    )

    assert result.best_candidate is not None

    assert (
        result.best_candidate.date
        == THURSDAY
    )

    assert (
        result.best_candidate.requires_confirmation
        is True
    )


def test_preferred_day_beats_non_preferred_day_at_same_distance() -> None:
    week = create_week(
        FakeDayAvailability(
            target_date=TUESDAY,
            preferred=False,
            requires_confirmation=True,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
            preferred=True,
        ),
    )

    result = place_assessment_session(
        spec=create_spec(),
        target_date=WEDNESDAY,
        week=week,
        existing_sessions=(),
    )

    assert result.best_candidate is not None

    assert (
        result.best_candidate.date
        == THURSDAY
    )


def test_duration_limit_can_reject_candidate() -> None:
    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
            preferred=True,
            max_duration_minutes=30,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
            preferred=False,
            max_duration_minutes=60,
            requires_confirmation=True,
        ),
    )

    result = place_assessment_session(
        spec=create_spec(),
        target_date=WEDNESDAY,
        week=week,
        existing_sessions=(),
    )

    rejected_dates = {
        candidate.date
        for candidate in result.rejected_candidates
    }

    assert WEDNESDAY in rejected_dates

    assert result.best_candidate is not None

    assert (
        result.best_candidate.date
        == THURSDAY
    )


def test_no_available_day_returns_no_solution() -> None:
    week = create_week(
        FakeDayAvailability(
            target_date=WEDNESDAY,
            training_allowed=False,
        ),
        FakeDayAvailability(
            target_date=THURSDAY,
            training_allowed=False,
        ),
        FakeDayAvailability(
            target_date=FRIDAY,
            training_allowed=False,
        ),
    )

    result = place_assessment_session(
        spec=create_spec(),
        target_date=WEDNESDAY,
        week=week,
        existing_sessions=(),
    )

    assert result.has_solution is False

    assert result.best_candidate is None
