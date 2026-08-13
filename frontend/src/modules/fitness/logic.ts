import type { FitnessData, FitnessStatus } from './types'

export function getFitnessStatus(score: number): FitnessStatus {
  if (score >= 85) {
    return 'excellent'
  }

  if (score >= 70) {
    return 'good'
  }

  if (score >= 50) {
    return 'moderate'
  }

  return 'low'
}

export function createFitnessData(
  score: number,
  trainingLoad: number,
  recovery: number,
  fatigue: number,
): FitnessData {
  const status = getFitnessStatus(score)

  const labels: Record<FitnessStatus, string> = {
    excellent: 'Excellente',
    good: 'Bonne',
    moderate: 'Modérée',
    low: 'Faible',
  }

  return {
    score,
    status,
    label: labels[status],
    trainingLoad,
    recovery,
    fatigue,
  }
}
