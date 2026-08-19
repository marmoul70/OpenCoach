export type CoachAction =
  | 'keep'
  | 'reduce'
  | 'replace'
  | 'rest'

export interface CoachSession {
  id?: string

  date: string
  type: string
  sportType: string

  title: string
  description: string

  durationMinutes: number

  distanceKm?: number
  elevationGainM?: number

  intensity: string
  heartRateZone?: string

  status: string
}

export interface CoachReadiness {
  score: number
  level: string

  warningCount: number
  criticalCount: number

  trainingConstraints: string[]
}

export interface CoachDecision {
  action: CoachAction
  reason: string

  originalDurationMinutes: number
  recommendedDurationMinutes?: number

  durationFactor?: number
  intensityFactor?: number

  originalIntensity: string
  recommendedIntensity?: string

  constraints: string[]
}

export interface CoachToday {
  date: string

  session: CoachSession
  readiness: CoachReadiness
  decision: CoachDecision
}
