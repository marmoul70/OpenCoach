import pytest
from pydantic import ValidationError

from opencoach.api.auth import (
    ChangePinRequest,
    router,
)


def test_change_pin_request():
    payload = ChangePinRequest(
        current_pin="123456",
        new_pin="654321",
    )

    assert (
        payload.current_pin
        == "123456"
    )

    assert (
        payload.new_pin
        == "654321"
    )


def test_change_pin_rejects_short_pin():
    with pytest.raises(
        ValidationError,
    ):
        ChangePinRequest(
            current_pin="123456",
            new_pin="123",
        )


def test_change_pin_route_exists():
    paths = {
        route.path
        for route in router.routes
    }

    assert (
        "/api/auth/change-pin"
        in paths
    )
