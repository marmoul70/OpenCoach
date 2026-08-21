import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  CalendarDays,
  Check,
  Clock3,
  Plus,
  Route,
  Trophy,
  X,
} from 'lucide-react'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  fetchTrainingStats,
} from '../../core/training/api'

import {
  races,
} from '../races/data'

import {
  AddTrainingSessionModal,
} from './AddTrainingSessionModal'

import {
  TrainingDetails,
} from './TrainingDetails'

import {
  useTrainingSessions,
} from './trainingStore'

import type {
  TrainingSession,
  TrainingStats,
} from './types'

import {
  formatTrainingIntensity,
} from './intensity'


const dayLabels = [
  'Lundi',
  'Mardi',
  'Mercredi',
  'Jeudi',
  'Vendredi',
  'Samedi',
  'Dimanche',
]


export function TrainingWeek() {
  const {
    sessions,
    updateSessionStatus,
    updateSessionActivity,
  } = useTrainingSessions()

  const [
    selectedSessionId,
    setSelectedSessionId,
  ] = useState<string | null>(
    null,
  )

  const [
    addSessionDate,
    setAddSessionDate,
  ] = useState<string | null>(
    null,
  )

  const [
    stats,
    setStats,
  ] = useState<TrainingStats | null>(
    null,
  )

  const [
    statsLoading,
    setStatsLoading,
  ] = useState(true)

  const [
    statsError,
    setStatsError,
  ] = useState<string | null>(
    null,
  )


  const loadStats = useCallback(
    async () => {
      const today = new Date()

      const start =
        `${today.getFullYear()}-01-01`

      const end =
        formatLocalDate(
          today,
        )

      setStatsLoading(true)
      setStatsError(null)

      try {
        const result =
          await fetchTrainingStats(
            start,
            end,
          )

        setStats(result)
      } catch (reason) {
        setStatsError(
          reason instanceof Error
            ? reason.message
            : (
                'Impossible de charger '
                + 'les statistiques.'
              ),
        )
      } finally {
        setStatsLoading(false)
      }
    },
    [],
  )


  useEffect(() => {
    void loadStats()
  }, [
    loadStats,
  ])


  const weekDays =
    getWeekSessions(
      sessions,
    )

  const selectedSession =
    selectedSessionId
      ? sessions.find(
          (session) =>
            session.id
            === selectedSessionId,
        )
      : undefined

  const plannedCount =
    sessions.filter(
      (session) =>
        session.status
        === 'planned'
        && session.type
        !== 'rest'
        && session.type
        !== 'supplementary',
    ).length

  const supplementaryCount =
    sessions.filter(
      (session) =>
        session.type
        === 'supplementary',
    ).length

  const restCount =
    sessions.filter(
      (session) =>
        session.type
        === 'rest',
    ).length

  const nextRace =
    getNextRace(
      races,
    )


  function openSession(
    sessionId: string,
  ) {
    setSelectedSessionId(
      sessionId,
    )
  }


  function closeSession() {
    setSelectedSessionId(
      null,
    )
  }


  function openAddSession(
    date: string,
  ) {
    setAddSessionDate(
      date,
    )
  }


  function closeAddSession() {
    setAddSessionDate(
      null,
    )
  }


  return (
    <main>
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:py-8">
        <header className="mb-6">
          <div className="flex items-start gap-4">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <CalendarDays
                size={24}
                strokeWidth={2}
              />
            </div>

            <div>
              <h1 className="text-3xl font-bold tracking-tight text-base-content">
                Entraînement
              </h1>

              <p className="mt-1 text-sm text-base-content/60">
                Votre semaine d&apos;entraînement et vos séances prévues.
              </p>
            </div>
          </div>
        </header>


        <TrainingOverview
          distanceKm={
            stats?.totalDistanceKm
            ?? 0
          }
          completedSessions={
            stats?.sessionsCount
            ?? 0
          }
          loading={
            statsLoading
          }
          raceName={
            nextRace?.name
            ?? 'Aucune course'
          }
          raceDescription={
            nextRace
              ? (
                  `${formatRaceDate(
                    nextRace.date,
                  )} · ${
                    nextRace.distanceKm
                  } km`
                )
              : 'Aucune course programmée'
          }
        />


        {statsError && (
          <div
            className="
              mt-3
              rounded-xl
              border border-warning/30
              bg-warning/5
              px-4 py-3
              text-sm
              text-warning
            "
          >
            {statsError}
          </div>
        )}


        <section className="mt-7 space-y-4">
          <div
            className="
              flex flex-col
              gap-3
              sm:flex-row
              sm:items-end
              sm:justify-between
            "
          >
            <div>
              <h2 className="text-xl font-bold text-base-content">
                Cette semaine
              </h2>

              <p className="mt-1 text-sm text-base-content/60">
                Votre planning et les séances réellement effectuées.
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <span className="badge badge-outline">
                {plannedCount}{' '}
                prévue
                {plannedCount > 1
                  ? 's'
                  : ''}
              </span>

              {supplementaryCount > 0 && (
                <span className="badge badge-outline">
                  {supplementaryCount}{' '}
                  supplémentaire
                  {supplementaryCount > 1
                    ? 's'
                    : ''}
                </span>
              )}

              <span className="badge badge-ghost">
                {restCount}{' '}
                repos
              </span>
            </div>
          </div>


          <div className="space-y-3">
            {weekDays.map(
              ({
                label,
                date,
                sessions:
                  daySessions,
                isToday,
              }) => (
                <DayRow
                  key={date}
                  label={label}
                  date={date}
                  sessions={
                    daySessions
                  }
                  isToday={
                    isToday
                  }
                  onOpenSession={
                    openSession
                  }
                  onAddSession={() =>
                    openAddSession(
                      date,
                    )
                  }
                />
              ),
            )}
          </div>
        </section>
      </div>


      {selectedSession && (
        <Modal
          title={
            selectedSession.title
          }
          open
          onClose={
            closeSession
          }
        >
          <TrainingDetails
            session={
              selectedSession
            }
            onStatusChange={async (
              status,
            ) => {
              await updateSessionStatus(
                selectedSession.id,
                status,
              )

              await loadStats()
            }}
            onActivityChange={async (
              activityId,
            ) => {
              await updateSessionActivity(
                selectedSession.id,
                activityId,
              )

              await loadStats()
            }}
          />
        </Modal>
      )}


      {addSessionDate && (
        <AddTrainingSessionModal
          open
          date={
            addSessionDate
          }
          onClose={() => {
            closeAddSession()

            void loadStats()
          }}
        />
      )}
    </main>
  )
}


