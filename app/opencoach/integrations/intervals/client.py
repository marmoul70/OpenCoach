from datetime import date

import httpx

from opencoach.integrations.intervals.errors import (
    IntervalsApiError,
    IntervalsAuthenticationError,
    IntervalsDataError,
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

    def trigger_partner_sync(
        self,
    ) -> None:
        """Demande à Intervals.icu de rafraîchir ses partenaires.

        Cet endpoint est utilisé par l'interface Intervals.icu
        pour déclencher une synchronisation des fournisseurs
        connectés, notamment Suunto.
        """

        try:
            import os

            web_cookie = os.environ.get(
                "OPENCOACH_INTERVALS_WEB_COOKIE"
            )

            if not web_cookie:
                raise IntervalsAuthenticationError(
                    "OPENCOACH_INTERVALS_WEB_COOKIE "
                    "n'est pas configurée."
                )

            with httpx.Client(
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = client.post(
                    (
                        "https://intervals.icu/api/"
                        f"athlete/{self.athlete_id}"
                        "/activities-sync"
                    ),
                    headers={
                        "Accept":
                            "application/json, text/plain, */*",
                        "Origin":
                            "https://intervals.icu",
                        "Referer":
                            "https://intervals.icu/",
                    },
                    cookies={
                        "athlete_id": web_cookie,
                        "locale": "fr",
                    },
                )

        except httpx.HTTPError as exc:
            raise IntervalsApiError(
                (
                    "Impossible de déclencher "
                    "la synchronisation partenaire "
                    "Intervals.icu."
                )
            ) from exc

        if response.status_code in {
            401,
            403,
        }:
            raise IntervalsAuthenticationError(
                "Authentification Intervals.icu refusée."
            )

        try:
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise IntervalsApiError(
                (
                    "La synchronisation partenaire "
                    "Intervals.icu a retourné HTTP "
                    f"{response.status_code}."
                )
            ) from exc


    def upsert_workouts(
        self,
        workouts: list[dict],
    ) -> list[dict]:
        """Crée ou met à jour des workouts planifiés.

        Intervals.icu rapproche les événements à partir de
        ``external_id`` lorsque ``upsert=true``.

        La méthode retourne la représentation complète des événements
        telle que renvoyée par Intervals.icu.
        """

        if not workouts:
            return []

        payload = self._write_json(
            "POST",
            f"/athlete/{self.athlete_id}/events/bulk",
            params={
                "upsert": "true",
            },
            json_body=workouts,
        )

        if not isinstance(payload, list):
            raise IntervalsDataError(
                "La réponse bulk workout Intervals.icu "
                "n'est pas une liste."
            )

        if not all(
            isinstance(item, dict)
            for item in payload
        ):
            raise IntervalsDataError(
                "La réponse bulk workout Intervals.icu "
                "contient un événement invalide."
            )

        return payload

    def delete_workouts(
        self,
        external_ids: list[str],
    ) -> int:
        """Supprime des workouts OpenCoach par ``external_id``.

        Les identifiants inexistants sont ignorés par Intervals.icu.
        """

        cleaned_ids = [
            value.strip()
            for value in external_ids
            if value
            and value.strip()
        ]

        if not cleaned_ids:
            return 0

        payload = self._write_json(
            "PUT",
            f"/athlete/{self.athlete_id}/events/bulk-delete",
            json_body=[
                {
                    "external_id": external_id,
                }
                for external_id in cleaned_ids
            ],
        )

        if (
            not isinstance(payload, int)
            or isinstance(payload, bool)
        ):
            raise IntervalsDataError(
                "La réponse bulk-delete Intervals.icu "
                "n'est pas un nombre."
            )

        return payload

    def _write_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, str] | None = None,
        json_body: object,
    ) -> object:
        """Exécute une écriture JSON authentifiée vers Intervals.icu."""

        try:
            with httpx.Client(
                auth=httpx.BasicAuth(
                    "API_KEY",
                    self.api_key,
                ),
                timeout=self.timeout,
                transport=self.transport,
            ) as client:
                response = client.request(
                    method=method,
                    url=f"{INTERVALS_BASE_URL}{path}",
                    params=params,
                    json=json_body,
                )

        except httpx.HTTPError as exc:
            raise IntervalsApiError(
                "Impossible de communiquer avec "
                "l'API Intervals.icu."
            ) from exc

        if response.status_code in {
            401,
            403,
        }:
            raise IntervalsAuthenticationError(
                "Authentification Intervals.icu refusée."
            )

        try:
            response.raise_for_status()

        except httpx.HTTPStatusError as exc:
            raise IntervalsApiError(
                "L'API Intervals.icu a retourné HTTP "
                f"{response.status_code}."
            ) from exc

        try:
            return response.json()

        except ValueError as exc:
            raise IntervalsDataError(
                "La réponse Intervals.icu n'est pas "
                "un JSON valide."
            ) from exc

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
