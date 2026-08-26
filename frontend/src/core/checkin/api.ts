export type PainArea =
  | 'head'
  | 'neck'
  | 'shoulder'
  | 'back'
  | 'lower_back'
  | 'hip'
  | 'groin'
  | 'thigh'
  | 'knee'
  | 'calf'
  | 'shin'
  | 'ankle'
  | 'achilles'
  | 'foot'
  | 'other'

export type BodySide =
  | 'left'
  | 'right'
  | 'both'
  | 'center'
  | 'not_applicable'

export interface PainLocation {
  area: PainArea
  side: BodySide
}

export interface DailyCheckIn {
  id: string
  date: string
  energy_rating: number
  pain_wellness_rating: number
  illness: boolean
  unavailable: boolean
  pain_locations: PainLocation[]
  note: string | null
}

export interface AdaptationProposal {
  id: string
  checkin_id: string
  reason: string
  recommendation: string
  decision:
    | 'pending'
    | 'accepted'
    | 'declined'
  awaiting_athlete_decision: boolean
  adaptation_authorized: boolean
}

export interface DailyCheckInState {
  checkin: DailyCheckIn
  adaptation: AdaptationProposal | null
}

export interface SaveDailyCheckInPayload {
  energy_rating: number
  pain_wellness_rating: number
  illness: boolean
  unavailable: boolean
  pain_locations: PainLocation[]
  note: string | null
}

export interface AdaptedSession {
  id: string | null
  date: string
  type: string
  sport_type: string
  title: string
  description: string
  duration_minutes: number
  intensity: string
  heart_rate_zone: string | null
  status: string
}

export interface AcceptAdaptationResponse {
  proposal: AdaptationProposal
  session_adapted: boolean
  already_accepted: boolean
  adapted_session: AdaptedSession | null
  reasons: string[]
}

async function apiError(
  response: Response,
): Promise<Error> {
  let detail =
    `Erreur HTTP ${response.status}`

  try {
    const body =
      await response.json() as {
        detail?: string
      }

    if (body.detail) {
      detail = body.detail
    }
  } catch {
    // Réponse non JSON.
  }

  return new Error(
    detail,
  )
}

export async function fetchTodayCheckIn(): Promise<
  DailyCheckInState | null
> {
  const response = await fetch(
    '/api/coach/check-in/today',
  )

  if (
    response.status === 404
  ) {
    return null
  }

  if (!response.ok) {
    throw await apiError(
      response,
    )
  }

  return response.json() as Promise<DailyCheckInState>
}

export async function saveDailyCheckIn(
  payload: SaveDailyCheckInPayload,
): Promise<DailyCheckInState> {
  const response = await fetch(
    '/api/coach/check-in',
    {
      method: 'POST',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify(
        payload,
      ),
    },
  )

  if (!response.ok) {
    throw await apiError(
      response,
    )
  }

  return response.json() as Promise<DailyCheckInState>
}

export async function acceptDailyAdaptation(
  checkinId: string,
): Promise<AcceptAdaptationResponse> {
  const response = await fetch(
    (
      '/api/coach/check-in/'
      + `${checkinId}`
      + '/adaptation/accept'
    ),
    {
      method: 'POST',
    },
  )

  if (!response.ok) {
    throw await apiError(
      response,
    )
  }

  return response.json() as Promise<AcceptAdaptationResponse>
}

export async function declineDailyAdaptation(
  checkinId: string,
): Promise<AdaptationProposal> {
  const response = await fetch(
    (
      '/api/coach/check-in/'
      + `${checkinId}`
      + '/adaptation/decline'
    ),
    {
      method: 'POST',
    },
  )

  if (!response.ok) {
    throw await apiError(
      response,
    )
  }

  return response.json() as Promise<AdaptationProposal>
}
