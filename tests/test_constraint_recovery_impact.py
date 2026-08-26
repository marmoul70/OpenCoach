from datetime import date
from uuid import uuid4

from opencoach.coaching.constraint_impact import (
    constraints_have_prolonged_physiological_disruption,
    constraints_require_weekly_recovery,
    evaluate_constraint_recovery_impact,
)
from opencoach.models import AthleteConstraint


TODAY = date(
    2026,
    8,
    25,
)


def _constraint(
    *,
    constraint_type: str,
    start_date: date,
    end_date: date,
    availability: str = "unavailable",
    running_allowed: bool = False,
    max_duration_minutes: int | None = None,
) -> AthleteConstraint:
    return AthleteConstraint(
        id=uuid4(),
        start_date=start_date,
        end_date=end_date,
        constraint_type=constraint_type,  # type: ignore[arg-type]
        availability=availability,  # type: ignore[arg-type]
        running_allowed=running_allowed,
        cross_training_allowed=True,
        max_duration_minutes=(
            max_duration_minutes
        ),
    )


def test_one_day_illness_stays_local() -> None:
    constraint = _constraint(
        constraint_type="illness",
        start_date=TODAY,
        end_date=TODAY,
    )

    impact = (
        evaluate_constraint_recovery_impact(
            constraint=constraint,
            reference_date=TODAY,
        )
    )

    assert not impact.requires_weekly_recovery
    assert not impact.prolonged_disruption


def test_three_day_illness_requires_weekly_recovery() -> None:
    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2026,
            8,
            26,
        ),
    )

    impact = (
        evaluate_constraint_recovery_impact(
            constraint=constraint,
            reference_date=TODAY,
        )
    )

    assert impact.requires_weekly_recovery
    assert not impact.prolonged_disruption


def test_long_illness_is_prolonged_disruption() -> None:
    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            23,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
    )

    impact = (
        evaluate_constraint_recovery_impact(
            constraint=constraint,
            reference_date=TODAY,
        )
    )

    assert impact.requires_weekly_recovery
    assert impact.prolonged_disruption


def test_injury_uses_same_physiological_policy() -> None:
    constraint = _constraint(
        constraint_type="injury",
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2026,
            8,
            27,
        ),
    )

    assert constraints_require_weekly_recovery(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_limited_injury_can_force_recovery() -> None:
    constraint = _constraint(
        constraint_type="injury",
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2026,
            8,
            27,
        ),
        availability="limited",
        running_allowed=False,
    )

    assert constraints_require_weekly_recovery(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_minor_limited_injury_does_not_force_recovery() -> None:
    constraint = _constraint(
        constraint_type="injury",
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2026,
            8,
            25,
        ),
        availability="limited",
        running_allowed=True,
        max_duration_minutes=60,
    )

    assert not constraints_require_weekly_recovery(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_work_absence_never_becomes_physiological_recovery() -> None:
    constraint = _constraint(
        constraint_type="work",
        start_date=date(
            2026,
            8,
            24,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
    )

    impact = (
        evaluate_constraint_recovery_impact(
            constraint=constraint,
            reference_date=TODAY,
        )
    )

    assert not impact.requires_weekly_recovery
    assert not impact.prolonged_disruption


def test_week_of_travel_does_not_force_recovery() -> None:
    constraint = _constraint(
        constraint_type="travel",
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
    )

    assert not constraints_require_weekly_recovery(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_prolonged_signal_only_applies_to_health_constraints() -> None:
    illness = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            23,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
    )

    work = _constraint(
        constraint_type="work",
        start_date=date(
            2026,
            8,
            23,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
    )

    assert (
        constraints_have_prolonged_physiological_disruption(
            constraints=(
                illness,
                work,
            ),
            reference_date=TODAY,
        )
    )


def test_active_long_illness_does_not_start_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            22,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_ended_long_illness_starts_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            19,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_ended_long_injury_starts_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="injury",
        start_date=date(
            2026,
            8,
            18,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_short_illness_does_not_start_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            23,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_old_illness_no_longer_requests_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            5,
        ),
        end_date=date(
            2026,
            8,
            15,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_ended_work_absence_never_starts_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="work",
        start_date=date(
            2026,
            8,
            17,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_ended_travel_never_starts_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="travel",
        start_date=date(
            2026,
            8,
            17,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_active_long_illness_does_not_start_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            22,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_ended_long_illness_starts_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            19,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_ended_long_injury_starts_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="injury",
        start_date=date(
            2026,
            8,
            18,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_short_illness_does_not_start_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            23,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_old_illness_no_longer_requests_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="illness",
        start_date=date(
            2026,
            8,
            5,
        ),
        end_date=date(
            2026,
            8,
            15,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_ended_work_absence_never_starts_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="work",
        start_date=date(
            2026,
            8,
            17,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )


def test_ended_travel_never_starts_return_to_training() -> None:
    from opencoach.coaching.constraint_impact import (
        constraints_require_return_to_training,
    )

    constraint = _constraint(
        constraint_type="travel",
        start_date=date(
            2026,
            8,
            17,
        ),
        end_date=date(
            2026,
            8,
            24,
        ),
    )

    assert not constraints_require_return_to_training(
        constraints=(
            constraint,
        ),
        reference_date=TODAY,
    )
