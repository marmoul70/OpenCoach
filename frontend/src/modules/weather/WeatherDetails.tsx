import { useEffect, useState } from 'react'

import { getWeather } from './api'
import { getWeatherAlerts } from './alerts'
import { useAthleteProfile } from '../../core/profile'
import { getWeatherDescription } from './logic'
import type { WeatherData } from './types'

export function WeatherDetails() {
  const profile = useAthleteProfile()

  const weatherLocation = {
    name: profile.location.name ?? '',
    latitude: profile.location.latitude,
    longitude: profile.location.longitude,
  }

  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function loadWeather() {
      try {
        setLoading(true)
        setError(false)

        if (
          weatherLocation.latitude == null ||
          weatherLocation.longitude == null
        ) {
          throw new Error(
            'La localisation du profil est incomplète.',
          )
        }

        const data = await getWeather({
          name: weatherLocation.name || 'Ma position',
          latitude: weatherLocation.latitude,
          longitude: weatherLocation.longitude,
        })

        if (!cancelled) {
          setWeather(data)
        }
      } catch {
        if (!cancelled) {
          setError(true)
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadWeather()

    return () => {
      cancelled = true
    }
  }, [
    weatherLocation.name,
    weatherLocation.latitude,
    weatherLocation.longitude,
  ])

  if (loading) {
    return (
      <div className="py-8 text-center text-slate-400">
        Chargement des prévisions…
      </div>
    )
  }

  if (error || !weather) {
    return (
      <div className="py-8 text-center text-red-500">
        Impossible de récupérer les prévisions météo.
      </div>
    )
  }

  const currentDescription = getWeatherDescription(
    weather.current.weatherCode,
  )
  const alerts = getWeatherAlerts(weather)
  const relevantAlerts = alerts.filter(isAlertRelevant)

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-slate-50 p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm text-slate-500">
              {weather.location.name}
            </p>

            <p className="mt-2 text-5xl font-bold text-slate-900">
              {Math.round(weather.current.temperature)}°C
            </p>

            <p className="mt-2 text-slate-500">
              {currentDescription.label}
            </p>
          </div>

          <span className="text-4xl">
            {currentDescription.icon}
          </span>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Metric
            label="Ressenti"
            value={`${Math.round(weather.current.apparentTemperature)}°C`}
          />

          <Metric
            label="Humidité"
            value={`${Math.round(weather.current.humidity)} %`}
          />

          <Metric
            label="Pluie"
            value={`${weather.current.precipitation.toFixed(1)} mm`}
          />

          <Metric
            label="Vent"
            value={`${Math.round(weather.current.windSpeed)} km/h`}
          />
        </div>
      </section>

      {relevantAlerts.length > 0 && (
        <details
          open={relevantAlerts.some(
            (alert) => alert.severity === 'danger',
          )}
          className="collapse collapse-arrow border border-base-300 bg-base-100"
        >
          <summary className="collapse-title flex items-center gap-2 font-semibold">
            <span>⚠️ Alertes météo</span>

            <span className="badge badge-sm badge-warning">
              {relevantAlerts.length}
            </span>
          </summary>

          <div className="collapse-content">
            <div className="space-y-3 pt-2">
              {relevantAlerts.map((alert) => (
                <WeatherAlertCard
                  key={`${alert.type}-${alert.severity}-${alert.time}`}
                  alert={alert}
                />
              ))}
            </div>
          </div>
        </details>
      )}

      <details className="group rounded-2xl border border-slate-200 bg-white">
        <summary className="flex cursor-pointer list-none items-center justify-between p-4 font-semibold text-slate-900">
          <span>Prochaines heures</span>
          <span className="text-slate-400 transition group-open:rotate-180">
            ▼
          </span>
        </summary>

        <div className="border-t border-slate-100 p-4">
          <div className="flex gap-3 overflow-x-auto pb-2">
          {weather.hourly.slice(0, 12).map((hour) => {
            const description = getWeatherDescription(
              hour.weatherCode,
            )

            return (
              <div
                key={hour.time}
                className="min-w-28 rounded-xl border border-slate-200 bg-white p-3 text-center"
              >
                <p className="text-xs text-slate-500">
                  {formatHour(hour.time)}
                </p>

                <p className="mt-2 text-xl">
                  {description.icon}
                </p>

                <p className="mt-1 font-semibold text-slate-900">
                  {Math.round(hour.temperature)}°C
                </p>

                <p className="mt-2 text-xs text-blue-600">
                  {Math.round(hour.precipitationProbability)} %
                </p>

                <p className="mt-1 text-xs text-slate-400">
                  {hour.precipitation.toFixed(1)} mm
                </p>
              </div>
            )
          })}
          </div>
        </div>
      </details>

      <details className="group rounded-2xl border border-slate-200 bg-white">
        <summary className="flex cursor-pointer list-none items-center justify-between p-4 font-semibold text-slate-900">
          <span>Prévisions à 7 jours</span>
          <span className="text-slate-400 transition group-open:rotate-180">
            ▼
          </span>
        </summary>

        <div className="space-y-2 border-t border-slate-100 p-4">
          {weather.daily.map((day) => {
            const description = getWeatherDescription(
              day.weatherCode,
            )

            return (
              <div
                key={day.date}
                className="grid grid-cols-[1fr_auto_auto] items-center gap-4 rounded-xl bg-slate-50 p-3"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl">
                    {description.icon}
                  </span>

                  <div>
                    <p className="font-medium text-slate-900">
                      {formatDate(day.date)}
                    </p>

                    <p className="text-xs text-slate-500">
                      {description.label}
                    </p>
                  </div>
                </div>

                <div className="text-right text-sm">
                  <p className="font-semibold text-slate-900">
                    {Math.round(day.temperatureMax)}°
                  </p>

                  <p className="text-slate-400">
                    {Math.round(day.temperatureMin)}°
                  </p>
                </div>

                <div className="text-right text-xs">
                  <p className="text-blue-600">
                    {Math.round(day.precipitationProbabilityMax)} %
                  </p>

                  <p className="text-slate-400">
                    {day.precipitationSum.toFixed(1)} mm
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </details>
    </div>
  )
}

interface WeatherAlertCardProps {
  alert: import('./alerts').WeatherAlert
}

function WeatherAlertCard({
  alert,
}: WeatherAlertCardProps) {
  const styles = getAlertStyles(alert.severity)

  return (
    <div className={`rounded-xl border p-4 ${styles.container}`}>
      <div className="flex items-start gap-3">
        <span className={`mt-0.5 text-lg ${styles.icon}`}>
          {styles.symbol}
        </span>

        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <p className={`font-semibold ${styles.title}`}>
              {alert.title}
            </p>

            {alert.time && (
              <span className="text-xs text-slate-400">
                {formatAlertTime(alert.time)}
              </span>
            )}
          </div>

          <p className="mt-1 text-sm text-slate-600">
            {alert.message}
          </p>
        </div>
      </div>
    </div>
  )
}

function getAlertStyles(
  severity: import('./alerts').WeatherAlertSeverity,
) {
  switch (severity) {
    case 'danger':
      return {
        container:
          'border-red-200 bg-red-50',
        icon: 'text-red-600',
        title: 'text-red-800',
        symbol: '⚠',
      }

    case 'warning':
      return {
        container:
          'border-amber-200 bg-amber-50',
        icon: 'text-amber-600',
        title: 'text-amber-800',
        symbol: '⚠',
      }

    default:
      return {
        container:
          'border-blue-200 bg-blue-50',
        icon: 'text-blue-600',
        title: 'text-blue-800',
        symbol: 'ℹ',
      }
  }
}

function formatAlertTime(value: string): string {
  if (value.includes('T')) {
    return new Intl.DateTimeFormat('fr-FR', {
      weekday: 'short',
      hour: '2-digit',
      minute: '2-digit',
    }).format(new Date(value))
  }

  return new Intl.DateTimeFormat('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(new Date(`${value}T12:00:00`))
}

interface MetricProps {
  label: string
  value: string
}

function Metric({
  label,
  value,
}: MetricProps) {
  return (
    <div className="rounded-xl bg-white p-3">
      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 font-semibold text-slate-900">
        {value}
      </p>
    </div>
  )
}

function formatHour(value: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(new Date(`${value}T12:00:00`))
}

function isAlertRelevant(
  alert: import('./alerts').WeatherAlert,
): boolean {
  if (!alert.time) {
    return true
  }

  const now = new Date()

  const today = new Date(
    now.getFullYear(),
    now.getMonth(),
    now.getDate(),
  )

  const tomorrow = new Date(today)
  tomorrow.setDate(tomorrow.getDate() + 1)

  const alertDate = new Date(alert.time)

  const alertDay = new Date(
    alertDate.getFullYear(),
    alertDate.getMonth(),
    alertDate.getDate(),
  )

  return (
    alertDay.getTime() === today.getTime() ||
    alertDay.getTime() === tomorrow.getTime()
  )
}
