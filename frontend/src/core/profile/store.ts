import { defaultAthleteProfile } from './defaults'
import type { AthleteProfile } from './types'

let profile: AthleteProfile = structuredClone(defaultAthleteProfile)

export function getAthleteProfile(): AthleteProfile {
  return structuredClone(profile)
}

export function setAthleteProfile(
  nextProfile: AthleteProfile,
): void {
  profile = structuredClone(nextProfile)
}

export function updateAthleteProfile(
  update: (currentProfile: AthleteProfile) => AthleteProfile,
): void {
  profile = structuredClone(update(structuredClone(profile)))
}

export function resetAthleteProfile(): void {
  profile = structuredClone(defaultAthleteProfile)
}
