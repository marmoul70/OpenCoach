from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from opencoach.api.coaching.dependencies import (
    build_weekly_debrief_application_service,
)
from opencoach.coaching.weekly_debrief_application import (
    WeeklyDebriefApplicationService,
)
from opencoach.coaching.weekly_debrief_sql_runtime import (
    SqlWeeklyDebriefRuntime,
)


def test_build_weekly_debrief_application_service() -> None:
    engine = create_engine(
        "sqlite:///:memory:"
    )

    with Session(engine) as database:
        service = (
            build_weekly_debrief_application_service(
                database
            )
        )

    assert isinstance(
        service,
        WeeklyDebriefApplicationService,
    )

    assert isinstance(
        service._runtime,
        SqlWeeklyDebriefRuntime,
    )

    assert service._planning_context_resolver is None

    assert callable(
        service._planning_context_factory
    )



def test_weekly_debrief_composition_exposes_profile_scoped_factory() -> None:
    """La composition batch doit pouvoir être construite par profil."""
    from inspect import signature

    parameters = signature(
        build_weekly_debrief_application_service
    ).parameters

    assert "planning_context_factory" in parameters
