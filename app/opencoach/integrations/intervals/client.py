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

    def get_athlete(
        self,
    ) -> dict:
        """Retourne le profil de l'athlète connecté."""
        return self._get_object(
            f"/athlete/{self.athlete_id}",
        )

    def get_wellness(
        self,
        oldest: date,
        newest: date,
    ) -> list[dict]:
        """Retourne les données Wellness sur une période."""
        return self._get_list(
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
        return self._get_list(
            f"/athlete/{self.athlete_id}/activities",
            params={
                "oldest": oldest.isoformat(),
                "newest": newest.isoformat(),
            },
        )

    def get_activity_details(
        self,
        activity_id: str,
        *,
        include_intervals: bool = True,
    ) -> dict:
        """Retourne le détail d'une activité Intervals.icu.

        Lorsque ``include_intervals`` est activé, la réponse contient
        notamment les intervalles analysés dans ``icu_intervals``.
        """

        activity_id = self._validate_activity_id(
            activity_id,
        )

        return self._get_object(
            f"/activity/{activity_id}",
            params={
                "intervals": (
                    "true"
                    if include_intervals
                    else "false"
                ),
            },
        )

    def get_activity_streams(
        self,
        activity_id: str,
        *,
        types: tuple[str, ...] = (
            "time",
            "distance",
            "heartrate",
            "velocity_smooth",
            "cadence",
            "watts",
        ),
    ) -> list[dict]:
        """Retourne les streams utiles à l'analyse d'une activité.

        Les flux GPS ne font volontairement pas partie du contrat
        OpenCoach.
        """

        activity_id = self._validate_activity_id(
            activity_id,
        )

        cleaned_types = tuple(
            stream_type.strip()
            for stream_type in types
            if stream_type.strip()
        )

        if not cleaned_types:
            raise ValueError(
                "Au moins un type de stream est requis."
            )

        return self._get_list(
            f"/activity/{activity_id}/streams.json",
            params={
                "types": ",".join(
                    cleaned_types,
                ),
            },
        )

    @staticmethod
    def _validate_activity_id(
        activity_id: str,
    ) -> str:
        value = activity_id.strip()

        if not value:
            raise ValueError(
                "L'identifiant d'activité Intervals.icu "
                "est obligatoire."
            )

        return value

    def _request(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> object:
        """Exécute une requête GET authentifiée vers Intervals.icu."""

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
            return response.json()

        except ValueError as exc:
            raise IntervalsApiError(
                "Réponse JSON Intervals.icu invalide."
            ) from exc

    def _get_list(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> list[dict]:
        """Retourne une réponse JSON de type liste."""

        data = self._request(
            path,
            params=params,
        )

        if not isinstance(data, list):
            raise IntervalsApiError(
                "Réponse Intervals.icu inattendue."
            )

        return data

    def _get_object(
        self,
        path: str,
        *,
        params: dict[str, str] | None = None,
    ) -> dict:
        """Retourne une réponse JSON de type objet."""

        data = self._request(
            path,
            params=params,
        )

        if not isinstance(data, dict):
            raise IntervalsApiError(
                "Réponse Intervals.icu inattendue."
            )

        return data