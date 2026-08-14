import type { AthleteProfile } from './types'

export const defaultAthleteProfile: AthleteProfile = {
  identity: {
    firstName: '',
    lastName: '',
    birthDate: '',
    gender: 'unspecified',
    avatar: undefined,
  },

  body: {
    heightCm: undefined,
    weightKg: undefined,
  },

  physiology: {
    maxHeartRate: undefined,
    restingHeartRate: undefined,
    vma: undefined,
    thresholdHeartRate1: undefined,
    thresholdHeartRate2: undefined,
  },

  training: {
    weeklySessions: undefined,
    weeklyDurationMinutes: undefined,
    weeklyDistanceKm: undefined,
    availableDays: [],
    fatigueThreshold: undefined,
    experience: undefined,
  },

  location: {
    name: undefined,
    latitude: undefined,
    longitude: undefined,
  },

  equipment: {
    shoes: [],
    bikes: [],
    watches: [],
  },

  nutrition: {
    carbohydratesPerHour: undefined,
    fluidsPerHour: undefined,
    sodiumPerHour: undefined,
  },
}
