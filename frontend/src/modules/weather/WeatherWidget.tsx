import {
  useEffect,
  useState,
} from 'react'

import {
  AlertTriangle,
  CloudSun,
  Droplets,
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
  isAlertRelevant,
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

import {
  WeatherIcon,
} from './components/WeatherIcon'


interface WeatherWidgetProps {
  onClick: () => void
  compact?: boolean
}


export function WeatherWidget({
  onClick,
  compact = false,
}: WeatherWidgetProps) {
  const {
    toast,
  } = useToast()

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
          setWeather(
            data,
          )
        }
      } catch {
        if (!cancelled) {
          setError(
            true,
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(
            false,
          )
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
        (alert) => (
          alert.time?.slice(
            0,
            10,
          ) === today
        ),
      )

    for (const alert of alerts) {
      const key = [
        'opencoach',
        'weather-alert',
        today,
        alert.type,
        alert.severity,
        alert.time ?? 'no-time',
        alert.endTime ?? 'no-end',
      ].join(':')

      let alreadyNotified =
        false

      try {
        alreadyNotified =
          window.localStorage.getItem(
            key,
          ) !== null
      } catch {
        alreadyNotified =
          false
      }

      if (alreadyNotified) {
        continue
      }

      try {
        window.localStorage.setItem(
          key,
          new Date().toISOString(),
        )
      } catch {
        // Notification toujours possible
        // si localStorage est indisponible.
      }

      toast({
        type:
          mapAlertSeverityToToastType(
            alert.severity,
          ),

        title:
          alert.title,

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
    if (compact) {
      return (
        <div
          className="
            flex
            h-14
            items-center
            justify-end
            px-3
          "
        >
          <span
            className="
              h-4
              w-4
              animate-spin
              rounded-full
              border-2
              border-slate-200
              border-t-emerald-500
              dark:border-white/[0.10]
              dark:border-t-emerald-400
            "
          />
        </div>
      )
    }

    return (
      <div
        className="
          flex
          min-h-36
          w-full
          items-center
          justify-center
          rounded-[14px]
          border
          border-black/[0.06]
          bg-white
          dark:border-white/[0.07]
          dark:bg-[#141a1e]
        "
      >
        <span
          className="
            h-6
            w-6
            animate-spin
            rounded-full
            border-[2.5px]
            border-slate-200
            border-t-emerald-500
            dark:border-white/[0.10]
            dark:border-t-emerald-400
          "
        />
      </div>
    )
  }


  if (
    error
    || !weather
  ) {
    if (compact) {
      return (
        <button
          type="button"
          onClick={onClick}
          className="
            inline-flex
            items-center
            gap-2
            rounded-[9px]
            px-2.5
            py-2
            text-[10.5px]
            text-rose-500
            transition
            hover:bg-rose-500/[0.05]
            dark:text-rose-400
          "
        >
          <CloudSun
            className="h-4 w-4"
          />

          Météo indisponible
        </button>
      )
    }

    return (
      <button
        type="button"
        onClick={onClick}
        className="
          w-full
          rounded-[14px]
          border
          border-rose-500/15
          bg-white
          p-4
          text-left
          transition
          hover:border-rose-500/25
          dark:border-rose-400/15
          dark:bg-[#141a1e]
        "
      >
        <p
          className="
            text-[9px]
            font-bold
            uppercase
            tracking-[0.08em]
            text-rose-500
            dark:text-rose-400
          "
        >
          Météo
        </p>

        <p
          className="
            mt-1
            text-[12px]
            font-semibold
            text-slate-800
            dark:text-slate-100
          "
        >
          Données indisponibles
        </p>
      </button>
    )
  }


  const description =
    getWeatherDescription(
      weather.current.weatherCode,
    )

  const relevantAlerts =
    getWeatherAlerts(
      weather,
    ).filter(
      isAlertRelevant,
    )

  const alertSeverity =
    getHighestAlertSeverity(
      relevantAlerts.map(
        (alert) => (
          alert.severity
        ),
      ),
    )

  const today =
    weather.daily[0]


  if (compact) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="
          group
          inline-flex
          items-center
          gap-2.5
          rounded-[10px]
          px-2.5
          py-1.5
          transition
        "
      >
        <div className="text-right">
          <p
            className="
              text-[15px]
              font-semibold
              text-slate-800
              dark:text-slate-100
            "
          >
            {Math.round(
              weather.current.temperature,
            )}
            °
          </p>

          <p
            className="
              mt-0.5
              text-[9px]
              text-slate-400
              dark:text-slate-500
            "
          >
            {description.label}
          </p>
        </div>

        <WeatherIcon
          weatherCode={
            weather.current.weatherCode
          }
          size={29}
        />
      </button>
    )
  }


  return (
    <button
      type="button"
      onClick={onClick}
      className="
        group
        min-h-[82px]
        w-full
        flex-1
        rounded-[13px]
        border
        border-black/[0.06]
        bg-white
        px-4
        py-3.5
        text-left
        shadow-[0_1px_2px_rgba(15,23,42,0.02)]
        transition
        hover:border-black/[0.10]
        
        dark:border-white/[0.07]
        dark:bg-[#141a1e]
        dark:shadow-none
        dark:hover:border-white/[0.11]
        
      "
      aria-label="Ouvrir la météo"
    >
      <div
        className="
          flex
          h-full
          items-center
          gap-3.5
        "
      >
        <div
          className="
            flex
            h-11
            w-11
            shrink-0
            items-center
            justify-center
            rounded-[10px]
            bg-slate-50
            dark:bg-white/[0.035]
          "
        >
          <WeatherIcon
            weatherCode={
              weather.current.weatherCode
            }
            size={33}
            className="
              transition-transform
              group-hover:scale-105
            "
          />
        </div>


        <div className="min-w-0 flex-1">
          <div
            className="
              flex
              items-center
              gap-2
            "
          >
            <span
              className="
                text-[22px]
                font-semibold
                leading-none
                tracking-[-0.035em]
                text-slate-900
                dark:text-white
              "
            >
              {Math.round(
                weather.current.temperature,
              )}
              °
            </span>

            <span
              className="
                min-w-0
                truncate
                text-[10.5px]
                font-medium
                text-slate-500
                dark:text-slate-400
              "
            >
              {description.label}
            </span>

            {alertSeverity && (
              <AlertTriangle
                className={[
                  'ml-auto h-3.5 w-3.5 shrink-0',
                  getAlertIndicatorClass(
                    alertSeverity,
                  ),
                ].join(' ')}
              />
            )}
          </div>


          <div
            className="
              mt-1.5
              flex
              flex-wrap
              items-center
              gap-x-3
              gap-y-1
              text-[9px]
              text-slate-500
              dark:text-slate-400
            "
          >
            <span
              className="
                inline-flex
                items-center
                gap-1
              "
            >
              <Droplets
                className="
                  h-3
                  w-3
                  text-sky-500
                "
                strokeWidth={1.8}
              />

              {
                today
                  ? `${Math.round(
                      today.precipitationProbabilityMax,
                    )}%`
                  : '—'
              }
            </span>

            <span
              className="
                inline-flex
                items-center
                gap-1
              "
            >
              <Wind
                className="
                  h-3
                  w-3
                  text-slate-400
                "
                strokeWidth={1.8}
              />

              {Math.round(
                weather.current.windSpeed,
              )}
              {' '}km/h
            </span>

            {today && (
              <span
                className="
                  text-slate-400
                  dark:text-slate-500
                "
              >
                {Math.round(
                  today.temperatureMin,
                )}
                ° /{' '}
                {Math.round(
                  today.temperatureMax,
                )}
                °
              </span>
            )}
          </div>
        </div>


        <span
          className="
            shrink-0
            text-[16px]
            text-slate-300
            transition
            group-hover:translate-x-0.5
            group-hover:text-slate-500
            dark:text-slate-600
            dark:group-hover:text-slate-400
          "
          aria-hidden="true"
        >
          →
        </span>
      </div>
    </button>
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
  if (severity === 'danger') {
    return 'text-rose-500 dark:text-rose-400'
  }

  if (severity === 'warning') {
    return 'text-amber-500 dark:text-amber-400'
  }

  return 'text-sky-500 dark:text-sky-400'
}


function mapAlertSeverityToToastType(
  severity: WeatherAlertSeverity,
): 'info' | 'warning' | 'error' {
  if (
    severity === 'danger'
  ) {
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

  if (!endTime) {
    return start
  }

  return (
    `${start}–`
    + formatAlertTime(
      endTime,
    )
  )
}


function formatAlertTime(
  value: string,
): string {
  const date =
    new Date(
      value,
    )

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value
  }

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(
    date,
  )
}