interface TrainingOverviewProps {
  distanceKm: number
  completedSessions: number
  loading: boolean
  raceName: string
  raceDescription: string
}


function TrainingOverview({
  distanceKm,
  completedSessions,
  loading,
  raceName,
  raceDescription,
}: TrainingOverviewProps) {
  return (
    <section
      aria-label="Synthèse entraînement"
      className="
        overflow-hidden
        rounded-2xl
        border border-base-300
        bg-base-100
        shadow-sm
      "
    >
      <div
        className="
          grid
          divide-y divide-base-300
          sm:grid-cols-[1fr_1fr_1.4fr]
          sm:divide-x
          sm:divide-y-0
        "
      >
        <OverviewItem
          icon={Route}
          value={
            loading
              ? '…'
              : (
                  `${formatNumber(
                    distanceKm,
                  )} km`
                )
          }
          label="Kilomètres"
          description="Depuis le début de l'année"
        />

        <OverviewItem
          icon={Check}
          value={
            loading
              ? '…'
              : `${completedSessions}`
          }
          label="Séances réalisées"
          description="Depuis le début de l'année"
        />

        <OverviewItem
          icon={Trophy}
          value={raceName}
          label="Prochaine course"
          description={
            raceDescription
          }
          wide
        />
      </div>
    </section>
  )
}


interface OverviewItemProps {
  icon: typeof Route
  value: string
  label: string
  description: string
  wide?: boolean
}


