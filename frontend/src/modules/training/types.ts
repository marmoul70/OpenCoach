export type TrainingSessionType =
  | 'easy'
  | 'tempo'
  | 'interval'
  | 'long'
  | 'recovery'
  | 'trail'
  | 'rest'

export type TrainingSessionStatus =
  | 'planned'
  | 'completed'
  | 'skipped'

export interface TrainingSession {
  id: string
  date: string
  type: TrainingSessionType
  title: string
  description: string
  durationMinutes: number
  distanceKm?: number
  intensity: string
  heartRateZone?: string
  status: TrainingSessionStatus
}
