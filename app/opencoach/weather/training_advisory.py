"""Conseils météo pour les séances OpenCoach."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from opencoach.weather.models import (
    HourlyWeather,
    WeatherForecast,
)


STORM_CODES = {
    95,
    96,
    99,
}

FREEZING_RAIN_CODES = {
    56,
    57,
    66,
    67,
}

SNOW_CODES = {
    71,
    73,
    75,
    77,
    85,
    86,
}

RAIN_CODES = {
    51,
    53,
    55,
    61,
    63,
    65,
    80,
    81,
    82,
}


@dataclass(
    frozen=True,
    slots=True,
)
class TrainingWeatherAdvice:
    message: str | None
    preferred_period: (
        str
        | None
    ) = None


@dataclass(
    frozen=True,
    slots=True,
)
class PeriodScore:
    name: str
    hours: tuple[
        HourlyWeather,
        ...,
    ]
    score: float


_PERIODS = (
    (
        "matin",
        6,
        12,
    ),
    (
        "après-midi",
        12,
        18,
    ),
    (
        "soir",
        18,
        22,
    ),
)


def build_training_weather_advice(
    forecast: WeatherForecast,
    *,
    target_date: date,
) -> TrainingWeatherAdvice:
    """Produit un conseil utile uniquement si nécessaire."""

    target_hours = tuple(
        hour
        for hour
        in forecast.hourly
        if hour.time.date()
        == target_date
    )

    if not target_hours:
        return TrainingWeatherAdvice(
            message=None,
        )

    if any(
        hour.weather_code
        in STORM_CODES
        for hour in target_hours
    ):
        periods = (
            _score_periods(
                target_hours
            )
        )

        best = _best_period(
            periods
        )

        if (
            best is not None
            and not _period_has_storm(
                best.hours
            )
        ):
            return TrainingWeatherAdvice(
                message=(
                    "Des orages sont annoncés "
                    "demain. Je te conseille "
                    f"de faire ta séance le "
                    f"{best.name}."
                ),
                preferred_period=(
                    best.name
                ),
            )

        return TrainingWeatherAdvice(
            message=(
                "Des orages sont annoncés "
                "demain. Vérifie les "
                "conditions avant de partir."
            ),
        )

    temperature_max = max(
        hour.temperature
        for hour in target_hours
    )

    if temperature_max >= 32:
        periods = (
            _score_periods(
                target_hours
            )
        )

        best = _best_period(
            periods
        )

        preferred = (
            best.name
            if best is not None
            else "matin"
        )

        return TrainingWeatherAdvice(
            message=(
                "Forte chaleur annoncée "
                "demain. Je te conseille "
                f"de faire ta séance le "
                f"{preferred}."
            ),
            preferred_period=(
                preferred
            ),
        )

    if temperature_max >= 28:
        morning = _find_period(
            target_hours,
            "matin",
        )

        evening = _find_period(
            target_hours,
            "soir",
        )

        candidates = [
            period
            for period
            in (
                morning,
                evening,
            )
            if period is not None
        ]

        best = (
            min(
                candidates,
                key=lambda item:
                    item.score,
            )
            if candidates
            else None
        )

        if best is not None:
            return TrainingWeatherAdvice(
                message=(
                    "Il fera chaud demain, "
                    f"privilégie le "
                    f"{best.name}."
                ),
                preferred_period=(
                    best.name
                ),
            )

    periods = (
        _score_periods(
            target_hours
        )
    )

    rainy_periods = [
        period
        for period
        in periods
        if _period_is_rainy(
            period.hours
        )
    ]

    dry_periods = [
        period
        for period
        in periods
        if not _period_is_rainy(
            period.hours
        )
    ]

    if (
        rainy_periods
        and dry_periods
    ):
        best = min(
            dry_periods,
            key=lambda item:
                item.score,
        )

        rainy_names = {
            item.name
            for item
            in rainy_periods
        }

        if (
            "après-midi"
            in rainy_names
            and best.name
            == "matin"
        ):
            message = (
                "Pluie annoncée surtout "
                "l’après-midi. Je te "
                "conseille de faire ta "
                "séance le matin."
            )

        elif (
            "matin"
            in rainy_names
            and best.name
            in {
                "après-midi",
                "soir",
            }
        ):
            message = (
                "Pluie annoncée le matin. "
                "Les conditions seront "
                "meilleures plus tard "
                "dans la journée."
            )

        else:
            message = (
                "La météo sera variable "
                "demain. Le créneau le "
                f"plus favorable semble "
                f"être le {best.name}."
            )

        return TrainingWeatherAdvice(
            message=message,
            preferred_period=(
                best.name
            ),
        )

    if any(
        hour.wind_speed >= 50
        for hour in target_hours
    ):
        return TrainingWeatherAdvice(
            message=(
                "Vent très fort annoncé "
                "demain. Évite les secteurs "
                "exposés et les crêtes."
            ),
        )

    if any(
        hour.weather_code
        in FREEZING_RAIN_CODES
        for hour in target_hours
    ):
        return TrainingWeatherAdvice(
            message=(
                "Risque de verglas demain. "
                "Sois prudent sur les "
                "routes et les chemins."
            ),
        )

    if any(
        hour.weather_code
        in SNOW_CODES
        for hour in target_hours
    ):
        return TrainingWeatherAdvice(
            message=(
                "Neige annoncée demain. "
                "Adapte ton parcours "
                "aux conditions."
            ),
        )

    return TrainingWeatherAdvice(
        message=None,
    )


def _score_periods(
    hours: tuple[
        HourlyWeather,
        ...,
    ],
) -> list[
    PeriodScore
]:
    results = []

    for (
        name,
        start_hour,
        end_hour,
    ) in _PERIODS:
        period_hours = tuple(
            hour
            for hour
            in hours
            if (
                start_hour
                <= hour.time.hour
                < end_hour
            )
        )

        if not period_hours:
            continue

        results.append(
            PeriodScore(
                name=name,
                hours=period_hours,
                score=_weather_score(
                    period_hours
                ),
            )
        )

    return results


def _find_period(
    hours: tuple[
        HourlyWeather,
        ...,
    ],
    name: str,
) -> PeriodScore | None:
    for period in _score_periods(
        hours
    ):
        if period.name == name:
            return period

    return None


def _best_period(
    periods: list[
        PeriodScore
    ],
) -> PeriodScore | None:
    if not periods:
        return None

    return min(
        periods,
        key=lambda item:
            item.score,
    )


def _weather_score(
    hours: tuple[
        HourlyWeather,
        ...,
    ],
) -> float:
    score = 0.0

    for hour in hours:
        score += (
            hour.precipitation_probability
            / 10
        )

        score += (
            hour.precipitation
            * 5
        )

        if hour.temperature >= 28:
            score += (
                hour.temperature
                - 27
            ) * 3

        if hour.wind_speed >= 35:
            score += (
                hour.wind_speed
                - 34
            )

        if (
            hour.weather_code
            in STORM_CODES
        ):
            score += 100

        if (
            hour.weather_code
            in FREEZING_RAIN_CODES
        ):
            score += 80

    return (
        score
        / len(hours)
    )


def _period_is_rainy(
    hours: tuple[
        HourlyWeather,
        ...,
    ],
) -> bool:
    return any(
        (
            hour.weather_code
            in RAIN_CODES
            and (
                hour.precipitation_probability
                >= 70
            )
        )
        or hour.precipitation
        >= 5
        for hour in hours
    )


def _period_has_storm(
    hours: tuple[
        HourlyWeather,
        ...,
    ],
) -> bool:
    return any(
        hour.weather_code
        in STORM_CODES
        for hour in hours
    )
