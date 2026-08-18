import {
  Activity,
  Check,
  Clock3,
  Gauge,
  Link2,
  MapPin,
  Mountain,
  Star,
  Unlink,
  X,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

import {
  fetchTrainingSessionActivityCandidates,
  type TrainingActivityCandidate,
} from '../../core/training/api'

import type { TrainingSession } from './types'


interface TrainingDetailsProps {
  session: TrainingSession

  onStatusChange: (
    status: TrainingSession['status'],
  ) => Promise<void>

  onActivityChange: (
    activityId: string | null,
  ) => Promise<void>
}


export function TrainingDetails({
  session,
  onStatusChange,
  onActivityChange,
}: TrainingDetailsProps) {
  const [activities, setActivities] =
    useState<TrainingActivityCandidate[]>([])

  const [loadingActivities, setLoadingActivities] =
    useState(true)

  const [activityError, setActivityError] =
    useState<string | null>(null)

  const [savingActivityId, setSavingActivityId] =
    useState<string | null>(null)

  const [savingStatus, setSavingStatus] =
    useState(false)


  useEffect(() => {
    let mounted = true

    setLoadingActivities(true)
    setActivityError(null)

    fetchTrainingSessionActivityCandidates(
      session.id,
    )
      .then((result) => {
        if (!mounted) {
          return
        }

        setActivities(result)
      })
      .catch((reason: unknown) => {
        if (!mounted) {
          return
        }

        setActivityError(
          reason instanceof Error
            ? reason.message
            : 'Impossible de rechercher les activités.',
        )
      })
      .finally(() => {
        if (mounted) {
          setLoadingActivities(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [session.id])


  async function handleActivityChange(
    activityId: string,
  ) {
    setActivityError(null)

    const nextActivityId =
      session.activityId === activityId
        ? null
        : activityId

    setSavingActivityId(activityId)

    try {
      await onActivityChange(
        nextActivityId,
      )
    } catch (reason) {
      setActivityError(
        reason instanceof Error
          ? reason.message
          : "Impossible d'associer l'activité.",
      )
    } finally {
      setSavingActivityId(null)
    }
  }


  async function handleStatusChange(
    status: TrainingSession['status'],
  ) {
    setSavingStatus(true)

    try {
      await onStatusChange(status)
    } finally {
      setSavingStatus(false)
    }
  }


  return (
    <div className="space-y-6">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="badge badge-primary">
            {formatDate(session.date)}
          </span>

          <StatusBadge
            status={session.status}
          />
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
            session.heartRateZone ??
            'Non définie'
          }
        />
      </div>


      {session.type !== 'rest' && (
        <div className="border-t border-base-300 pt-5">
          <div className="mb-4">
            <h3 className="font-semibold text-base-content">
              Activité réalisée
            </h3>

            <p className="mt-1 text-sm text-base-content/60">
              OpenCoach recherche les activités enregistrées
              le même jour que cette séance.
            </p>
          </div>


          {loadingActivities && (
            <div className="flex items-center gap-3 rounded-xl bg-base-200 p-4">
              <span className="loading loading-spinner loading-sm" />

              <span className="text-sm text-base-content/60">
                Recherche des activités…
              </span>
            </div>
          )}


          {!loadingActivities &&
            activityError && (
              <div className="alert alert-error">
                <span>
                  {activityError}
                </span>
              </div>
            )}


          {!loadingActivities &&
            !activityError &&
            activities.length === 0 && (
              <div className="rounded-xl bg-base-200 p-4">
                <p className="font-medium text-base-content">
                  Aucune activité détectée
                </p>

                <p className="mt-1 text-sm text-base-content/50">
                  Aucune activité Intervals.icu n&apos;a été
                  trouvée pour cette journée.
                </p>
              </div>
            )}


          {!loadingActivities &&
            activities.length > 0 && (
              <div className="space-y-3">
                {activities.map((activity) => {
                  const selected =
                    session.activityId ===
                    activity.id

                  const saving =
                    savingActivityId ===
                    activity.id

                  return (
                    <button
                      key={activity.id}
                      type="button"
                      disabled={
                        savingActivityId !== null
                      }
                      onClick={() =>
                        void handleActivityChange(
                          activity.id,
                        )
                      }
                      className={[
                        'w-full rounded-xl border p-4 text-left transition',
                        selected
                          ? 'border-primary bg-primary/5 ring-1 ring-primary/20'
                          : 'border-base-300 bg-base-100 hover:bg-base-200',
                      ].join(' ')}
                    >
                      <div className="flex gap-3">
                        <div className="pt-1">
                          <input
                            type="checkbox"
                            checked={selected}
                            readOnly
                            className="checkbox checkbox-primary checkbox-sm"
                          />
                        </div>

                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-start justify-between gap-3">
                            <div>
                              <p className="font-semibold text-base-content">
                                {activity.name}
                              </p>

                              <p className="mt-1 text-xs text-base-content/50">
                                {formatSportType(
                                  activity.sportType,
                                )}

                                {activity.startAtLocal
                                  ? ` · ${formatActivityTime(
                                      activity.startAtLocal,
                                    )}`
                                  : ''}
                              </p>
                            </div>

                            <div className="flex flex-wrap items-center gap-2">
                              {activity.bestMatch && (
                                <span className="badge badge-success badge-sm">
                                  Meilleure correspondance
                                </span>
                              )}

                              <span
                                className={[
                                  'badge badge-sm',
                                  getMatchBadgeClass(
                                    activity.matchScore,
                                  ),
                                ].join(' ')}
                              >
                                {Math.round(
                                  activity.matchScore,
                                )}{' '}
                                %
                              </span>

                              {selected && (
                                <span className="badge badge-primary gap-1">
                                  <Link2 className="h-3 w-3" />
                                  Associée
                                </span>
                              )}
                            </div>
                          </div>


                          <div className="mt-3 flex flex-wrap gap-x-4 gap-y-2 text-sm text-base-content/60">
                            {activity.distanceM !== undefined && (
                              <span>
                                {formatDistance(
                                  activity.distanceM,
                                )}
                              </span>
                            )}

                            {activity.movingTimeSeconds !== undefined && (
                              <span>
                                {formatDuration(
                                  activity.movingTimeSeconds,
                                )}
                              </span>
                            )}

                            {activity.elevationGainM !== undefined && (
                              <span>
                                {Math.round(
                                  activity.elevationGainM,
                                )}{' '}
                                m D+
                              </span>
                            )}
                          </div>


                          <div className="mt-4 rounded-lg bg-base-200 p-3">
                            <p className="text-xs font-semibold uppercase tracking-wide text-base-content/50">
                              Correspondance avec la séance
                            </p>

                            <div className="mt-3 space-y-2">
                              <MatchCriterion
                                label="Sport"
                                planned={formatSportType(
                                  session.sportType,
                                )}
                                actual={formatSportType(
                                  activity.sportType,
                                )}
                                score={activity.sportScore}
                                maxScore={40}
                              />

                              {activity.distanceScore !== undefined && (
                                <MatchCriterion
                                  label="Distance"
                                  planned={
                                    session.distanceKm !== undefined
                                      ? `${session.distanceKm.toFixed(
                                          1,
                                        )} km`
                                      : '—'
                                  }
                                  actual={
                                    activity.distanceM !== undefined
                                      ? formatDistance(
                                          activity.distanceM,
                                        )
                                      : '—'
                                  }
                                  score={
                                    activity.distanceScore
                                  }
                                  maxScore={25}
                                />
                              )}

                              {activity.durationScore !== undefined && (
                                <MatchCriterion
                                  label="Durée"
                                  planned={`${session.durationMinutes} min`}
                                  actual={
                                    activity.movingTimeSeconds !== undefined
                                      ? formatDuration(
                                          activity.movingTimeSeconds,
                                        )
                                      : '—'
                                  }
                                  score={
                                    activity.durationScore
                                  }
                                  maxScore={25}
                                />
                              )}

                              {activity.elevationScore !== undefined && (
                                <MatchCriterion
                                  label="Dénivelé"
                                  planned={
                                    session.elevationGainM !== undefined
                                      ? `${Math.round(
                                          session.elevationGainM,
                                        )} m`
                                      : '—'
                                  }
                                  actual={
                                    activity.elevationGainM !== undefined
                                      ? `${Math.round(
                                          activity.elevationGainM,
                                        )} m`
                                      : '—'
                                  }
                                  score={
                                    activity.elevationScore
                                  }
                                  maxScore={10}
                                />
                              )}
                            </div>
                          </div>


                          {activity.feel !== undefined && (
                            <div className="mt-4 flex flex-wrap items-center gap-3">
                              <span className="text-sm text-base-content/60">
                                Ressenti Intervals.icu
                              </span>

                              <FeelStars
                                feel={activity.feel}
                              />

                              <span className="text-xs text-base-content/50">
                                {formatFeelLabel(
                                  activity.feel,
                                )}
                              </span>
                            </div>
                          )}


                          {saving && (
                            <div className="mt-3 flex items-center gap-2 text-sm text-primary">
                              <span className="loading loading-spinner loading-xs" />

                              Enregistrement…
                            </div>
                          )}


                          {selected && !saving && (
                            <div className="mt-3 flex items-center gap-2 text-xs text-base-content/50">
                              <Unlink className="h-3.5 w-3.5" />

                              Cliquez à nouveau pour désassocier.
                            </div>
                          )}
                        </div>
                      </div>
                    </button>
                  )
                })}
              </div>
            )}
        </div>
      )}


      <div className="border-t border-base-300 pt-5">
        <p className="mb-3 text-sm font-semibold text-base-content">
          Statut de la séance
        </p>

        <div className="flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            disabled={savingStatus}
            onClick={() =>
              void handleStatusChange(
                'completed',
              )
            }
            className={[
              'btn flex-1',
              session.status === 'completed'
                ? 'btn-success'
                : 'btn-success btn-outline',
            ].join(' ')}
          >
            {savingStatus ? (
              <span className="loading loading-spinner loading-sm" />
            ) : (
              <Check className="h-4 w-4" />
            )}

            Réalisée
          </button>


          <button
            type="button"
            disabled={savingStatus}
            onClick={() =>
              void handleStatusChange(
                'skipped',
              )
            }
            className={[
              'btn flex-1',
              session.status === 'skipped'
                ? 'btn-error'
                : 'btn-error btn-outline',
            ].join(' ')}
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
  icon: React.ComponentType<{
    className?: string
  }>
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


function MatchCriterion({
  label,
  planned,
  actual,
  score,
  maxScore,
}: {
  label: string
  planned: string
  actual: string
  score: number
  maxScore: number
}) {
  const percentage =
    maxScore > 0
      ? Math.round(
          (score / maxScore) * 100,
        )
      : 0

  return (
    <div className="flex items-center justify-between gap-4 text-sm">
      <div className="min-w-0">
        <span className="font-medium text-base-content">
          {label}
        </span>

        <span className="ml-2 text-xs text-base-content/50">
          {actual} / {planned}
        </span>
      </div>

      <span
        className={[
          'badge badge-sm',
          getMatchBadgeClass(
            percentage,
          ),
        ].join(' ')}
      >
        {percentage} %
      </span>
    </div>
  )
}


function FeelStars({
  feel,
}: {
  feel: number
}) {
  const normalizedFeel =
    Math.min(
      5,
      Math.max(
        1,
        Math.round(feel),
      ),
    )

  /*
   * Intervals.icu :
   * 1 = meilleur ressenti
   * 5 = plus mauvais ressenti.
   *
   * Pour l'affichage en étoiles,
   * on inverse uniquement la représentation.
   */
  const stars =
    6 - normalizedFeel

  return (
    <div
      className="flex items-center gap-0.5"
      aria-label={`${stars} étoiles sur 5`}
    >
      {Array.from(
        { length: 5 },
        (_, index) => (
          <Star
            key={index}
            className={[
              'h-4 w-4',
              index < stars
                ? 'fill-current text-warning'
                : 'text-base-content/20',
            ].join(' ')}
          />
        ),
      )}
    </div>
  )
}


function getMatchBadgeClass(
  score: number,
): string {
  if (score >= 85) {
    return 'badge-success'
  }

  if (score >= 65) {
    return 'badge-warning'
  }

  return 'badge-error'
}


function formatFeelLabel(
  feel: number,
): string {
  switch (Math.round(feel)) {
    case 1:
      return 'Excellent'

    case 2:
      return 'Bon'

    case 3:
      return 'Moyen'

    case 4:
      return 'Difficile'

    case 5:
      return 'Très difficile'

    default:
      return 'Non défini'
  }
}


function formatDistance(
  distanceM: number,
): string {
  return `${(
    distanceM / 1000
  ).toFixed(2)} km`
}


function formatDuration(
  seconds: number,
): string {
  const totalMinutes =
    Math.round(
      seconds / 60,
    )

  const hours =
    Math.floor(
      totalMinutes / 60,
    )

  const minutes =
    totalMinutes % 60

  if (hours === 0) {
    return `${minutes} min`
  }

  if (minutes === 0) {
    return `${hours} h`
  }

  return `${hours} h ${minutes} min`
}


function formatActivityTime(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(
    new Date(dateString),
  )
}


function formatSportType(
  sportType: string,
): string {
  const sportLabels: Record<
    string,
    string
  > = {
    Run: 'Course à pied',
    TrailRun: 'Trail',
    Ride: 'Cyclisme',
    VirtualRide: 'Cyclisme virtuel',
    Walk: 'Marche',
    Hike: 'Randonnée',
    Swim: 'Natation',
  }

  return (
    sportLabels[sportType] ??
    sportType
  )
}


function formatDate(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  ).format(
    new Date(
      `${dateString}T12:00:00`,
    ),
  )
}