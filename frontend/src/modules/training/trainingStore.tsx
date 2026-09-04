/* oxlint-disable react/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  createTrainingSession as createTrainingSessionApi,
  fetchTrainingSessions,
  updateTrainingSessionActivity as updateTrainingSessionActivityApi,
  moveTrainingSession as moveTrainingSessionApi,
  updateTrainingSessionStatus as updateTrainingSessionStatusApi,
  validateTrainingSession as validateTrainingSessionApi,
} from '../../core/training/api'

import type {
  SessionExecutionDebrief,
} from '../../core/training/api'

import type {
  TrainingSession,
  TrainingSessionCreate,
  TrainingSessionStatus,
} from './types'

import {
  TRAINING_SESSION_UPDATED_EVENT,
} from '../../core/events'


interface TrainingStoreValue {
  sessions: TrainingSession[]
  loading: boolean
  error: string | null

  weekStart: string
  weekEnd: string

  goToPreviousWeek: () => void
  goToNextWeek: () => void
  goToCurrentWeek: () => void
  goToDate: (
    date: string,
  ) => void

  createSession: (
    session: TrainingSessionCreate,
  ) => Promise<TrainingSession>

  updateSessionStatus: (
    sessionId: string,
    status: TrainingSessionStatus,
  ) => Promise<void>

  updateSessionActivity: (
    sessionId: string,
    activityId: string | null,
  ) => Promise<void>

  moveSession: (
    sessionId: string,
    targetDate: string,
  ) => Promise<TrainingSession>

  validateSession: (
    sessionId: string,
    activityId: string,
  ) => Promise<SessionExecutionDebrief>

  refreshSessions: () => Promise<void>
}


const TrainingStoreContext =
  createContext<TrainingStoreValue | undefined>(
    undefined,
  )


interface TrainingProviderProps {
  children: ReactNode
}


function formatLocalDate(
  date: Date,
): string {
  const year = date.getFullYear()

  const month = String(
    date.getMonth() + 1,
  ).padStart(2, '0')

  const day = String(
    date.getDate(),
  ).padStart(2, '0')

  return `${year}-${month}-${day}`
}


function getWeekRangeFromDate(
  referenceDate: Date,
): {
  start: string
  end: string
} {
  const currentDay =
    referenceDate.getDay()

  const mondayOffset =
    currentDay === 0
      ? -6
      : 1 - currentDay

  const monday =
    new Date(referenceDate)

  monday.setHours(
    12,
    0,
    0,
    0,
  )

  monday.setDate(
    referenceDate.getDate()
    + mondayOffset,
  )

  const sunday =
    new Date(monday)

  sunday.setDate(
    monday.getDate() + 6,
  )

  return {
    start: formatLocalDate(monday),
    end: formatLocalDate(sunday),
  }
}


function shiftWeek(
  weekStart: string,
  offsetWeeks: number,
): {
  start: string
  end: string
} {
  const reference =
    new Date(
      `${weekStart}T12:00:00`,
    )

  reference.setDate(
    reference.getDate()
    + offsetWeeks * 7,
  )

  return getWeekRangeFromDate(
    reference,
  )
}


function getCurrentWeekRange(): {
  start: string
  end: string
} {
  return getWeekRangeFromDate(
    new Date(),
  )
}


export function TrainingProvider({
  children,
}: TrainingProviderProps) {
  const [sessions, setSessions] = useState<
    TrainingSession[]
  >([])

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState<string | null>(null)

  const [
    selectedWeek,
    setSelectedWeek,
  ] = useState(
    getCurrentWeekRange,
  )


  const refreshSessions =
    useCallback(async () => {
      setLoading(true)
      setError(null)

      try {
        const result =
          await fetchTrainingSessions(
            selectedWeek.start,
            selectedWeek.end,
          )

        setSessions(result)
      } catch (caughtError) {
        setError(
          caughtError instanceof Error
            ? caughtError.message
            : 'Impossible de charger les séances.',
        )
      } finally {
        setLoading(false)
      }
    }, [
      selectedWeek.start,
      selectedWeek.end,
    ])


  useEffect(() => {
    void refreshSessions()
  }, [refreshSessions])


  function goToPreviousWeek() {
    setSelectedWeek(
      current =>
        shiftWeek(
          current.start,
          -1,
        ),
    )
  }


  function goToNextWeek() {
    setSelectedWeek(
      current =>
        shiftWeek(
          current.start,
          1,
        ),
    )
  }


  function goToCurrentWeek() {
    setSelectedWeek(
      getCurrentWeekRange(),
    )
  }



  function goToDate(
    date: string,
  ) {
    const reference =
      new Date(
        `${date}T12:00:00`,
      )

    if (
      Number.isNaN(
        reference.getTime(),
      )
    ) {
      return
    }

    setSelectedWeek(
      getWeekRangeFromDate(
        reference,
      ),
    )
  }


  useEffect(() => {
    function handleTrainingSessionUpdated() {
      void refreshSessions()
    }

    window.addEventListener(
      TRAINING_SESSION_UPDATED_EVENT,
      handleTrainingSessionUpdated,
    )

    return () => {
      window.removeEventListener(
        TRAINING_SESSION_UPDATED_EVENT,
        handleTrainingSessionUpdated,
      )
    }
  }, [
    refreshSessions,
  ])


  async function createSession(
    session: TrainingSessionCreate,
  ): Promise<TrainingSession> {
    setError(null)

    try {
      const createdSession =
        await createTrainingSessionApi(
          session,
        )

      setSessions((current) => {
        const next = [
          ...current,
          createdSession,
        ]

        return next.sort(
          (first, second) => {
            const dateComparison =
              first.date.localeCompare(
                second.date,
              )

            if (dateComparison !== 0) {
              return dateComparison
            }

            return first.title.localeCompare(
              second.title,
            )
          },
        )
      })

      return createdSession
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : 'Impossible de créer la séance.',
      )

      throw caughtError
    }
  }


  async function updateSessionStatus(
    sessionId: string,
    status: TrainingSessionStatus,
  ): Promise<void> {
    setError(null)

    try {
      const updatedSession =
        await updateTrainingSessionStatusApi(
          sessionId,
          status,
        )

      setSessions((current) =>
        current.map((session) =>
          session.id === updatedSession.id
            ? updatedSession
            : session,
        ),
      )
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : 'Impossible de modifier la séance.',
      )

      throw caughtError
    }
  }


  async function updateSessionActivity(
    sessionId: string,
    activityId: string | null,
  ): Promise<void> {
    setError(null)

    try {
      const updatedSession =
        await updateTrainingSessionActivityApi(
          sessionId,
          activityId,
        )

      setSessions((current) =>
        current.map((session) =>
          session.id === updatedSession.id
            ? updatedSession
            : session,
        ),
      )
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Impossible d'associer l'activité.",
      )

      throw caughtError
    }
  }


  async function moveSession(
    sessionId: string,
    targetDate: string,
  ): Promise<TrainingSession> {
    setError(null)

    try {
      const updatedSession =
        await moveTrainingSessionApi(
          sessionId,
          targetDate,
        )

      setSessions(current =>
        current
          .map(session =>
            session.id === updatedSession.id
              ? updatedSession
              : session,
          )
          .sort(
            (first, second) => {
              const dateComparison =
                first.date.localeCompare(
                  second.date,
                )

              if (
                dateComparison !== 0
              ) {
                return dateComparison
              }

              return first.title.localeCompare(
                second.title,
              )
            },
          ),
      )

      return updatedSession
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : (
              'Impossible de déplacer '
              + 'la séance.'
            ),
      )

      throw caughtError
    }
  }


  async function validateSession(
    sessionId: string,
    activityId: string,
  ): Promise<SessionExecutionDebrief> {
    setError(null)

    try {
      const result =
        await validateTrainingSessionApi(
          sessionId,
          activityId,
        )

      setSessions((current) =>
        current.map((session) =>
          session.id === result.session.id
            ? result.session
            : session,
        ),
      )

      return result.analysis
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : (
              'Impossible de valider '
              + 'la séance.'
            ),
      )

      throw caughtError
    }
  }


  return (
    <TrainingStoreContext.Provider
      value={{
        sessions,
        loading,
        error,
        weekStart: selectedWeek.start,
        weekEnd: selectedWeek.end,
        goToPreviousWeek,
        goToNextWeek,
        goToCurrentWeek,
        goToDate,
        createSession,
        updateSessionStatus,
        updateSessionActivity,
        moveSession,
        validateSession,
        refreshSessions,
      }}
    >
      {children}
    </TrainingStoreContext.Provider>
  )
}


export function useTrainingSessions():
TrainingStoreValue {
  const context =
    useContext(TrainingStoreContext)

  if (!context) {
    throw new Error(
      'useTrainingSessions doit être utilisé dans TrainingProvider',
    )
  }

  return context
}
