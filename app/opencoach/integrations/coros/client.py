from __future__ import annotations

import json
from typing import Any

import httpx

from opencoach.integrations.coros.errors import (
    CorosMcpAuthenticationError,
    CorosMcpProtocolError,
    CorosMcpToolError,
)


DEFAULT_COROS_MCP_URL = "https://mcpeu.coros.com/mcp"
MCP_PROTOCOL_VERSION = "2025-06-18"


class CorosMcpClient:
    """Client HTTP MCP Streamable HTTP pour le serveur COROS officiel.

    Le client ne conserve aucun jeton : le service appelant fournit le
    jeton d'accès à chaque opération. Cela permet au service applicatif
    de gérer le chiffrement et le renouvellement OAuth séparément.
    """

    def __init__(
        self,
        access_token: str,
        *,
        endpoint: str = DEFAULT_COROS_MCP_URL,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        token = access_token.strip()
        if not token:
            raise ValueError("Le jeton d'accès COROS est obligatoire.")
        if not endpoint.startswith("https://"):
            raise ValueError("Le serveur MCP COROS doit utiliser HTTPS.")

        self._access_token = token
        self.endpoint = endpoint
        self.timeout = timeout
        self.transport = transport

    def list_tools(self) -> list[dict[str, Any]]:
        """Retourne le catalogue d'outils exposé par COROS MCP."""
        self._initialize()
        response = self._rpc("tools/list", {})
        result = response.get("result")
        if not isinstance(result, dict):
            raise CorosMcpProtocolError(
                "La réponse tools/list COROS est invalide."
            )

        tools = result.get("tools")
        if not isinstance(tools, list) or not all(
            isinstance(tool, dict) for tool in tools
        ):
            raise CorosMcpProtocolError(
                "Le catalogue d'outils COROS est invalide."
            )

        return tools

    def call_tool(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Exécute un outil COROS MCP découvert dans le catalogue."""
        normalized_name = name.strip()
        if not normalized_name:
            raise ValueError("Le nom de l'outil MCP est obligatoire.")

        self._initialize()
        response = self._rpc(
            "tools/call",
            {
                "name": normalized_name,
                "arguments": arguments or {},
            },
        )

        result = response.get("result")
        if not isinstance(result, dict):
            raise CorosMcpProtocolError(
                f"La réponse de l'outil COROS '{normalized_name}' est invalide."
            )

        if result.get("isError") is True:
            detail = _tool_error_detail(result)
            raise CorosMcpToolError(
                f"L'outil COROS '{normalized_name}' a refusé la requête"
                + (f" : {detail}" if detail else ".")
            )

        return result

    def _initialize(self) -> None:
        response = self._rpc(
            "initialize",
            {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {
                    "name": "OpenCoach",
                    "version": "0.1.0",
                },
            },
        )

        result = response.get("result")
        if not isinstance(result, dict):
            raise CorosMcpProtocolError(
                "La négociation MCP COROS n'a pas retourné de résultat."
            )

        self._notify_initialized()

    def _notify_initialized(self) -> None:
        payload = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }
        self._post(payload, expect_response=False)

    def _rpc(
        self,
        method: str,
        params: dict[str, Any],
    ) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }
        response = self._post(payload, expect_response=True)

        error = response.get("error")
        if isinstance(error, dict):
            code = error.get("code", "inconnu")
            message = error.get("message", "Erreur MCP")
            raise CorosMcpProtocolError(
                f"Erreur MCP COROS ({code}) : {message}"
            )

        return response

    def _post(
        self,
        payload: dict[str, Any],
        *,
        expect_response: bool,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "MCP-Protocol-Version": MCP_PROTOCOL_VERSION,
        }

        try:
            with httpx.Client(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = client.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                )
        except httpx.HTTPError as exc:
            raise CorosMcpProtocolError(
                "Impossible de joindre le serveur COROS MCP."
            ) from exc

        if response.status_code in {401, 403}:
            raise CorosMcpAuthenticationError(
                "Le serveur COROS MCP a refusé l'authentification."
            )

        if not response.is_success:
            raise CorosMcpProtocolError(
                f"Le serveur COROS MCP a retourné HTTP {response.status_code}."
            )

        if not expect_response:
            return {}

        try:
            data = self._decode_response(response)
        except (ValueError, json.JSONDecodeError) as exc:
            raise CorosMcpProtocolError(
                "Le serveur COROS MCP a retourné un JSON invalide."
            ) from exc

        if not isinstance(data, dict):
            raise CorosMcpProtocolError(
                "La réponse JSON-RPC COROS doit être un objet."
            )

        if data.get("jsonrpc") != "2.0":
            raise CorosMcpProtocolError(
                "La réponse COROS n'est pas une réponse JSON-RPC 2.0."
            )

        return data

    @staticmethod
    def _decode_response(response: httpx.Response) -> dict[str, Any]:
        content_type = response.headers.get("content-type", "").lower()
        if "text/event-stream" not in content_type:
            payload = response.json()
            if not isinstance(payload, dict):
                raise ValueError("Réponse JSON-RPC non objet.")
            return payload

        events = [
            line[5:].strip()
            for line in response.text.splitlines()
            if line.startswith("data:")
        ]
        if not events:
            raise ValueError("Flux SSE sans événement data.")
        payload = json.loads(events[-1])
        if not isinstance(payload, dict):
            raise ValueError("Événement SSE non objet.")
        return payload



def _tool_error_detail(result: dict[str, Any]) -> str:
    """Extrait un message textuel sans exposer les données de requête."""
    content = result.get("content")
    if not isinstance(content, list):
        return ""
    messages = [
        str(item.get("text", "")).strip()
        for item in content
        if isinstance(item, dict)
        and item.get("type") == "text"
        and item.get("text")
    ]
    return " ".join(messages)[:500]
