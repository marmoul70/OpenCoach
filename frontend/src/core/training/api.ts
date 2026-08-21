import type {
  TrainingAvailableActivity,
  TrainingSession,
  TrainingSessionCreate,
  TrainingSessionStatus,
  TrainingStats,
} from '../../modules/training/types'

interface TrainingSessionApiResponse {
  id: string
  date: string
  type: TrainingSession['type']
  sport_type: string
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

interface TrainingAvailableActivityApiResponse {
  id: string
  provider: string
  provider_activity_id: string
  name: string
  sport_type: string
  start_at_local: string | null
  moving_time_seconds: number | null
  distance_m: number | null
  elevation_gain_m: number | null
  training_load: number | null
  feel: number | null
}

function mapTrainingSession(
  data: TrainingSessionApiResponse,
): TrainingSession {
  return {
    id: data.id,
    date: data.date,
    type: data.type,
    sportType: data.sport_type,
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

  matchScore: number
  bestMatch: boolean

  sportMatches: boolean

  sportScore: number
  distanceScore?: number
  durationScore?: number
  elevationScore?: number
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

  match_score: number
  best_match: boolean

  sport_matches: boolean

  sport_score: number
  distance_score: number | null
  duration_score: number | null
  elevation_score: number | null
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
    distanceM:
      data.distance_m ?? undefined,
    elevationGainM:
      data.elevation_gain_m ?? undefined,
    feel:
      data.feel ?? undefined,

    matchScore:
      data.match_score,

    bestMatch:
      data.best_match,

    sportMatches:
      data.sport_matches,

    sportScore:
      data.sport_score,

    distanceScore:
      data.distance_score ?? undefined,

    durationScore:
      data.duration_score ?? undefined,

    elevationScore:
      data.elevation_score ?? undefined,
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

export async function createTrainingSession(
  session: TrainingSessionCreate,
): Promise<TrainingSession> {
  const response = await fetch(
    '/api/training-sessions',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        date: session.date,
        type: session.type,
        sport_type: session.sportType,
        title: session.title,
        description: session.description,
        duration_minutes: session.durationMinutes,
        distance_km: session.distanceKm ?? null,
        elevation_gain_m:
          session.elevationGainM ?? null,
        intensity: session.intensity,
        heart_rate_zone:
          session.heartRateZone ?? null,
        status: session.status,
        activity_id:
          session.activityId ?? null,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de créer la séance (${response.status}).`,
    )
  }

  const data =
    (await response.json()) as TrainingSessionApiResponse

  return mapTrainingSession(data)
}


export async function fetchAvailableTrainingActivities(
  date: string,
): Promise<TrainingAvailableActivity[]> {
  const params = new URLSearchParams({
    date,
  })

  const response = await fetch(
    `/api/training-sessions/available-activities?${params.toString()}`,
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger les activités disponibles (${response.status}).`,
    )
  }

  const data =
    (await response.json()) as TrainingAvailableActivityApiResponse[]

  return data.map((activity) => ({
    id: activity.id,
    provider: activity.provider,
    providerActivityId:
      activity.provider_activity_id,
    name: activity.name,
    sportType: activity.sport_type,
    startAtLocal:
      activity.start_at_local ?? undefined,
    movingTimeSeconds:
      activity.moving_time_seconds ?? undefined,
    distanceM:
      activity.distance_m ?? undefined,
    elevationGainM:
      activity.elevation_gain_m ?? undefined,
    trainingLoad:
      activity.training_load ?? undefined,
    feel:
      activity.feel ?? undefined,
  }))
}

interface TrainingStatsApiResponse {
  start_date: string
  end_date: string

  activities_count: number
  manual_sessions_count: number
  sessions_count: number

  total_duration_minutes: number
  total_distance_km: number
  total_elevation_gain_m: number

  measured_load: number
  estimated_load: number
  total_load: number
}


export async function fetchTrainingStats(
  start: string,
  end: string,
): Promise<TrainingStats> {
  const params = new URLSearchParams({
    start,
    end,
  })

  const response = await fetch(
    `/api/training-stats?${params.toString()}`,
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger les statistiques (${response.status}).`,
    )
  }

  const data =
    (await response.json()) as TrainingStatsApiResponse

  return {
    startDate:
      data.start_date,

    endDate:
      data.end_date,

    activitiesCount:
      data.activities_count,

    manualSessionsCount:
      data.manual_sessions_count,

    sessionsCount:
      data.sessions_count,

    totalDurationMinutes:
      data.total_duration_minutes,

    totalDistanceKm:
      data.total_distance_km,

    totalElevationGainM:
      data.total_elevation_gain_m,

    measuredLoad:
      data.measured_load,

    estimatedLoad:
      data.estimated_load,

    totalLoad:
      data.total_load,
  }
}
