from datetime import (
    date,
    datetime,
)

from opencoach.weather.models import (
    HourlyWeather,
    WeatherForecast,
)
from opencoach.weather.training_advisory import (
    build_training_weather_advice,
)


TARGET = date(
    2026,
    9,
    2,
)


def hour(
    value: int,
    *,
    temperature: float = 20,
    rain_probability: int = 10,
    precipitation: float = 0,
    weather_code: int = 1,
    wind_speed: float = 10,
) -> HourlyWeather:
    return HourlyWeather(
        time=datetime(
            2026,
            9,
            2,
            value,
        ),
        temperature=temperature,
        precipitation_probability=(
            rain_probability
        ),
        precipitation=precipitation,
        weather_code=weather_code,
        wind_speed=wind_speed,
    )


def forecast(
    *hours: HourlyWeather,
) -> WeatherForecast:
    return WeatherForecast(
        hourly=hours,
    )


def test_normal_weather_has_no_advice():
    result = (
        build_training_weather_advice(
            forecast(
                *[
                    hour(value)
                    for value
                    in range(
                        6,
                        22,
                    )
                ]
            ),
            target_date=TARGET,
        )
    )

    assert result.message is None


def test_hot_afternoon_prefers_morning():
    hours = []

    for value in range(
        6,
        22,
    ):
        temperature = (
            33
            if 12 <= value < 18
            else 20
        )

        hours.append(
            hour(
                value,
                temperature=temperature,
            )
        )

    result = (
        build_training_weather_advice(
            forecast(
                *hours
            ),
            target_date=TARGET,
        )
    )

    assert result.message
    assert (
        "chaleur"
        in result.message.lower()
    )

    assert (
        result.preferred_period
        == "matin"
    )


def test_afternoon_rain_prefers_morning():
    hours = []

    for value in range(
        6,
        22,
    ):
        rainy = (
            12 <= value < 18
        )

        hours.append(
            hour(
                value,
                rain_probability=(
                    90
                    if rainy
                    else 10
                ),
                weather_code=(
                    63
                    if rainy
                    else 1
                ),
            )
        )

    result = (
        build_training_weather_advice(
            forecast(
                *hours
            ),
            target_date=TARGET,
        )
    )

    assert result.message
    assert (
        "après-midi"
        in result.message
    )

    assert (
        result.preferred_period
        == "matin"
    )


def test_storm_prefers_safe_period():
    hours = []

    for value in range(
        6,
        22,
    ):
        storm = (
            15 <= value < 20
        )

        hours.append(
            hour(
                value,
                weather_code=(
                    95
                    if storm
                    else 1
                ),
            )
        )

    result = (
        build_training_weather_advice(
            forecast(
                *hours
            ),
            target_date=TARGET,
        )
    )

    assert result.message
    assert (
        "orage"
        in result.message.lower()
    )
