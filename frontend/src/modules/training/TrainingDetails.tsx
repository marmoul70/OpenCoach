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

import type {
  TrainingSession,
} from './types'
import {
  formatTrainingIntensity,
} from './intensity'

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
  const [
    activities,
    setActivities,
  ] = useState<
    TrainingActivityCandidate[]
  >([])

  const [
    loadingActivities,
    setLoadingActivities,
  ] = useState(true)

  const [
    activityError,
    setActivityError,
  ] = useState<string | null>(
    null,
  )

  const [
    savingActivityId,
    setSavingActivityId,
  ] = useState<string | null>(
    null,
  )

  const [
    savingStatus,
    setSavingStatus,
  ] = useState(false)


  useEffect(() => {
    if (
      session.type === 'rest'
    ) {
      setLoadingActivities(false)
      setActivities([])
      return
    }

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
          setLoadingActivities(
            false,
          )
        }
      })

    return () => {
      mounted = false
    }
  }, [
    session.id,
    session.type,
  ])


  async function handleActivityChange(
    activityId: string,
  ) {
    setActivityError(null)

    const nextActivityId =
      session.activityId
      === activityId
        ? null
        : activityId

    setSavingActivityId(
      activityId,
    )

    try {
      await onActivityChange(
        nextActivityId,
      )
    } catch (reason) {
      setActivityError(
        reason instanceof Error
          ? reason.message
          : (
              "Impossible d'associer "
              + "l'activité."
            ),
      )
    } finally {
      setSavingActivityId(
        null,
      )
    }
  }


  async function handleStatusChange(
    status:
      TrainingSession['status'],
  ) {
    setSavingStatus(true)

    try {
      await onStatusChange(
        status,
      )
    } finally {
      setSavingStatus(false)
    }
  }


  return (
    <div className="space-y-5">
      <SessionHeader
        session={session}
      />

      {session.description && (
        <p
          className="
            text-sm
            leading-relaxed
            text-base-content/60
          "
        >
          {session.description}
        </p>
      )}

      <SessionSummary
        session={session}
      />

      {session.type
        !== 'rest' && (
          <ActivitySection
            session={session}
            activities={
              activities
            }
            loading={
              loadingActivities
            }
            error={
              activityError
            }
            savingActivityId={
              savingActivityId
            }
            onActivityChange={
              handleActivityChange
            }
          />
        )}

      <StatusSection
        session={session}
        saving={
          savingStatus
        }
        onChange={
          handleStatusChange
        }
      />
    </div>
  )
}


function SessionHeader({
  session,
}: {
  session: TrainingSession
}) {
  return (
    <div
      className="
        flex flex-col
        gap-3
        sm:flex-row
        sm:items-start
        sm:justify-between
      "
    >
      <div className="min-w-0">
        <div
          className="
            flex flex-wrap
            items-center
            gap-2
          "
        >
          <span className="text-sm font-medium text-base-content/55">
            {formatDate(
              session.date,
            )}
          </span>

          {session.type
            === 'supplementary' && (
              <span className="badge badge-outline badge-sm">
                Supplémentaire
              </span>
            )}
        </div>

        <h2
          className="
            mt-1
            text-xl
            font-bold
            text-base-content
          "
        >
          {session.title}
        </h2>

        <p
          className="
            mt-1 text-sm
            text-base-content/50
          "
        >
          {formatSportType(
            session.sportType,
          )}
        </p>
      </div>

      <StatusBadge
        status={
          session.status
        }
      />
    </div>
  )
}


