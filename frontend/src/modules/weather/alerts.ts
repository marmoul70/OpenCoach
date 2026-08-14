import type {
  DailyWeather,
  HourlyWeather,
  WeatherData,
} from './types'

export type WeatherAlertSeverity =
  | 'info'
  | 'warning'
  | 'danger'

export type WeatherAlertType =
  | 'storm'
  | 'heavy-rain'
  | 'strong-wind'
  | 'heat'
  | 'cold'
  | 'freezing-rain'
  | 'snow'
  | 'rain'

export interface WeatherAlert {
  type: WeatherAlertType
  severity: WeatherAlertSeverity
  title: string
  message: string
  time?: string
}

const STORM_CODES = [95, 96, 99]
const FREEZING_RAIN_CODES = [56, 57, 66, 67]
const SNOW_CODES = [71, 73, 75, 77, 85, 86]
const RAIN_CODES = [51, 53, 55, 61, 63, 65, 80, 81, 82]

export function getWeatherAlerts(
  weather: WeatherData,
): WeatherAlert[] {
  const alerts: WeatherAlert[] = []

  analyseHourlyWeather(weather.hourly, alerts)

  const currentDate = weather.current.time.slice(0, 10)
  analyseDailyWeather(weather.daily, alerts, currentDate)

  return deduplicateAlerts(alerts)
}

function analyseHourlyWeather(
  hourly: HourlyWeather[],
  alerts: WeatherAlert[],
): void {
  for (const hour of hourly.slice(0, 24)) {
    if (STORM_CODES.includes(hour.weatherCode)) {
      alerts.push({
        type: 'storm',
        severity: 'danger',
        title: 'Orage prévu',
        message:
          'Risque d’orage pendant cette période. Évitez les sorties trail exposées.',
        time: hour.time,
      })
    }

    if (FREEZING_RAIN_CODES.includes(hour.weatherCode)) {
      alerts.push({
        type: 'freezing-rain',
        severity: 'danger',
        title: 'Risque de verglas',
        message:
          'Des précipitations verglaçantes sont prévues. Prudence sur les chemins et routes.',
        time: hour.time,
      })
    }

    if (SNOW_CODES.includes(hour.weatherCode)) {
      alerts.push({
        type: 'snow',
        severity: 'warning',
        title: 'Neige prévue',
        message:
          'Des conditions neigeuses sont prévues. Adaptez votre parcours et votre allure.',
        time: hour.time,
      })
    }

    if (
      RAIN_CODES.includes(hour.weatherCode) &&
      hour.precipitationProbability >= 70
    ) {
      alerts.push({
        type: 'rain',
        severity: 'info',
        title: 'Pluie probable',
        message:
          'Une forte probabilité de pluie est prévue. Prévoyez une protection adaptée.',
        time: hour.time,
      })
    }

    if (hour.precipitation >= 5) {
      alerts.push({
        type: 'heavy-rain',
        severity: 'warning',
        title: 'Fortes précipitations',
        message:
          'Des précipitations importantes sont prévues. Les sentiers peuvent être très humides ou glissants.',
        time: hour.time,
      })
    }

    if (hour.windSpeed >= 50) {
      alerts.push({
        type: 'strong-wind',
        severity: 'danger',
        title: 'Vent très fort',
        message:
          'Vent très fort prévu. Évitez les secteurs exposés et les crêtes.',
        time: hour.time,
      })
    } else if (hour.windSpeed >= 35) {
      alerts.push({
        type: 'strong-wind',
        severity: 'warning',
        title: 'Vent fort',
        message:
          'Vent fort prévu. Soyez prudent sur les secteurs exposés.',
        time: hour.time,
      })
    }
  }
}

function analyseDailyWeather(
  daily: DailyWeather[],
  alerts: WeatherAlert[],
  currentDate: string,
): void {
  const today = new Date(`${currentDate}T12:00:00`)
  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  const allowedDates = new Set([
    currentDate,
    tomorrow.toISOString().slice(0, 10),
  ])

  for (const day of daily) {
    if (!allowedDates.has(day.date)) {
      continue
    }
    if (day.temperatureMax >= 32) {
      alerts.push({
        type: 'heat',
        severity: 'danger',
        title: 'Forte chaleur',
        message:
          'Températures élevées prévues. Privilégiez les horaires frais et adaptez hydratation et intensité.',
        time: day.date,
      })
    } else if (day.temperatureMax >= 28) {
      alerts.push({
        type: 'heat',
        severity: 'warning',
        title: 'Chaleur importante',
        message:
          'Températures élevées prévues. Privilégiez les horaires frais et adaptez l’intensité.',
        time: day.date,
      })
    }

    if (day.temperatureMin <= -5) {
      alerts.push({
        type: 'cold',
        severity: 'danger',
        title: 'Froid important',
        message:
          'Températures très basses prévues. Adaptez votre équipement et soyez attentif au risque de verglas.',
        time: day.date,
      })
    } else if (day.temperatureMin <= 0) {
      alerts.push({
        type: 'cold',
        severity: 'warning',
        title: 'Températures froides',
        message:
          'Températures proches ou inférieures à 0 °C. Adaptez votre équipement.',
        time: day.date,
      })
    }
  }
}

function deduplicateAlerts(
  alerts: WeatherAlert[],
): WeatherAlert[] {
  const seen = new Set<string>()

  return alerts.filter((alert) => {
    const key = `${alert.type}-${alert.severity}-${alert.time}`

    if (seen.has(key)) {
      return false
    }

    seen.add(key)
    return true
  })
}
