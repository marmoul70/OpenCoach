export type TrainingIntensity =
  | 'very_easy'
  | 'easy'
  | 'moderate'
  | 'hard'
  | 'very_hard'


export const TRAINING_INTENSITIES: Array<{
  value: TrainingIntensity
  label: string
}> = [
  {
    value: 'very_easy',
    label: 'Très facile',
  },
  {
    value: 'easy',
    label: 'Facile',
  },
  {
    value: 'moderate',
    label: 'Modérée',
  },
  {
    value: 'hard',
    label: 'Soutenue',
  },
  {
    value: 'very_hard',
    label: 'Élevée',
  },
]


export const TRAINING_INTENSITY_LABELS:
Record<string, string> = {
  very_easy: 'Très facile',
  easy: 'Facile',
  moderate: 'Modérée',
  hard: 'Soutenue',
  very_hard: 'Élevée',

  // Compatibilité anciennes données
  'Très facile': 'Très facile',
  Facile: 'Facile',
  'Modérée': 'Modérée',
  Soutenue: 'Soutenue',
  'Élevée': 'Élevée',

  // Compatibilité anciennes décisions Coach
  recovery: 'Très facile',
}


export function formatTrainingIntensity(
  intensity: string | null | undefined,
): string {
  if (!intensity) {
    return '—'
  }

  return (
    TRAINING_INTENSITY_LABELS[intensity]
    ?? intensity
  )
}