function SessionSummary({
  session,
}: {
  session: TrainingSession
}) {
  return (
    <div
      className="
        overflow-hidden
        rounded-xl
        border border-base-300
      "
    >
      <div
        className="
          grid
          divide-y divide-base-300
          sm:grid-cols-2
          sm:divide-x
          sm:divide-y-0
          lg:grid-cols-5
        "
      >
        <SummaryValue
          icon={Clock3}
          label="Durée"
          value={
            session.type
            === 'rest'
              ? 'Repos'
              : (
                `${session.durationMinutes} min`
              )
          }
        />

        <SummaryValue
          icon={MapPin}
          label="Distance"
          value={
            session.distanceKm
            !== undefined
              ? (
                `${formatNumber(
                  session.distanceKm,
                )} km`
              )
              : '—'
          }
        />

        <SummaryValue
          icon={Mountain}
          label="Dénivelé"
          value={
            session.elevationGainM
            !== undefined
              ? (
                `${Math.round(
                  session.elevationGainM,
                )} m`
              )
              : '—'
          }
        />

        <SummaryValue
          icon={Gauge}
          label="Intensité"
          value={
            formatTrainingIntensity(
              session.intensity,
            )
            || '—'
          }
        />

        <SummaryValue
          icon={Activity}
          label="Zone"
          value={
            session.heartRateZone
            ?? '—'
          }
        />
      </div>
    </div>
  )
}


interface SummaryValueProps {
  icon:
    typeof Clock3
  label: string
  value: string
}


function SummaryValue({
  icon: Icon,
  label,
  value,
}: SummaryValueProps) {
  return (
    <div
      className="
        flex items-center
        gap-3 px-3 py-3
      "
    >
      <Icon
        size={16}
        className="
          shrink-0
          text-base-content/40
        "
      />

      <div className="min-w-0">
        <p
          className="
            text-[11px]
            uppercase
            tracking-wide
            text-base-content/40
          "
        >
          {label}
        </p>

        <p
          className="
            truncate
            text-sm
            font-semibold
            text-base-content
          "
        >
          {value}
        </p>
      </div>
    </div>
  )
}


interface ActivitySectionProps {
  session:
    TrainingSession

  activities:
    TrainingActivityCandidate[]

  loading: boolean

  error:
    string | null

  savingActivityId:
    string | null

  onActivityChange: (
    activityId: string,
  ) => Promise<void>
}


function ActivitySection({
  session,
  activities,
  loading,
  error,
  savingActivityId,
  onActivityChange,
}: ActivitySectionProps) {
  return (
    <section
      className="
        border-t
        border-base-300
        pt-5
      "
    >
      <div
        className="
          flex flex-col
          gap-2
          sm:flex-row
          sm:items-end
          sm:justify-between
        "
      >
        <div>
          <h3
            className="
              font-semibold
              text-base-content
            "
          >
            Activité réalisée
          </h3>

          <p
            className="
              mt-1 text-sm
              text-base-content/50
            "
          >
            Activités Intervals.icu
            détectées le même jour.
          </p>
        </div>

        {session.activityId && (
          <span
            className="
              badge
              badge-success
              badge-sm
              gap-1
            "
          >
            <Link2
              size={12}
            />

            Associée
          </span>
        )}
      </div>


      {loading && (
        <div
          className="
            mt-4
            flex items-center
            gap-2
            rounded-xl
            bg-base-200/60
            px-4 py-3
          "
        >
          <span
            className="
              loading
              loading-spinner
              loading-sm
            "
          />

          <span
            className="
              text-sm
              text-base-content/55
            "
          >
            Recherche des activités…
          </span>
        </div>
      )}


      {!loading
        && error && (
          <div
            className="
              mt-4
              rounded-xl
              border
              border-error/30
              bg-error/5
              px-4 py-3
              text-sm
              text-error
            "
          >
            {error}
          </div>
        )}


      {!loading
        && !error
        && activities.length
        === 0 && (
          <div
            className="
              mt-4
              rounded-xl
              bg-base-200/60
              px-4 py-3
            "
          >
            <p
              className="
                text-sm
                font-medium
                text-base-content/70
              "
            >
              Aucune activité détectée
            </p>

            <p
              className="
                mt-1 text-xs
                text-base-content/45
              "
            >
              Synchronisez Intervals.icu
              si votre activité vient
              d&apos;être enregistrée.
            </p>
          </div>
        )}


      {!loading
        && !error
        && activities.length
        > 0 && (
          <div className="mt-4 space-y-2">
            {activities.map(
              (activity) => (
                <ActivityRow
                  key={
                    activity.id
                  }
                  session={
                    session
                  }
                  activity={
                    activity
                  }
                  saving={
                    savingActivityId
                    === activity.id
                  }
                  disabled={
                    savingActivityId
                    !== null
                  }
                  onClick={() =>
                    void onActivityChange(
                      activity.id,
                    )
                  }
                />
              ),
            )}
          </div>
        )}
    </section>
  )
}


