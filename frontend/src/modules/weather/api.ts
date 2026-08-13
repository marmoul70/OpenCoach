import type {
  CurrentWeather,
  DailyWeather,
  HourlyWeather,
  WeatherData,
  WeatherLocation,
} from './types'

const OPEN_METEO_URL = 'https://api.open-meteo.com/v1/forecast'

interface OpenMeteoResponse {
  current: {
    temperature_2m: number
    apparent_temperature: number
    relative_humidity_2m: number
    precipitation: number
    wind_speed_10m: number
    weather_code: number
    time: string
  }
  hourly: {
    time: string[]
    temperature_2m: number[]
    precipitation_probability: number[]
    precipitation: number[]
    weather_code: number[]
    wind_speed_10m: number[]
  }
  daily: {
    time: string[]
    weather_code: number[]
    temperature_2m_max: number[]
    temperature_2m_min: number[]
    precipitation_probability_max: number[]
    precipitation_sum: number[]
    wind_speed_10m_max: number[]
  }
}

export async function fetchWeather(
  location: WeatherLocation,
): Promise<WeatherData> {
  const url = new URL(OPEN_METEO_URL)

  url.searchParams.set('latitude', String(location.latitude))
  url.searchParams.set('longitude', String(location.longitude))

  url.searchParams.set(
    'current',
    [
      'temperature_2m',
      'apparent_temperature',
      'relative_humidity_2m',
      'precipitation',
      'wind_speed_10m',
      'weather_code',
    ].join(','),
  )

  url.searchParams.set(
    'hourly',
    [
      'temperature_2m',
      'precipitation_probability',
      'precipitation',
      'weather_code',
      'wind_speed_10m',
    ].join(','),
  )

  url.searchParams.set(
    'daily',
    [
      'weather_code',
      'temperature_2m_max',
      'temperature_2m_min',
      'precipitation_probability_max',
      'precipitation_sum',
      'wind_speed_10m_max',
    ].join(','),
  )

  url.searchParams.set('forecast_days', '7')
  url.searchParams.set('timezone', 'auto')

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(
      `Erreur Open-Meteo : HTTP ${response.status}`,
    )
  }

  const data = (await response.json()) as OpenMeteoResponse

  const current: CurrentWeather = {
    temperature: data.current.temperature_2m,
    apparentTemperature: data.current.apparent_temperature,
    humidity: data.current.relative_humidity_2m,
    precipitation: data.current.precipitation,
    windSpeed: data.current.wind_speed_10m,
    weatherCode: data.current.weather_code,
    time: data.current.time,
  }

  const hourly: HourlyWeather[] = data.hourly.time.map(
    (_, index) => ({
      time: data.hourly.time[index],
      temperature: data.hourly.temperature_2m[index],
      precipitationProbability:
        data.hourly.precipitation_probability[index],
      precipitation: data.hourly.precipitation[index],
      weatherCode: data.hourly.weather_code[index],
      windSpeed: data.hourly.wind_speed_10m[index],
    }),
  )

  const daily: DailyWeather[] = data.daily.time.map(
    (_, index) => ({
      date: data.daily.time[index],
      weatherCode: data.daily.weather_code[index],
      temperatureMax: data.daily.temperature_2m_max[index],
      temperatureMin: data.daily.temperature_2m_min[index],
      precipitationProbabilityMax:
        data.daily.precipitation_probability_max[index],
      precipitationSum: data.daily.precipitation_sum[index],
      windSpeedMax: data.daily.wind_speed_10m_max[index],
    }),
  )

  return {
    location,
    current,
    hourly,
    daily,
  }
}

export async function getWeather(
  location: WeatherLocation,
): Promise<WeatherData> {
  return fetchWeather(location)
}
