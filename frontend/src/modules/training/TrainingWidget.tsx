import {
  CalendarDays,
} from 'lucide-react'

import {
  useTrainingSessions,
} from './trainingStore'


interface TrainingWidgetProps {
  onClick: () => void
}


export function TrainingWidget({
  onClick,
}: TrainingWidgetProps) {
  const {
    sessions,
    loading,
    error,
  } = useTrainingSessions()

  const today = formatLocalDate(
    new Date(),
  )

  const session =
    sessions.find(
      (item) => item.date === today,
    ) ??
    sessions[0]

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
                Entraînement
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

  if (!session) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
      >
        <div className="card-body gap-2 p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
                Entraînement du jour
              </p>

              <h2 className="mt-1 text-lg font-bold">
                Repos
              </h2>
            </div>

            <CalendarDays className="h-4 w-4 text-base-content/40" />
          </div>

          <p className="text-sm text-base-content/55">
            Aucune séance planifiée aujourd’hui.
          </p>
        </div>
      </button>
    )
  }

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
              Entraînement du jour
            </p>

            <div className="mt-1 flex flex-wrap items-center gap-2">
              <h2 className="truncate text-lg font-bold">
                {session.title}
              </h2>

              <StatusBadge
                status={session.status}
              />
            </div>
          </div>

          <CalendarDays className="h-4 w-4 shrink-0 text-base-content/40" />
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <InlineMetric
            label="Durée"
            value={`${session.durationMinutes} min`}
          />

          <InlineMetric
            label="Intensité"
            value={session.intensity}
          />

          <InlineMetric
            label="Zone"
            value={
              session.heartRateZone
                ?? '—'
            }
          />

          {session.distanceKm !== undefined && (
            <InlineMetric
              label="Distance"
              value={`${session.distanceKm} km`}
            />
          )}
        </div>
      </div>
    </button>
  )
}


function StatusBadge({
  status,
}: {
  status:
    | 'planned'
    | 'completed'
    | 'skipped'
}) {
  if (status === 'completed') {
    return (
      <span className="badge badge-success badge-sm">
        Réalisée
      </span>
    )
  }

  if (status === 'skipped') {
    return (
      <span className="badge badge-error badge-sm">
        Non réalisée
      </span>
    )
  }

  return (
    <span className="badge badge-warning badge-sm">
      À faire
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


function formatLocalDate(
  date: Date,
): string {
  const year = date.getFullYear()

  const month = String(
    date.getMonth() + 1,
  ).padStart(2, '0')

  const day = String(
    date.getDate(),
  ).padStart(2, '0')

  return `${year}-${month}-${day}`
}