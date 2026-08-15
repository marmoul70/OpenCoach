import type { Race } from '../races/types'
import type { TrainingSession } from './types'

export interface TrainingStats {
  distanceKm: number
  completedSessions: number
  elevationGainM: number
  nextRace?: Race
}

export function getTrainingStats(
  sessions: TrainingSession[],
  races: Race[],
  today = new Date(),
): TrainingStats {
  const year = today.getFullYear()

  const completedSessions = sessions.filter(
    (session) =>
      session.status === 'completed' &&
      new Date(`${session.date}T12:00:00`).getFullYear() === year,
  )

  const distanceKm = completedSessions.reduce(
    (total, session) =>
      total + (session.distanceKm ?? 0),
    0,
  )

  const elevationGainM = completedSessions.reduce(
    (total, session) =>
      total + (session.elevationGainM ?? 0),
    0,
  )

  const nextRace = races
    .filter(
      (race) =>
        new Date(`${race.date}T12:00:00`) >= today,
    )
    .sort(
      (a, b) =>
        new Date(`${a.date}T12:00:00`).getTime() -
        new Date(`${b.date}T12:00:00`).getTime(),
    )[0]

  return {
    distanceKm,
    completedSessions: completedSessions.length,
    elevationGainM,
    nextRace,
  }
}
