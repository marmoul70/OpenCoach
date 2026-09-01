"""Modèles météo internes OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(
    frozen=True,
    slots=True,
)
class HourlyWeather:
    time: datetime
    temperature: float
    precipitation_probability: int
    precipitation: float
    weather_code: int
    wind_speed: float


@dataclass(
    frozen=True,
    slots=True,
)
class WeatherForecast:
    hourly: tuple[
        HourlyWeather,
        ...,
    ]
