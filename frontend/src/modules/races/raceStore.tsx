import {
  createContext,
  useContext,
  useState,
  type ReactNode,
} from 'react'

import { races as initialRaces } from './data'
import type { Race } from './types'

interface RaceStoreValue {
  races: Race[]
  addRace: (race: Race) => void
  updateRace: (race: Race) => void
}

const RaceStoreContext =
  createContext<RaceStoreValue | undefined>(undefined)

interface RaceProviderProps {
  children: ReactNode
}

export function RaceProvider({
  children,
}: RaceProviderProps) {
  const [races, setRaces] =
    useState<Race[]>(initialRaces)

  function addRace(race: Race) {
    setRaces((current) => [...current, race])
  }

  function updateRace(updatedRace: Race) {
      setRaces((current) =>
        current.map((race) =>
          race.id === updatedRace.id
            ? updatedRace
            : race,
        ),
      )
    }

  return (
    <RaceStoreContext.Provider
      value={{
        races,
        addRace,
        updateRace,
      }}
    >
      {children}
    </RaceStoreContext.Provider>
  )
}

export function useRaces(): RaceStoreValue {
  const context = useContext(RaceStoreContext)

  if (!context) {
    throw new Error(
      'useRaces doit être utilisé dans RaceProvider',
    )
  }

  return context
}
