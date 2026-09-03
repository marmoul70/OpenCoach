import pytest
from pydantic import ValidationError

from opencoach.api.auth import (
    LoginRequest,
    router,
)


def test_login_requires_username_and_pin():
    request = LoginRequest(
        username="ys001",
        pin="123456",
    )

    assert request.username == "ys001"
    assert request.pin == "123456"


def test_login_refuses_missing_username():
    with pytest.raises(
        ValidationError,
    ):
        LoginRequest(
            pin="123456",
        )


def test_legacy_login_route_removed():
    paths = {
        route.path
        for route in router.routes
    }

    assert "/api/auth/login" in paths
    assert (
        "/api/auth/login/legacy"
        not in paths
    )
