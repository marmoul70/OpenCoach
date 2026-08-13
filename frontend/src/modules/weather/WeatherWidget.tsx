import { useEffect, useState } from 'react'

import { getWeather } from './api'
import { DEFAULT_WEATHER_LOCATION } from './location'
import { getWeatherDescription } from './logic'
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
        className="w-full rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm"
      >
        <p className="text-sm font-medium text-slate-500">
          Météo
        </p>

        <p className="mt-3 text-slate-400">
          Chargement de la météo…
        </p>
      </button>
    )
  }

  if (error || !weather) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="w-full rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm"
      >
        <p className="text-sm font-medium text-slate-500">
          Météo
        </p>

        <p className="mt-3 text-sm text-red-500">
          Impossible de récupérer la météo.
        </p>
      </button>
    )
  }

  const description = getWeatherDescription(
    weather.current.weatherCode,
  )

  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-slate-500">
            Météo
          </p>

          <p className="mt-1 text-sm text-slate-400">
            {weather.location.name}
          </p>

          <p className="mt-2 text-3xl font-bold text-slate-900">
            {Math.round(weather.current.temperature)}°C
          </p>
        </div>

        <div className="text-right">
          <span className="text-3xl">
            {description.icon}
          </span>

          <p className="mt-1 text-sm font-medium text-slate-600">
            {description.label}
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <Metric
          label="Ressenti"
          value={`${Math.round(weather.current.apparentTemperature)}°C`}
        />

        <Metric
          label="Vent"
          value={`${Math.round(weather.current.windSpeed)} km/h`}
        />
      </div>

      <p className="mt-4 text-sm text-slate-400">
        Cliquez pour voir les prévisions
      </p>
    </button>
  )
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
    <div className="rounded-xl bg-slate-50 p-3">
      <p className="text-xs text-slate-500">
        {label}
      </p>

      <p className="mt-1 font-semibold text-slate-900">
        {value}
      </p>
    </div>
  )
}
