import type {
  Race,
  RaceActivityCandidate,
  RaceActualResult,
  RacePriority,
  RaceStatus,
  RaceType,
} from '../../modules/races/types'


interface RaceActualResultApiResponse {
  source:
    | 'activity'
    | 'manual'
    | 'none'

  activity_id: string | null

  distance_km: number | null
  elevation_gain_m: number | null
  duration_minutes: number | null

  training_load: number | null
}


interface RaceApiResponse {
  id: string
  date: string

  name: string
  location: string

  race_type: RaceType
  priority: RacePriority

  distance_km: number
  elevation_gain_m: number | null
  target_time_minutes: number | null

  status: RaceStatus

  actual_distance_km: number | null
  actual_elevation_gain_m: number | null
  actual_time_minutes: number | null

  ranking: number | null
  notes: string

  activity_id: string | null

  actual_result:
    RaceActualResultApiResponse
}


interface RaceActivityCandidateApiResponse {
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


export interface RaceWritePayload {
  date: string

  name: string
  location: string

  raceType: RaceType
  priority: RacePriority

  distanceKm: number
  elevationGainM?: number
  targetTimeMinutes?: number

  status: RaceStatus

  actualDistanceKm?: number
  actualElevationGainM?: number
  actualTimeMinutes?: number

  ranking?: number
  notes?: string

  activityId?: string
}


function mapActualResult(
  data: RaceActualResultApiResponse,
): RaceActualResult {
  return {
    source:
      data.source,

    activityId:
      data.activity_id ?? undefined,

    distanceKm:
      data.distance_km ?? undefined,

    elevationGainM:
      data.elevation_gain_m ?? undefined,

    durationMinutes:
      data.duration_minutes ?? undefined,

    trainingLoad:
      data.training_load ?? undefined,
  }
}


function mapRace(
  data: RaceApiResponse,
): Race {
  return {
    id:
      data.id,

    date:
      data.date,

    name:
      data.name,

    location:
      data.location,

    type:
      data.race_type,

    priority:
      data.priority,

    distanceKm:
      data.distance_km,

    elevationGainM:
      data.elevation_gain_m ?? undefined,

    targetTimeMinutes:
      data.target_time_minutes ?? undefined,

    status:
      data.status,

    actualDistanceKm:
      data.actual_distance_km ?? undefined,

    actualElevationGainM:
      data.actual_elevation_gain_m ?? undefined,

    actualTimeMinutes:
      data.actual_time_minutes ?? undefined,

    ranking:
      data.ranking ?? undefined,

    notes:
      data.notes || undefined,

    activityId:
      data.activity_id ?? undefined,

    actualResult:
      mapActualResult(
        data.actual_result,
      ),
  }
}


function mapRaceActivityCandidate(
  data: RaceActivityCandidateApiResponse,
): RaceActivityCandidate {
  return {
    id:
      data.id,

    provider:
      data.provider,

    providerActivityId:
      data.provider_activity_id,

    name:
      data.name,

    sportType:
      data.sport_type,

    startAtLocal:
      data.start_at_local ?? undefined,

    movingTimeSeconds:
      data.moving_time_seconds ?? undefined,

    distanceM:
      data.distance_m ?? undefined,

    elevationGainM:
      data.elevation_gain_m ?? undefined,

    trainingLoad:
      data.training_load ?? undefined,

    feel:
      data.feel ?? undefined,
  }
}


function toApiPayload(
  payload: RaceWritePayload,
) {
  return {
    date:
      payload.date,

    name:
      payload.name,

    location:
      payload.location,

    race_type:
      payload.raceType,

    priority:
      payload.priority,

    distance_km:
      payload.distanceKm,

    elevation_gain_m:
      payload.elevationGainM ?? null,

    target_time_minutes:
      payload.targetTimeMinutes ?? null,

    status:
      payload.status,

    actual_distance_km:
      payload.actualDistanceKm ?? null,

    actual_elevation_gain_m:
      payload.actualElevationGainM ?? null,

    actual_time_minutes:
      payload.actualTimeMinutes ?? null,

    ranking:
      payload.ranking ?? null,

    notes:
      payload.notes ?? '',

    activity_id:
      payload.activityId ?? null,
  }
}


export async function fetchRaces(
  start?: string,
  end?: string,
): Promise<Race[]> {
  const params =
    new URLSearchParams()

  if (
    start !== undefined
    && end !== undefined
  ) {
    params.set(
      'start',
      start,
    )

    params.set(
      'end',
      end,
    )
  }

  const query =
    params.toString()

  const response = await fetch(
    query
      ? `/api/races?${query}`
      : '/api/races',
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger les courses (${response.status}).`,
    )
  }

  const data =
    await response.json() as RaceApiResponse[]

  return data.map(
    mapRace,
  )
}


export async function fetchRace(
  raceId: string,
): Promise<Race> {
  const response = await fetch(
    `/api/races/${raceId}`,
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger la course (${response.status}).`,
    )
  }

  const data =
    await response.json() as RaceApiResponse

  return mapRace(
    data,
  )
}


export async function createRace(
  payload: RaceWritePayload,
): Promise<Race> {
  const response = await fetch(
    '/api/races',
    {
      method:
        'POST',

      headers: {
        'Content-Type':
          'application/json',
      },

      body: JSON.stringify(
        toApiPayload(
          payload,
        ),
      ),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de créer la course (${response.status}).`,
    )
  }

  const data =
    await response.json() as RaceApiResponse

  return mapRace(
    data,
  )
}


export async function updateRace(
  raceId: string,
  payload: RaceWritePayload,
): Promise<Race> {
  const response = await fetch(
    `/api/races/${raceId}`,
    {
      method:
        'PUT',

      headers: {
        'Content-Type':
          'application/json',
      },

      body: JSON.stringify(
        toApiPayload(
          payload,
        ),
      ),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de modifier la course (${response.status}).`,
    )
  }

  const data =
    await response.json() as RaceApiResponse

  return mapRace(
    data,
  )
}


export async function deleteRace(
  raceId: string,
): Promise<void> {
  const response = await fetch(
    `/api/races/${raceId}`,
    {
      method:
        'DELETE',
    },
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de supprimer la course (${response.status}).`,
    )
  }
}


export async function fetchRaceActivityCandidates(
  raceId: string,
): Promise<RaceActivityCandidate[]> {
  const response = await fetch(
    `/api/races/${raceId}/candidate-activities`,
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de rechercher les activités (${response.status}).`,
    )
  }

  const data =
    await response.json() as RaceActivityCandidateApiResponse[]

  return data.map(
    mapRaceActivityCandidate,
  )
}


export async function updateRaceActivity(
  raceId: string,
  activityId?: string,
): Promise<Race> {
  const response = await fetch(
    `/api/races/${raceId}/activity`,
    {
      method:
        'PATCH',

      headers: {
        'Content-Type':
          'application/json',
      },

      body: JSON.stringify({
        activity_id:
          activityId ?? null,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Impossible d'associer l'activité (${response.status}).`,
    )
  }

  const data =
    await response.json() as RaceApiResponse

  return mapRace(
    data,
  )
}
