from __future__ import annotations

from copy import deepcopy
from typing import Any

from opencoach.integrations.coros.errors import CorosMcpAuthenticationError
from opencoach.integrations.coros.oauth import CorosOAuthClientService

TOKEN_REFRESH_SKEW_SECONDS = 60


def refresh_secret_if_needed(secret: dict[str, Any], oauth: CorosOAuthClientService, *, now: float, skew_seconds: int = TOKEN_REFRESH_SKEW_SECONDS) -> dict[str, Any]:
    """Renouvelle les jetons avant expiration et conserve leur rotation."""
    refreshed = deepcopy(secret)
    try:
        expires_at = float(refreshed.get("expires_at", 0))
    except (TypeError, ValueError):
        expires_at = 0.0
    if expires_at > now + skew_seconds:
        return refreshed
    client_id = refreshed.get("client_id")
    refresh_token = refreshed.get("refresh_token")
    if not isinstance(client_id, str) or not client_id or not isinstance(refresh_token, str) or not refresh_token:
        raise CorosMcpAuthenticationError("La connexion COROS doit être réautorisée.")
    tokens = oauth.refresh(client_id, refresh_token)
    refreshed.update({"status": "connected", "access_token": tokens.access_token, "refresh_token": tokens.refresh_token, "token_type": tokens.token_type, "scope": tokens.scope, "expires_at": now + tokens.expires_in})
    return refreshed
