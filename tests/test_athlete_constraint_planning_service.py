from __future__ import annotations

from datetime import date
from uuid import UUID, uuid4

from opencoach.coaching.constraint_planning import (
    AthleteConstraintPlanningService,
    constraint_affects_current_week,
)
from opencoach.models import AthleteConstraint


class FakeConstraintRepository:
    def __init__(self) -> None:
        self.constraints: dict[
            UUID,
            AthleteConstraint,
        ] = {}

    def save_constraint(
        self,
        athlete_profile_id: UUID,
        constraint: AthleteConstraint,
    ) -> AthleteConstraint:
        self.constraints[
            constraint.id
        ] = constraint

        return constraint

    def get_constraint(
        self,
        athlete_profile_id: UUID,
        constraint_id: UUID,
    ) -> AthleteConstraint | None:
        return self.constraints.get(
            constraint_id
        )

    def delete_constraint(
        self,
        athlete_profile_id: UUID,
        constraint_id: UUID,
    ) -> None:
        if constraint_id not in self.constraints:
            raise RuntimeError(
                "Contrainte introuvable."
            )

        del self.constraints[
            constraint_id
        ]


class FakeCurrentWeekPlanningService:
    def __init__(self) -> None:
        self.calls: list[
            dict[str, object]
        ] = []

    def refresh(
        self,
        **kwargs,
    ) -> object:
        self.calls.append(
            kwargs
        )

        return object()


def _constraint(
    *,
    start_date: date,
    end_date: date,
    constraint_type: str = "work",
    availability: str = "unavailable",
    constraint_id: UUID | None = None,
) -> AthleteConstraint:
    return AthleteConstraint(
        id=(
            constraint_id
            or uuid4()
        ),
        start_date=start_date,
        end_date=end_date,
        constraint_type=constraint_type,  # type: ignore[arg-type]
        availability=availability,  # type: ignore[arg-type]
        running_allowed=False,
        cross_training_allowed=False,
    )


def _service():
    repository = (
        FakeConstraintRepository()
    )

    planner = (
        FakeCurrentWeekPlanningService()
    )

    service = (
        AthleteConstraintPlanningService(
            repository=repository,  # type: ignore[arg-type]
            current_week_planning_service=planner,  # type: ignore[arg-type]
        )
    )

    return (
        service,
        repository,
        planner,
    )


def test_constraint_detects_current_week_overlap() -> None:
    constraint = _constraint(
        start_date=date(
            2026,
            8,
            26,
        ),
        end_date=date(
            2026,
            8,
            26,
        ),
    )

    assert constraint_affects_current_week(
        constraint=constraint,
        reference_date=date(
            2026,
            8,
            25,
        ),
    )


def test_work_absence_refreshes_current_week() -> None:
    service, _, planner = (
        _service()
    )

    athlete_profile_id = uuid4()

    service.save(
        athlete_profile_id=(
            athlete_profile_id
        ),
        constraint=_constraint(
            start_date=date(
                2026,
                8,
                26,
            ),
            end_date=date(
                2026,
                8,
                26,
            ),
            constraint_type="work",
        ),
        reference_date=date(
            2026,
            8,
            25,
        ),
    )

    assert len(
        planner.calls
    ) == 1

    assert (
        planner.calls[0][
            "athlete_profile_id"
        ]
        == athlete_profile_id
    )

    assert (
        planner.calls[0][
            "additional_context"
        ]
        == (
            "contrainte professionnelle",
        )
    )


def test_illness_refreshes_current_week() -> None:
    service, _, planner = (
        _service()
    )

    service.save(
        athlete_profile_id=uuid4(),
        constraint=_constraint(
            start_date=date(
                2026,
                8,
                25,
            ),
            end_date=date(
                2026,
                8,
                27,
            ),
            constraint_type="illness",
        ),
        reference_date=date(
            2026,
            8,
            25,
        ),
    )

    assert len(
        planner.calls
    ) == 1

    assert (
        planner.calls[0][
            "additional_context"
        ]
        == (
            "maladie ou problème de santé temporaire",
        )
    )


def test_future_constraint_does_not_refresh_current_week(
) -> None:
    service, _, planner = (
        _service()
    )

    service.save(
        athlete_profile_id=uuid4(),
        constraint=_constraint(
            start_date=date(
                2026,
                9,
                10,
            ),
            end_date=date(
                2026,
                9,
                12,
            ),
        ),
        reference_date=date(
            2026,
            8,
            25,
        ),
    )

    assert (
        planner.calls
        == []
    )


def test_moving_constraint_out_of_week_refreshes_old_state(
) -> None:
    service, repository, planner = (
        _service()
    )

    athlete_profile_id = uuid4()
    constraint_id = uuid4()

    repository.constraints[
        constraint_id
    ] = _constraint(
        constraint_id=constraint_id,
        start_date=date(
            2026,
            8,
            26,
        ),
        end_date=date(
            2026,
            8,
            26,
        ),
    )

    service.save(
        athlete_profile_id=(
            athlete_profile_id
        ),
        constraint=_constraint(
            constraint_id=constraint_id,
            start_date=date(
                2026,
                9,
                10,
            ),
            end_date=date(
                2026,
                9,
                10,
            ),
        ),
        reference_date=date(
            2026,
            8,
            25,
        ),
    )

    assert len(
        planner.calls
    ) == 1


def test_deleting_current_constraint_refreshes_week() -> None:
    service, repository, planner = (
        _service()
    )

    athlete_profile_id = uuid4()
    constraint_id = uuid4()

    repository.constraints[
        constraint_id
    ] = _constraint(
        constraint_id=constraint_id,
        start_date=date(
            2026,
            8,
            25,
        ),
        end_date=date(
            2026,
            8,
            28,
        ),
        constraint_type="illness",
    )

    service.delete(
        athlete_profile_id=(
            athlete_profile_id
        ),
        constraint_id=(
            constraint_id
        ),
        reference_date=date(
            2026,
            8,
            25,
        ),
    )

    assert len(
        planner.calls
    ) == 1

    assert (
        planner.calls[0][
            "additional_context"
        ]
        == (
            "contrainte athlète supprimée",
        )
    )
