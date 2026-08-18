import type {
  TrainingSession,
  TrainingSessionStatus,
} from '../../modules/training/types'

interface TrainingSessionApiResponse {
  id: string
  date: string
  type: TrainingSession['type']
  title: string
  description: string
  duration_minutes: number
  distance_km: number | null
  elevation_gain_m: number | null
  intensity: string
  heart_rate_zone: string | null
  status: TrainingSessionStatus
  activity_id: string | null
}

function mapTrainingSession(
  data: TrainingSessionApiResponse,
): TrainingSession {
  return {
    id: data.id,
    date: data.date,
    type: data.type,
    title: data.title,
    description: data.description,
    durationMinutes: data.duration_minutes,
    distanceKm: data.distance_km ?? undefined,
    elevationGainM: data.elevation_gain_m ?? undefined,
    intensity: data.intensity,
    heartRateZone: data.heart_rate_zone ?? undefined,
    status: data.status,
    activityId: data.activity_id ?? undefined,
  }
}

export async function fetchTrainingSessions(
  start: string,
  end: string,
): Promise<TrainingSession[]> {
  const params = new URLSearchParams({
    start,
    end,
  })

  const response = await fetch(
    `/api/training-sessions?${params.toString()}`,
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger les séances (${response.status}).`,
    )
  }

  const data =
    (await response.json()) as TrainingSessionApiResponse[]

  return data.map(mapTrainingSession)
}

export async function updateTrainingSessionStatus(
  sessionId: string,
  status: TrainingSessionStatus,
): Promise<TrainingSession> {
  const response = await fetch(
    `/api/training-sessions/${sessionId}/status`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        status,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de modifier la séance (${response.status}).`,
    )
  }

  const data =
    (await response.json()) as TrainingSessionApiResponse

  return mapTrainingSession(data)
}

export interface TrainingActivityCandidate {
  id: string
  provider: string
  providerActivityId: string
  name: string
  sportType: string
  startAtLocal?: string
  movingTimeSeconds?: number
  distanceM?: number
  elevationGainM?: number
  feel?: number
}

interface TrainingActivityCandidateApiResponse {
  id: string
  provider: string
  provider_activity_id: string
  name: string
  sport_type: string
  start_at_local: string | null
  moving_time_seconds: number | null
  distance_m: number | null
  elevation_gain_m: number | null
  feel: number | null
}

function mapTrainingActivityCandidate(
  data: TrainingActivityCandidateApiResponse,
): TrainingActivityCandidate {
  return {
    id: data.id,
    provider: data.provider,
    providerActivityId: data.provider_activity_id,
    name: data.name,
    sportType: data.sport_type,
    startAtLocal: data.start_at_local ?? undefined,
    movingTimeSeconds:
      data.moving_time_seconds ?? undefined,
    distanceM: data.distance_m ?? undefined,
    elevationGainM:
      data.elevation_gain_m ?? undefined,
    feel: data.feel ?? undefined,
  }
}

export async function fetchTrainingSessionActivityCandidates(
  sessionId: string,
): Promise<TrainingActivityCandidate[]> {
  const response = await fetch(
    `/api/training-sessions/${sessionId}/candidate-activities`,
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de rechercher les activités (${response.status}).`,
    )
  }

  const data =
    (await response.json()) as TrainingActivityCandidateApiResponse[]

  return data.map(mapTrainingActivityCandidate)
}

export async function updateTrainingSessionActivity(
  sessionId: string,
  activityId: string | null,
): Promise<TrainingSession> {
  const response = await fetch(
    `/api/training-sessions/${sessionId}/activity`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        activity_id: activityId,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Impossible d'associer l'activité (${response.status}).`,
    )
  }

  const data =
    (await response.json()) as TrainingSessionApiResponse

  return mapTrainingSession(data)
}