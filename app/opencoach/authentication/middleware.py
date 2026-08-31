"""Middleware de protection HTTP OpenCoach."""

from __future__ import annotations

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)
from starlette.requests import Request
from starlette.responses import (
    JSONResponse,
)

from opencoach.authentication.auth import (
    COOKIE_NAME,
    verify_session_token,
)


PUBLIC_PATHS = {
    "/api/auth/login",
    "/api/auth/session",
    "/api/auth/logout",
    "/api/health",
    "/api/health/ready",
}

PROTECTED_EXACT_PATHS = {
    "/docs",
    "/redoc",
    "/openapi.json",
}


class AuthenticationMiddleware(
    BaseHTTPMiddleware
):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ):
        path = (
            request.url.path
        )

        requires_auth = (
            (
                path.startswith(
                    "/api/"
                )
                and path
                not in PUBLIC_PATHS
            )
            or path
            in PROTECTED_EXACT_PATHS
        )

        if requires_auth:
            token = (
                request.cookies.get(
                    COOKIE_NAME
                )
            )

            if not (
                verify_session_token(
                    token
                )
            ):
                return JSONResponse(
                    status_code=401,
                    content={
                        "detail": (
                            "Authentification "
                            "requise."
                        )
                    },
                )

        return await call_next(
            request
        )