function OverviewItem({
  icon: Icon,
  value,
  label,
  description,
  wide = false,
}: OverviewItemProps) {
  return (
    <div
      className="
        flex min-w-0
        items-center
        gap-3
        px-4 py-3.5
        sm:px-5
      "
    >
      <div
        className="
          flex size-9
          shrink-0
          items-center
          justify-center
          rounded-xl
          bg-primary/10
          text-primary
        "
      >
        <Icon
          size={18}
          strokeWidth={2}
        />
      </div>

      <div className="min-w-0">
        <p
          className={[
            'font-bold text-base-content',
            wide
              ? 'truncate text-base'
              : 'text-lg',
          ].join(' ')}
          title={
            wide
              ? value
              : undefined
          }
        >
          {value}
        </p>

        <div
          className="
            mt-0.5
            flex flex-wrap
            items-baseline
            gap-x-2
          "
        >
          <span
            className="
              text-xs
              font-medium
              text-base-content/65
            "
          >
            {label}
          </span>

          <span
            className="
              text-xs
              text-base-content/40
            "
          >
            {description}
          </span>
        </div>
      </div>
    </div>
  )
}


interface DayRowProps {
  label: string
  date: string

  sessions:
    TrainingSession[]

  isToday: boolean

  onOpenSession: (
    sessionId: string,
  ) => void

  onAddSession: () => void
}


function DayRow({
  label,
  date,
  sessions,
  isToday,
  onOpenSession,
  onAddSession,
}: DayRowProps) {
  const restSession =
    sessions.find(
      (session) =>
        session.type
        === 'rest',
    )

  const trainingSessions =
    sessions.filter(
      (session) =>
        session.type
        !== 'rest',
    )

  return (
    <article
      className={[
        'rounded-2xl border bg-base-100 shadow-sm',
        isToday
          ? (
              'border-primary '
              + 'ring-1 '
              + 'ring-primary/20'
            )
          : 'border-base-300',
      ].join(' ')}
    >
      <div
        className="
          grid gap-4
          p-4
          md:grid-cols-[150px_minmax(0,1fr)_auto]
          md:items-start
        "
      >
        <DayHeading
          label={label}
          date={date}
          isToday={isToday}
        />


        <div className="min-w-0 space-y-2">
          {restSession && (
            <RestSessionRow
              session={
                restSession
              }
              onOpen={() =>
                onOpenSession(
                  restSession.id,
                )
              }
            />
          )}

          {trainingSessions.length
            === 0
            && !restSession && (
              <EmptyDay />
            )}

          {trainingSessions.map(
            (session) => (
              <SessionRow
                key={
                  session.id
                }
                session={
                  session
                }
                onOpen={() =>
                  onOpenSession(
                    session.id,
                  )
                }
              />
            ),
          )}
        </div>


        <div
          className="
            flex
            md:justify-end
          "
        >
          <button
            type="button"
            className="
              btn btn-ghost btn-sm
              gap-1
              text-base-content/60
            "
            onClick={
              onAddSession
            }
          >
            <Plus
              size={15}
            />

            Ajouter
          </button>
        </div>
      </div>
    </article>
  )
}


interface DayHeadingProps {
  label: string
  date: string
  isToday: boolean
}


function DayHeading({
  label,
  date,
  isToday,
}: DayHeadingProps) {
  return (
    <div>
      <div
        className="
          flex flex-wrap
          items-center
          gap-2
        "
      >
        <p className="text-sm font-bold uppercase tracking-wide text-base-content">
          {label}
        </p>

        {isToday && (
          <span className="badge badge-primary badge-sm">
            Aujourd&apos;hui
          </span>
        )}
      </div>

      <p className="mt-1 text-xs text-base-content/50">
        {formatLongDate(
          date,
        )}
      </p>
    </div>
  )
}


interface RestSessionRowProps {
  session: TrainingSession
  onOpen: () => void
}


function RestSessionRow({
  session,
  onOpen,
}: RestSessionRowProps) {
  return (
    <button
      type="button"
      onClick={
        onOpen
      }
      className="
        flex w-full
        items-center
        justify-between
        gap-4
        rounded-xl
        bg-base-200/70
        px-4 py-3
        text-left
        transition
        hover:bg-base-200
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
          <h3 className="font-semibold text-base-content">
            Repos
          </h3>

          <span className="badge badge-ghost badge-sm">
            OpenCoach
          </span>
        </div>

        <p className="mt-1 text-sm text-base-content/50">
          Récupération recommandée
        </p>
      </div>

      <StatusBadge
        status={
          session.status
        }
      />
    </button>
  )
}


function EmptyDay() {
  return (
    <div
      className="
        rounded-xl
        bg-base-200/50
        px-4 py-3
      "
    >
      <p className="font-medium text-base-content/70">
        Repos
      </p>

      <p className="mt-1 text-sm text-base-content/45">
        Aucune séance prévue
      </p>
    </div>
  )
}


