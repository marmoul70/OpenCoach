export type TrainingSessionType =
  | 'easy'
  | 'tempo'
  | 'interval'
  | 'long'
  | 'recovery'
  | 'trail'
  | 'rest'
  | 'supplementary'
  | 'aerobic_easy'
  | 'long_endurance'
  | 'threshold'
  | 'vo2max'
  | 'speed_development'
  | 'strength_lower_body'
  | 'physiological_test'


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

export interface TrainingStats {
  startDate: string
  endDate: string

  activitiesCount: number
  manualSessionsCount: number
  sessionsCount: number

  totalDurationMinutes: number
  totalDistanceKm: number
  totalElevationGainM: number

  measuredLoad: number
  estimatedLoad: number
  totalLoad: number
}