interface ActivityRowProps {
  session:
    TrainingSession

  activity:
    TrainingActivityCandidate

  saving: boolean
  disabled: boolean

  onClick: () => void
}


function ActivityRow({
  session,
  activity,
  saving,
  disabled,
  onClick,
}: ActivityRowProps) {
  const selected =
    session.activityId
    === activity.id

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={[
        (
          'w-full rounded-xl '
          + 'border px-4 py-3 '
          + 'text-left transition'
        ),
        selected
          ? (
            'border-primary '
            + 'bg-primary/5 '
            + 'ring-1 '
            + 'ring-primary/15'
          )
          : (
            'border-base-300 '
            + 'hover:bg-base-200/50'
          ),
      ].join(' ')}
    >
      <div
        className="
          flex flex-col
          gap-3
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div className="min-w-0">
          <div
            className="
              flex flex-wrap
              items-center
              gap-2
            "
          >
            <p
              className="
                truncate
                font-semibold
                text-base-content
              "
            >
              {activity.name}
            </p>

            {activity.bestMatch && (
              <span
                className="
                  badge
                  badge-success
                  badge-sm
                "
              >
                Meilleur choix
              </span>
            )}
          </div>

          <p
            className="
              mt-1 text-xs
              text-base-content/50
            "
          >
            {formatSportType(
              activity.sportType,
            )}

            {activity.startAtLocal
              ? (
                ` · ${formatActivityTime(
                  activity.startAtLocal,
                )}`
              )
              : ''}
          </p>
        </div>


        <div
          className="
            flex flex-wrap
            items-center
            gap-3
            text-sm
            text-base-content/60
          "
        >
          {activity.movingTimeSeconds
            !== undefined && (
              <span>
                {formatDuration(
                  activity
                    .movingTimeSeconds,
                )}
              </span>
            )}

          {activity.distanceM
            !== undefined && (
              <span>
                {formatDistance(
                  activity.distanceM,
                )}
              </span>
            )}

          {activity.elevationGainM
            !== undefined && (
              <span>
                {Math.round(
                  activity
                    .elevationGainM,
                )}{' '}
                m D+
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

          {saving ? (
            <span
              className="
                loading
                loading-spinner
                loading-sm
              "
            />
          ) : selected ? (
            <Unlink
              size={15}
              className="
                text-primary
              "
            />
          ) : (
            <Link2
              size={15}
              className="
                text-base-content/40
              "
            />
          )}
        </div>
      </div>


      {selected && (
        <div
          className="
            mt-3
            border-t
            border-primary/15
            pt-3
          "
        >
          <p
            className="
              text-xs
              text-base-content/50
            "
          >
            Cliquez à nouveau pour
            désassocier cette activité.
          </p>
        </div>
      )}


      {activity.feel
        !== undefined && (
          <div
            className="
              mt-2
              flex items-center
              gap-2
            "
          >
            <FeelStars
              feel={
                activity.feel
              }
            />

            <span
              className="
                text-xs
                text-base-content/45
              "
            >
              {formatFeelLabel(
                activity.feel,
              )}
            </span>
          </div>
        )}
    </button>
  )
}


interface StatusSectionProps {
  session:
    TrainingSession

  saving: boolean

  onChange: (
    status:
      TrainingSession['status'],
  ) => Promise<void>
}


function StatusSection({
  session,
  saving,
  onChange,
}: StatusSectionProps) {
  return (
    <section
      className="
        border-t
        border-base-300
        pt-5
      "
    >
      <div
        className="
          flex flex-col
          gap-3
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div>
          <h3
            className="
              font-semibold
              text-base-content
            "
          >
            Statut
          </h3>

          <p
            className="
              mt-1 text-sm
              text-base-content/50
            "
          >
            Indiquez si la séance
            a été réalisée.
          </p>
        </div>

        <div
          className="
            flex flex-wrap
            gap-2
          "
        >
          <button
            type="button"
            disabled={saving}
            onClick={() =>
              void onChange(
                'completed',
              )
            }
            className={[
              'btn btn-sm',
              session.status
              === 'completed'
                ? 'btn-success'
                : (
                  'btn-success '
                  + 'btn-outline'
                ),
            ].join(' ')}
          >
            {saving ? (
              <span
                className="
                  loading
                  loading-spinner
                  loading-xs
                "
              />
            ) : (
              <Check
                size={14}
              />
            )}

            Réalisée
          </button>

          <button
            type="button"
            disabled={saving}
            onClick={() =>
              void onChange(
                'skipped',
              )
            }
            className={[
              'btn btn-sm',
              session.status
              === 'skipped'
                ? 'btn-error'
                : (
                  'btn-error '
                  + 'btn-outline'
                ),
            ].join(' ')}
          >
            <X
              size={14}
            />

            Non réalisée
          </button>
        </div>
      </div>
    </section>
  )
}


function StatusBadge({
  status,
}: {
  status:
    TrainingSession['status']
}) {
  if (
    status === 'completed'
  ) {
    return (
      <span
        className="
          badge
          badge-success
          badge-sm
          gap-1
        "
      >
        <Check
          size={12}
        />

        Réalisée
      </span>
    )
  }

  if (
    status === 'skipped'
  ) {
    return (
      <span
        className="
          badge
          badge-error
          badge-sm
          gap-1
        "
      >
        <X
          size={12}
        />

        Non réalisée
      </span>
    )
  }

  return (
    <span
      className="
        badge
        badge-warning
        badge-sm
      "
    >
      À faire
    </span>
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
        Math.round(
          feel,
        ),
      ),
    )

  const stars =
    6 - normalizedFeel

  return (
    <div
      className="
        flex items-center
        gap-0.5
      "
      aria-label={
        `${stars} étoiles sur 5`
      }
    >
      {Array.from(
        {
          length: 5,
        },
        (
          _,
          index,
        ) => (
          <Star
            key={index}
            className={[
              'h-3.5 w-3.5',
              index < stars
                ? (
                  'fill-current '
                  + 'text-warning'
                )
                : (
                  'text-base-content/20'
                ),
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
  switch (
    Math.round(
      feel,
    )
  ) {
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
  return (
    `${
      (
        distanceM / 1000
      ).toFixed(2)
    } km`
  )
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

  return (
    `${hours} h ${minutes} min`
  )
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
    new Date(
      dateString,
    ),
  )
}


function formatSportType(
  sportType: string,
): string {
  const labels:
    Record<string, string> = {
      Run:
        'Course à pied',
      TrailRun:
        'Trail',
      Ride:
        'Cyclisme',
      VirtualRide:
        'Cyclisme virtuel',
      Walk:
        'Marche',
      Hike:
        'Randonnée',
      Swim:
        'Natation',
      StrengthTraining:
        'Renforcement',
      WeightTraining:
        'Renforcement',
      Other:
        'Autre',
    }

  return (
    labels[sportType]
    ?? sportType
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


function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    'fr-FR',
    {
      maximumFractionDigits: 1,
    },
  ).format(
    value,
  )
}