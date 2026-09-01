"""Client Open-Meteo du backend OpenCoach."""

from __future__ import annotations

from datetime import datetime

import httpx

from opencoach.weather.models import (
    HourlyWeather,
    WeatherForecast,
)


OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
)


class OpenMeteoError(
    RuntimeError
):
    """Erreur de communication Open-Meteo."""


class OpenMeteoClient:
    """Récupère les prévisions horaires Open-Meteo."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 10.0,
    ) -> None:
        self.timeout_seconds = (
            timeout_seconds
        )

    def fetch_forecast(
        self,
        *,
        latitude: float,
        longitude: float,
    ) -> WeatherForecast:
        params = {
            "latitude":
                latitude,
            "longitude":
                longitude,
            "hourly": ",".join(
                [
                    "temperature_2m",
                    (
                        "precipitation_"
                        "probability"
                    ),
                    "precipitation",
                    "weather_code",
                    "wind_speed_10m",
                ]
            ),
            "forecast_days": 2,
            "timezone": "auto",
        }

        try:
            response = httpx.get(
                OPEN_METEO_URL,
                params=params,
                timeout=(
                    self.timeout_seconds
                ),
            )

            response.raise_for_status()

            payload = (
                response.json()
            )

        except (
            httpx.HTTPError,
            ValueError,
        ) as exc:
            raise OpenMeteoError(
                "Impossible de récupérer "
                "les prévisions Open-Meteo."
            ) from exc

        hourly = payload.get(
            "hourly"
        )

        if not isinstance(
            hourly,
            dict,
        ):
            raise OpenMeteoError(
                "Réponse horaire "
                "Open-Meteo invalide."
            )

        required = (
            "time",
            "temperature_2m",
            (
                "precipitation_"
                "probability"
            ),
            "precipitation",
            "weather_code",
            "wind_speed_10m",
        )

        if any(
            key not in hourly
            for key in required
        ):
            raise OpenMeteoError(
                "Données horaires "
                "Open-Meteo incomplètes."
            )

        size = len(
            hourly["time"]
        )

        if any(
            len(hourly[key])
            != size
            for key in required
        ):
            raise OpenMeteoError(
                "Séries horaires "
                "Open-Meteo incohérentes."
            )

        hours = tuple(
            HourlyWeather(
                time=datetime.fromisoformat(
                    hourly["time"][
                        index
                    ]
                ),
                temperature=float(
                    hourly[
                        "temperature_2m"
                    ][index]
                ),
                precipitation_probability=int(
                    hourly[
                        (
                            "precipitation_"
                            "probability"
                        )
                    ][index]
                ),
                precipitation=float(
                    hourly[
                        "precipitation"
                    ][index]
                ),
                weather_code=int(
                    hourly[
                        "weather_code"
                    ][index]
                ),
                wind_speed=float(
                    hourly[
                        "wind_speed_10m"
                    ][index]
                ),
            )
            for index
            in range(size)
        )

        return WeatherForecast(
            hourly=hours,
        )
