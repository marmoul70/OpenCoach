from opencoach.integrations.coros.errors import CorosMcpAuthenticationError
from opencoach.integrations.coros.oauth import CorosTokenSet
from opencoach.integrations.coros.tokens import refresh_secret_if_needed


class FakeOAuth:
    def __init__(self):
        self.calls = []

    def refresh(self, client_id, refresh_token):
        self.calls.append((client_id, refresh_token))
        return CorosTokenSet(access_token="new-access", refresh_token="rotated-refresh", expires_in=1800)


def test_tokens_are_not_refreshed_before_safety_window():
    oauth = FakeOAuth()
    secret = {"client_id": "client", "access_token": "valid-access", "refresh_token": "valid-refresh", "expires_at": 2000}
    result = refresh_secret_if_needed(secret, oauth, now=1000)
    assert result["access_token"] == "valid-access"
    assert oauth.calls == []
    assert secret["access_token"] == "valid-access"


def test_expiring_tokens_are_refreshed_and_rotation_is_persistable():
    oauth = FakeOAuth()
    secret = {"client_id": "client", "access_token": "old-access", "refresh_token": "old-refresh", "expires_at": 1050}
    result = refresh_secret_if_needed(secret, oauth, now=1000)
    assert oauth.calls == [("client", "old-refresh")]
    assert result["access_token"] == "new-access"
    assert result["refresh_token"] == "rotated-refresh"
    assert result["expires_at"] == 2800
    assert secret["refresh_token"] == "old-refresh"


def test_missing_refresh_token_requires_reauthorization():
    oauth = FakeOAuth()
    try:
        refresh_secret_if_needed({"client_id": "client", "expires_at": 0}, oauth, now=1000)
    except CorosMcpAuthenticationError:
        return
    raise AssertionError("Expected reauthorization error")
