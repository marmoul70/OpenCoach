import {
  CloudRain,
  Droplets,
  MapPin,
  Thermometer,
  Wind,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

import {
  useAthleteProfile,
} from '../../core/profile'

import {
  getWeatherAlerts,
} from './alerts'

import {
  getWeather,
} from './api'

import {
  getWeatherDescription,
} from './logic'

import type {
  WeatherData,
} from './types'


export function WeatherDetails() {
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
  ] = useState<
    WeatherData | null
  >(null)

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
          weatherLocation.latitude
          == null
          || weatherLocation.longitude
          == null
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


  if (loading) {
    return (
      <div
        className="
          flex items-center
          justify-center
          gap-3
          py-10
          text-base-content/50
        "
      >
        <span
          className="
            loading
            loading-spinner
            loading-sm
          "
        />

        <span className="text-sm">
          Chargement des prévisions…
        </span>
      </div>
    )
  }


  if (
    error
    || !weather
  ) {
    return (
      <div
        className="
          rounded-xl
          border
          border-error/30
          bg-error/5
          px-4 py-4
          text-sm
          text-error
        "
      >
        Impossible de récupérer
        les prévisions météo.
      </div>
    )
  }


  const currentDescription =
    getWeatherDescription(
      weather.current.weatherCode,
    )

  const alerts =
    getWeatherAlerts(
      weather,
    )

  const relevantAlerts =
    alerts.filter(
      isAlertRelevant,
    )


  return (
    <div className="space-y-5">
      <WeatherHeader
        location={
          weather.location.name
          ?? weatherLocation.name
          ?? 'Ma position'
        }
        temperature={
          weather.current.temperature
        }
        label={
          currentDescription.label
        }
        icon={
          currentDescription.icon
        }
      />

      <CurrentMetrics
        apparentTemperature={
          weather.current
            .apparentTemperature
        }
        humidity={
          weather.current.humidity
        }
        precipitation={
          weather.current.precipitation
        }
        windSpeed={
          weather.current.windSpeed
        }
      />

      {relevantAlerts.length > 0 && (
        <WeatherAlerts
          alerts={
            relevantAlerts
          }
        />
      )}

      <HourlyForecast
        weather={weather}
      />

      <DailyForecast
        weather={weather}
      />
    </div>
  )
}


interface WeatherHeaderProps {
  location: string
  temperature: number
  label: string
  icon: string
}


function WeatherHeader({
  location,
  temperature,
  label,
  icon,
}: WeatherHeaderProps) {
  return (
    <div
      className="
        flex items-center
        justify-between
        gap-4
      "
    >
      <div
        className="
          flex min-w-0
          items-center
          gap-3
        "
      >
        <div
          className="
            flex size-11
            shrink-0
            items-center
            justify-center
            rounded-xl
            bg-info/10
            text-2xl
          "
        >
          {icon}
        </div>

        <div className="min-w-0">
          <div
            className="
              flex items-center
              gap-1.5
              text-sm
              text-base-content/50
            "
          >
            <MapPin
              size={13}
            />

            <span className="truncate">
              {location}
            </span>
          </div>

          <p
            className="
              mt-0.5
              font-semibold
              text-base-content
            "
          >
            {label}
          </p>
        </div>
      </div>

      <div
        className="
          shrink-0
          text-right
        "
      >
        <span
          className="
            text-3xl
            font-bold
            text-base-content
          "
        >
          {Math.round(
            temperature,
          )}
        </span>

        <span
          className="
            text-lg
            font-medium
            text-base-content/45
          "
        >
          °C
        </span>
      </div>
    </div>
  )
}


interface CurrentMetricsProps {
  apparentTemperature: number
  humidity: number
  precipitation: number
  windSpeed: number
}


