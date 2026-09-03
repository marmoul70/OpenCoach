import pytest
from pydantic import ValidationError

from opencoach.api.auth import (
    AccountResponse,
    UpdateAccountRequest,
    router,
)


def test_account_response():
    response = AccountResponse(
        username="ys001",
        email="user@example.com",
        active=True,
    )

    assert response.username == "ys001"
    assert response.active is True


def test_update_account_request():
    payload = UpdateAccountRequest(
        email="new@example.com",
    )

    assert (
        payload.email
        == "new@example.com"
    )


def test_update_account_rejects_empty_email():
    with pytest.raises(
        ValidationError,
    ):
        UpdateAccountRequest(
            email="",
        )


def test_account_routes_exist():
    routes = {
        (
            route.path,
            tuple(
                sorted(
                    route.methods
                    or set(),
                )
            ),
        )
        for route in router.routes
    }

    assert any(
        path
        == "/api/auth/account"
        and "GET" in methods
        for path, methods in routes
    )

    assert any(
        path
        == "/api/auth/account"
        and "PATCH" in methods
        for path, methods in routes
    )
