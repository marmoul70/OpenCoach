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


function getCurrentWeekRange(): {
  start: string
  end: string
} {
  const today = new Date()

  const currentDay = today.getDay()

  const mondayOffset =
    currentDay === 0
      ? -6
      : 1 - currentDay

  const monday = new Date(today)

  monday.setHours(
    12,
    0,
    0,
    0,
  )

  monday.setDate(
    today.getDate() + mondayOffset,
  )

  const sunday = new Date(monday)

  sunday.setDate(
    monday.getDate() + 6,
  )

  return {
    start: formatLocalDate(monday),
    end: formatLocalDate(sunday),
  }
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


  const refreshSessions =
    useCallback(async () => {
      setLoading(true)
      setError(null)

      try {
        const {
          start,
          end,
        } = getCurrentWeekRange()

        const result =
          await fetchTrainingSessions(
            start,
            end,
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
    }, [])


  useEffect(() => {
    void refreshSessions()
  }, [refreshSessions])


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
        createSession,
        updateSessionStatus,
        updateSessionActivity,
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
