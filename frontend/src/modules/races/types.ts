export type RaceType =
  | 'trail'
  | 'road'
  | 'ultra'
  | 'other'

export type RaceStatus =
  | 'planned'
  | 'completed'
  | 'abandoned'
  | 'not_participated'

export interface Race {
  id: string

  // Informations sur la course
  name: string
  location: string
  date: string
  type: RaceType
  distanceKm: number
  elevationGainM?: number
  targetTimeMinutes?: number

  // Résultat
  status: RaceStatus
  actualDistanceKm?: number
  actualElevationGainM?: number
  actualTimeMinutes?: number
  ranking?: number

  // Retour personnel
  notes?: string
}