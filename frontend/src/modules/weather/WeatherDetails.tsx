import { useEffect, useState } from 'react'

import { getWeather } from './api'
import { DEFAULT_WEATHER_LOCATION } from './location'
import { getWeatherDescription } from './logic'
import type { WeatherData } from './types'

export function WeatherDetails() {
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

      <section>
        <h3 className="text-lg font-semibold text-slate-900">
          Prochaines heures
        </h3>

        <div className="mt-3 flex gap-3 overflow-x-auto pb-2">
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
      </section>

      <section>
        <h3 className="text-lg font-semibold text-slate-900">
          Prévisions à 7 jours
        </h3>

        <div className="mt-3 space-y-2">
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
      </section>
    </div>
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
