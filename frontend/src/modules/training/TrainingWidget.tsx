import { Clock3, Gauge } from 'lucide-react'

import { useTrainingSessions } from './trainingStore'


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
        <div className="card-body flex min-h-48 items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card w-full border border-error/30 bg-base-100 shadow-sm">
        <div className="card-body">
          <p className="font-semibold text-error">
            Entraînement indisponible
          </p>

          <p className="mt-1 text-sm text-base-content/60">
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
        className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
      >
        <div className="card-body p-5">
          <p className="text-sm font-medium text-base-content/60">
            Entraînement du jour
          </p>

          <h2 className="mt-2 text-xl font-bold text-base-content">
            Aucune séance prévue
          </h2>

          <p className="mt-2 text-sm text-base-content/50">
            Aucun entraînement n&apos;est programmé pour cette semaine.
          </p>

          <div className="mt-4 text-right">
            <span className="text-sm font-medium text-primary">
              Voir le planning →
            </span>
          </div>
        </div>
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="card-body p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-base-content/60">
              Entraînement du jour
            </p>

            <h2 className="mt-2 text-xl font-bold text-base-content">
              {session.title}
            </h2>
          </div>

          <StatusBadge
            status={session.status}
          />
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <Metric
            icon={
              <Clock3 className="h-4 w-4" />
            }
            label="Durée"
            value={`${session.durationMinutes} min`}
          />

          <Metric
            icon={
              <Gauge className="h-4 w-4" />
            }
            label="Intensité"
            value={
              `${session.intensity} · ${
                session.heartRateZone ?? '—'
              }`
            }
          />
        </div>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-base-content/50">
            {session.distanceKm !== undefined
              ? `${session.distanceKm} km prévus`
              : 'Séance prévue'}
          </span>

          <span className="text-sm font-medium text-primary">
            Voir la séance →
          </span>
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
      <span className="badge badge-success">
        Réalisée
      </span>
    )
  }

  if (status === 'skipped') {
    return (
      <span className="badge badge-error">
        Non réalisée
      </span>
    )
  }

  return (
    <span className="badge badge-warning">
      À faire
    </span>
  )
}


interface MetricProps {
  icon: React.ReactNode
  label: string
  value: string
}


function Metric({
  icon,
  label,
  value,
}: MetricProps) {
  return (
    <div className="rounded-xl bg-base-200 p-3">
      <div className="flex items-center gap-2 text-base-content/50">
        {icon}

        <span className="text-xs">
          {label}
        </span>
      </div>

      <p className="mt-1 font-semibold text-base-content">
        {value}
      </p>
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