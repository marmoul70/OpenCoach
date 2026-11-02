import json

import httpx
import pytest

from opencoach.integrations.coros.client import (
    CorosMcpClient,
    DEFAULT_COROS_MCP_URL,
)
from opencoach.integrations.coros.errors import (
    CorosMcpAuthenticationError,
    CorosMcpProtocolError,
)


def test_coros_client_uses_streamable_http_and_lists_tools():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        payload = json.loads(request.content)

        if payload["method"] == "initialize":
            result = {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "serverInfo": {"name": "COROS MCP", "version": "1"},
            }
            return httpx.Response(
                200,
                json={"jsonrpc": "2.0", "id": payload["id"], "result": result},
            )

        if payload["method"] == "notifications/initialized":
            return httpx.Response(202)

        if payload["method"] == "tools/list":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": payload["id"],
                    "result": {
                        "tools": [{"name": "querySportRecords", "inputSchema": {}}],
                    },
                },
            )

        return httpx.Response(400)

    client = CorosMcpClient(
        "test-access-token",
        transport=httpx.MockTransport(handler),
    )

    tools = client.list_tools()

    assert tools[0]["name"] == "querySportRecords"
    assert [json.loads(item.content)["method"] for item in requests] == [
        "initialize",
        "notifications/initialized",
        "tools/list",
    ]
    assert all(
        item.headers["authorization"] == "Bearer test-access-token"
        for item in requests
    )


def test_coros_client_calls_tool():
    def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)

        if payload["method"] == "initialize":
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": payload["id"],
                    "result": {"protocolVersion": "2025-06-18"},
                },
            )

        if payload["method"] == "notifications/initialized":
            return httpx.Response(202)

        if payload["method"] == "tools/call":
            assert payload["params"] == {
                "name": "querySleepOverview",
                "arguments": {"days": 7},
            }
            return httpx.Response(
                200,
                json={
                    "jsonrpc": "2.0",
                    "id": payload["id"],
                    "result": {"content": [{"type": "text", "text": "sleep"}]},
                },
            )

        return httpx.Response(400)

    client = CorosMcpClient(
        "test-access-token",
        transport=httpx.MockTransport(handler),
    )

    result = client.call_tool(
        "querySleepOverview",
        {"days": 7},
    )

    assert result["content"][0]["text"] == "sleep"


def test_coros_client_rejects_non_https_endpoint():
    with pytest.raises(ValueError, match="HTTPS"):
        CorosMcpClient(
            "test-access-token",
            endpoint="http://localhost/mcp",
        )


def test_coros_client_maps_unauthorized_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401)

    client = CorosMcpClient(
        "test-access-token",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(CorosMcpAuthenticationError):
        client.list_tools()


def test_coros_client_rejects_invalid_json_rpc_response():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"unexpected": True})

    client = CorosMcpClient(
        "test-access-token",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(CorosMcpProtocolError, match="JSON-RPC"):
        client.list_tools()


def test_coros_endpoint_defaults_to_europe():
    assert DEFAULT_COROS_MCP_URL == "https://mcp.coros.com/mcp"
