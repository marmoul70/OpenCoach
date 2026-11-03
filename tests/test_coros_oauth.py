from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from opencoach.integrations.coros.oauth import (
    CorosOAuthClientService,
    CorosPendingLogin,
)


def test_begin_login_registers_client_and_creates_browser_session():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path == "/connect/register":
            return httpx.Response(201, json={"client_id": "client-123"})
        if request.url.path == "/api/v1/cli/login-sessions":
            return httpx.Response(
                201,
                json={
                    "sessionId": "session-123",
                    "pollToken": "poll-secret",
                    "loginUrl": "https://coros.com/authorize",
                },
            )
        return httpx.Response(404)

    service = CorosOAuthClientService(
        redirect_uri="https://opencoach.example.com/api/integrations/coros/oauth/callback",
        transport=httpx.MockTransport(handler),
    )

    pending = service.begin_login()

    assert pending.client_id == "client-123"
    assert pending.session_id == "session-123"
    assert pending.poll_token == "poll-secret"
    query = parse_qs(urlparse(pending.authorize_url).query)
    assert query["code_challenge_method"] == ["S256"]
    assert query["scope"] == ["openid offline_access mcp.tools"]
    assert query["resource"] == ["https://mcpeu.coros.com/mcp"]
    assert len(calls) == 2


def test_claim_login_ticket_returns_none_while_pending():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"status": "pending"})

    service = CorosOAuthClientService(
        redirect_uri="https://opencoach.example.com/callback",
        transport=httpx.MockTransport(handler),
    )
    pending = CorosPendingLogin(
        client_id="client",
        code_verifier="verifier",
        state="state",
        authorize_url="https://mcpeu.coros.com/oauth2/authorize",
        session_id="session",
        poll_token="poll",
        login_url="https://coros.com/login",
    )

    assert service.claim_login_ticket(pending) is None


def test_claim_login_ticket_returns_authorized_ticket():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-poll-token"] == "poll-secret"
        return httpx.Response(
            200,
            json={"status": "authorized", "loginTicket": "ticket-123"},
        )

    service = CorosOAuthClientService(
        redirect_uri="https://opencoach.example.com/callback",
        transport=httpx.MockTransport(handler),
    )
    pending = CorosPendingLogin(
        client_id="client",
        code_verifier="verifier",
        state="state",
        authorize_url="https://mcpeu.coros.com/oauth2/authorize",
        session_id="session",
        poll_token="poll-secret",
        login_url="https://coros.com/login",
    )

    assert service.claim_login_ticket(pending) == "ticket-123"


def test_oauth_rejects_insecure_redirect_uri():
    with pytest.raises(ValueError, match="sécurisées"):
        CorosOAuthClientService(
            redirect_uri="http://opencoach.example.com/callback",
        )
