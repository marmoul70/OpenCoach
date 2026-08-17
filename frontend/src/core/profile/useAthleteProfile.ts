import { useSyncExternalStore } from 'react'

import {
  getAthleteProfileSnapshot,
  subscribeAthleteProfile,
} from './store'
import type { AthleteProfile } from './types'

export function useAthleteProfile(): AthleteProfile {
  return useSyncExternalStore(
    subscribeAthleteProfile,
    getAthleteProfileSnapshot,
    getAthleteProfileSnapshot,
  )
}
