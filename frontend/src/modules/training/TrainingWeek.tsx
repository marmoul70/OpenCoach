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
  RaceGoalCard,
} from './RaceGoalCard'

import {
  TodayTrainingCard,
} from './TodayTrainingCard'

import {
  WeeklyLoadCard,
} from './WeeklyLoadCard'

import {
  TrainingWeekDays,
} from './TrainingWeekDays'

import {
  TrainingWeekHeader,
} from './TrainingWeekHeader'

import {
  formatLocalDate,
  getWeekSessions,
} from './trainingWeekCalendar'

import {
  formatWeekType,
  weekTypeBadgeClass,
  phaseTextClass,
  formatTrainingPhase,
  formatTrainingWeekRange,
  humanizeWeeklyTrainingStatus,
  formatRaceDate,
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
    validateSession,
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
        <TrainingWeekHeader
          weekRange={
            weeklyPlan
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
                )
          }
          weekTypeLabel={
            weeklyPlan?.weekType
              ? formatWeekType(
                  weeklyPlan.weekType,
                )
              : undefined
          }
          weekTypeClass={
            weeklyPlan?.weekType
              ? weekTypeBadgeClass(
                  weeklyPlan.weekType,
                )
              : undefined
          }
          phaseLabel={
            weeklyPlan
              ? formatTrainingPhase(
                  weeklyPlan.phase,
                )
              : undefined
          }
          phaseClass={
            weeklyPlan
              ? phaseTextClass(
                  weeklyPlan.phase,
                )
              : undefined
          }
          phaseWeekIndex={
            weeklyPlan?.phaseWeekIndex
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

          {todayDay && (
            <TodayTrainingCard
              sessions={
                todayDay.sessions
              }
              onOpenSession={
                openSession
              }
            />
          )}


          {weeklyAssessment && (
            <WeeklyLoadCard
              actualPercent={
                weeklyActualPercent
              }
              projectedPercent={
                weeklyProjectedPercent
              }
              status={
                weeklyAssessment.status
              }
              statusLabel={
                humanizeWeeklyTrainingStatus(
                  weeklyAssessment.status,
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
              supplementaryCount={
                supplementaryCount
              }
              restCount={
                restCount
              }
              remainingSessionsCount={
                weeklyAssessment
                  .remainingSessionsCount
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
            />
          )}


          <RaceGoalCard
            name={
              nextPrimaryRace?.name
            }
            details={
              nextPrimaryRace
                ? (
                  `${formatRaceDate(
                    nextPrimaryRace.date,
                  )} · ${
                    nextPrimaryRace.distanceKm
                  } km`
                )
                : undefined
            }
          />


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
