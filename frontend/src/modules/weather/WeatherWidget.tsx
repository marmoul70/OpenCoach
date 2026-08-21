import {
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  AlertTriangle,
  CloudSun,
  MapPin,
  Wind,
} from 'lucide-react'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import {
  useAthleteProfile,
} from '../../core/profile'

import {
  getWeather,
} from './api'

import {
  getWeatherAlerts,
} from './alerts'

import type {
  WeatherAlertSeverity,
} from './alerts'

import {
  getWeatherDescription,
} from './logic'

import type {
  WeatherData,
} from './types'


interface WeatherWidgetProps {
  onClick: () => void
}


export function WeatherWidget({
  onClick,
}: WeatherWidgetProps) {
  const {
    toast,
  } = useToast()

  const notifiedAlerts =
    useRef<Set<string>>(
      new Set(),
    )

  const profile =
    useAthleteProfile()

  const weatherLocation = {
    name:
      profile.location.name
      ?? '',
    latitude:
      profile.location.latitude,
    longitude:
      profile.location.longitude,
  }

  const [
    weather,
    setWeather,
  ] = useState<WeatherData | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    error,
    setError,
  ] = useState(false)

  useEffect(() => {
    let cancelled = false

    async function loadWeather() {
      try {
        setLoading(true)
        setError(false)

        if (
          weatherLocation.latitude == null
          || weatherLocation.longitude == null
        ) {
          throw new Error(
            'La localisation du profil est incomplète.',
          )
        }

        const data =
          await getWeather({
            name:
              weatherLocation.name
              || 'Ma position',
            latitude:
              weatherLocation.latitude,
            longitude:
              weatherLocation.longitude,
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

  useEffect(() => {
    if (!weather) {
      return
    }

    const today =
      weather.current.time.slice(
        0,
        10,
      )

    const alerts =
      getWeatherAlerts(
        weather,
      ).filter(
        (alert) =>
          alert.time?.slice(
            0,
            10,
          ) === today,
      )

    for (const alert of alerts) {
      const key = [
        alert.type,
        alert.severity,
      ].join('-')

      if (
        notifiedAlerts.current.has(
          key,
        )
      ) {
        continue
      }

      notifiedAlerts.current.add(
        key,
      )

      toast({
        type:
          mapAlertSeverityToToastType(
            alert.severity,
          ),
        title: alert.title,
        message:
          alert.time
            ? (
                `${formatAlertPeriod(
                  alert.time,
                  alert.endTime,
                )} · ${alert.message}`
              )
            : alert.message,
        duration:
          alert.severity === 'info'
          ? 5000
          : null,
      })
    }
  }, [
    weather,
    toast,
  ])

  if (loading) {
    return (
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body flex min-h-28 items-center justify-center p-4">
          <span className="loading loading-spinner loading-sm text-info" />
        </div>
      </div>
    )
  }

  if (
    error
    || !weather
  ) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="card w-full border border-error/30 bg-base-100 text-left shadow-sm"
      >
        <div className="card-body p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-error">
                Météo
              </p>

              <p className="mt-1 font-semibold text-error">
                Données indisponibles
              </p>
            </div>

            <CloudSun className="h-4 w-4 text-error" />
          </div>
        </div>
      </button>
    )
  }

  const description =
    getWeatherDescription(
      weather.current.weatherCode,
    )

  const today =
    weather.current.time.slice(
      0,
      10,
    )

  const todayAlerts =
    getWeatherAlerts(
      weather,
    ).filter(
      (alert) =>
        alert.time?.slice(
          0,
          10,
        ) === today,
    )

  const alertSeverity =
    getHighestAlertSeverity(
      todayAlerts.map(
        (alert) => alert.severity,
      ),
    )

  return (
    <button
      type="button"
      onClick={onClick}
      className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="card-body gap-3 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
              Météo
            </p>

            <div className="mt-1 flex items-center gap-1.5 text-sm text-base-content/50">
              <MapPin className="h-3.5 w-3.5 shrink-0" />

              <span className="truncate">
                {weather.location.name}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {alertSeverity && (
              <span
                className={
                  getAlertIndicatorClass(
                    alertSeverity,
                  )
                }
                title={
                  getAlertIndicatorTitle(
                    alertSeverity,
                  )
                }
                aria-label={
                  getAlertIndicatorTitle(
                    alertSeverity,
                  )
                }
              >
                <AlertTriangle className="h-4 w-4" />
              </span>
            )}

            <span className="text-2xl">
              {description.icon}
            </span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <InlineMetric
            label="Temp."
            value={
              `${Math.round(
                weather.current.temperature,
              )}°C`
            }
          />

          <InlineMetric
            label="Ressenti"
            value={
              `${Math.round(
                weather.current.apparentTemperature,
              )}°C`
            }
          />

          <InlineMetric
            icon={
              <Wind className="h-3.5 w-3.5" />
            }
            label="Vent"
            value={
              `${Math.round(
                weather.current.windSpeed,
              )} km/h`
            }
          />

          <InlineMetric
            label=""
            value={description.label}
          />
        </div>
      </div>
    </button>
  )
}


function InlineMetric({
  icon,
  label,
  value,
}: {
  icon?: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div className="flex items-center gap-1.5 text-sm">
      {icon && (
        <span className="text-base-content/40">
          {icon}
        </span>
      )}

      {label && (
        <span className="text-xs text-base-content/45">
          {label}
        </span>
      )}

      <span className="font-semibold text-base-content">
        {value}
      </span>
    </div>
  )
}


function getHighestAlertSeverity(
  severities: WeatherAlertSeverity[],
): WeatherAlertSeverity | null {
  if (
    severities.includes(
      'danger',
    )
  ) {
    return 'danger'
  }

  if (
    severities.includes(
      'warning',
    )
  ) {
    return 'warning'
  }

  if (
    severities.includes(
      'info',
    )
  ) {
    return 'info'
  }

  return null
}


function getAlertIndicatorClass(
  severity: WeatherAlertSeverity,
): string {
  const classes = {
    danger:
      'text-error',
    warning:
      'text-warning',
    info:
      'text-info',
  }

  return classes[severity]
}


function getAlertIndicatorTitle(
  severity: WeatherAlertSeverity,
): string {
  const labels = {
    danger:
      'Alerte météo importante',
    warning:
      'Vigilance météo',
    info:
      'Information météo',
  }

  return labels[severity]
}


function mapAlertSeverityToToastType(
  severity: WeatherAlertSeverity,
): 'info' | 'warning' | 'error' {
  if (severity === 'danger') {
    return 'error'
  }

  return severity
}

function formatAlertPeriod(
  startTime: string,
  endTime?: string,
): string {
  const start =
    formatAlertTime(
      startTime,
    )

  if (
    !endTime
    || endTime === startTime
  ) {
    return start
  }

  return (
    `${start} → ${
      formatAlertTime(
        endTime,
      )
    }`
  )
}


function formatAlertTime(
  time: string,
): string {
  if (!time.includes('T')) {
    return new Intl.DateTimeFormat(
      'fr-FR',
      {
        day: 'numeric',
        month: 'short',
      },
    ).format(
      new Date(
        `${time}T12:00:00`,
      ),
    )
  }

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(
    new Date(time),
  )
}