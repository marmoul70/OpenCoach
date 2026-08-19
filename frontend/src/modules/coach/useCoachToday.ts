import {
  useEffect,
  useState,
} from 'react'

import {
  CoachTodayUnavailableError,
  fetchCoachToday,
} from '../../core/coach/api'

import type {
  CoachToday,
} from './types'


interface CoachTodayState {
  coach: CoachToday | null
  loading: boolean
  unavailable: boolean
  error: string | null
}


export function useCoachToday(): CoachTodayState {
  const [
    coach,
    setCoach,
  ] = useState<CoachToday | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    unavailable,
    setUnavailable,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )

  useEffect(() => {
    let active = true

    async function load() {
      try {
        const result =
          await fetchCoachToday()

        if (!active) {
          return
        }

        setCoach(result)
        setUnavailable(false)
        setError(null)
      } catch (caught) {
        if (!active) {
          return
        }

        if (
          caught
          instanceof CoachTodayUnavailableError
        ) {
          setCoach(null)
          setUnavailable(true)
          setError(null)

          return
        }

        setCoach(null)
        setUnavailable(false)

        setError(
          caught instanceof Error
            ? caught.message
            : 'Erreur inconnue.',
        )
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => {
      active = false
    }
  }, [])

  return {
    coach,
    loading,
    unavailable,
    error,
  }
}
