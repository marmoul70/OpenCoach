import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'

import {
} from 'lucide-react'

import {
  SidePanel,
} from '../../components/ui/SidePanel'

import {
  fetchTrainingStats,
} from '../../core/training/api'
import {
  applyWeeklyDebrief,
  fetchWeeklyDebrief,
} from './weeklyDebriefApi'
import type {
  WeeklyDebriefHistory,
} from './weeklyDebriefApi'

import {
  AddTrainingSessionModal,
} from './AddTrainingSessionModal'

import {
  TrainingDetails,
} from './TrainingDetails'

import {
  TodayTrainingCard,
} from './TodayTrainingCard'

import {
  TrainingWeekDays,
} from './TrainingWeekDays'

import {
  TrainingWeekHeader,
} from './TrainingWeekHeader'
import {
  fetchCoachTrajectory,
} from './trajectoryApi'

import type {
  CoachTrajectory,
  CoachTrajectoryWeek,
} from './trajectoryApi'
import {
  fetchTrainingWeeklyPlan,
} from './weeklyPlanApi'

import type {
  TrainingWeeklyPlan,
} from './weeklyPlanApi'

import {
  formatLocalDate,
  getWeekSessions,
} from './trainingWeekCalendar'

import {
  formatWeekType,
  phaseTextClass,
  formatTrainingPhase,
  formatTrainingWeekRange,
  humanizeWeeklyTrainingStatus,
  formatNumber,
} from './trainingWeekPresentation'

import {
  useCoachToday,
} from '../coach/useCoachToday'

import {
  useTrainingSessions,
} from './trainingStore'

import type {
  TrainingStats,
} from './types'

import './TrainingPolish.css'


import {
  getPendingPhysiologicalTests,
} from '../physiological-tests'

import type {
  PhysiologicalTestProposal,
} from '../physiological-tests'


