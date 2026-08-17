import { defaultAthleteProfile } from './defaults'
import {
  fetchAthleteProfile,
  saveAthleteProfile,
} from './api'
import type { AthleteProfile } from './types'

let profile: AthleteProfile = structuredClone(
  defaultAthleteProfile,
)

let initialized = false

type ProfileListener = (
  profile: AthleteProfile,
) => void

const listeners = new Set<ProfileListener>()

function notify(): void {
  const snapshot = structuredClone(profile)

  for (const listener of listeners) {
    listener(snapshot)
  }
}

export function getAthleteProfile(): AthleteProfile {
  return structuredClone(profile)
}

export function getAthleteProfileSnapshot(): AthleteProfile {
  return profile
}

export function subscribeAthleteProfile(
  listener: ProfileListener,
): () => void {
  listeners.add(listener)

  return () => {
    listeners.delete(listener)
  }
}

export async function loadAthleteProfile(): Promise<AthleteProfile> {
  const loadedProfile = await fetchAthleteProfile()

  profile = structuredClone(loadedProfile)
  initialized = true

  notify()

  return getAthleteProfile()
}

export async function setAthleteProfile(
  nextProfile: AthleteProfile,
): Promise<AthleteProfile> {
  const savedProfile = await saveAthleteProfile(nextProfile)

  profile = structuredClone(savedProfile)
  initialized = true

  notify()

  return getAthleteProfile()
}

export async function updateAthleteProfile(
  update: (
    currentProfile: AthleteProfile,
  ) => AthleteProfile,
): Promise<AthleteProfile> {
  const nextProfile = update(getAthleteProfile())

  return setAthleteProfile(nextProfile)
}

export async function resetAthleteProfile(): Promise<AthleteProfile> {
  const resetProfile = structuredClone(
    defaultAthleteProfile,
  )

  return setAthleteProfile(resetProfile)
}

export function isAthleteProfileInitialized(): boolean {
  return initialized
}
