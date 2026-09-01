import {
  ArrowRight,
  CircleAlert,
  Gauge,
} from 'lucide-react'

import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  fetchTodayCheckIn,
  type DailyCheckInState,
} from '../../core/checkin'

import {
  RatingIcons,
} from './RatingIcons'


interface FeelingWidgetProps {
  onClick: () => void
}


export function FeelingWidget({
  onClick,
}: FeelingWidgetProps) {
  const [
    state,
    setState,
  ] = useState<DailyCheckInState | null>(
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


  const load =
    useCallback(
      async () => {
        try {
          setError(false)

          const result =
            await fetchTodayCheckIn()

          setState(result)
        } catch {
          setError(true)
        } finally {
          setLoading(false)
        }
      },
      [],
    )


  useEffect(() => {
    void load()

    window.addEventListener(
      'opencoach:daily-checkin-updated',
      load,
    )

    return () => {
      window.removeEventListener(
        'opencoach:daily-checkin-updated',
        load,
      )
    }
  }, [
    load,
  ])


  if (loading) {
    return (
      <div
        className="
          flex min-h-48
          items-center
          justify-center
          rounded-2xl
          border
          border-black/[0.07]
          bg-white
          dark:border-white/[0.08]
          dark:bg-[#141a1e]
        "
      >
        <span
          className="
            loading
            loading-spinner
            loading-sm
            text-emerald-500
          "
        />
      </div>
    )
  }


  const status =
    getStatus(state)


  return (
    <button
      type="button"
      onClick={onClick}
      className="
        group
        flex
        min-h-48
        w-full
        flex-col
        rounded-2xl
        border
        border-black/[0.07]
        bg-white
        p-5
        text-left
        shadow-[0_1px_2px_rgba(15,23,42,0.025)]
        transition
        duration-200
        hover:-translate-y-0.5
        hover:shadow-[0_12px_35px_rgba(15,23,42,0.055)]
        dark:border-white/[0.08]
        dark:bg-[#141a1e]
      "
    >
      <div
        className="
          flex
          items-start
          justify-between
          gap-4
        "
      >
        <div
          className="
            flex h-10 w-10
            items-center
            justify-center
            rounded-xl
            bg-emerald-50
            text-emerald-600
            dark:bg-emerald-500/10
            dark:text-emerald-400
          "
        >
          <Gauge
            className="h-5 w-5"
          />
        </div>

        {status.warning && (
          <CircleAlert
            className="
              h-4 w-4
              text-amber-500
            "
          />
        )}
      </div>


      <div className="mt-4 flex-1">
        {error ? (
          <>
            <p
              className="
                text-lg
                font-bold
                text-red-500
              "
            >
              Données indisponibles
            </p>

            <p
              className="
                mt-1
                text-sm
                text-slate-500
                dark:text-slate-400
              "
            >
              Impossible de charger
              ton ressenti du jour.
            </p>
          </>
        ) : !state ? (
          <>
            <p
              className="
                text-lg
                font-bold
                tracking-[-0.02em]
                text-slate-950
                dark:text-white
              "
            >
              Comment te sens-tu ?
            </p>

            <p
              className="
                mt-1
                text-sm
                leading-6
                text-slate-500
                dark:text-slate-400
              "
            >
              Ton retour aide OpenCoach
              à adapter la recommandation.
            </p>
          </>
        ) : (
          <>
            <div
              className="
                flex
                items-center
                justify-between
                gap-3
              "
            >
              <p
                className="
                  text-lg
                  font-bold
                  tracking-[-0.02em]
                  text-slate-950
                  dark:text-white
                "
              >
                {status.label}
              </p>

              <span
                className={
                  `text-xs font-semibold ${status.className}`
                }
              >
                Aujourd’hui
              </span>
            </div>

            <div
              className="
                mt-4
                space-y-3
              "
            >
              <RatingRow
                label="Énergie"
              >
                <RatingIcons
                  kind="energy"
                  value={
                    state.checkin
                      .energy_rating
                  }
                />
              </RatingRow>

              <RatingRow
                label="Confort"
              >
                <RatingIcons
                  kind="comfort"
                  value={
                    state.checkin
                      .pain_wellness_rating
                  }
                />
              </RatingRow>
            </div>
          </>
        )}
      </div>


      <div
        className="
          mt-4
          flex
          items-center
          justify-between
          border-t
          border-black/[0.06]
          pt-4
          dark:border-white/[0.07]
        "
      >
        <span
          className="
            text-xs
            font-semibold
            text-emerald-600
            dark:text-emerald-400
          "
        >
          {!state
            ? 'Renseigner mon état'
            : 'Voir mon ressenti'}
        </span>

        <ArrowRight
          className="
            h-4 w-4
            text-slate-300
            transition-transform
            group-hover:translate-x-1
            dark:text-slate-600
          "
        />
      </div>
    </button>
  )
}


function RatingRow({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div
      className="
        flex
        items-center
        justify-between
        gap-3
      "
    >
      <span
        className="
          text-xs
          font-medium
          text-slate-400
          dark:text-slate-500
        "
      >
        {label}
      </span>

      {children}
    </div>
  )
}


function getStatus(
  state: DailyCheckInState | null,
): {
  label: string
  className: string
  warning: boolean
} {
  if (!state) {
    return {
      label: 'À renseigner',
      className:
        'text-slate-400',
      warning: false,
    }
  }

  if (
    state.adaptation
      ?.awaiting_athlete_decision
  ) {
    return {
      label: 'Décision à prendre',
      className:
        'text-amber-500',
      warning: true,
    }
  }

  if (
    state.checkin.illness
    || state.checkin.unavailable
    || state.checkin.energy_rating <= 2
    || state.checkin.pain_wellness_rating <= 2
  ) {
    return {
      label: 'À surveiller',
      className:
        'text-amber-500',
      warning: true,
    }
  }

  if (
    state.adaptation?.decision
    === 'accepted'
  ) {
    return {
      label: 'Séance adaptée',
      className:
        'text-emerald-600 dark:text-emerald-400',
      warning: false,
    }
  }

  return {
    label: 'Bon ressenti',
    className:
      'text-emerald-600 dark:text-emerald-400',
    warning: false,
  }
}
