import {
  Activity,
  Clock3,
  Gauge,
  MapPin,
} from 'lucide-react'

import { trainingSession } from './data'

export function TrainingDetails() {
  const session = trainingSession

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <span className="badge badge-primary">
            Aujourd’hui
          </span>

          <span className="badge badge-warning">
            À faire
          </span>
        </div>

        <h2 className="mt-3 text-2xl font-bold text-base-content">
          {session.title}
        </h2>

        <p className="mt-2 leading-6 text-base-content/60">
          {session.description}
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Metric
          icon={Clock3}
          label="Durée"
          value={`${session.durationMinutes} minutes`}
        />

        <Metric
          icon={MapPin}
          label="Distance"
          value={
            session.distanceKm
              ? `${session.distanceKm} km`
              : 'Non définie'
          }
        />

        <Metric
          icon={Gauge}
          label="Intensité"
          value={session.intensity}
        />

        <Metric
          icon={Activity}
          label="Zone cardio"
          value={session.heartRateZone ?? 'Non définie'}
        />
      </div>

      <div className="alert alert-info">
        <Activity className="h-5 w-5" />

        <span>
          L’objectif est de rester en aisance respiratoire
          pendant toute la séance.
        </span>
      </div>
    </div>
  )
}

interface MetricProps {
  icon: React.ComponentType<{ className?: string }>
  label: string
  value: string
}

function Metric({
  icon: Icon,
  label,
  value,
}: MetricProps) {
  return (
    <div className="rounded-xl bg-base-200 p-4">
      <div className="flex items-center gap-2 text-base-content/50">
        <Icon className="h-4 w-4" />

        <span className="text-sm">
          {label}
        </span>
      </div>

      <p className="mt-2 font-semibold text-base-content">
        {value}
      </p>
    </div>
  )
}
