import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
} from 'lucide-react'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  fetchTrainingStats,
} from '../../core/training/api'

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
        min-h-screen
        bg-[#f5f7f6]
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          mx-auto
          max-w-[1380px]
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
            onValidateSession={async (
              activityId,
            ) => {
              const analysis =
                await validateSession(
                  selectedSession.id,
                  activityId,
                )

              await loadStats()

              return analysis
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
