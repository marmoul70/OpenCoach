from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import httpx

from opencoach.integrations.coros.client import DEFAULT_COROS_MCP_URL
from opencoach.integrations.coros.errors import (
    CorosMcpAuthenticationError,
    CorosMcpProtocolError,
)


DEFAULT_COROS_ISSUER = "https://mcpeu.coros.com"
DEFAULT_COROS_SCOPES = "openid offline_access mcp.tools"


@dataclass(frozen=True, slots=True)
class CorosOAuthClient:
    client_id: str
    redirect_uri: str


@dataclass(frozen=True, slots=True)
class CorosPendingLogin:
    client_id: str
    code_verifier: str
    state: str
    authorize_url: str
    session_id: str
    poll_token: str
    login_url: str


@dataclass(frozen=True, slots=True)
class CorosTokenSet:
    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "Bearer"
    scope: str = DEFAULT_COROS_SCOPES


class CorosOAuthClientService:
    """Flux OAuth navigateur documenté par COROS MCP.

    Les objets contenant poll_token, code_verifier et jetons sont des
    données sensibles : l'appelant doit les chiffrer avant persistance.
    """

    def __init__(
        self,
        *,
        issuer: str = DEFAULT_COROS_ISSUER,
        mcp_url: str = DEFAULT_COROS_MCP_URL,
        redirect_uri: str,
        timeout: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not redirect_uri.startswith("https://") and not redirect_uri.startswith(
            "http://127.0.0.1"
        ):
            raise ValueError("L'URI de redirection OAuth doit être sécurisée.")

        self.issuer = issuer.rstrip("/")
        self.mcp_url = mcp_url
        self.redirect_uri = redirect_uri
        self.timeout = timeout
        self.transport = transport

    def begin_login(self) -> CorosPendingLogin:
        client_id = self._register_client()
        verifier = _create_pkce_verifier()
        challenge = _create_pkce_challenge(verifier)
        state = secrets.token_urlsafe(32)

        query = urlencode(
            {
                "response_type": "code",
                "client_id": client_id,
                "redirect_uri": self.redirect_uri,
                "scope": DEFAULT_COROS_SCOPES,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
                "resource": self.mcp_url,
                "state": state,
            }
        )
        authorize_url = f"{self.issuer}/oauth2/authorize?{query}"

        session = self._request_json(
            "POST",
            f"{self.issuer}/api/v1/cli/login-sessions",
            json_body={"clientId": client_id},
        )

        required = ("sessionId", "pollToken", "loginUrl")
        if not all(
            isinstance(session.get(key), str) and session[key]
            for key in required
        ):
            raise CorosMcpProtocolError(
                "COROS n'a pas retourné une session de connexion complète."
            )

        return CorosPendingLogin(
            client_id=client_id,
            code_verifier=verifier,
            state=state,
            authorize_url=authorize_url,
            session_id=session["sessionId"],
            poll_token=session["pollToken"],
            login_url=session["loginUrl"],
        )

    def claim_login_ticket(
        self,
        pending: CorosPendingLogin,
    ) -> str | None:
        """Retourne le login ticket après consentement, ou None si pending."""
        payload = self._request_json(
            "POST",
            (
                f"{self.issuer}/api/v1/cli/login-sessions/"
                f"{pending.session_id}/claim"
            ),
            headers={"X-Poll-Token": pending.poll_token},
        )

        status = str(payload.get("status", "")).lower()
        if status == "pending":
            return None
        if status == "authorized":
            ticket = payload.get("loginTicket")
            if isinstance(ticket, str) and ticket:
                return ticket
            raise CorosMcpProtocolError(
                "La session COROS autorisée ne contient pas de login ticket."
            )
        if status in {"expired", "failed", "claimed"}:
            raise CorosMcpAuthenticationError(
                f"La session de connexion COROS est {status}."
            )
        raise CorosMcpProtocolError(
            "COROS a retourné un état de connexion inconnu."
        )

    def exchange_login_ticket(
        self,
        pending: CorosPendingLogin,
        login_ticket: str,
    ) -> CorosTokenSet:
        if not login_ticket:
            raise ValueError("Le login ticket COROS est obligatoire.")

        parsed = urlparse(pending.authorize_url)
        query = list(
            __import__("urllib.parse", fromlist=["parse_qsl"]).parse_qsl(
                parsed.query,
                keep_blank_values=True,
            )
        )
        query.append(("login_ticket", login_ticket))
        authorize_url = urlunparse(
            parsed._replace(query=urlencode(query))
        )

        try:
            with httpx.Client(
                timeout=self.timeout,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                response = client.get(authorize_url)
        except httpx.HTTPError as exc:
            raise CorosMcpProtocolError(
                "Impossible de terminer l'autorisation COROS."
            ) from exc

        if response.status_code not in {302, 303}:
            raise CorosMcpAuthenticationError(
                "COROS n'a pas finalisé l'autorisation OAuth."
            )

        callback_url = response.headers.get("location")
        if not callback_url:
            raise CorosMcpProtocolError(
                "La redirection OAuth COROS ne contient pas de callback."
            )

        callback_query = parse_qs(urlparse(callback_url).query)
        code = callback_query.get("code", [""])[0]
        returned_state = callback_query.get("state", [""])[0]

        if not code or not returned_state:
            raise CorosMcpProtocolError(
                "Le callback COROS ne contient pas code et state."
            )
        if not secrets.compare_digest(returned_state, pending.state):
            raise CorosMcpAuthenticationError(
                "La validation state OAuth COROS a échoué."
            )

        payload = self._request_form(
            f"{self.issuer}/oauth2/token",
            {
                "grant_type": "authorization_code",
                "client_id": pending.client_id,
                "code": code,
                "redirect_uri": self.redirect_uri,
                "code_verifier": pending.code_verifier,
            },
        )
        return _token_set(payload)

    def refresh(self, client_id: str, refresh_token: str) -> CorosTokenSet:
        payload = self._request_form(
            f"{self.issuer}/oauth2/token",
            {
                "grant_type": "refresh_token",
                "client_id": client_id,
                "refresh_token": refresh_token,
            },
        )
        return _token_set(payload)

    def _register_client(self) -> str:
        payload = self._request_json(
            "POST",
            f"{self.issuer}/connect/register",
            json_body={
                "client_name": "OpenCoach",
                "redirect_uris": [self.redirect_uri],
                "grant_types": ["authorization_code", "refresh_token"],
                "response_types": ["code"],
                "scope": DEFAULT_COROS_SCOPES,
                "token_endpoint_auth_method": "none",
            },
        )
        client_id = payload.get("client_id")
        if not isinstance(client_id, str) or not client_id:
            raise CorosMcpProtocolError(
                "COROS n'a pas retourné de client_id OAuth."
            )
        return client_id

    def _request_json(
        self,
        method: str,
        url: str,
        *,
        json_body: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict:
        request_headers = {"Accept": "application/json"}
        request_headers.update(headers or {})
        try:
            with httpx.Client(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = client.request(
                    method,
                    url,
                    json=json_body,
                    headers=request_headers,
                )
        except httpx.HTTPError as exc:
            raise CorosMcpProtocolError(
                "Impossible de communiquer avec le service OAuth COROS."
            ) from exc

        if response.status_code in {400, 401, 403}:
            raise CorosMcpAuthenticationError(
                "Le service OAuth COROS a refusé la requête."
            )
        if not response.is_success:
            raise CorosMcpProtocolError(
                f"Le service OAuth COROS a retourné HTTP {response.status_code}."
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise CorosMcpProtocolError(
                "Le service OAuth COROS a retourné un JSON invalide."
            ) from exc
        if not isinstance(payload, dict):
            raise CorosMcpProtocolError(
                "La réponse OAuth COROS doit être un objet."
            )
        return payload

    def _request_form(
        self,
        url: str,
        form: dict[str, str],
    ) -> dict:
        try:
            with httpx.Client(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = client.post(url, data=form)
        except httpx.HTTPError as exc:
            raise CorosMcpProtocolError(
                "Impossible d'échanger les jetons OAuth COROS."
            ) from exc

        if response.status_code in {400, 401, 403}:
            raise CorosMcpAuthenticationError(
                "L'échange OAuth COROS a été refusé."
            )
        if not response.is_success:
            raise CorosMcpProtocolError(
                f"L'échange OAuth COROS a retourné HTTP {response.status_code}."
            )
        try:
            payload = response.json()
        except ValueError as exc:
            raise CorosMcpProtocolError(
                "La réponse de jetons COROS est invalide."
            ) from exc
        if not isinstance(payload, dict):
            raise CorosMcpProtocolError(
                "La réponse de jetons COROS doit être un objet."
            )
        return payload


def _create_pkce_verifier() -> str:
    return base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode("ascii").rstrip("=")


def _create_pkce_challenge(verifier: str) -> str:
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _token_set(payload: dict) -> CorosTokenSet:
    access_token = payload.get("access_token")
    refresh_token = payload.get("refresh_token")
    if not isinstance(access_token, str) or not access_token:
        raise CorosMcpProtocolError(
            "La réponse OAuth COROS ne contient pas d'access_token."
        )
    if not isinstance(refresh_token, str) or not refresh_token:
        raise CorosMcpProtocolError(
            "La réponse OAuth COROS ne contient pas de refresh_token."
        )
    try:
        expires_in = int(payload.get("expires_in", 3600))
    except (TypeError, ValueError) as exc:
        raise CorosMcpProtocolError(
            "La durée de validité du jeton COROS est invalide."
        ) from exc

    return CorosTokenSet(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
        token_type=str(payload.get("token_type", "Bearer")),
        scope=str(payload.get("scope", DEFAULT_COROS_SCOPES)),
    )
