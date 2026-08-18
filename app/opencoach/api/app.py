from fastapi import FastAPI

from opencoach.api.intervals import router as intervals_router
from opencoach.api.profile import router as profile_router
from opencoach.api.activities import router as activities_router
from opencoach.api.wellness import router as wellness_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenCoach API",
        version="0.1.0",
    )

    app.include_router(profile_router)
    app.include_router(intervals_router)
    app.include_router(activities_router)
    app.include_router(wellness_router)

    return app


app = create_app()