function CurrentMetrics({
  apparentTemperature,
  humidity,
  precipitation,
  windSpeed,
}: CurrentMetricsProps) {
  return (
    <section
      className="
        overflow-hidden
        rounded-xl
        border
        border-base-300
      "
    >
      <div
        className="
          grid
          grid-cols-2
          divide-base-300
          sm:grid-cols-4
        "
      >
        <WeatherMetric
          icon={Thermometer}
          label="Ressenti"
          value={
            `${Math.round(
              apparentTemperature,
            )} °C`
          }
        />

        <WeatherMetric
          icon={Droplets}
          label="Humidité"
          value={
            `${Math.round(
              humidity,
            )} %`
          }
        />

        <WeatherMetric
          icon={CloudRain}
          label="Pluie"
          value={
            `${precipitation.toFixed(
              1,
            )} mm`
          }
        />

        <WeatherMetric
          icon={Wind}
          label="Vent"
          value={
            `${Math.round(
              windSpeed,
            )} km/h`
          }
        />
      </div>
    </section>
  )
}


interface WeatherMetricProps {
  icon:
    typeof Thermometer

  label: string
  value: string
}


function WeatherMetric({
  icon: Icon,
  label,
  value,
}: WeatherMetricProps) {
  return (
    <div
      className="
        flex items-center
        gap-3
        border-b
        border-base-300
        px-3 py-3
        odd:border-r
        sm:border-b-0
        sm:border-r
        sm:last:border-r-0
      "
    >
      <Icon
        size={16}
        className="
          shrink-0
          text-base-content/40
        "
      />

      <div className="min-w-0">
        <p
          className="
            text-[11px]
            uppercase
            tracking-wide
            text-base-content/40
          "
        >
          {label}
        </p>

        <p
          className="
            truncate
            text-sm
            font-semibold
            text-base-content
          "
        >
          {value}
        </p>
      </div>
    </div>
  )
}


interface WeatherAlertsProps {
  alerts:
    import('./alerts')
      .WeatherAlert[]
}


function WeatherAlerts({
  alerts,
}: WeatherAlertsProps) {
  const hasDanger =
    alerts.some(
      (alert) =>
        alert.severity
        === 'danger',
    )

  return (
    <section
      className="
        border-t
        border-base-300
        pt-5
      "
    >
      <details
        open={hasDanger}
        className="group"
      >
        <summary
          className="
            flex cursor-pointer
            list-none
            items-center
            justify-between
            gap-3
          "
        >
          <div
            className="
              flex items-center
              gap-2
            "
          >
            <span
              className="
                text-warning
              "
            >
              ⚠
            </span>

            <span
              className="
                font-semibold
                text-base-content
              "
            >
              Alertes météo
            </span>

            <span
              className="
                badge
                badge-warning
                badge-sm
              "
            >
              {alerts.length}
            </span>
          </div>

          <span
            className="
              text-xs
              text-base-content/35
              transition-transform
              group-open:rotate-180
            "
          >
            ▼
          </span>
        </summary>

        <div className="mt-3 space-y-2">
          {alerts.map(
            (alert) => (
              <WeatherAlertRow
                key={
                  `${alert.type}-${alert.severity}-${alert.time}`
                }
                alert={alert}
              />
            ),
          )}
        </div>
      </details>
    </section>
  )
}


interface WeatherAlertRowProps {
  alert:
    import('./alerts')
      .WeatherAlert
}


function WeatherAlertRow({
  alert,
}: WeatherAlertRowProps) {
  const style =
    getAlertStyle(
      alert.severity,
    )

  return (
    <div
      className={[
        (
          'rounded-xl border '
          + 'px-4 py-3'
        ),
        style,
      ].join(' ')}
    >
      <div
        className="
          flex items-start
          justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-sm
              font-semibold
            "
          >
            {alert.title}
          </p>

          <p
            className="
              mt-1
              text-sm
              leading-relaxed
              text-base-content/60
            "
          >
            {alert.message}
          </p>
        </div>

        {alert.time && (
          <span
            className="
              shrink-0
              text-xs
              text-base-content/40
            "
          >
            {formatAlertPeriod(
              alert.time,
              alert.endTime,
            )}
          </span>
        )}
      </div>
    </div>
  )
}


