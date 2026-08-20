export type TrainingSessionType =
  | 'easy'
  | 'tempo'
  | 'interval'
  | 'long'
  | 'recovery'
  | 'trail'
  | 'rest'
  | 'supplementary'

export type TrainingSessionStatus =
  | 'planned'
  | 'completed'
  | 'skipped'

export interface TrainingSession {
  id: string
  date: string
  type: TrainingSessionType
  sportType: string
  title: string
  description: string
  durationMinutes: number
  distanceKm?: number
  elevationGainM?: number
  intensity: string
  heartRateZone?: string
  status: TrainingSessionStatus
  activityId?: string
}

export interface TrainingSessionCreate {
  date: string
  type: TrainingSessionType
  sportType: string
  title: string
  description: string
  durationMinutes: number
  distanceKm?: number
  elevationGainM?: number
  intensity: string
  heartRateZone?: string
  status: TrainingSessionStatus
  activityId?: string
}

export interface TrainingAvailableActivity {
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