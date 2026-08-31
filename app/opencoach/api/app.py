from fastapi import FastAPI

from opencoach.api.backups import router as backups_router
from opencoach.api.intervals import router as intervals_router
from opencoach.api.health import router as health_router
from opencoach.api.profile import router as profile_router
from opencoach.api.activities import router as activities_router
from opencoach.api.wellness import router as wellness_router
from opencoach.api.training_sessions import (
    router as training_sessions_router,
)
from opencoach.api.readiness import (
    router as readiness_router,
)
from opencoach.api.daily_context import (
    router as daily_context_router,
)
from opencoach.api.coach import (
    router as coach_router,
)
from opencoach.api.training_stats import (
    router as training_stats_router,
)
from opencoach.api.races import (
    router as races_router,
)
from opencoach.api.coaching.generation import (
    router as coach_generation_router,
)
from opencoach.api.coaching.constraints import (
    router as coach_constraints_router,
)
from opencoach.api.coaching.daily_checkin import (
    router as coach_daily_checkin_router,
)

from opencoach.api.coaching.physiological_tests import (
    router as coach_physiological_tests_router,
)

def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenCoach API",
        version="0.1.0",
    )

    app.include_router(health_router)
    app.include_router(backups_router)
    app.include_router(profile_router)
    app.include_router(intervals_router)
    app.include_router(activities_router)
    app.include_router(wellness_router)
    app.include_router(daily_context_router)
    app.include_router(training_sessions_router)
    app.include_router(races_router)
    app.include_router(training_stats_router)
    app.include_router(readiness_router)
    app.include_router(coach_router)
    app.include_router(
        coach_generation_router
    )
    app.include_router(
        coach_constraints_router
    )

    app.include_router(
        coach_daily_checkin_router
    )

    app.include_router(
        coach_physiological_tests_router
    )

    return app


app = create_app()