interface SessionRowProps {
  session: TrainingSession
  onOpen: () => void
}


function SessionRow({
  session,
  onOpen,
}: SessionRowProps) {
  const supplementary =
    session.type
    === 'supplementary'

  return (
    <button
      type="button"
      onClick={
        onOpen
      }
      className="
        flex w-full
        flex-col
        gap-3
        rounded-xl
        border border-base-300
        px-4 py-3
        text-left
        transition
        hover:bg-base-200/60
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
          <h3
            className="
              truncate
              font-semibold
              text-base-content
            "
          >
            {session.title}
          </h3>

          {supplementary && (
            <span className="badge badge-outline badge-sm">
              Supplémentaire
            </span>
          )}
        </div>

        <p className="mt-1 text-sm text-base-content/50">
          {formatSportType(
            session.sportType,
          )}
        </p>
      </div>


      <div
        className="
          flex flex-wrap
          items-center
          gap-x-4
          gap-y-2
          text-sm
        "
      >
        <InlineValue
          value={
            `${session.durationMinutes} min`
          }
        />

        {session.distanceKm
          !== undefined && (
            <InlineValue
              value={
                `${
                  formatNumber(
                    session.distanceKm,
                  )
                } km`
              }
            />
          )}

        {session.intensity && (
          <InlineValue
            value={
              formatTrainingIntensity(
                session.intensity,
              )
            }
          />
        )}

        {session.heartRateZone && (
          <InlineValue
            value={
              session.heartRateZone
            }
          />
        )}

        <StatusBadge
          status={
            session.status
          }
        />
      </div>
    </button>
  )
}


function InlineValue({
  value,
}: {
  value: string
}) {
  return (
    <span className="text-base-content/60">
      {value}
    </span>
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
        className="badge badge-success badge-sm gap-1"
        title="Séance réalisée"
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
        className="badge badge-error badge-sm gap-1"
        title="Séance non réalisée"
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
      className="badge badge-warning badge-sm gap-1"
      title="Séance à faire"
    >
      <Clock3
        size={12}
      />

      À faire
    </span>
  )
}


function getWeekSessions(
  sessions:
    TrainingSession[],
) {
  const today =
    new Date()

  const currentDay =
    today.getDay()

  const mondayOffset =
    currentDay === 0
      ? -6
      : 1 - currentDay

  const monday =
    new Date(
      today,
    )

  monday.setHours(
    12,
    0,
    0,
    0,
  )

  monday.setDate(
    today.getDate()
    + mondayOffset,
  )

  const todayString =
    formatLocalDate(
      today,
    )

  return dayLabels.map(
    (
      label,
      index,
    ) => {
      const date =
        new Date(
          monday,
        )

      date.setDate(
        monday.getDate()
        + index,
      )

      const dateString =
        formatLocalDate(
          date,
        )

      return {
        label,
        date:
          dateString,

        sessions:
          sessions.filter(
            (session) =>
              session.date
              === dateString,
          ),

        isToday:
          dateString
          === todayString,
      }
    },
  )
}


function getNextRace(
  availableRaces: typeof races,
) {
  const today =
    new Date()

  today.setHours(
    0,
    0,
    0,
    0,
  )

  return [
    ...availableRaces,
  ]
    .filter(
      (race) =>
        new Date(
          `${race.date}T12:00:00`,
        ) >= today,
    )
    .sort(
      (
        first,
        second,
      ) =>
        new Date(
          `${first.date}T12:00:00`,
        ).getTime()
        -
        new Date(
          `${second.date}T12:00:00`,
        ).getTime(),
    )[0]
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


function formatLongDate(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'long',
    },
  ).format(
    new Date(
      `${dateString}T12:00:00`,
    ),
  )
}


function formatRaceDate(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'short',
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


function formatSportType(
  sportType: string,
): string {
  const labels:
    Record<string, string> = {
      Run:
        'Course',
      TrailRun:
        'Trail',
      Ride:
        'Vélo',
      Swim:
        'Natation',
      StrengthTraining:
        'Renforcement',
      WeightTraining:
        'Renforcement',
      Walk:
        'Marche',
      Other:
        'Autre',
    }

  return (
    labels[sportType]
    ?? sportType
  )
}