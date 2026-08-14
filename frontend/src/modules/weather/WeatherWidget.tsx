import { useEffect, useState } from 'react'
import {
  AlertTriangle,
  CloudSun,
  MapPin,
  Wind,
} from 'lucide-react'

import { getWeather } from './api'
import { DEFAULT_WEATHER_LOCATION } from './location'
import { getWeatherDescription } from './logic'
import { getWeatherAlerts } from './alerts'
import type { WeatherAlertSeverity } from './alerts'
import type { WeatherData } from './types'

interface WeatherWidgetProps {
  onClick: () => void
}

export function WeatherWidget({
  onClick,
}: WeatherWidgetProps) {
  const [weather, setWeather] = useState<WeatherData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function loadWeather() {
      try {
        setLoading(true)
        setError(false)

        const data = await getWeather(
          DEFAULT_WEATHER_LOCATION,
        )

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
  }, [])

  if (loading) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="card w-full border border-base-300 bg-base-100 text-left shadow-sm"
      >
        <div className="card-body p-5">
          <div className="flex items-center gap-3">
            <div className="skeleton h-11 w-11 shrink-0 rounded-xl" />

            <div className="space-y-2">
              <div className="skeleton h-4 w-24" />
              <div className="skeleton h-3 w-32" />
            </div>
          </div>

          <div className="mt-5 skeleton h-10 w-28" />

          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="skeleton h-16 w-full rounded-xl" />
            <div className="skeleton h-16 w-full rounded-xl" />
          </div>
        </div>
      </button>
    )
  }

  if (error || !weather) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="card w-full border border-base-300 bg-base-100 text-left shadow-sm"
      >
        <div className="card-body p-5">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-error/10">
              <CloudSun className="h-5 w-5 text-error" />
            </div>

            <div>
              <p className="text-sm font-medium text-base-content/60">
                Météo
              </p>

              <p className="mt-1 text-sm text-base-content/40">
                Conditions météorologiques
              </p>
            </div>
          </div>

          <div className="alert alert-error mt-5">
            <AlertTriangle className="h-5 w-5" />

            <span className="text-sm">
              Impossible de récupérer la météo.
            </span>
          </div>
        </div>
      </button>
    )
  }

  const description = getWeatherDescription(
    weather.current.weatherCode,
  )

  const today = weather.current.time.slice(0, 10)

  const todayAlerts = getWeatherAlerts(weather).filter(
    (alert) => alert.time?.slice(0, 10) === today,
  )

  const alertSeverity = getHighestAlertSeverity(
    todayAlerts.map((alert) => alert.severity),
  )

  return (
    <button
      type="button"
      onClick={onClick}
      className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="card-body p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-info/10">
              <CloudSun className="h-5 w-5 text-info" />
            </div>

            <div className="min-w-0">
              <p className="text-sm font-medium text-base-content/60">
                Météo
              </p>

              <div className="mt-1 flex items-center gap-1 text-sm text-base-content/40">
                <MapPin className="h-3.5 w-3.5" />

                <span className="truncate">
                  {weather.location.name}
                </span>
              </div>
            </div>
          </div>

          {alertSeverity && (
            <span
              className={getAlertIndicatorClass(
                alertSeverity,
              )}
              title={getAlertIndicatorTitle(alertSeverity)}
              aria-label={getAlertIndicatorTitle(
                alertSeverity,
              )}
            >
              <AlertTriangle className="h-4 w-4" />
            </span>
          )}
        </div>

        <div className="mt-5 flex items-center justify-between gap-4">
          <div>
            <div className="flex items-baseline gap-1">
              <span className="text-4xl font-bold text-base-content">
                {Math.round(weather.current.temperature)}
              </span>

              <span className="text-xl text-base-content/50">
                °C
              </span>
            </div>

            <p className="mt-1 text-sm text-base-content/60">
              {description.label}
            </p>
          </div>

          <span className="text-5xl">
            {description.icon}
          </span>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <Metric
            icon={<CloudSun className="h-4 w-4" />}
            label="Ressenti"
            value={`${Math.round(weather.current.apparentTemperature)}°C`}
          />

          <Metric
            icon={<Wind className="h-4 w-4" />}
            label="Vent"
            value={`${Math.round(weather.current.windSpeed)} km/h`}
          />
        </div>

        {alertSeverity && (
          <div
            className={`mt-4 rounded-xl p-3 ${getAlertBackgroundClass(alertSeverity)}`}
          >
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />

              <span className="text-sm font-medium">
                {getAlertIndicatorTitle(alertSeverity)}
              </span>
            </div>
          </div>
        )}

        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-base-content/40">
            Prévisions et détails météo
          </span>

          <span className="text-sm font-medium text-info">
            Voir →
          </span>
        </div>
      </div>
    </button>
  )
}

interface MetricProps {
  icon: React.ReactNode
  label: string
  value: string
}

function Metric({
  icon,
  label,
  value,
}: MetricProps) {
  return (
    <div className="rounded-xl bg-base-200 p-3">
      <div className="flex items-center gap-2 text-base-content/50">
        {icon}

        <span className="text-xs">
          {label}
        </span>
      </div>

      <p className="mt-1 font-semibold text-base-content">
        {value}
      </p>
    </div>
  )
}

function getHighestAlertSeverity(
  severities: WeatherAlertSeverity[],
): WeatherAlertSeverity | null {
  if (severities.includes('danger')) {
    return 'danger'
  }

  if (severities.includes('warning')) {
    return 'warning'
  }

  if (severities.includes('info')) {
    return 'info'
  }

  return null
}

function getAlertIndicatorClass(
  severity: WeatherAlertSeverity,
): string {
  if (severity === 'danger') {
    return 'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-error/10 text-error'
  }

  if (severity === 'warning') {
    return 'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-warning/10 text-warning'
  }

  return 'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-info/10 text-info'
}

function getAlertBackgroundClass(
  severity: WeatherAlertSeverity,
): string {
  if (severity === 'danger') {
    return 'bg-error/10 text-error'
  }

  if (severity === 'warning') {
    return 'bg-warning/10 text-warning'
  }

  return 'bg-info/10 text-info'
}

function getAlertIndicatorTitle(
  severity: WeatherAlertSeverity,
): string {
  if (severity === 'danger') {
    return 'Alerte météo importante aujourd’hui'
  }

  if (severity === 'warning') {
    return 'Alerte météo aujourd’hui'
  }

  return 'Information météo aujourd’hui'
}