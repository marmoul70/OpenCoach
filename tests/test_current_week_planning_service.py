from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID, uuid4

from opencoach.coaching.generation.current_week import (
    CurrentWeekPlanningService,
    current_week_start,
)


def test_current_week_start_returns_monday() -> None:
    assert (
        current_week_start(
            date(
                2026,
                8,
                25,
            )
        )
        == date(
            2026,
            8,
            24,
        )
    )


def test_current_week_start_keeps_monday() -> None:
    monday = date(
        2026,
        8,
        24,
    )

    assert (
        current_week_start(
            monday
        )
        == monday
    )


@dataclass
class _PreparedContext:
    planning_input: object


class _ContextBuilder:
    def __init__(self) -> None:
        self.calls: list[
            dict[str, object]
        ] = []

        self.planning_input = object()

    def build(
        self,
        *,
        athlete_profile_id: UUID,
        planning_date: date,
        trajectory_start_date: date,
    ) -> _PreparedContext:
        self.calls.append(
            {
                "athlete_profile_id": (
                    athlete_profile_id
                ),
                "planning_date": (
                    planning_date
                ),
                "trajectory_start_date": (
                    trajectory_start_date
                ),
            }
        )

        return _PreparedContext(
            planning_input=(
                self.planning_input
            )
        )


class _GenerationService:
    def __init__(self) -> None:
        self.calls: list[
            dict[str, object]
        ] = []

        self.result = object()

    def execute(
        self,
        *,
        athlete_profile_id: UUID,
        planning_input: object,
        physiological_reference_date: date,
        reconcile_from_date: date,
        additional_context: tuple[str, ...],
    ) -> object:
        self.calls.append(
            {
                "athlete_profile_id": (
                    athlete_profile_id
                ),
                "planning_input": (
                    planning_input
                ),
                "physiological_reference_date": (
                    physiological_reference_date
                ),
                "reconcile_from_date": (
                    reconcile_from_date
                ),
                "additional_context": (
                    additional_context
                ),
            }
        )

        return self.result


def test_refresh_uses_today_for_context_and_monday_for_trajectory(
) -> None:
    athlete_profile_id = uuid4()

    context_builder = (
        _ContextBuilder()
    )

    generation_service = (
        _GenerationService()
    )

    service = CurrentWeekPlanningService(
        context_builder=context_builder,  # type: ignore[arg-type]
        generation_service=generation_service,  # type: ignore[arg-type]
    )

    reference_date = date(
        2026,
        8,
        25,
    )

    result = service.refresh(
        athlete_profile_id=(
            athlete_profile_id
        ),
        reference_date=(
            reference_date
        ),
        additional_context=(
            "course principale modifiée",
        ),
    )

    assert result is generation_service.result

    assert context_builder.calls == [
        {
            "athlete_profile_id": (
                athlete_profile_id
            ),
            "planning_date": (
                date(
                    2026,
                    8,
                    25,
                )
            ),
            "trajectory_start_date": (
                date(
                    2026,
                    8,
                    24,
                )
            ),
        }
    ]

    assert generation_service.calls == [
        {
            "athlete_profile_id": (
                athlete_profile_id
            ),
            "planning_input": (
                context_builder.planning_input
            ),
            "physiological_reference_date": (
                reference_date
            ),
            "reconcile_from_date": (
                reference_date
            ),
            "additional_context": (
                "course principale modifiée",
            ),
        }
    ]
