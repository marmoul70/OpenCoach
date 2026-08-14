import type { TrainingSession } from './types'

export const trainingSession: TrainingSession = {
  id: 'training-today',
  date: new Date().toISOString().slice(0, 10),
  type: 'easy',
  title: 'Endurance fondamentale',
  description:
    'Course facile en aisance respiratoire. Rester confortable et régulier pendant toute la séance.',
  durationMinutes: 50,
  distanceKm: 8,
  intensity: 'Facile',
  heartRateZone: 'Z2',
  status: 'planned',
}
