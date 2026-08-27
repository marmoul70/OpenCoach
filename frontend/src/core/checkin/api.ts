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

export interface ReschedulingProposal {
  suggested_date: string
  requires_confirmation: boolean
  reasons: string[]
}

export interface RescheduledSession {
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

export interface AcceptReschedulingResponse {
  created: boolean
  already_rescheduled: boolean
  source_session_id: string
  rescheduled_session: RescheduledSession
}

export type ReplanningAction =
  | 'cancel'
  | 'move_unchanged'
  | 'move_adapted'


export type ReplanningRisk =
  | 'low'
  | 'moderate'
  | 'high'


export interface ReplanningSession {
  id: string | null
  date: string
  type: string
  sport_type: string
  title: string
  description: string
  duration_minutes: number
  distance_km?: number | null
  elevation_gain_m?: number | null
  intensity: string
  heart_rate_zone: string | null
  status: string
}


export interface ReplanningOption {
  action: ReplanningAction
  target_date: string | null
  risk: ReplanningRisk
  recommended: boolean
  globally_recommended?: boolean
  requires_confirmation: boolean
  reasons: string[]
  session: ReplanningSession | null
}


export interface ReplanningProposal {
  source_session: ReplanningSession
  recommended_action: ReplanningAction
  recommended_target_date: string | null
  options: ReplanningOption[]
}


export interface DailyReplanningState {
  checkin_id: string
  date: string
  coordination_reasons: string[]
  proposals: ReplanningProposal[]
}


export interface ApplyReplanningResponse {
  source_session_id: string | null
  action: ReplanningAction
  created: boolean
  cancelled: boolean
  already_applied: boolean
  applied_session: ReplanningSession | null
}


export interface AcceptAdaptationResponse {
  proposal: AdaptationProposal
  session_adapted: boolean
  already_accepted: boolean
  adapted_session: AdaptedSession | null
  reasons: string[]
  rescheduling_proposal: ReschedulingProposal | null
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

export async function acceptDailyRescheduling(
  checkinId: string,
  sourceSessionId: string,
): Promise<AcceptReschedulingResponse> {
  const response = await fetch(
    (
      '/api/coach/check-in/'
      + `${checkinId}`
      + '/rescheduling/accept'
    ),
    {
      method: 'POST',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        source_session_id:
          sourceSessionId,
      }),
    },
  )

  if (!response.ok) {
    throw await apiError(
      response,
    )
  }

  return response.json() as Promise<
    AcceptReschedulingResponse
  >
}


export async function fetchDailyReplanning(
  checkinId: string,
): Promise<DailyReplanningState> {
  const response = await fetch(
    (
      '/api/coach/check-in/'
      + `${checkinId}`
      + '/replanning'
    ),
  )

  if (!response.ok) {
    throw await apiError(
      response,
    )
  }

  return response.json() as Promise<
    DailyReplanningState
  >
}


export async function applyDailyReplanning(
  checkinId: string,
  input: {
    source_session_id: string
    action: ReplanningAction
    target_date: string | null
  },
): Promise<ApplyReplanningResponse> {
  const response = await fetch(
    (
      '/api/coach/check-in/'
      + `${checkinId}`
      + '/replanning/apply'
    ),
    {
      method: 'POST',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify(
        input,
      ),
    },
  )

  if (!response.ok) {
    throw await apiError(
      response,
    )
  }

  return response.json() as Promise<
    ApplyReplanningResponse
  >
}