function HourlyForecast({
  weather,
}: {
  weather: WeatherData
}) {
  const upcomingHours =
    weather.hourly
      .filter(
        (hour) =>
          hour.time
          >= weather.current.time,
      )
      .slice(
        0,
        12,
      )
  return (
    <section
      className="
        border-t
        border-base-300
        pt-5
      "
    >
      <details className="group">
        <summary
          className="
            flex cursor-pointer
            list-none
            items-center
            justify-between
          "
        >
          <div>
            <h3
              className="
                font-semibold
                text-base-content
              "
            >
              Prochaines heures
            </h3>

            <p
              className="
                mt-0.5
                text-xs
                text-base-content/45
              "
            >
              Température et risque
              de précipitations
            </p>
          </div>

          <span
            className="
              text-xs
              text-base-content/35
              transition-transform
              group-open:rotate-180
            "
          >
            ▼
          </span>
        </summary>

        <div
          className="
            mt-4
            flex gap-2
            overflow-x-auto
            pb-2
          "
        >
          {upcomingHours.map(
            (hour) => {
                const description =
                  getWeatherDescription(
                    hour.weatherCode,
                  )

                return (
                  <HourlyItem
                    key={
                      hour.time
                    }
                    time={
                      hour.time
                    }
                    icon={
                      description.icon
                    }
                    temperature={
                      hour.temperature
                    }
                    precipitationProbability={
                      hour
                        .precipitationProbability
                    }
                    precipitation={
                      hour.precipitation
                    }
                  />
                )
              },
            )}
        </div>
      </details>
    </section>
  )
}


interface HourlyItemProps {
  time: string
  icon: string
  temperature: number
  precipitationProbability: number
  precipitation: number
}


function HourlyItem({
  time,
  icon,
  temperature,
  precipitationProbability,
  precipitation,
}: HourlyItemProps) {
  return (
    <div
      className="
        min-w-24
        rounded-xl
        border
        border-base-300
        px-3 py-3
        text-center
      "
    >
      <p
        className="
          text-xs
          text-base-content/45
        "
      >
        {formatHour(
          time,
        )}
      </p>

      <div
        className="
          my-2
          text-xl
        "
      >
        {icon}
      </div>

      <p
        className="
          text-sm
          font-bold
          text-base-content
        "
      >
        {Math.round(
          temperature,
        )}
        °
      </p>

      <p
        className="
          mt-2
          text-xs
          font-medium
          text-info
        "
      >
        {Math.round(
          precipitationProbability,
        )}
        %
      </p>

      <p
        className="
          mt-0.5
          text-[11px]
          text-base-content/35
        "
      >
        {precipitation.toFixed(
          1,
        )}
        {' '}
        mm
      </p>
    </div>
  )
}


function DailyForecast({
  weather,
}: {
  weather: WeatherData
}) {
  return (
    <section
      className="
        border-t
        border-base-300
        pt-5
      "
    >
      <details className="group">
        <summary
          className="
            flex cursor-pointer
            list-none
            items-center
            justify-between
          "
        >
          <div>
            <h3
              className="
                font-semibold
                text-base-content
              "
            >
              Prévisions à 7 jours
            </h3>

            <p
              className="
                mt-0.5
                text-xs
                text-base-content/45
              "
            >
              Tendance météo
              de la semaine
            </p>
          </div>

          <span
            className="
              text-xs
              text-base-content/35
              transition-transform
              group-open:rotate-180
            "
          >
            ▼
          </span>
        </summary>

        <div
          className="
            mt-4
            divide-y
            divide-base-300
          "
        >
          {weather.daily.map(
            (day) => {
              const description =
                getWeatherDescription(
                  day.weatherCode,
                )

              return (
                <DailyRow
                  key={
                    day.date
                  }
                  date={
                    day.date
                  }
                  icon={
                    description.icon
                  }
                  label={
                    description.label
                  }
                  temperatureMax={
                    day.temperatureMax
                  }
                  temperatureMin={
                    day.temperatureMin
                  }
                  precipitationProbability={
                    day
                      .precipitationProbabilityMax
                  }
                  precipitation={
                    day.precipitationSum
                  }
                />
              )
            },
          )}
        </div>
      </details>
    </section>
  )
}


