import type { TrainingSession } from './types'

function dateAtOffset(offset: number): string {
  const date = new Date()
  date.setDate(date.getDate() + offset)

  return date.toISOString().slice(0, 10)
}

export const trainingSessions: TrainingSession[] = [
  {
    id: 'training-monday',
    date: dateAtOffset(-3),
    type: 'rest',
    title: 'Repos',
    description:
      'Journée de récupération. Aucun entraînement prévu.',
    durationMinutes: 0,
    intensity: 'Repos',
    status: 'completed',
  },
  {
    id: 'training-tuesday',
    date: dateAtOffset(-2),
    type: 'easy',
    title: 'Endurance fondamentale',
    description:
      'Course facile en aisance respiratoire. Rester confortable et régulier pendant toute la séance.',
    durationMinutes: 50,
    distanceKm: 8,
    elevationGainM: 100,
    intensity: 'Facile',
    heartRateZone: 'Z2',
    status: 'completed',
  },
  {
    id: 'training-wednesday',
    date: dateAtOffset(-1),
    type: 'recovery',
    title: 'Récupération',
    description:
      'Footing très léger destiné à favoriser la récupération.',
    durationMinutes: 40,
    distanceKm: 6,
    elevationGainM: 50,
    intensity: 'Très facile',
    heartRateZone: 'Z1-Z2',
    status: 'completed',
  },
  {
    id: 'training-thursday',
    date: dateAtOffset(0),
    type: 'interval',
    title: 'VMA courte',
    description:
      'Séance de fractionné destinée à travailler la vitesse maximale aérobie.',
    durationMinutes: 55,
    distanceKm: 8,
    elevationGainM: 80,
    intensity: 'Soutenue',
    heartRateZone: 'Z4-Z5',
    status: 'planned',
  },
  {
    id: 'training-friday',
    date: dateAtOffset(1),
    type: 'rest',
    title: 'Repos',
    description:
      'Journée sans entraînement pour assimiler la charge.',
    durationMinutes: 0,
    intensity: 'Repos',
    status: 'planned',
  },
  {
    id: 'training-saturday',
    date: dateAtOffset(2),
    type: 'trail',
    title: 'Sortie longue trail',
    description:
      'Sortie longue sur terrain vallonné avec travail de l’endurance spécifique trail.',
    durationMinutes: 135,
    distanceKm: 18,
    elevationGainM: 850,
    intensity: 'Modérée',
    heartRateZone: 'Z2-Z3',
    status: 'planned',
  },
  {
    id: 'training-sunday',
    date: dateAtOffset(3),
    type: 'easy',
    title: 'Endurance',
    description:
      'Footing d’endurance à intensité confortable.',
    durationMinutes: 60,
    distanceKm: 9,
    elevationGainM: 120,
    intensity: 'Facile',
    heartRateZone: 'Z2',
    status: 'planned',
  },
]

export const trainingSession = trainingSessions[3]