import { Clock3, Gauge } from 'lucide-react'

import { trainingSession } from './data'

interface TrainingWidgetProps {
  onClick: () => void
}

export function TrainingWidget({
  onClick,
}: TrainingWidgetProps) {
  const session = trainingSession

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

          <span className="badge badge-warning">
            À faire
          </span>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <Metric
            icon={<Clock3 className="h-4 w-4" />}
            label="Durée"
            value={`${session.durationMinutes} min`}
          />

          <Metric
            icon={<Gauge className="h-4 w-4" />}
            label="Intensité"
            value={`${session.intensity} · ${session.heartRateZone ?? '—'}`}
          />
        </div>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-base-content/50">
            {session.distanceKm
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
