import {
  Activity,
  CircleAlert,
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
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="flex min-h-20 items-center justify-center">
          <span className="loading loading-spinner loading-sm text-info" />
        </div>
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
        card
        w-full
        border
        border-base-300
        bg-base-100
        text-left
        shadow-sm
        transition-all
        duration-200
        hover:-translate-y-0.5
        hover:shadow-md
      "
    >
      <div className="flex min-h-20 items-center gap-5 px-4 py-3">

        <div
          className="
            flex h-10 w-10
            shrink-0
            items-center
            justify-center
            rounded-xl
            bg-info/10
            text-info
          "
        >
          <Activity className="h-5 w-5" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-base-content/50">
              Ressenti
            </p>

            {status.warning && (
              <CircleAlert className="h-3.5 w-3.5 text-warning" />
            )}
          </div>

          {error ? (
            <p className="mt-1 text-sm font-medium text-error">
              Données indisponibles
            </p>
          ) : !state ? (
            <p className="mt-1 text-sm font-medium text-base-content">
              Renseigner mon état du jour
            </p>
          ) : (
            <div className="mt-1.5 flex flex-wrap items-center gap-x-5 gap-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs text-base-content/45">
                  Énergie
                </span>

                <RatingIcons
                  kind="energy"
                  value={state.checkin.energy_rating}
                />
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-base-content/45">
                  Douleur
                </span>

                <RatingIcons
                  kind="comfort"
                  value={state.checkin.pain_wellness_rating}
                />
              </div>

              <span
                className={
                  `text-xs font-medium ${status.className}`
                }
              >
                {status.label}
              </span>
            </div>
          )}
        </div>

        <span className="text-lg text-base-content/25 transition-transform group-hover:translate-x-0.5">
          ›
        </span>
      </div>
    </button>
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
        'text-base-content/45',
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
        'text-warning',
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
        'text-warning',
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
        'text-success',
      warning: false,
    }
  }

  return {
    label: 'Renseigné',
    className:
      'text-success',
    warning: false,
  }
}
