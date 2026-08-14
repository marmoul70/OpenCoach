import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react'

import { trainingSessions } from './data'
import type { TrainingSession } from './types'

interface TrainingStoreValue {
  sessions: TrainingSession[]
  updateSessionStatus: (
    sessionId: string,
    status: TrainingSession['status'],
  ) => void
}

const TrainingStoreContext =
  createContext<TrainingStoreValue | undefined>(
    undefined,
  )

interface TrainingProviderProps {
  children: ReactNode
}

export function TrainingProvider({
  children,
}: TrainingProviderProps) {
  const [sessions, setSessions] =
    useState<TrainingSession[]>(trainingSessions)

  function updateSessionStatus(
    sessionId: string,
    status: TrainingSession['status'],
  ) {
    setSessions((current) =>
      current.map((session) =>
        session.id === sessionId
          ? { ...session, status }
          : session,
      ),
    )
  }

  return (
    <TrainingStoreContext.Provider
      value={{
        sessions,
        updateSessionStatus,
      }}
    >
      {children}
    </TrainingStoreContext.Provider>
  )
}

export function useTrainingSessions(): TrainingStoreValue {
  const context = useContext(TrainingStoreContext)

  if (!context) {
    throw new Error(
      'useTrainingSessions doit être utilisé dans TrainingProvider',
    )
  }

  return context
}
