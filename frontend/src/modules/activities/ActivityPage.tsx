import { useEffect, useState } from 'react'

import {
  fetchActivities,
  type ActivitySummary,
} from '../../core/activities'


export function ActivityPage() {
  const [activities, setActivities] = useState<ActivitySummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    fetchActivities()
      .then((data) => {
        if (mounted) {
          setActivities(data)
        }
      })
      .catch((reason: unknown) => {
        if (!mounted) {
          return
        }

        setError(
          reason instanceof Error
            ? reason.message
            : 'Impossible de charger les activités.',
        )
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  return (
    <main className="min-h-screen bg-base-200">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:py-8">
        <header className="mb-6">
          <h1 className="text-3xl font-bold tracking-tight text-base-content">
            Activités
          </h1>

          <p className="mt-1 text-sm text-base-content/60">
            Historique des activités synchronisées.
          </p>
        </header>

        <div className="card border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body p-0">
            {loading && (
              <div className="flex justify-center py-12">
                <span className="loading loading-spinner loading-md" />
              </div>
            )}

            {!loading && error && (
              <div className="alert alert-error m-4">
                {error}
              </div>
            )}

            {!loading && !error && activities.length === 0 && (
              <div className="py-12 text-center text-sm text-base-content/60">
                Aucune activité disponible.
              </div>
            )}

            {!loading && !error && activities.length > 0 && (
              <div className="overflow-x-auto">
                <table className="table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Activité</th>
                      <th className="text-right">Distance</th>
                      <th className="text-right">Durée</th>
                      <th className="text-right">Allure</th>
                      <th className="text-right">D+</th>
                    </tr>
                  </thead>

                  <tbody>
                    {activities.map((activity) => (
                      <tr key={`${activity.provider}-${activity.provider_activity_id}`}>
                        <td className="whitespace-nowrap">
                          {formatDate(
                            activity.start_at_local ?? activity.start_at,
                          )}
                        </td>

                        <td>
                          <div className="font-medium">
                            {activity.name}
                          </div>

                          <div className="text-xs text-base-content/50">
                            {formatSportType(activity.sport_type)}
                          </div>
                        </td>

                        <td className="text-right">
                          {formatDistance(activity.distance_m)}
                        </td>

                        <td className="text-right">
                          {formatDuration(
                            activity.moving_time_seconds
                              ?? activity.elapsed_time_seconds,
                          )}
                        </td>

                        <td className="text-right">
                          {formatPace(
                            activity.distance_m,
                            activity.moving_time_seconds,
                          )}
                        </td>

                        <td className="text-right">
                          {formatElevation(activity.elevation_gain_m)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}


function formatDate(value: string): string {
  const date = new Date(value)

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    },
  ).format(date)
}


function formatDistance(
  distanceM: number | null | undefined,
): string {
  if (distanceM == null) {
    return '—'
  }

  return `${(distanceM / 1000).toLocaleString(
    'fr-FR',
    {
      minimumFractionDigits: 1,
      maximumFractionDigits: 2,
    },
  )} km`
}


function formatDuration(
  seconds: number | null | undefined,
): string {
  if (seconds == null) {
    return '—'
  }

  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60

  if (hours > 0) {
    return `${hours}:${minutes
      .toString()
      .padStart(2, '0')}:${remainingSeconds
      .toString()
      .padStart(2, '0')}`
  }

  return `${minutes}:${remainingSeconds
    .toString()
    .padStart(2, '0')}`
}


function formatPace(
  distanceM: number | null | undefined,
  movingTimeSeconds: number | null | undefined,
): string {
  if (
    distanceM == null
    || movingTimeSeconds == null
    || distanceM <= 0
  ) {
    return '—'
  }

  const paceSecondsPerKm =
    movingTimeSeconds / (distanceM / 1000)

  const minutes = Math.floor(paceSecondsPerKm / 60)
  const seconds = Math.round(paceSecondsPerKm % 60)

  return `${minutes}:${seconds
    .toString()
    .padStart(2, '0')}/km`
}


function formatElevation(
  elevationM: number | null | undefined,
): string {
  if (elevationM == null) {
    return '—'
  }

  return `${Math.round(elevationM)} m`
}


function formatSportType(
  sportType: string,
): string {
  const labels: Record<string, string> = {
    Run: 'Course à pied',
    Walk: 'Marche',
    Swim: 'Natation',
    Soccer: 'Football',
    Workout: 'Entraînement',
    VirtualRide: 'Vélo virtuel',
  }

  return labels[sportType] ?? sportType
}
