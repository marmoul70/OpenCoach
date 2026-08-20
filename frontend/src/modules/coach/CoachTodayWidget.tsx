import {
  useState,
} from 'react'

import {
  Eye,
} from 'lucide-react'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  CoachTodayDetails,
} from './CoachTodayDetails'

import type {
  CoachAction,
} from './types'

import {
  useCoachToday,
} from './useCoachToday'
import {
  formatTrainingIntensity,
} from '../training/intensity'

export function CoachTodayWidget() {
  const [
    detailsOpen,
    setDetailsOpen,
  ] = useState(false)

  const {
    coach,
    loading,
    unavailable,
    error,
  } = useCoachToday()

  if (loading) {
    return (
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body flex min-h-28 items-center justify-center p-4">
          <span className="loading loading-spinner loading-sm text-primary" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card w-full border border-error/30 bg-base-100 shadow-sm">
        <div className="card-body p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-error">
                Coach
              </p>

              <p className="mt-1 font-semibold text-error">
                Indisponible
              </p>
            </div>

            <span className="badge badge-error badge-sm">
              Erreur
            </span>
          </div>

          <p className="mt-2 text-sm text-base-content/60">
            {error}
          </p>
        </div>
      </div>
    )
  }

  if (
    unavailable
    || !coach
  ) {
    return (
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
            Coach du jour
          </p>

          <p className="mt-1 font-semibold">
            Données indisponibles
          </p>

          <p className="mt-1 text-sm text-base-content/50">
            Les données nécessaires au calcul du Readiness
            ne sont pas encore disponibles.
          </p>
        </div>
      </div>
    )
  }

  const {
    session,
    readiness,
    decision,
  } = coach

  return (
    <>
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body gap-3 p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
                Coach du jour
              </p>

              <div className="mt-1 flex flex-wrap items-center gap-2">
                <h2 className="truncate text-lg font-bold">
                  {session
                    ? session.title
                    : 'Repos aujourd’hui'}
                </h2>

                <DecisionBadge
                  action={decision.action}
                />
              </div>
            </div>

            <button
              type="button"
              className="btn btn-ghost btn-sm btn-circle shrink-0"
              onClick={() =>
                setDetailsOpen(true)
              }
              aria-label="Voir le détail du coach"
              title="Voir le détail"
            >
              <Eye className="h-4 w-4" />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
            <InlineMetric
              label="Readiness"
              value={`${Math.round(readiness.score)}/100`}
            />

            <InlineMetric
              label="Durée"
              value={
                decision.recommendedDurationMinutes
                  !== undefined
                  ? `${decision.recommendedDurationMinutes} min`
                  : 'Repos'
              }
            />

            <InlineMetric
              label="Intensité"
              value={
                formatIntensity(
                  decision.recommendedIntensity,
                )
              }
            />
          </div>

          <p className="line-clamp-2 text-sm leading-snug text-base-content/60">
            {decision.reason}
          </p>
        </div>
      </div>

      <Modal
        title="Coach du jour"
        open={detailsOpen}
        onClose={() =>
          setDetailsOpen(false)
        }
      >
        <CoachTodayDetails
          coach={coach}
        />
      </Modal>
    </>
  )
}


function DecisionBadge({
  action,
}: {
  action: CoachAction
}) {
  const label = {
    keep: 'Maintenir',
    reduce: 'Réduire',
    replace: 'Remplacer',
    rest: 'Repos',
  }[action]

  const className = {
    keep: 'badge-success',
    reduce: 'badge-warning',
    replace: 'badge-info',
    rest: 'badge-neutral',
  }[action]

  return (
    <span
      className={`badge badge-sm ${className}`}
    >
      {label}
    </span>
  )
}


function InlineMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="flex items-baseline gap-1.5 text-sm">
      <span className="text-xs text-base-content/45">
        {label}
      </span>

      <span className="font-semibold text-base-content">
        {value}
      </span>
    </div>
  )
}


function formatIntensity(
  intensity: string | null | undefined,
): string {
  return formatTrainingIntensity(
    intensity,
  )
}