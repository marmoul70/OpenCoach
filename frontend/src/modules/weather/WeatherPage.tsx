import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  AlertTriangle,
  ArrowUpRight,
  CloudRain,
  Droplets,
  MapPin,
  ShieldCheck,
  Sun,
  Sunrise,
  Sunset,
  Thermometer,
  Wind,
} from 'lucide-react'

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
  WeatherAlert,
} from './alerts'

import {
  getWeatherDescription,
} from './logic'

import type {
  DailyWeather,
  HourlyWeather,
  WeatherData,
} from './types'

import {
  WeatherIcon,
} from './components/WeatherIcon'


export function WeatherPage() {
  const profile =
    useAthleteProfile()

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
  ] = useState<string | null>(
    null,
  )


  useEffect(() => {
    let cancelled = false

    async function loadWeather() {
      try {
        setLoading(true)
        setError(null)

        const latitude =
          profile.location.latitude

        const longitude =
          profile.location.longitude

        if (
          latitude == null
          || longitude == null
        ) {
          throw new Error(
            'La localisation du profil est incomplète.',
          )
        }

        const data =
          await getWeather({
            name:
              profile.location.name
              || 'Ma position',

            latitude,
            longitude,
          })

        if (!cancelled) {
          setWeather(
            data,
          )
        }
      } catch (reason) {
        if (!cancelled) {
          setError(
            reason instanceof Error
              ? reason.message
              : (
                  'Impossible de charger '
                  + 'les données météo.'
                ),
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
    profile.location.latitude,
    profile.location.longitude,
    profile.location.name,
  ])


  const alerts =
    useMemo(
      () => (
        weather
          ? getWeatherAlerts(
              weather,
            ).filter(
              isAlertRelevant,
            )
          : []
      ),
      [
        weather,
      ],
    )


  if (loading) {
    return (
      <WeatherPageShell>
        <div
          className="
            flex
            min-h-[420px]
            items-center
            justify-center
          "
        >
          <span
            className="
              h-8
              w-8
              animate-spin
              rounded-full
              border-[2.5px]
              border-slate-200
              border-t-emerald-500
              dark:border-white/[0.10]
              dark:border-t-emerald-400
            "
            aria-hidden="true"
          />
        </div>
      </WeatherPageShell>
    )
  }


  if (
    error
    || !weather
  ) {
    return (
      <WeatherPageShell>
        <div
          className="
            flex
            min-h-[380px]
            items-center
            justify-center
          "
        >
          <div
            className="
              max-w-md
              rounded-[14px]
              border
              border-rose-500/15
              bg-rose-500/[0.04]
              p-5
              text-center
              dark:border-rose-400/15
              dark:bg-rose-400/[0.04]
            "
          >
            <AlertTriangle
              className="
                mx-auto
                h-6
                w-6
                text-rose-500
                dark:text-rose-400
              "
            />

            <p
              className="
                mt-3
                text-[13px]
                font-semibold
                text-slate-800
                dark:text-slate-100
              "
            >
              Météo indisponible
            </p>

            <p
              className="
                mt-1.5
                text-[10.5px]
                leading-relaxed
                text-slate-500
                dark:text-slate-400
              "
            >
              {error}
            </p>
          </div>
        </div>
      </WeatherPageShell>
    )
  }


  return (
    <WeatherPageShell>
      <WeatherContent
        weather={weather}
        alerts={alerts}
      />
    </WeatherPageShell>
  )
}


function WeatherPageShell({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <main
      className="
        min-h-screen
        bg-slate-50
        px-4
        py-5
        sm:px-6
        lg:px-8
        lg:py-7
        dark:bg-[#0f1417]
      "
    >
      <div
        className="
          mx-auto
          w-full
          max-w-[1500px]
        "
      >
        {children}
      </div>
    </main>
  )
}


function WeatherContent({
  weather,
  alerts,
}: {
  weather: WeatherData
  alerts: WeatherAlert[]
}) {
  const todayDate =
    weather.current.time.slice(
      0,
      10,
    )

  const today =
    weather.daily.find(
      (day) =>
        day.date === todayDate,
    )
    ?? weather.daily[0]

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

  const todayHours =
    weather.hourly.filter(
      (hour) =>
        hour.time.slice(
          0,
          10,
        ) === todayDate,
    )

  const description =
    getWeatherDescription(
      weather.current.weatherCode,
    )


  return (
    <div className="space-y-4">

      {/* =====================================================
          HEADER
         ===================================================== */}

      <header
        className="
          flex
          flex-col
          gap-4
          sm:flex-row
          sm:items-end
          sm:justify-between
        "
      >
        <div>
          <div
            className="
              flex
              items-center
              gap-2
              text-[10px]
              font-medium
              text-slate-400
              dark:text-slate-500
            "
          >
            <MapPin
              className="h-3.5 w-3.5"
              strokeWidth={1.8}
            />

            {
              weather.location.name
              ?? 'Ma position'
            }
          </div>

          <h1
            className="
              mt-1
              text-[23px]
              font-semibold
              tracking-[-0.035em]
              text-slate-900
              sm:text-[26px]
              dark:text-white
            "
          >
            Météo
          </h1>

          <p
            className="
              mt-1
              text-[10.5px]
              text-slate-500
              dark:text-slate-400
            "
          >
            Prévisions locales pour
            organiser tes entraînements.
          </p>
        </div>

        <p
          className="
            text-[9.5px]
            text-slate-400
            dark:text-slate-500
          "
        >
          Mis à jour à{' '}
          {formatHour(
            weather.current.time,
          )}
        </p>
      </header>


      {/* =====================================================
          HERO + ALERTES
         ===================================================== */}

      <WeatherAlertBanner
        alerts={alerts}
      />


      <div>
        <section
          className="
            overflow-hidden
            rounded-[16px]
            border
            border-black/[0.06]
            bg-white
            p-5
            shadow-[0_1px_2px_rgba(15,23,42,0.02)]
            sm:p-5
            dark:border-white/[0.07]
            dark:bg-[#151b1f]
            dark:shadow-none
          "
        >
          <div
            className="
              flex
              flex-col
              gap-6
              md:flex-row
              md:items-center
              md:justify-between
            "
          >
            <div
              className="
                flex
                items-center
                gap-5
              "
            >
              <div
                className="
                  flex
                  h-[72px]
                  w-[72px]
                  shrink-0
                  items-center
                  justify-center
                  rounded-[16px]
                  bg-slate-50
                  dark:bg-white/[0.035]
                "
              >
                <WeatherIcon
                  weatherCode={
                    weather.current.weatherCode
                  }
                  size={49}
                />
              </div>

              <div>
                <div
                  className="
                    flex
                    items-start
                    gap-1
                  "
                >
                  <span
                    className="
                      text-[54px]
                      font-semibold
                      leading-none
                      tracking-[-0.06em]
                      text-slate-950
                      dark:text-white
                    "
                  >
                    {Math.round(
                      weather.current.temperature,
                    )}
                  </span>

                  <span
                    className="
                      mt-1
                      text-[18px]
                      font-medium
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    °C
                  </span>
                </div>

                <p
                  className="
                    mt-2
                    text-[13px]
                    font-semibold
                    text-slate-700
                    dark:text-slate-200
                  "
                >
                  {description.label}
                </p>

                <p
                  className="
                    mt-1
                    text-[9.5px]
                    text-slate-400
                    dark:text-slate-500
                  "
                >
                  Ressenti{' '}
                  {Math.round(
                    weather.current
                      .apparentTemperature,
                  )}
                  °
                </p>
              </div>
            </div>


            {today && (
              <div
                className="
                  flex
                  items-center
                  gap-4
                  md:text-right
                "
              >
                <div>
                  <p
                    className="
                      text-[9px]
                      uppercase
                      tracking-[0.07em]
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    Minimum
                  </p>

                  <p
                    className="
                      mt-1
                      text-[17px]
                      font-semibold
                      text-slate-700
                      dark:text-slate-200
                    "
                  >
                    {Math.round(
                      today.temperatureMin,
                    )}
                    °
                  </p>
                </div>

                <div
                  className="
                    h-8
                    w-px
                    bg-black/[0.06]
                    dark:bg-white/[0.07]
                  "
                />

                <div>
                  <p
                    className="
                      text-[9px]
                      uppercase
                      tracking-[0.07em]
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    Maximum
                  </p>

                  <p
                    className="
                      mt-1
                      text-[17px]
                      font-semibold
                      text-slate-700
                      dark:text-slate-200
                    "
                  >
                    {Math.round(
                      today.temperatureMax,
                    )}
                    °
                  </p>
                </div>
              </div>
            )}
          </div>


          <div
            className="
              mt-6
              grid
              grid-cols-2
              gap-2
              sm:grid-cols-4
            "
          >
            <HeroMetric
              icon={Droplets}
              label="Humidité"
              value={
                `${Math.round(
                  weather.current.humidity,
                )}%`
              }
            />

            <HeroMetric
              icon={CloudRain}
              label="Pluie"
              value={
                today
                  ? (
                      `${Math.round(
                        today
                          .precipitationProbabilityMax,
                      )}%`
                    )
                  : '—'
              }
            />

            <HeroMetric
              icon={Wind}
              label="Vent"
              value={
                `${Math.round(
                  weather.current.windSpeed,
                )} km/h`
              }
            />

            <HeroMetric
              icon={ArrowUpRight}
              label="Rafales"
              value={
                `${Math.round(
                  weather.current.windGusts,
                )} km/h`
              }
            />
          </div>
        </section>
      </div>


      <TrainingWeatherInsight
        weather={weather}
        todayHours={todayHours}
      />


      {/* =====================================================
          PLUIE AUJOURD'HUI
         ===================================================== */}

      <RainSection
        hours={todayHours}
      />


      {/* =====================================================
          HOURLY
         ===================================================== */}

      <HourlySection
        hours={upcomingHours}
      />


      {/* =====================================================
          DAILY + CONDITIONS
         ===================================================== */}

      <div
        className="
          grid
          gap-5
          xl:grid-cols-12
          xl:items-start
        "
      >
        <DailySection
          days={weather.daily}
        />

        <ConditionsSection
          weather={weather}
          today={today}
        />
      </div>
    </div>
  )
}


function HeroMetric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Wind
  label: string
  value: string
}) {
  return (
    <div
      className="
        rounded-[11px]
        bg-slate-50/80
        px-3
        py-2.5
        dark:bg-white/[0.025]
      "
    >
      <div
        className="
          flex
          items-center
          gap-1.5
          text-[8.5px]
          text-slate-400
          dark:text-slate-500
        "
      >
        <Icon
          className="h-3.5 w-3.5"
          strokeWidth={1.8}
        />

        {label}
      </div>

      <p
        className="
          mt-1
          text-[11px]
          font-semibold
          text-slate-700
          dark:text-slate-200
        "
      >
        {value}
      </p>
    </div>
  )
}


function WeatherAlertBanner({
  alerts,
}: {
  alerts: WeatherAlert[]
}) {
  if (alerts.length === 0) {
    return (
      <div
        className="
          flex
          items-center
          gap-2
          rounded-[11px]
          border
          border-emerald-500/10
          bg-emerald-500/[0.025]
          px-3.5
          py-2.5
          text-[9.5px]
          text-emerald-700
          dark:border-emerald-400/10
          dark:bg-emerald-400/[0.025]
          dark:text-emerald-300
        "
      >
        <ShieldCheck
          className="
            h-3.5
            w-3.5
            shrink-0
          "
          strokeWidth={1.9}
        />

        Aucune vigilance météo actuellement
      </div>
    )
  }


  const primary =
    alerts[0]

  const tone =
    primary.severity === 'danger'
      ? (
          'border-rose-500/15 '
          + 'bg-rose-500/[0.04] '
          + 'dark:border-rose-400/15 '
          + 'dark:bg-rose-400/[0.04]'
        )
      : (
          'border-amber-500/15 '
          + 'bg-amber-500/[0.04] '
          + 'dark:border-amber-400/15 '
          + 'dark:bg-amber-400/[0.04]'
        )

  const iconTone =
    primary.severity === 'danger'
      ? (
          'text-rose-500 '
          + 'dark:text-rose-400'
        )
      : (
          'text-amber-500 '
          + 'dark:text-amber-400'
        )

  return (
    <section
      className={[
        (
          'rounded-[13px] '
          + 'border '
          + 'px-4 '
          + 'py-3.5'
        ),
        tone,
      ].join(' ')}
    >
      <div
        className="
          flex
          items-start
          gap-3
        "
      >
        <AlertTriangle
          className={[
            (
              'mt-0.5 '
              + 'h-4 '
              + 'w-4 '
              + 'shrink-0'
            ),
            iconTone,
          ].join(' ')}
          strokeWidth={1.9}
        />

        <div className="min-w-0 flex-1">
          <div
            className="
              flex
              flex-wrap
              items-center
              gap-x-3
              gap-y-1
            "
          >
            <p
              className="
                text-[10.5px]
                font-semibold
                text-slate-800
                dark:text-slate-100
              "
            >
              {primary.title}
            </p>

            {primary.time && (
              <span
                className="
                  text-[8.5px]
                  text-slate-400
                  dark:text-slate-500
                "
              >
                {formatAlertRange(
                  primary,
                )}
              </span>
            )}
          </div>

          <p
            className="
              mt-1
              text-[9.5px]
              leading-relaxed
              text-slate-500
              dark:text-slate-400
            "
          >
            {primary.message}
          </p>

          {alerts.length > 1 && (
            <p
              className="
                mt-1.5
                text-[8.5px]
                font-medium
                text-slate-400
                dark:text-slate-500
              "
            >
              + {alerts.length - 1}
              {' '}
              autre
              {alerts.length > 2 ? 's' : ''}
              {' '}
              alerte
              {alerts.length > 2 ? 's' : ''}
            </p>
          )}
        </div>
      </div>
    </section>
  )
}


function TrainingWeatherInsight({
  weather,
  todayHours,
}: {
  weather: WeatherData
  todayHours: HourlyWeather[]
}) {
  const assessment =
    getTrainingWeatherAssessment(
      weather,
      todayHours,
    )

  const toneClasses = {
    favorable:
      (
        'border-emerald-500/12 '
        + 'bg-emerald-500/[0.035] '
        + 'dark:border-emerald-400/12 '
        + 'dark:bg-emerald-400/[0.035]'
      ),

    caution:
      (
        'border-amber-500/15 '
        + 'bg-amber-500/[0.035] '
        + 'dark:border-amber-400/15 '
        + 'dark:bg-amber-400/[0.035]'
      ),

    unfavorable:
      (
        'border-rose-500/15 '
        + 'bg-rose-500/[0.035] '
        + 'dark:border-rose-400/15 '
        + 'dark:bg-rose-400/[0.035]'
      ),
  }

  const statusClasses = {
    favorable:
      (
        'bg-emerald-500 '
        + 'dark:bg-emerald-400'
      ),

    caution:
      (
        'bg-amber-500 '
        + 'dark:bg-amber-400'
      ),

    unfavorable:
      (
        'bg-rose-500 '
        + 'dark:bg-rose-400'
      ),
  }

  return (
    <section
      className={[
        (
          'rounded-[16px] '
          + 'border '
          + 'p-4 '
          + 'sm:p-5'
        ),
        toneClasses[
          assessment.level
        ],
      ].join(' ')}
    >
      <div
        className="
          flex
          flex-col
          gap-4
          lg:flex-row
          lg:items-center
          lg:justify-between
        "
      >
        <div className="min-w-0">
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-slate-500
              dark:text-slate-400
            "
          >
            Conditions pour l’entraînement
          </p>

          <div
            className="
              mt-2
              flex
              items-center
              gap-2
            "
          >
            <span
              className={[
                (
                  'h-2 '
                  + 'w-2 '
                  + 'rounded-full'
                ),
                statusClasses[
                  assessment.level
                ],
              ].join(' ')}
            />

            <p
              className="
                text-[14px]
                font-semibold
                text-slate-800
                dark:text-slate-100
              "
            >
              {assessment.title}
            </p>
          </div>

          <p
            className="
              mt-2
              max-w-3xl
              text-[10.5px]
              leading-[1.65]
              text-slate-500
              dark:text-slate-400
            "
          >
            {assessment.message}
          </p>
        </div>


        <div
          className="
            shrink-0
            rounded-[11px]
            border
            border-black/[0.05]
            bg-white/55
            px-4
            py-3
            dark:border-white/[0.06]
            dark:bg-white/[0.025]
          "
        >
          <p
            className="
              text-[8.5px]
              font-medium
              uppercase
              tracking-[0.06em]
              text-slate-400
              dark:text-slate-500
            "
          >
            Meilleur créneau
          </p>

          <p
            className="
              mt-1
              text-[12px]
              font-semibold
              text-slate-700
              dark:text-slate-200
            "
          >
            {assessment.window}
          </p>
        </div>
      </div>
    </section>
  )
}


interface TrainingWeatherAssessment {
  level:
    | 'favorable'
    | 'caution'
    | 'unfavorable'

  title: string
  message: string
  window: string
}


function getTrainingWeatherAssessment(
  weather: WeatherData,
  todayHours: HourlyWeather[],
): TrainingWeatherAssessment {
  const temperature =
    weather.current.temperature

  const wind =
    weather.current.windSpeed

  const gusts =
    weather.current.windGusts

  const nextHours =
    todayHours.filter(
      (hour) =>
        hour.time >= weather.current.time,
    )

  const maxRain =
    Math.max(
      0,
      ...nextHours.map(
        (hour) =>
          hour.precipitationProbability,
      ),
    )

  const dryHours =
    nextHours.filter(
      (hour) => (
        hour.precipitationProbability <= 30
        && hour.windSpeed < 30
      ),
    )

  const window =
    formatBestWeatherWindow(
      dryHours,
    )


  if (
    gusts >= 60
    || wind >= 45
    || maxRain >= 85
    || temperature >= 34
    || temperature <= -5
  ) {
    return {
      level: 'unfavorable',
      title: 'Conditions défavorables',
      message:
        (
          'Les conditions météo demandent '
          + 'de la prudence. Vent, pluie '
          + 'ou température peuvent rendre '
          + 'la séance extérieure moins adaptée.'
        ),
      window,
    }
  }


  if (
    gusts >= 40
    || wind >= 30
    || maxRain >= 60
    || temperature >= 29
    || temperature <= 1
  ) {
    return {
      level: 'caution',
      title: 'Conditions à surveiller',
      message:
        (
          'La séance reste envisageable, '
          + 'mais certaines conditions peuvent '
          + 'nécessiter une adaptation du créneau, '
          + 'du parcours ou de l’équipement.'
        ),
      window,
    }
  }


  return {
    level: 'favorable',
    title: 'Conditions favorables',
    message:
      (
        'Les conditions sont actuellement '
        + 'favorables à un entraînement extérieur. '
        + 'Le vent reste modéré et aucun risque '
        + 'météo important n’est détecté.'
      ),
    window,
  }
}


function formatBestWeatherWindow(
  hours: HourlyWeather[],
): string {
  if (hours.length === 0) {
    return 'Aucun créneau idéal'
  }

  let bestStart =
    hours[0]

  let bestEnd =
    hours[0]

  let currentStart =
    hours[0]

  let previous =
    hours[0]


  for (
    let index = 1;
    index < hours.length;
    index += 1
  ) {
    const hour =
      hours[index]

    const previousDate =
      new Date(
        previous.time,
      )

    const currentDate =
      new Date(
        hour.time,
      )

    const consecutive =
      (
        currentDate.getTime()
        - previousDate.getTime()
      ) === 60 * 60 * 1000

    if (!consecutive) {
      if (
        getWindowDuration(
          currentStart,
          previous,
        )
        > getWindowDuration(
            bestStart,
            bestEnd,
          )
      ) {
        bestStart =
          currentStart

        bestEnd =
          previous
      }

      currentStart =
        hour
    }

    previous =
      hour
  }


  if (
    getWindowDuration(
      currentStart,
      previous,
    )
    > getWindowDuration(
        bestStart,
        bestEnd,
      )
  ) {
    bestStart =
      currentStart

    bestEnd =
      previous
  }


  return (
    `${formatHour(
      bestStart.time,
    )} → ${formatHour(
      bestEnd.time,
    )}`
  )
}


function getWindowDuration(
  start: HourlyWeather,
  end: HourlyWeather,
): number {
  return (
    new Date(
      end.time,
    ).getTime()
    - new Date(
        start.time,
      ).getTime()
  )
}


function RainSection({
  hours,
}: {
  hours: HourlyWeather[]
}) {
  const usefulHours =
    hours.filter(
      (_, index) =>
        index % 2 === 0,
    )

  const maxRain =
    Math.max(
      0,
      ...hours.map(
        (hour) =>
          hour.precipitationProbability,
      ),
    )

  const wettest =
    hours.reduce<
      HourlyWeather | null
    >(
      (
        current,
        hour,
      ) => (
        !current
        || hour.precipitationProbability
          > current.precipitationProbability
          ? hour
          : current
      ),
      null,
    )

  const dryHours =
    hours.filter(
      (hour) =>
        hour.precipitationProbability <= 20,
    )

  const dryWindow =
    formatBestWeatherWindow(
      dryHours,
    )

  const chartPoints =
    usefulHours.map(
      (
        hour,
        index,
      ) => {
        const x =
          usefulHours.length <= 1
            ? 0
            : (
                index
                / (usefulHours.length - 1)
              ) * 100

        const y =
          100
          - Math.max(
              5,
              Math.min(
                100,
                hour.precipitationProbability,
              ),
            )

        return {
          x,
          y,
          hour,
        }
      },
    )

  const polyline =
    chartPoints
      .map(
        (point) =>
          `${point.x},${point.y}`,
      )
      .join(' ')

  const areaPoints =
    chartPoints.length > 0
      ? (
          `0,100 ${polyline} 100,100`
        )
      : ''


  return (
    <section
      className="
        overflow-hidden
        rounded-[16px]
        border
        border-black/[0.06]
        bg-white
        p-4
        sm:p-5
        dark:border-white/[0.07]
        dark:bg-[#151b1f]
      "
    >
      <div
        className="
          flex
          flex-col
          gap-4
          sm:flex-row
          sm:items-start
          sm:justify-between
        "
      >
        <div>
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-sky-600
              dark:text-sky-400
            "
          >
            Pluie aujourd’hui
          </p>

          <h2
            className="
              mt-1
              text-[14px]
              font-semibold
              tracking-[-0.015em]
              text-slate-800
              dark:text-slate-100
            "
          >
            Risque de précipitations
          </h2>

          <p
            className="
              mt-1.5
              text-[9.5px]
              text-slate-400
              dark:text-slate-500
            "
          >
            Fenêtre la plus sèche :
            {' '}
            {dryWindow}
          </p>
        </div>


        <div
          className="
            flex
            items-center
            gap-5
            sm:text-right
          "
        >
          <div>
            <p
              className="
                text-[8.5px]
                uppercase
                tracking-[0.06em]
                text-slate-400
                dark:text-slate-500
              "
            >
              Risque max
            </p>

            <p
              className="
                mt-1
                text-[14px]
                font-semibold
                text-slate-800
                dark:text-slate-100
              "
            >
              {Math.round(
                maxRain,
              )}
              %
            </p>
          </div>

          {wettest && (
            <div>
              <p
                className="
                  text-[8.5px]
                  uppercase
                  tracking-[0.06em]
                  text-slate-400
                  dark:text-slate-500
                "
              >
                Pic prévu
              </p>

              <p
                className="
                  mt-1
                  text-[14px]
                  font-semibold
                  text-slate-800
                  dark:text-slate-100
                "
              >
                {formatHour(
                  wettest.time,
                )}
              </p>
            </div>
          )}
        </div>
      </div>


      <div
        className="
          relative
          mt-5
          h-[155px]
          overflow-hidden
          rounded-[12px]
          border
          border-black/[0.045]
          bg-slate-50/70
          dark:border-white/[0.055]
          dark:bg-white/[0.02]
        "
      >
        <div
          className="
            pointer-events-none
            absolute
            inset-x-0
            top-1/4
            border-t
            border-dashed
            border-black/[0.04]
            dark:border-white/[0.04]
          "
        />

        <div
          className="
            pointer-events-none
            absolute
            inset-x-0
            top-1/2
            border-t
            border-dashed
            border-black/[0.04]
            dark:border-white/[0.04]
          "
        />

        <div
          className="
            pointer-events-none
            absolute
            inset-x-0
            top-3/4
            border-t
            border-dashed
            border-black/[0.04]
            dark:border-white/[0.04]
          "
        />


        {chartPoints.length > 0 && (
          <svg
            viewBox="0 0 100 100"
            preserveAspectRatio="none"
            className="
              absolute
              inset-x-0
              top-3
              h-[105px]
              w-full
              overflow-visible
            "
            aria-hidden="true"
          >
            <polygon
              points={areaPoints}
              className="
                fill-sky-500/[0.10]
                dark:fill-sky-400/[0.10]
              "
            />

            <polyline
              points={polyline}
              fill="none"
              vectorEffect="non-scaling-stroke"
              className="
                stroke-sky-500
                dark:stroke-sky-400
              "
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}


        <div
          className="
            absolute
            inset-x-3
            bottom-3
            top-3
          "
        >
          {chartPoints.map(
            (point) => (
              <div
                key={point.hour.time}
                className="
                  absolute
                  top-0
                  bottom-0
                  -translate-x-1/2
                "
                style={{
                  left:
                    `${point.x}%`,
                }}
              >
                <div
                  className="
                    absolute
                    left-1/2
                    h-2
                    w-2
                    -translate-x-1/2
                    -translate-y-1/2
                    rounded-full
                    border-2
                    border-white
                    bg-sky-500
                    shadow-sm
                    dark:border-[#151b1f]
                    dark:bg-sky-400
                  "
                  style={{
                    top:
                      `${Math.max(
                        4,
                        Math.min(
                          72,
                          point.y * 0.72,
                        ),
                      )}%`,
                  }}
                />

                <div
                  className="
                    absolute
                    bottom-0
                    left-1/2
                    -translate-x-1/2
                    whitespace-nowrap
                    text-center
                  "
                >
                  <p
                    className="
                      text-[8px]
                      font-medium
                      text-slate-500
                      dark:text-slate-400
                    "
                  >
                    {Math.round(
                      point.hour
                        .precipitationProbability,
                    )}
                    %
                  </p>

                  <p
                    className="
                      mt-0.5
                      text-[7.5px]
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    {formatHour(
                      point.hour.time,
                    )}
                  </p>
                </div>
              </div>
            ),
          )}
        </div>
      </div>
    </section>
  )
}


function HourlySection({
  hours,
}: {
  hours: HourlyWeather[]
}) {
  return (
    <section
      className="
        overflow-hidden
        rounded-[16px]
        border
        border-black/[0.06]
        bg-white
        p-4
        sm:p-5
        dark:border-white/[0.07]
        dark:bg-[#151b1f]
      "
    >
      <div
        className="
          flex
          items-end
          justify-between
          gap-4
        "
      >
        <div>
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Prochaines heures
          </p>

          <h2
            className="
              mt-1
              text-[14px]
              font-semibold
              tracking-[-0.015em]
              text-slate-800
              dark:text-slate-100
            "
          >
            Évolution heure par heure
          </h2>
        </div>

        <p
          className="
            hidden
            text-[8.5px]
            text-slate-400
            sm:block
            dark:text-slate-500
          "
        >
          Température · pluie · vent
        </p>
      </div>


      <div
        className="
          mt-5
          overflow-x-auto
          pb-1
        "
      >
        <div
          className="
            grid
            min-w-[980px]
            grid-cols-12
            gap-0
          "
        >
          {hours.map(
            (
              hour,
              index,
            ) => {
              const description =
                getWeatherDescription(
                  hour.weatherCode,
                )

              return (
                <div
                  key={hour.time}
                  className={[
                    (
                      'relative '
                      + 'px-3 '
                      + 'py-2.5 '
                      + 'text-center'
                    ),
                    (
                      index !== 0
                        ? (
                            'border-l '
                            + 'border-black/[0.045] '
                            + 'dark:border-white/[0.05]'
                          )
                        : ''
                    ),
                  ].join(' ')}
                >
                  <p
                    className="
                      text-[8.5px]
                      font-medium
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    {formatHour(
                      hour.time,
                    )}
                  </p>

                  <div
                    className="
                      mt-2.5
                      flex
                      justify-center
                    "
                  >
                    <WeatherIcon
                      weatherCode={
                        hour.weatherCode
                      }
                      size={27}
                    />
                  </div>

                  <p
                    className="
                      mt-2
                      text-[15px]
                      font-semibold
                      tracking-[-0.02em]
                      text-slate-800
                      dark:text-slate-100
                    "
                  >
                    {Math.round(
                      hour.temperature,
                    )}
                    °
                  </p>

                  <p
                    className="
                      mt-1
                      truncate
                      text-[7.5px]
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    {description.label}
                  </p>


                  <div
                    className="
                      mt-3
                      flex
                      flex-col
                      items-center
                      gap-1.5
                    "
                  >
                    <div
                      className="
                        inline-flex
                        items-center
                        gap-1
                        text-[8px]
                        font-medium
                        text-sky-500
                        dark:text-sky-400
                      "
                    >
                      <Droplets
                        className="h-3 w-3"
                        strokeWidth={1.8}
                      />

                      {Math.round(
                        hour
                          .precipitationProbability,
                      )}
                      %
                    </div>

                    <div
                      className="
                        inline-flex
                        items-center
                        gap-1
                        text-[8px]
                        text-slate-400
                        dark:text-slate-500
                      "
                    >
                      <Wind
                        className="h-3 w-3"
                        strokeWidth={1.8}
                      />

                      {Math.round(
                        hour.windSpeed,
                      )}
                      {' '}km/h
                    </div>
                  </div>
                </div>
              )
            },
          )}
        </div>
      </div>
    </section>
  )
}


function DailySection({
  days,
}: {
  days: DailyWeather[]
}) {
  const weeklyMin =
    Math.min(
      ...days.map(
        (day) =>
          day.temperatureMin,
      ),
    )

  const weeklyMax =
    Math.max(
      ...days.map(
        (day) =>
          day.temperatureMax,
      ),
    )

  return (
    <section
      className="
        rounded-[16px]
        border
        border-black/[0.06]
        bg-white
        p-4
        sm:p-5
        xl:col-span-8
        xl:min-h-full
        dark:border-white/[0.07]
        dark:bg-[#151b1f]
      "
    >
      <div
        className="
          flex
          items-end
          justify-between
          gap-4
        "
      >
        <div>
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            7 prochains jours
          </p>

          <h2
            className="
              mt-1
              text-[14px]
              font-semibold
              text-slate-800
              dark:text-slate-100
            "
          >
            Tendance de la semaine
          </h2>
        </div>

        <p
          className="
            hidden
            text-[8.5px]
            text-slate-400
            sm:block
            dark:text-slate-500
          "
        >
          {Math.round(
            weeklyMin,
          )}
          ° →{' '}
          {Math.round(
            weeklyMax,
          )}
          °
        </p>
      </div>

      <div className="mt-3">
        {days.map(
          (
            day,
            index,
          ) => (
            <DailyRow
              key={day.date}
              day={day}
              today={index === 0}
              weeklyMin={weeklyMin}
              weeklyMax={weeklyMax}
            />
          ),
        )}
      </div>
    </section>
  )
}


function DailyRow({
  day,
  today,
  weeklyMin,
  weeklyMax,
}: {
  day: DailyWeather
  today: boolean
  weeklyMin: number
  weeklyMax: number
}) {
  const description =
    getWeatherDescription(
      day.weatherCode,
    )

  const range =
    Math.max(
      1,
      weeklyMax - weeklyMin,
    )

  const start =
    (
      (day.temperatureMin - weeklyMin)
      / range
    ) * 100

  const width =
    Math.max(
      8,
      (
        (
          day.temperatureMax
          - day.temperatureMin
        )
        / range
      ) * 100,
    )


  return (
    <div
      className={[
        (
          'grid '
          + 'grid-cols-[82px_30px_minmax(0,1fr)_132px] '
          + 'items-center '
          + 'gap-3 '
          + 'border-b '
          + 'border-black/[0.05] '
          + 'py-3 '
          + 'last:border-b-0 '
          + 'sm:grid-cols-[90px_34px_minmax(0,1fr)_150px] '
          + 'dark:border-white/[0.055]'
        ),
        today
          ? (
              '-mx-2 rounded-[10px] '
              + 'bg-emerald-500/[0.035] '
              + 'px-2 '
              + 'dark:bg-emerald-400/[0.035]'
            )
          : '',
      ].join(' ')}
    >
      <p
        className={[
          (
            'text-[10.5px] '
            + 'font-semibold'
          ),
          today
            ? (
                'text-emerald-700 '
                + 'dark:text-emerald-300'
              )
            : (
                'text-slate-700 '
                + 'dark:text-slate-200'
              ),
        ].join(' ')}
      >
        {
          today
            ? 'Aujourd’hui'
            : formatDay(
                day.date,
              )
        }
      </p>

      <WeatherIcon
        weatherCode={
          day.weatherCode
        }
        size={24}
      />


      <div className="min-w-0">
        <p
          className="
            truncate
            text-[9.5px]
            text-slate-500
            dark:text-slate-400
          "
        >
          {description.label}
        </p>

        <div
          className="
            mt-1
            flex
            items-center
            gap-1.5
            text-[8px]
          "
        >
          <span
            className="
              inline-flex
              items-center
              gap-1
              text-sky-500
              dark:text-sky-400
            "
          >
            <Droplets
              className="h-3 w-3"
            />

            {Math.round(
              day.precipitationProbabilityMax,
            )}
            %
          </span>

          <span
            className="
              text-slate-300
              dark:text-slate-600
            "
          >
            ·
          </span>

          <span
            className="
              text-slate-400
              dark:text-slate-500
            "
          >
            {day.precipitationSum.toFixed(
              1,
            )}
            {' '}mm
          </span>
        </div>
      </div>


      <div
        className="
          flex
          items-center
          gap-2
        "
      >
        <span
          className="
            w-8
            text-right
            text-[10px]
            font-medium
            text-slate-400
            dark:text-slate-500
          "
        >
          {Math.round(
            day.temperatureMin,
          )}
          °
        </span>

        <div
          className="
            relative
            h-1.5
            flex-1
            overflow-hidden
            rounded-full
            bg-slate-100
            dark:bg-white/[0.06]
          "
        >
          <div
            className="
              absolute
              inset-y-0
              rounded-full
              bg-gradient-to-r
              from-sky-400/70
              via-emerald-400/70
              to-amber-400/80
            "
            style={{
              left:
                `${start}%`,

              width:
                `${Math.min(
                  width,
                  100 - start,
                )}%`,
            }}
          />
        </div>

        <span
          className="
            w-8
            text-[10px]
            font-semibold
            text-slate-700
            dark:text-slate-200
          "
        >
          {Math.round(
            day.temperatureMax,
          )}
          °
        </span>
      </div>
    </div>
  )
}


function ConditionsSection({
  weather,
  today,
}: {
  weather: WeatherData
  today?: DailyWeather
}) {
  return (
    <section
      className="
        rounded-[16px]
        border
        border-black/[0.06]
        bg-white
        p-4
        sm:p-5
        xl:col-span-4
        dark:border-white/[0.07]
        dark:bg-[#151b1f]
      "
    >
      <div
        className="
          flex
          items-end
          justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Conditions
          </p>

          <h2
            className="
              mt-1
              text-[14px]
              font-semibold
              text-slate-800
              dark:text-slate-100
            "
          >
            Détails du jour
          </h2>
        </div>

        <p
          className="
            hidden
            text-[8.5px]
            text-slate-400
            sm:block
            dark:text-slate-500
          "
        >
          Valeurs locales
        </p>
      </div>


      <div
        className="
          mt-4
          grid
          grid-cols-2
          gap-2
        "
      >
        <ConditionCard
          icon={Wind}
          label="Vent"
          value={
            `${Math.round(
              weather.current.windSpeed,
            )} km/h`
          }
        />

        <ConditionCard
          icon={ArrowUpRight}
          label="Rafales"
          value={
            `${Math.round(
              weather.current.windGusts,
            )} km/h`
          }
        />

        <ConditionCard
          icon={Droplets}
          label="Humidité"
          value={
            `${Math.round(
              weather.current.humidity,
            )}%`
          }
        />

        <ConditionCard
          icon={Sun}
          label="UV max"
          value={
            today
              ? today.uvIndexMax.toFixed(1)
              : '—'
          }
        />

        <ConditionCard
          icon={Sunrise}
          label="Lever"
          value={
            today
              ? formatHour(
                  today.sunrise,
                )
              : '—'
          }
        />

        <ConditionCard
          icon={Sunset}
          label="Coucher"
          value={
            today
              ? formatHour(
                  today.sunset,
                )
              : '—'
          }
        />

        <ConditionCard
          icon={CloudRain}
          label="Cumul pluie"
          value={
            today
              ? (
                  `${today
                    .precipitationSum
                    .toFixed(1)} mm`
                )
              : '—'
          }
        />

        <ConditionCard
          icon={Thermometer}
          label="Ressenti"
          value={
            `${Math.round(
              weather.current
                .apparentTemperature,
            )}°`
          }
        />
      </div>
    </section>
  )
}


function ConditionCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Wind
  label: string
  value: string
}) {
  return (
    <div
      className="
        rounded-[10px]
        border
        border-black/[0.045]
        bg-slate-50/65
        px-3
        py-2.5
        dark:border-white/[0.05]
        dark:bg-white/[0.02]
      "
    >
      <div
        className="
          flex
          items-center
          gap-2
        "
      >
        <div
          className="
            flex
            h-7
            w-7
            shrink-0
            items-center
            justify-center
            rounded-[8px]
            bg-white
            text-slate-400
            dark:bg-white/[0.035]
            dark:text-slate-500
          "
        >
          <Icon
            className="h-3.5 w-3.5"
            strokeWidth={1.8}
          />
        </div>

        <div className="min-w-0">
          <p
            className="
              text-[8px]
              text-slate-400
              dark:text-slate-500
            "
          >
            {label}
          </p>

          <p
            className="
              mt-0.5
              truncate
              text-[10.5px]
              font-semibold
              text-slate-700
              dark:text-slate-200
            "
          >
            {value}
          </p>
        </div>
      </div>
    </div>
  )
}


function formatHour(
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


function formatDay(
  value: string,
): string {
  const date =
    new Date(
      `${value}T12:00:00`,
    )

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
    },
  ).format(
    date,
  )
}


function formatAlertRange(
  alert: WeatherAlert,
): string {
  if (!alert.time) {
    return ''
  }

  if (!alert.endTime) {
    return formatHour(
      alert.time,
    )
  }

  return (
    `${formatHour(
      alert.time,
    )} – ${formatHour(
      alert.endTime,
    )}`
  )
}
