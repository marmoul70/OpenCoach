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
    read_session_identity,
    verify_session_token,
)


PUBLIC_PATHS = {
    "/api/auth/register",
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

            identity = (
                read_session_identity(
                    token
                )
            )

            if (
                identity is None
                or identity.user_id is None
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

            request.state.user_id = (
                identity.user_id
            )

        return await call_next(
            request
        )
