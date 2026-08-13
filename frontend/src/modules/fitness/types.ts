export type FitnessStatus =
  | 'excellent'
  | 'good'
  | 'moderate'
  | 'low'

export interface FitnessData {
  score: number
  status: FitnessStatus
  label: string
  trainingLoad: number
  recovery: number
  fatigue: number
}