export function TrainingWeek() {

  useEffect(() => {
    window.scrollTo({
      top: 0,
      left: 0,
      behavior: 'auto',
    })
  }, [])

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
    sessions,
    updateSessionStatus,
    moveSession,
    validateSession,
    weekStart,
    weekEnd,
    goToPreviousWeek,
    goToNextWeek,
    goToCurrentWeek,
    goToDate,
  } = useTrainingSessions()

  const [
    displayedWeeklyPlan,
    setDisplayedWeeklyPlan,
  ] = useState<
    TrainingWeeklyPlan | null
  >(null)

  useEffect(() => {
    let cancelled = false

    async function loadWeeklyPlan() {
      try {
        const plan =
          await fetchTrainingWeeklyPlan(
            weekStart,
          )

        if (!cancelled) {
          setDisplayedWeeklyPlan(
            plan,
          )
        }
      } catch {
        if (!cancelled) {
          setDisplayedWeeklyPlan(
            null,
          )
        }
      }
    }

    void loadWeeklyPlan()

    return () => {
      cancelled = true
    }
  }, [
    weekStart,
  ])


  const [
    trajectory,
    setTrajectory,
  ] = useState<CoachTrajectory | null>(
    null,
  )


  useEffect(() => {
    let cancelled = false

    async function loadTrajectory() {
      try {
        const result =
          await fetchCoachTrajectory()

        if (!cancelled) {
          setTrajectory(
            result,
          )
        }
      } catch {
        if (!cancelled) {
          setTrajectory(
            null,
          )
        }
      }
    }

    void loadTrajectory()

    return () => {
      cancelled = true
    }
  }, [])


  const [
    weeklyDebrief,
    setWeeklyDebrief,
  ] = useState<WeeklyDebriefHistory | null>(null)

  const [
    weeklyDebriefOpen,
    setWeeklyDebriefOpen,
  ] = useState(false)

  const [
    weeklyDebriefLoading,
    setWeeklyDebriefLoading,
  ] = useState(false)

  const [
    weeklyDebriefError,
    setWeeklyDebriefError,
  ] = useState<string | null>(null)

  const [
    applyingWeeklyDebrief,
    setApplyingWeeklyDebrief,
  ] = useState(false)

  const weeklyDebriefRequestId = useRef(0)

  useEffect(() => {
    weeklyDebriefRequestId.current += 1
    setWeeklyDebriefOpen(false)
    setWeeklyDebrief(null)
    setWeeklyDebriefError(null)
    setWeeklyDebriefLoading(false)
    setApplyingWeeklyDebrief(false)
  }, [weekStart])

  async function openWeeklyDebrief() {
    const requestId = ++weeklyDebriefRequestId.current
    setWeeklyDebriefOpen(true)
    setWeeklyDebriefLoading(true)
    setWeeklyDebriefError(null)
    setWeeklyDebrief(null)
    try {
      const result = await fetchWeeklyDebrief(weekStart)
      if (requestId === weeklyDebriefRequestId.current) {
        setWeeklyDebrief(result)
      }
    } catch (reason) {
      if (requestId === weeklyDebriefRequestId.current) {
        setWeeklyDebriefError(
          reason instanceof Error ? reason.message : 'Impossible de charger le bilan.',
        )
      }
    } finally {
      if (requestId === weeklyDebriefRequestId.current) {
        setWeeklyDebriefLoading(false)
      }
    }
  }

  async function confirmWeeklyAdaptation() {
    const appliedWeekStart = weekStart
    const requestId = weeklyDebriefRequestId.current
    setApplyingWeeklyDebrief(true)
    setWeeklyDebriefError(null)
    try {
      await applyWeeklyDebrief(appliedWeekStart)
      const refreshed = await fetchWeeklyDebrief(appliedWeekStart)
      if (requestId === weeklyDebriefRequestId.current) {
        setWeeklyDebrief(refreshed)
        await loadWeeklyStats()
      }
    } catch (reason) {
      if (requestId === weeklyDebriefRequestId.current) {
        setWeeklyDebriefError(
          reason instanceof Error ? reason.message : 'Impossible d’appliquer la proposition.',
        )
      }
    } finally {
      if (requestId === weeklyDebriefRequestId.current) {
        setApplyingWeeklyDebrief(false)
      }
    }
  }

  const [
    selectedSessionId,
    setSelectedSessionId,
  ] = useState<string | null>(
    null,
  )

  const [
    deepLinkSessionId,
    setDeepLinkSessionId,
  ] = useState<string | null>(
    null,
  )


  useEffect(() => {
    const url =
      new URL(
        window.location.href,
      )

    const sessionId =
      url.searchParams.get(
        'session',
      )

    const sessionDate =
      url.searchParams.get(
        'date',
      )

    if (!sessionId) {
      return
    }

    setDeepLinkSessionId(
      sessionId,
    )

    if (sessionDate) {
      goToDate(
        sessionDate,
      )
    }
  }, [
    goToDate,
  ])


  useEffect(() => {
    if (!deepLinkSessionId) {
      return
    }

    const exists =
      sessions.some(
        (session) =>
          session.id
          === deepLinkSessionId,
      )

    if (!exists) {
      return
    }

    setSelectedSessionId(
      deepLinkSessionId,
    )

    const url =
      new URL(
        window.location.href,
      )

    url.searchParams.delete(
      'session',
    )

    url.searchParams.delete(
      'date',
    )

    window.history.replaceState(
      {},
      '',
      (
        url.pathname
        + url.search
        + url.hash
      ),
    )

    setDeepLinkSessionId(
      null,
    )
  }, [
    sessions,
    deepLinkSessionId,
  ])


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


  const [
    weeklyStats,
    setWeeklyStats,
  ] = useState<TrainingStats | null>(
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



  const loadWeeklyStats =
    useCallback(
      async () => {
        try {
          const result =
            await fetchTrainingStats(
              weekStart,
              weekEnd,
            )

          setWeeklyStats(
            result,
          )
        } catch {
          setWeeklyStats(
            null,
          )
        }
      },
      [
        weekStart,
        weekEnd,
      ],
    )


  useEffect(() => {
    void loadWeeklyStats()
  }, [
    loadWeeklyStats,
  ])


  const weekDays =
    getWeekSessions(
      sessions,
      weekStart,
    )

  const todayDay =
    weekDays.find(
      (day) =>
        day.isToday,
    )

  const otherWeekDays =
    weekDays.filter(
      (day) =>
        !day.isToday,
    )


  const trajectoryWeek:
    CoachTrajectoryWeek | undefined =
    trajectory?.weeks.find(
      (week: CoachTrajectoryWeek) =>
        week.weekStart === weekStart,
    )


  const currentWeekStart =
    getCurrentWeekStart()

  const isCurrentWeek =
    weekStart === currentWeekStart


  const isFutureWeek =
    weekStart > currentWeekStart


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

  const restCount =
    sessions.filter(
      (session) =>
        session.type === 'rest',
    ).length



  const strengthCount =
    sessions.filter(
      (session) =>
        session.type
        === 'strength_lower_body',
    ).length

  const workCount =
    sessions.filter(
      (session) =>
        session.type !== 'rest'
        && session.type
          !== 'strength_lower_body'
        && session.type
          !== 'supplementary',
    ).length



  const weeklyAssessment =
    coach?.weeklyAssessment

  const weeklyActualPercent = (
    isCurrentWeek
    && weeklyAssessment?.targetLoad
      ? percentageOfTarget(
          weeklyAssessment.actualLoadToDate,
          weeklyAssessment.targetLoad,
        )
      : undefined
  )

  const displayedWeeklyLoad =
    isFutureWeek
      ? 0
      : (
          weeklyStats?.totalLoad
          ?? 0
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
    <main
      className="
        oc-app-shell
        min-h-screen
      "
    >
      <div
        className="
          mx-auto
          max-w-[1240px]
          px-3
          py-4
          sm:px-5
          lg:px-5
          lg:py-[18px]
        "
      >
        <TrainingWeekHeader
          weekRange={
            formatTrainingWeekRange(
              weekStart,
              weekEnd,
            )
          }
          weekTypeLabel={
            displayedWeeklyPlan?.weekType
              ? formatWeekType(
                  displayedWeeklyPlan.weekType,
                )
              : undefined
          }
phaseLabel={
            trajectoryWeek
              ? (
                  trajectoryWeek.mode
                  === 'maintenance'
                    ? 'Base'
                    : formatTrainingPhase(
                        trajectoryWeek.phase,
                      )
                )
              : undefined
          }
          phaseClass={
            displayedWeeklyPlan
              ? phaseTextClass(
                  displayedWeeklyPlan.phase,
                )
              : undefined
          }
          phaseWeekIndex={
            displayedWeeklyPlan?.phaseWeekIndex
          }
          workCount={
            workCount
          }
          restCount={
            restCount
          }
          strengthCount={
            strengthCount
          }
          isCurrentWeek={
            isCurrentWeek
          }
          onPreviousWeek={
            goToPreviousWeek
          }
          onNextWeek={
            goToNextWeek
          }
          onCurrentWeek={
            goToCurrentWeek
          }

          isFutureWeek={
            isFutureWeek
          }
          actualPercent={
            weeklyActualPercent
          }
          actualLoad={
            displayedWeeklyLoad
          }
          statusLabel={
            humanizeWeeklyTrainingStatus(
              weeklyAssessment?.status
              ?? 'unavailable',
            )
          }
          completedCount={
            completedCount
          }
          remainingCount={
            remainingCount
          }
          skippedCount={
            skippedCount
          }
          statsLoading={
            statsLoading
          }
          totalDistanceLabel={
            `${
              formatNumber(
                stats?.totalDistanceKm
                ?? 0,
              )
            } km`
          }
          sessionsCount={
            stats?.sessionsCount
            ?? 0
          }
          targetRaceName={
            trajectory?.targetRaceName
          }
          targetRaceDate={
            trajectory?.targetRaceDate
          }
        />

        <div className="mt-3 flex justify-end">
          <button
            type="button"
            onClick={() => void openWeeklyDebrief()}
            className="rounded-lg border border-[var(--oc-border)] bg-[var(--oc-surface)] px-3 py-2 text-sm font-semibold text-[var(--oc-text)] hover:bg-[var(--oc-surface-hover)]"
          >
            Voir le bilan de cette semaine
          </button>
        </div>

        {statsError && (
          <div
            className="
              mt-3
              rounded-xl
              border border-amber-500/20 dark:border-amber-400/20
              bg-amber-500/[0.05] dark:bg-amber-400/[0.055]
              px-4 py-3
              text-sm
              text-amber-600 dark:text-amber-400
            "
          >
            {statsError}
          </div>
        )}


        <section className="mt-4 space-y-3">

          {todayDay && (
            <TodayTrainingCard
              sessions={
                todayDay.sessions
              }
              onOpenSession={
                openSession
              }
              onAddSession={() =>
                openAddSession(
                  todayDay.date,
                )
              }
            />
          )}


          <TrainingWeekDays
            days={
              otherWeekDays
            }
            physiologicalTestProposals={
              physiologicalTestProposals
            }
            onOpenSession={
              openSession
            }
            onAddSession={
              openAddSession
            }
          />
        </section>
      </div>


      {weeklyDebriefOpen && (
        <SidePanel
          title="Bilan hebdomadaire"
          eyebrow="Historique du coaching"
          open
          onClose={() => setWeeklyDebriefOpen(false)}
        >
          {weeklyDebriefLoading && (
            <p className="text-sm text-[var(--oc-text-secondary)]">Chargement du bilan…</p>
          )}

          {weeklyDebriefError && (
            <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.05] p-3 text-sm text-amber-700 dark:text-amber-300">
              {weeklyDebriefError}
            </div>
          )}

          {weeklyDebrief && (
            <div className="space-y-4 text-sm">
              <section className="rounded-xl border border-[var(--oc-border)] p-4">
                <p className="text-xs font-semibold uppercase tracking-wide text-[var(--oc-text-secondary)]">
                  {weeklyDebrief.debrief.week_start} au {weeklyDebrief.debrief.week_end}
                </p>
                <h3 className="mt-2 text-base font-semibold text-[var(--oc-text)]">
                  {weeklyDebrief.debrief.headline}
                </h3>
                <p className="mt-2 text-[var(--oc-text-secondary)]">
                  {weeklyDebrief.debrief.analysis}
                </p>
                <p className="mt-3 font-semibold">
                  Score global : {weeklyDebrief.debrief.overall_score ?? 'Non calculable'}
                  {weeklyDebrief.debrief.overall_score !== null ? ' / 100' : ''}
                </p>
              </section>

              <section className="rounded-xl border border-[var(--oc-border)] p-4">
                <h3 className="font-semibold">Indicateurs de la semaine</h3>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <Metric label="Séances prévues" value={weeklyDebrief.facts.planned_sessions} />
                  <Metric label="Séances réalisées" value={weeklyDebrief.facts.completed_sessions} />
                  <Metric label="Durée prévue" value={weeklyDebrief.facts.planned_duration_minutes != null ? `${weeklyDebrief.facts.planned_duration_minutes} min` : '—'} />
                  <Metric label="Durée réalisée" value={weeklyDebrief.facts.actual_duration_minutes != null ? `${weeklyDebrief.facts.actual_duration_minutes} min` : '—'} />
                  <Metric label="Charge prévue" value={weeklyDebrief.facts.planned_load} />
                  <Metric label="Charge réalisée" value={weeklyDebrief.facts.actual_load} />
                  <Metric label="Séances prioritaires prévues" value={weeklyDebrief.facts.key_sessions_planned} />
                  <Metric label="Séances prioritaires réalisées" value={weeklyDebrief.facts.key_sessions_completed} />
                </div>
              </section>

              <section className="rounded-xl border border-[var(--oc-border)] p-4">
                <h3 className="font-semibold">Fréquence cardiaque enregistrée</h3>
                {weeklyDebrief.heart_rate_activities.length === 0 ? (
                  <p className="mt-2 text-[var(--oc-text-secondary)]">
                    Aucun flux de fréquence cardiaque détaillé n’est disponible pour cette semaine.
                  </p>
                ) : (
                  <div className="mt-3 space-y-3">
                    {weeklyDebrief.heart_rate_activities.map((activity) => (
                      <details key={activity.activity_name + activity.started_at} className="rounded-lg bg-[var(--oc-surface-muted)] p-3">
                        <summary className="cursor-pointer font-medium">
                          {activity.activity_name} — {activity.sample_count} mesures
                        </summary>
                        <p className="mt-2 text-xs text-[var(--oc-text-secondary)]">
                          Moyenne : {activity.average_bpm ?? '—'} bpm · Maximum : {activity.maximum_bpm ?? '—'} bpm
                        </p>
                        <div className="mt-2 max-h-48 overflow-auto">
                          <table className="w-full text-xs">
                            <thead><tr><th className="py-1 text-left">Temps (s)</th><th className="py-1 text-right">FC (bpm)</th></tr></thead>
                            <tbody>
                              {activity.samples.map((sample, index) => (
                                <tr key={index} className="border-t border-[var(--oc-border)]">
                                  <td className="py-1">{sample.time_seconds}</td>
                                  <td className="py-1 text-right">{sample.bpm}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    ))}
                  </div>
                )}
              </section>

              {weeklyDebrief.debrief.strengths.length > 0 && (
                <section>
                  <h3 className="font-semibold">Points positifs</h3>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-[var(--oc-text-secondary)]">
                    {weeklyDebrief.debrief.strengths.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </section>
              )}

              {weeklyDebrief.debrief.warnings.length > 0 && (
                <section>
                  <h3 className="font-semibold">Points de vigilance</h3>
                  <ul className="mt-2 list-disc space-y-1 pl-5 text-[var(--oc-text-secondary)]">
                    {weeklyDebrief.debrief.warnings.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </section>
              )}

              <section className="rounded-xl border border-[var(--oc-border)] p-4">
                <h3 className="font-semibold">Proposition du coach</h3>
                <p className="mt-2 font-semibold">{weeklyDebrief.adaptation.direction}</p>
                <p className="mt-1 text-[var(--oc-text-secondary)]">{weeklyDebrief.adaptation.reason}</p>
                <div className="mt-3 grid grid-cols-2 gap-3">
                  <Metric label="Facteur de charge" value={weeklyDebrief.adaptation.load_factor} />
                  <Metric label="Facteur de volume" value={weeklyDebrief.adaptation.volume_factor} />
                </div>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-[var(--oc-text-secondary)]">
                  {weeklyDebrief.adaptation.guardrails.map((item) => <li key={item}>{item}</li>)}
                </ul>
                {weeklyDebrief.planning_updated ? (
                  <p className="mt-4 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                    Cette proposition a déjà été appliquée.
                  </p>
                ) : (
                  <div className="mt-4 flex flex-wrap gap-2">
                    <button
                      type="button"
                      disabled={applyingWeeklyDebrief}
                      onClick={() => void confirmWeeklyAdaptation()}
                      className="rounded-lg bg-emerald-600 px-3 py-2 font-semibold text-white disabled:opacity-50"
                    >
                      {applyingWeeklyDebrief ? 'Application…' : 'Appliquer la proposition'}
                    </button>
                    <button
                      type="button"
                      onClick={() => setWeeklyDebriefOpen(false)}
                      className="rounded-lg border border-[var(--oc-border)] px-3 py-2 font-semibold"
                    >
                      Conserver mon planning
                    </button>
                  </div>
                )}
              </section>
            </div>
          )}
        </SidePanel>
      )}

      {selectedSession && (
        <SidePanel
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
            onValidateSession={async (
              activityId,
              shoeId,
            ) => {
              const analysis =
                await validateSession(
                  selectedSession.id,
                  activityId,
                  shoeId,
                )

              await loadStats()

              return analysis
            }}

            onSkipSession={async () => {
              await updateSessionStatus(
                selectedSession.id,
                'skipped',
              )

              await loadWeeklyStats()
            }}

            onMoveSession={async (
              targetDate,
            ) => {
              await moveSession(
                selectedSession.id,
                targetDate,
              )
            }}
          />
        </SidePanel>
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







function getCurrentWeekStart(): string {
  const today = new Date()

  const currentDay =
    today.getDay()

  const mondayOffset =
    currentDay === 0
      ? -6
      : 1 - currentDay

  const monday =
    new Date(today)

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

  return formatLocalDate(
    monday,
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


function Metric({ label, value }: { label: string; value: unknown }) {
  return (
    <div>
      <p className="text-xs text-[var(--oc-text-secondary)]">{label}</p>
      <p className="mt-1 font-semibold text-[var(--oc-text)]">{value == null ? '—' : String(value)}</p>
    </div>
  )
}
