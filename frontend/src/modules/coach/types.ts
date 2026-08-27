export type CoachAction =
  | 'keep'
  | 'reduce'
  | 'replace'
  | 'rest'


export type RecentLoadSignalLevel =
  | 'info'
  | 'warning'
  | 'critical'


export type RecentLoadSignalKind =
  | 'recent_overload'
  | 'repeated_overload'
  | 'broken_rest'
  | 'repeated_broken_rest'


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


export interface CoachReadinessSignal {
  metric: string
  level: string
  reason: string

  currentValue?: number
  referenceValue?: number
}


export interface CoachReadiness {
  score: number
  level: string

  warningCount: number
  criticalCount: number

  trainingConstraints: string[]

  signals: CoachReadinessSignal[]

  sourceDate: string
  dataAgeDays: number
  dataStatus: 'fresh' | 'stale'
}


export interface CoachDecision {
  action: CoachAction
  reason: string

  originalDurationMinutes?: number
  recommendedDurationMinutes?: number

  durationFactor?: number
  intensityFactor?: number

  originalIntensity?: string
  recommendedIntensity?: string

  constraints: string[]
}


export interface CoachRecentLoad {
  analyzedDays: number

  plannedLoadTotal: number
  actualLoadTotal: number

  loadDeltaTotal: number
  loadRatio?: number

  abovePlanDays: number
  belowPlanDays: number
  onPlanDays: number

  brokenRestDays: number
  respectedRestDays: number

  hasTrainingHistory: boolean
}


export interface CoachRecentLoadSignal {
  kind: RecentLoadSignalKind
  level: RecentLoadSignalLevel
  reason: string
}


export interface CoachRecentLoadAssessment {
  hasWarning: boolean
  hasCritical: boolean
  hasOverload: boolean
  hasBrokenRest: boolean

  signals: CoachRecentLoadSignal[]
}


export interface CoachSessionDecision {
  session: CoachSession | null
  decision: CoachDecision
}


export type CoachWeeklyStatus =
  | 'aligned'
  | 'under_target'
  | 'over_target'
  | 'unknown'


export type CoachHistoryConfidenceLevel =
  | 'low'
  | 'moderate'
  | 'good'
  | 'high'


export type CoachWeekType =
  | 'loading'
  | 'recovery'
  | 'taper'
  | 'return_to_training'
  | 'suspended'


export type CoachTrainingPhase =
  | 'foundation'
  | 'base'
  | 'build'
  | 'specific'
  | 'taper'
  | 'recovery'
  | 'return_to_training'


export interface CoachWeeklyPlan {
  weekStart: string
  weekEnd: string

  phase: CoachTrainingPhase
  weekType?: CoachWeekType
  phaseWeekIndex: number
}


export interface CoachWeeklyAssessment {
  status: CoachWeeklyStatus

  targetLoad?: number
  actualLoadToDate: number
  remainingPlannedLoad: number
  projectedWeekLoad: number

  projectedGap?: number
  projectedGapPercent?: number

  remainingDays: number
  remainingSessionsCount: number

  adaptationOpportunity: boolean
  adaptationDirection?:
    | 'increase'
    | 'reduce'

  historyWindowDays: number
  historyConfidence: number
  historyConfidenceLevel:
    CoachHistoryConfidenceLevel

  headline: string
  analysis: string
  instruction: string
}


export interface CoachToday {
  date: string

  sessionDecisions: CoachSessionDecision[]

  readiness: CoachReadiness

  recentLoad: CoachRecentLoad | null
  recentLoadAssessment:
    CoachRecentLoadAssessment | null

  weeklyAssessment: CoachWeeklyAssessment

  weeklyPlan: CoachWeeklyPlan | null

  dataWarning?: string
}
