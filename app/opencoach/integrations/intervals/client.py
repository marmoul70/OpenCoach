from datetime import date

import httpx

from opencoach.integrations.intervals.errors import (
    IntervalsApiError,
    IntervalsAuthenticationError,
)


INTERVALS_BASE_URL = "https://intervals.icu/api/v1"


class IntervalsClient:
    """Client HTTP pour l'API Intervals.icu."""

    def __init__(
        self,
        api_key: str,
        athlete_id: str,
        *,
        timeout: float = 20.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        if not api_key:
            raise ValueError(
                "La clé API Intervals.icu est obligatoire."
            )

        if not athlete_id:
            raise ValueError(
                "L'identifiant athlète Intervals.icu est obligatoire."
            )

        self.api_key = api_key
        self.athlete_id = athlete_id
        self.timeout = timeout
        self.transport = transport

    def get_wellness(
        self,
        oldest: date,
        newest: date,
    ) -> list[dict]:
        """Retourne les données Wellness sur une période."""
        return self._get(
            f"/athlete/{self.athlete_id}/wellness",
            params={
                "oldest": oldest.isoformat(),
                "newest": newest.isoformat(),
            },
        )

    def get_activities(
        self,
        oldest: date,
        newest: date,
    ) -> list[dict]:
        """Retourne les activités sur une période."""
        return self._get(
            f"/athlete/{self.athlete_id}/activities",
            params={
                "oldest": oldest.isoformat(),
                "newest": newest.isoformat(),
            },
        )

    def _get(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> list[dict]:
        try:
            with httpx.Client(
                auth=httpx.BasicAuth(
                    "API_KEY",
                    self.api_key,
                ),
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = client.get(
                    f"{INTERVALS_BASE_URL}{path}",
                    params=params,
                )
        except httpx.HTTPError as exc:
            raise IntervalsApiError(
                "Impossible de contacter Intervals.icu."
            ) from exc

        if response.status_code in {401, 403}:
            raise IntervalsAuthenticationError(
                "Authentification Intervals.icu refusée."
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise IntervalsApiError(
                f"Intervals.icu a retourné HTTP "
                f"{response.status_code}."
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise IntervalsApiError(
                "Réponse JSON Intervals.icu invalide."
            ) from exc

        if not isinstance(data, list):
            raise IntervalsApiError(
                "Réponse Intervals.icu inattendue."
            )

        return data