from dataclasses import dataclass
from datetime import date
from typing import Literal

from opencoach.models import (
    AthleteConstraint,
    AthleteProfile,
)


DayAvailabilityStatus = Literal[
    "preferred",
    "non_preferred",
    "available_override",
    "limited",
    "unavailable",
]


@dataclass(frozen=True)
class DayAvailability:
    """Disponibilité effective de l'athlète pour une journée."""

    date: date

    preferred: bool
    status: DayAvailabilityStatus

    training_allowed: bool
    requires_confirmation: bool

    running_allowed: bool
    cross_training_allowed: bool

    max_duration_minutes: int | None

    constraints: tuple[AthleteConstraint, ...]


def resolve_day_availability(
    *,
    athlete: AthleteProfile,
    target_date: date,
    constraints: tuple[AthleteConstraint, ...] = (),
) -> DayAvailability:
    """Calcule la disponibilité effective pour une journée."""

    preferred = (
        target_date.weekday()
        in athlete.training.available_days
    )

    active_constraints = tuple(
        constraint
        for constraint in constraints
        if constraint.is_active_on(
            target_date
        )
    )

    unavailable_constraints = tuple(
        constraint
        for constraint in active_constraints
        if constraint.availability
        == "unavailable"
    )

    if unavailable_constraints:
        return DayAvailability(
            date=target_date,
            preferred=preferred,
            status="unavailable",
            training_allowed=False,
            requires_confirmation=False,
            running_allowed=False,
            cross_training_allowed=False,
            max_duration_minutes=None,
            constraints=active_constraints,
        )

    limited_constraints = tuple(
        constraint
        for constraint in active_constraints
        if constraint.availability
        == "limited"
    )

    if limited_constraints:
        running_allowed = all(
            constraint.running_allowed
            for constraint in limited_constraints
        )

        cross_training_allowed = all(
            constraint.cross_training_allowed
            for constraint in limited_constraints
        )

        duration_limits = [
            constraint.max_duration_minutes
            for constraint in limited_constraints
            if constraint.max_duration_minutes
            is not None
        ]

        max_duration_minutes = (
            min(duration_limits)
            if duration_limits
            else None
        )

        training_allowed = (
            running_allowed
            or cross_training_allowed
        )

        return DayAvailability(
            date=target_date,
            preferred=preferred,
            status=(
                "limited"
                if training_allowed
                else "unavailable"
            ),
            training_allowed=training_allowed,
            requires_confirmation=False,
            running_allowed=running_allowed,
            cross_training_allowed=(
                cross_training_allowed
            ),
            max_duration_minutes=(
                max_duration_minutes
            ),
            constraints=active_constraints,
        )

    has_available_override = any(
        constraint.availability
        == "available_override"
        for constraint in active_constraints
    )

    if has_available_override:
        return DayAvailability(
            date=target_date,
            preferred=preferred,
            status="available_override",
            training_allowed=True,
            requires_confirmation=False,
            running_allowed=True,
            cross_training_allowed=True,
            max_duration_minutes=None,
            constraints=active_constraints,
        )

    if preferred:
        return DayAvailability(
            date=target_date,
            preferred=True,
            status="preferred",
            training_allowed=True,
            requires_confirmation=False,
            running_allowed=True,
            cross_training_allowed=True,
            max_duration_minutes=None,
            constraints=(),
        )

    return DayAvailability(
        date=target_date,
        preferred=False,
        status="non_preferred",
        training_allowed=True,
        requires_confirmation=True,
        running_allowed=True,
        cross_training_allowed=True,
        max_duration_minutes=None,
        constraints=(),
    )
