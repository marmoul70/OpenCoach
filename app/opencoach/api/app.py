from fastapi import FastAPI

from opencoach.api.profile import router as profile_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="OpenCoach API",
        version="0.1.0",
    )

    app.include_router(profile_router)

    return app


app = create_app()