interface DailyRowProps {
  date: string
  icon: string
  label: string
  temperatureMax: number
  temperatureMin: number
  precipitationProbability: number
  precipitation: number
}


function DailyRow({
  date,
  icon,
  label,
  temperatureMax,
  temperatureMin,
  precipitationProbability,
  precipitation,
}: DailyRowProps) {
  return (
    <div
      className="
        grid
        grid-cols-[1fr_auto]
        items-center
        gap-4
        py-3
      "
    >
      <div
        className="
          flex min-w-0
          items-center
          gap-3
        "
      >
        <span
          className="
            w-7
            shrink-0
            text-center
            text-xl
          "
        >
          {icon}
        </span>

        <div className="min-w-0">
          <p
            className="
              text-sm
              font-medium
              text-base-content
            "
          >
            {formatDate(
              date,
            )}
          </p>

          <p
            className="
              truncate
              text-xs
              text-base-content/45
            "
          >
            {label}
          </p>
        </div>
      </div>

      <div
        className="
          flex items-center
          gap-5
        "
      >
        <div
          className="
            text-right
            text-xs
          "
        >
          <p
            className="
              font-medium
              text-info
            "
          >
            {Math.round(
              precipitationProbability,
            )}
            %
          </p>

          <p
            className="
              text-base-content/35
            "
          >
            {precipitation.toFixed(
              1,
            )}
            {' '}
            mm
          </p>
        </div>

        <div
          className="
            min-w-14
            text-right
          "
        >
          <span
            className="
              text-sm
              font-bold
              text-base-content
            "
          >
            {Math.round(
              temperatureMax,
            )}
            °
          </span>

          <span
            className="
              ml-2
              text-sm
              text-base-content/35
            "
          >
            {Math.round(
              temperatureMin,
            )}
            °
          </span>
        </div>
      </div>
    </div>
  )
}


function getAlertStyle(
  severity:
    import('./alerts')
      .WeatherAlertSeverity,
): string {
  switch (severity) {
    case 'danger':
      return (
        'border-error/30 '
        + 'bg-error/5 '
        + 'text-error'
      )

    case 'warning':
      return (
        'border-warning/30 '
        + 'bg-warning/5 '
        + 'text-warning'
      )

    default:
      return (
        'border-info/30 '
        + 'bg-info/5 '
        + 'text-info'
      )
  }
}


function formatAlertTime(
  value: string,
): string {
  if (
    value.includes('T')
  ) {
    return new Intl.DateTimeFormat(
      'fr-FR',
      {
        weekday: 'short',
        hour: '2-digit',
        minute: '2-digit',
      },
    ).format(
      new Date(
        value,
      ),
    )
  }

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    },
  ).format(
    new Date(
      `${value}T12:00:00`,
    ),
  )
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


function formatHour(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(
    new Date(
      value,
    ),
  )
}


function formatDate(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    },
  ).format(
    new Date(
      `${value}T12:00:00`,
    ),
  )
}


function isAlertRelevant(
  alert:
    import('./alerts')
      .WeatherAlert,
): boolean {
  if (!alert.time) {
    return true
  }

  const now =
    new Date()

  const today =
    new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
    )

  const tomorrow =
    new Date(
      today,
    )

  tomorrow.setDate(
    tomorrow.getDate() + 1,
  )

  const alertDate =
    new Date(
      alert.time,
    )

  const alertDay =
    new Date(
      alertDate.getFullYear(),
      alertDate.getMonth(),
      alertDate.getDate(),
    )

  return (
    alertDay.getTime()
    === today.getTime()
    || alertDay.getTime()
    === tomorrow.getTime()
  )
}
