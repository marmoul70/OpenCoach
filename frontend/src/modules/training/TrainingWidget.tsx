import {
  CalendarDays,
} from 'lucide-react'

import {
  useTrainingSessions,
} from './trainingStore'

import type {
  TrainingSession,
} from './types'


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

  const todaySessions =
    sessions.filter(
      (item) =>
        item.date === today
        && item.type !== 'supplementary',
    )

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
          <p className="text-xs font-medium uppercase tracking-wide text-error">
            Entraînement du jour
          </p>

          <p className="mt-1 font-semibold text-error">
            Indisponible
          </p>

          <p className="mt-2 text-sm text-base-content/60">
            {error}
          </p>
        </div>
      </div>
    )
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="
        card w-full
        border border-base-300
        bg-base-100
        text-left
        shadow-sm
        transition-all
        duration-200
        hover:-translate-y-0.5
        hover:shadow-md
      "
    >
      <div className="card-body gap-3 p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
              Entraînement du jour
            </p>

            {todaySessions.length > 0 && (
              <p className="mt-1 text-sm text-base-content/50">
                {todaySessions.length}{' '}
                séance
                {todaySessions.length > 1
                  ? 's'
                  : ''}
              </p>
            )}
          </div>

          <CalendarDays className="h-4 w-4 text-base-content/40" />
        </div>

        {todaySessions.length > 0 ? (
          <div className="divide-y divide-base-300">
            {todaySessions.map(
              (
                session,
                index,
              ) => (
                <div
                  key={
                    session.id
                    ?? `${session.date}-${index}`
                  }
                  className="flex items-center gap-3 py-2.5 first:pt-0 last:pb-0"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-semibold">
                      {formatActivityType(
                        session.sportType,
                        session.type,
                      )}
                    </p>

                    <p className="mt-0.5 truncate text-xs text-base-content/50">
                      {session.title}
                    </p>
                  </div>

                  <span className="shrink-0 text-sm font-semibold">
                    {session.durationMinutes} min
                  </span>

                  <StatusBadge
                    status={
                      session.status
                    }
                  />
                </div>
              ),
            )}
          </div>
        ) : (
          <p className="py-2 font-semibold">
            Repos
          </p>
        )}
      </div>
    </button>
  )
}


function StatusBadge({
  status,
}: {
  status:
    TrainingSession['status']
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


function formatActivityType(
  sportType: string,
  type: string,
): string {
  const value =
    sportType.toLowerCase()

  const labels:
    Record<string, string> = {
      run: 'Course',
      running: 'Course',
      trailrunning: 'Trail',
      trail_running: 'Trail',
      strength: 'Renforcement',
      strength_training: 'Renforcement',
      bike: 'Vélo',
      cycling: 'Vélo',
      walking: 'Marche',
      hiking: 'Randonnée',
      swimming: 'Natation',
    }

  return labels[value]
    ?? sportType
    ?? type
}


function formatLocalDate(
  date: Date,
): string {
  const year =
    date.getFullYear()

  const month =
    String(
      date.getMonth()
      + 1,
    ).padStart(
      2,
      '0',
    )

  const day =
    String(
      date.getDate(),
    ).padStart(
      2,
      '0',
    )

  return (
    `${year}-${month}-${day}`
  )
}
