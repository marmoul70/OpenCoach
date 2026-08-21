export type RaceType =
  | 'trail'
  | 'road'
  | 'ultra'
  | 'other'


export type RaceStatus =
  | 'planned'
  | 'completed'
  | 'abandoned'
  | 'not_participated'


export type RacePriority =
  | 'primary'
  | 'training'

export type RaceResultSource =
  | 'activity'
  | 'manual'
  | 'none'


export interface RaceActualResult {
  source: RaceResultSource

  activityId?: string

  distanceKm?: number
  elevationGainM?: number
  durationMinutes?: number

  trainingLoad?: number
}


export interface RaceActivityCandidate {
  id: string

  provider: string
  providerActivityId: string

  name: string
  sportType: string

  startAtLocal?: string

  movingTimeSeconds?: number

  distanceM?: number
  elevationGainM?: number

  trainingLoad?: number
  feel?: number
}

export interface Race {
  id: string

  // Informations sur la course
  name: string
  location: string
  date: string
  type: RaceType

  // Rôle dans la planification
  priority: RacePriority

  distanceKm: number
  elevationGainM?: number
  targetTimeMinutes?: number

  // Résultat
  status: RaceStatus
  actualDistanceKm?: number
  actualElevationGainM?: number
  actualTimeMinutes?: number
  ranking?: number
  activityId?: string

  actualResult: RaceActualResult

  // Retour personnel
  notes?: string
}