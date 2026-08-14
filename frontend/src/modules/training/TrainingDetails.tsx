import {
  Activity,
  Check,
  Clock3,
  Gauge,
  MapPin,
  Mountain,
  X,
} from 'lucide-react'

import type { TrainingSession } from './types'

interface TrainingDetailsProps {
  session: TrainingSession
  onStatusChange: (
    status: TrainingSession['status'],
  ) => void
}

export function TrainingDetails({
  session,
  onStatusChange,
}: TrainingDetailsProps) {
  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge badge-primary">
            {formatDate(session.date)}
          </span>

          <StatusBadge status={session.status} />
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
            session.distanceKm !== undefined
              ? `${session.distanceKm} km`
              : 'Non définie'
          }
        />

        <Metric
          icon={Mountain}
          label="Dénivelé"
          value={
            session.elevationGainM !== undefined
              ? `${session.elevationGainM} m D+`
              : 'Non défini'
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
          value={
            session.heartRateZone ?? 'Non définie'
          }
        />
      </div>

      {session.type !== 'rest' && (
        <div className="alert alert-info">
          <Activity className="h-5 w-5" />

          <span>
            L’objectif est de respecter l’intensité
            prévue et de rester régulier pendant la
            séance.
          </span>
        </div>
      )}

      <div className="border-t border-base-300 pt-5">
        <p className="mb-3 text-sm font-semibold text-base-content">
          Statut de la séance
        </p>

        <div className="flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            onClick={() =>
              onStatusChange('completed')
            }
            className="btn btn-success flex-1"
          >
            <Check className="h-4 w-4" />
            Réalisée
          </button>

          <button
            type="button"
            onClick={() =>
              onStatusChange('skipped')
            }
            className="btn btn-error btn-outline flex-1"
          >
            <X className="h-4 w-4" />
            Non réalisée
          </button>
        </div>
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

function StatusBadge({
  status,
}: {
  status: TrainingSession['status']
}) {
  if (status === 'completed') {
    return (
      <span className="badge badge-success gap-1">
        <Check className="h-3.5 w-3.5" />
        Réalisée
      </span>
    )
  }

  if (status === 'skipped') {
    return (
      <span className="badge badge-error gap-1">
        <X className="h-3.5 w-3.5" />
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

function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  }).format(new Date(`${dateString}T12:00:00`))
}
