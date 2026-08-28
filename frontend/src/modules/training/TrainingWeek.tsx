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
  useRaces,
} from '../races/raceStore'

import {
  getNextPrimaryRace,
} from '../races/selectors'

import {
  AddTrainingSessionModal,
} from './AddTrainingSessionModal'

import {
  TrainingDetails,
} from './TrainingDetails'

import {
  useCoachToday,
} from '../coach/useCoachToday'

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


import {
  formatPhysiologicalTestProtocol,
  getPendingPhysiologicalTests,
} from '../physiological-tests'

import type {
  PhysiologicalTestProposal,
} from '../physiological-tests'


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

  const [
    physiologicalTestProposals,
    setPhysiologicalTestProposals,
  ] = useState<
    PhysiologicalTestProposal[]
  >([])

  useEffect(() => {
    let cancelled = false

    async function loadPhysiologicalTests() {
      try {
        const proposals =
          await getPendingPhysiologicalTests()

        if (!cancelled) {
          setPhysiologicalTestProposals(
            proposals,
          )
        }
      } catch {
        if (!cancelled) {
          setPhysiologicalTestProposals(
            [],
          )
        }
      }
    }

    void loadPhysiologicalTests()

    function handleTrainingChanged() {
      void loadPhysiologicalTests()
    }

    window.addEventListener(
      'opencoach:training-changed',
      handleTrainingChanged,
    )

    return () => {
      cancelled = true

      window.removeEventListener(
        'opencoach:training-changed',
        handleTrainingChanged,
      )
    }
  }, [])

  const {
    coach,
  } = useCoachToday()

  const {
    races,
  } = useRaces()

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

  const weekStartDate =
    weekDays.at(0)?.date

  const weekEndDate =
    weekDays.at(-1)?.date

  const selectedSession =
    selectedSessionId
      ? sessions.find(
          (session) =>
            session.id
            === selectedSessionId,
        )
      : undefined

  const trainingSessions =
    sessions.filter(
      (session) =>
        session.type !== 'rest'
        && session.type !== 'supplementary',
    )

  const completedCount =
    trainingSessions.filter(
      (session) =>
        session.status === 'completed',
    ).length

  const remainingCount =
    trainingSessions.filter(
      (session) =>
        session.status === 'planned',
    ).length

  const skippedCount =
    trainingSessions.filter(
      (session) =>
        session.status === 'skipped',
    ).length

  const supplementaryCount =
    sessions.filter(
      (session) =>
        session.type === 'supplementary',
    ).length

  const restCount =
    sessions.filter(
      (session) =>
        session.type === 'rest',
    ).length


  const nextPrimaryRace =
    getNextPrimaryRace(
      races,
    )


  const weeklyAssessment =
    coach?.weeklyAssessment

  const weeklyPlan =
    coach?.weeklyPlan

  const weeklyActualPercent = (
    weeklyAssessment?.targetLoad
      ? percentageOfTarget(
          weeklyAssessment.actualLoadToDate,
          weeklyAssessment.targetLoad,
        )
      : undefined
  )

  const weeklyProjectedPercent = (
    weeklyAssessment?.targetLoad
      ? percentageOfTarget(
          weeklyAssessment.projectedWeekLoad,
          weeklyAssessment.targetLoad,
        )
      : undefined
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
          <div className="flex items-start justify-between gap-6">

            <div className="min-w-0">

              <p className="text-sm text-base-content/60">
                {weeklyPlan
                  ? formatTrainingWeekRange(
                      weeklyPlan.weekStart,
                      weeklyPlan.weekEnd,
                    )
                  : (
                      weekStartDate
                      && weekEndDate
                        ? formatTrainingWeekRange(
                            weekStartDate,
                            weekEndDate,
                          )
                        : 'Planning hebdomadaire'
                    )}
              </p>

              {weeklyPlan && (
                <div
                  className="
                    mt-3
                    flex
                    items-center
                    justify-between
                    gap-4
                  "
                >

                  <div className="flex flex-wrap items-center gap-x-4 gap-y-2">

                    {weeklyPlan.weekType && (
                      <div
                        className={
                          weekTypeBadgeClass(
                            weeklyPlan.weekType,
                          )
                        }
                      >
                        <span className="size-2 rounded-full bg-current opacity-80" />

                        <span className="font-semibold">
                          {formatWeekType(
                            weeklyPlan.weekType,
                          )}
                        </span>
                      </div>
                    )}

                    <div className="flex items-center gap-1.5 text-sm">

                      <span className="text-base-content/40">
                        Phase
                      </span>

                      <span
                        className={
                          phaseTextClass(
                            weeklyPlan.phase,
                          )
                        }
                      >
                        {formatTrainingPhase(
                          weeklyPlan.phase,
                        )}
                      </span>

                    </div>

                  </div>


                  <div className="shrink-0 text-right">

                    <span className="text-xs text-base-content/40">
                      Semaine
                    </span>

                    <span className="ml-1.5 font-semibold tabular-nums text-base-content/80">
                      {weeklyPlan.phaseWeekIndex}
                    </span>

                  </div>

                </div>
              )}
            </div>

            <div className="flex shrink-0 items-center gap-3">

              <div className="text-right">
                <h1 className="text-3xl font-bold tracking-tight text-base-content">
                  Entraînement
                </h1>
              </div>

              <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <CalendarDays
                  size={24}
                  strokeWidth={2}
                />
              </div>

            </div>

          </div>
        </header>


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

          {weeklyAssessment && (
            <section
              aria-label="Synthèse de la semaine"
              className="
                overflow-hidden
                rounded-2xl
                border border-base-300
                bg-base-100
                shadow-sm
              "
            >

              {/* --------------------------------------------
                  Progression hebdomadaire
              --------------------------------------------- */}

              <div className="px-4 py-4 sm:px-5">

                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">

                  <div>

                    <p className="text-xs font-medium text-base-content/45">
                      Charge semaine
                    </p>

                    <p className="mt-0.5 text-xl font-bold tabular-nums">
                      {weeklyActualPercent !== undefined
                        ? `${Math.round(
                            weeklyActualPercent,
                          )} %`
                        : '—'}

                      <span className="ml-1 text-xs font-medium text-base-content/40">
                        réalisé
                      </span>
                    </p>

                  </div>


                  <div className="flex flex-wrap gap-1.5 sm:justify-end">

                    <span
                      className={
                        weeklyAssessment.status === 'aligned'
                          ? 'badge badge-success badge-outline'
                          : (
                              weeklyAssessment.status === 'over_target'
                                ? 'badge badge-warning badge-outline'
                                : 'badge badge-outline'
                            )
                      }
                    >
                      {humanizeWeeklyTrainingStatus(
                        weeklyAssessment.status,
                      )}
                    </span>


                    {completedCount > 0 && (
                      <span className="badge badge-success badge-outline gap-1">

                        <Check
                          size={12}
                          strokeWidth={2.5}
                        />

                        {completedCount}{' '}
                        réalisée
                        {completedCount > 1
                          ? 's'
                          : ''}

                      </span>
                    )}


                    {remainingCount > 0 && (
                      <span className="badge badge-primary badge-outline gap-1">

                        <Clock3
                          size={12}
                          strokeWidth={2}
                        />

                        {remainingCount}{' '}
                        à faire

                      </span>
                    )}


                    {skippedCount > 0 && (
                      <span className="badge badge-error badge-outline gap-1">

                        <X
                          size={12}
                          strokeWidth={2}
                        />

                        {skippedCount}{' '}
                        non réalisée
                        {skippedCount > 1
                          ? 's'
                          : ''}

                      </span>
                    )}


                    {supplementaryCount > 0 && (
                      <span className="badge badge-outline">

                        {supplementaryCount}{' '}
                        supplémentaire
                        {supplementaryCount > 1
                          ? 's'
                          : ''}

                      </span>
                    )}


                    {restCount > 0 && (
                      <span className="badge badge-ghost">

                        {restCount}{' '}
                        repos

                      </span>
                    )}

                  </div>

                </div>


                <progress
                  className="progress progress-primary mt-3 h-2 w-full"
                  value={
                    weeklyActualPercent !== undefined
                      ? Math.min(
                          100,
                          Math.max(
                            0,
                            weeklyActualPercent,
                          ),
                        )
                      : 0
                  }
                  max={100}
                />


                <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-base-content/50">

                  <span>
                    {weeklyProjectedPercent !== undefined
                      ? `${Math.round(
                          weeklyProjectedPercent,
                        )} % projeté`
                      : 'Projection indisponible'}
                  </span>

                  <span aria-hidden="true">
                    ·
                  </span>

                  <span>
                    {weeklyAssessment.remainingSessionsCount} séance${
                      weeklyAssessment.remainingSessionsCount > 1
                        ? 's'
                        : ''
                    } restante${
                      weeklyAssessment.remainingSessionsCount > 1
                        ? 's'
                        : ''
                    }
                  </span>

                </div>

              </div>


              {/* --------------------------------------------
                  Statistiques générales
              --------------------------------------------- */}

              <div
                className="
                  grid
                  border-t border-base-300
                  divide-y divide-base-300
                  sm:grid-cols-[1fr_1fr_1.4fr]
                  sm:divide-x
                  sm:divide-y-0
                "
              >

                <CompactOverviewItem
                  icon={Route}
                  value={
                    statsLoading
                      ? '…'
                      : `${formatNumber(
                          stats?.totalDistanceKm
                          ?? 0,
                        )} km`
                  }
                  label="Cette année"
                />

                <CompactOverviewItem
                  icon={Check}
                  value={
                    statsLoading
                      ? '…'
                      : `${stats?.sessionsCount ?? 0}`
                  }
                  label="Séances réalisées"
                />

                <CompactOverviewItem
                  icon={Trophy}
                  value={
                    nextPrimaryRace?.name
                    ?? 'Aucun objectif'
                  }
                  label={
                    nextPrimaryRace
                      ? (
                          `${formatRaceDate(
                            nextPrimaryRace.date,
                          )} · ${
                            nextPrimaryRace.distanceKm
                          } km`
                        )
                      : 'Aucune course prioritaire'
                  }
                  wide
                />

              </div>

            </section>
          )}


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
          physiologicalTestProposals={
            physiologicalTestProposals
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


interface CompactOverviewItemProps {
  icon: typeof Route
  value: string
  label: string
  wide?: boolean
}


function CompactOverviewItem({
  icon: Icon,
  value,
  label,
  wide = false,
}: CompactOverviewItemProps) {
  return (
    <div className="flex min-w-0 items-center gap-3 px-4 py-3 sm:px-5">

      <div
        className="
          flex size-8 shrink-0
          items-center justify-center
          rounded-lg
          bg-primary/10
          text-primary
        "
      >
        <Icon
          size={16}
          strokeWidth={2}
        />
      </div>


      <div className="min-w-0">

        <p
          className={[
            'font-bold text-base-content',
            wide
              ? 'truncate text-sm'
              : 'text-base',
          ].join(' ')}
          title={
            wide
              ? value
              : undefined
          }
        >
          {value}
        </p>

        <p className="mt-0.5 truncate text-xs text-base-content/45">
          {label}
        </p>

      </div>

    </div>
  )
}


interface DayRowProps {
  label: string
  date: string

  sessions:
    TrainingSession[]

  physiologicalTestProposals:
    PhysiologicalTestProposal[]

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
  physiologicalTestProposals,
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
                physiologicalTestProposal={
                  physiologicalTestProposals.find(
                    (proposal) =>
                      proposal.target_session_id
                      === session.id,
                  )
                  ?? null
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

  physiologicalTestProposal:
    PhysiologicalTestProposal
    | null

  onOpen: () => void
}


function SessionStatusLabel({
  status,
}: {
  status: TrainingSession['status']
}) {
  if (status === 'completed') {
    return (
      <span className="badge badge-success badge-sm gap-1">
        <Check
          size={11}
          strokeWidth={3}
        />
        Réalisée
      </span>
    )
  }

  if (status === 'skipped') {
    return (
      <span className="badge badge-error badge-outline badge-sm gap-1">
        <X
          size={11}
          strokeWidth={2.5}
        />
        Non réalisée
      </span>
    )
  }

  return (
    <span className="badge badge-primary badge-outline badge-sm">
      À faire
    </span>
  )
}


function SessionRow({
  session,
  physiologicalTestProposal,
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
      className={[
        'flex w-full flex-col gap-3 rounded-xl border px-4 py-3',
        'text-left transition',
        'sm:flex-row sm:items-center sm:justify-between',
        session.status === 'completed'
          ? 'border-success/25 bg-success/5 hover:bg-success/10'
          : '',
        session.status === 'skipped'
          ? 'border-error/25 bg-error/5 hover:bg-error/10'
          : '',
        session.status !== 'completed'
          && session.status !== 'skipped'
          ? 'border-base-300 hover:bg-base-200/60'
          : '',
      ].join(' ')}
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

          <SessionStatusLabel
            status={session.status}
          />


          {physiologicalTestProposal && (
            <span
              className="
                badge
                badge-primary
                badge-outline
                badge-sm
                gap-1
              "
              title={
                physiologicalTestProposal.recommendation
              }
            >
              Test proposé · {
                formatPhysiologicalTestProtocol(
                  physiologicalTestProposal.protocol,
                )
              }
            </span>
          )}

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


function formatWeekType(
  weekType: NonNullable<
    NonNullable<
      ReturnType<typeof useCoachToday>['coach']
    >['weeklyPlan']
  >['weekType'],
): string {
  if (weekType === 'loading') {
    return 'Travail'
  }

  if (weekType === 'recovery') {
    return 'Récupération'
  }

  if (weekType === 'taper') {
    return 'Affûtage'
  }

  if (weekType === 'return_to_training') {
    return 'Reprise'
  }

  return 'Suspendue'
}


function weekTypeBadgeClass(
  weekType: NonNullable<
    NonNullable<
      ReturnType<typeof useCoachToday>['coach']
    >['weeklyPlan']
  >['weekType'],
): string {
  const base = (
    'inline-flex items-center gap-2 '
    + 'rounded-full border px-3 py-1.5 '
    + 'text-xs shadow-sm'
  )

  if (weekType === 'recovery') {
    return (
      base
      + ' border-success/25'
      + ' bg-success/10'
      + ' text-success'
    )
  }

  if (weekType === 'taper') {
    return (
      base
      + ' border-secondary/25'
      + ' bg-secondary/10'
      + ' text-secondary'
    )
  }

  if (weekType === 'return_to_training') {
    return (
      base
      + ' border-info/25'
      + ' bg-info/10'
      + ' text-info'
    )
  }

  if (weekType === 'suspended') {
    return (
      base
      + ' border-warning/25'
      + ' bg-warning/10'
      + ' text-warning'
    )
  }

  return (
    base
    + ' border-primary/25'
    + ' bg-primary/10'
    + ' text-primary'
  )
}


function phaseTextClass(
  phase: NonNullable<
    NonNullable<
      ReturnType<typeof useCoachToday>['coach']
    >['weeklyPlan']
  >['phase'],
): string {
  const base =
    'font-semibold'

  if (phase === 'foundation') {
    return (
      base
      + ' text-info'
    )
  }

  if (phase === 'base') {
    return (
      base
      + ' text-primary'
    )
  }

  if (phase === 'build') {
    return (
      base
      + ' text-warning'
    )
  }

  if (phase === 'specific') {
    return (
      base
      + ' text-secondary'
    )
  }

  if (phase === 'taper') {
    return (
      base
      + ' text-accent'
    )
  }

  if (phase === 'recovery') {
    return (
      base
      + ' text-success'
    )
  }

  return (
    base
    + ' text-info'
  )
}


function formatTrainingPhase(
  phase: NonNullable<
    NonNullable<
      ReturnType<typeof useCoachToday>['coach']
    >['weeklyPlan']
  >['phase'],
): string {
  if (phase === 'foundation') {
    return 'Fondation'
  }

  if (phase === 'base') {
    return 'Base'
  }

  if (phase === 'build') {
    return 'Développement'
  }

  if (phase === 'specific') {
    return 'Spécifique'
  }

  if (phase === 'taper') {
    return 'Affûtage'
  }

  if (phase === 'recovery') {
    return 'Récupération'
  }

  return 'Reprise'
}


function formatTrainingWeekRange(
  start: string,
  end: string,
): string {
  const startDate = new Date(
    `${start}T12:00:00`,
  )

  const endDate = new Date(
    `${end}T12:00:00`,
  )

  const startDay =
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        day: 'numeric',
      },
    ).format(
      startDate,
    )

  const endDateFormatted =
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
      },
    ).format(
      endDate,
    )

  return (
    `Semaine du ${startDay} au ${endDateFormatted}`
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


function percentageOfTarget(
  value: number,
  target: number,
): number {
  if (target <= 0) {
    return 0
  }

  return (
    value
    / target
    * 100
  )
}


function humanizeWeeklyTrainingStatus(
  status: string,
): string {
  if (status === 'aligned') {
    return 'Semaine dans la cible'
  }

  if (status === 'under_target') {
    return 'Charge sous la cible'
  }

  if (status === 'over_target') {
    return 'Charge au-dessus de la cible'
  }

  return 'Cible en cours d’évaluation'
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