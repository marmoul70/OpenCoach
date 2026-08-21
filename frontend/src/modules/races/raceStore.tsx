import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import {
  createRace,
  deleteRace,
  fetchRaces,
  updateRace,
  updateRaceActivity,
  type RaceWritePayload,
} from '../../core/races/api'

import type {
  Race,
} from './types'


interface RaceStoreValue {
  races: Race[]

  loading: boolean
  error: string | null

  refreshRaces: () => Promise<void>

  addRace: (
    payload: RaceWritePayload,
  ) => Promise<Race>

  updateRace: (
    raceId: string,
    payload: RaceWritePayload,
  ) => Promise<Race>

  removeRace: (
    raceId: string,
  ) => Promise<void>

  setRaceActivity: (
    raceId: string,
    activityId?: string,
  ) => Promise<Race>
}


const RaceStoreContext =
  createContext<
    RaceStoreValue | undefined
  >(undefined)


interface RaceProviderProps {
  children: ReactNode
}


export function RaceProvider({
  children,
}: RaceProviderProps) {
  const [races, setRaces] =
    useState<Race[]>([])

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState<string | null>(null)


  const refreshRaces =
    useCallback(
      async () => {
        setLoading(true)
        setError(null)

        try {
          const loadedRaces =
            await fetchRaces()

          setRaces(
            loadedRaces,
          )
        } catch (caughtError) {
          const message =
            caughtError instanceof Error
              ? caughtError.message
              : (
                'Impossible de charger '
                + 'les courses.'
              )

          setError(
            message,
          )
        } finally {
          setLoading(false)
        }
      },
      [],
    )


  useEffect(
    () => {
      void refreshRaces()
    },
    [refreshRaces],
  )


  const addRace =
    useCallback(
      async (
        payload: RaceWritePayload,
      ): Promise<Race> => {
        setError(null)

        try {
          const createdRace =
            await createRace(
              payload,
            )

          setRaces(
            (current) => [
              ...current,
              createdRace,
            ],
          )

          return createdRace
        } catch (caughtError) {
          const message =
            caughtError instanceof Error
              ? caughtError.message
              : (
                'Impossible de créer '
                + 'la course.'
              )

          setError(
            message,
          )

          throw caughtError
        }
      },
      [],
    )


  const updateStoredRace =
    useCallback(
      (
        updatedRace: Race,
      ) => {
        setRaces(
          (current) =>
            current.map(
              (race) =>
                race.id
                === updatedRace.id
                  ? updatedRace
                  : race,
            ),
        )
      },
      [],
    )


  const updateRaceEntry =
    useCallback(
      async (
        raceId: string,
        payload: RaceWritePayload,
      ): Promise<Race> => {
        setError(null)

        try {
          const updatedRace =
            await updateRace(
              raceId,
              payload,
            )

          updateStoredRace(
            updatedRace,
          )

          return updatedRace
        } catch (caughtError) {
          const message =
            caughtError instanceof Error
              ? caughtError.message
              : (
                'Impossible de modifier '
                + 'la course.'
              )

          setError(
            message,
          )

          throw caughtError
        }
      },
      [updateStoredRace],
    )


  const removeRace =
    useCallback(
      async (
        raceId: string,
      ): Promise<void> => {
        setError(null)

        try {
          await deleteRace(
            raceId,
          )

          setRaces(
            (current) =>
              current.filter(
                (race) =>
                  race.id
                  !== raceId,
              ),
          )
        } catch (caughtError) {
          const message =
            caughtError instanceof Error
              ? caughtError.message
              : (
                'Impossible de supprimer '
                + 'la course.'
              )

          setError(
            message,
          )

          throw caughtError
        }
      },
      [],
    )


  const setRaceActivity =
    useCallback(
      async (
        raceId: string,
        activityId?: string,
      ): Promise<Race> => {
        setError(null)

        try {
          const updatedRace =
            await updateRaceActivity(
              raceId,
              activityId,
            )

          updateStoredRace(
            updatedRace,
          )

          return updatedRace
        } catch (caughtError) {
          const message =
            caughtError instanceof Error
              ? caughtError.message
              : (
                'Impossible de modifier '
                + "l'activité associée."
              )

          setError(
            message,
          )

          throw caughtError
        }
      },
      [updateStoredRace],
    )


  const value =
    useMemo<RaceStoreValue>(
      () => ({
        races,

        loading,
        error,

        refreshRaces,

        addRace,

        updateRace:
          updateRaceEntry,

        removeRace,

        setRaceActivity,
      }),
      [
        races,
        loading,
        error,
        refreshRaces,
        addRace,
        updateRaceEntry,
        removeRace,
        setRaceActivity,
      ],
    )


  return (
    <RaceStoreContext.Provider
      value={value}
    >
      {children}
    </RaceStoreContext.Provider>
  )
}


export function useRaces():
RaceStoreValue {
  const context =
    useContext(
      RaceStoreContext,
    )

  if (!context) {
    throw new Error(
      (
        'useRaces doit être utilisé '
        + 'dans RaceProvider'
      ),
    )
  }

  return context
}