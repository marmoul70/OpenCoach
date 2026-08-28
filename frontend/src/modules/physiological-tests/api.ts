export type PhysiologicalTestDecision =
  | 'pending'
  | 'accepted'
  | 'declined'

export type PhysiologicalTestProtocol =
  | 'half_cooper'
  | string

export interface PhysiologicalTestProposal {
  id: string
  protocol: PhysiologicalTestProtocol
  target_metrics: string[]
  proposed_date: string
  reason: string
  recommendation: string
  replacement_stimulus: string
  target_session_id?: string | null
  decision: PhysiologicalTestDecision
}

export interface PhysiologicalTestSession {
  id: string
  date: string
  type: string
  sport_type: string
  title: string
  description: string
  duration_minutes: number
  planning_key?: string | null
  distance_km?: number | null
  elevation_gain_m?: number | null
  intensity: string
  heart_rate_zone?: string | null
  status: string
  activity_id?: string | null
}



export interface PhysiologicalTestProtocolStep {
  title: string
  description: string
  duration_minutes: number | null
}


export interface PhysiologicalTestProtocolDetails {
  protocol: string

  title: string
  short_description: string

  target_metrics: string[]

  total_duration_minutes: number

  terrain_recommendation: string

  preparation: string[]

  warmup:
    PhysiologicalTestProtocolStep[]

  test_steps:
    PhysiologicalTestProtocolStep[]

  cooldown:
    PhysiologicalTestProtocolStep[]

  execution_advice: string[]

  invalidation_reasons: string[]

  required_activity_data: string[]

  useful_activity_data: string[]

  analysis_notes: string[]
}


export interface PhysiologicalTestDecisionResult {
  proposal: PhysiologicalTestProposal
  application_status: string
  changed: boolean
  session?: PhysiologicalTestSession | null
  message: string
}


async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(
    input,
    init,
  )

  if (!response.ok) {
    let detail = ''

    try {
      const payload = await response.json()

      detail =
        typeof payload?.detail === 'string'
          ? payload.detail
          : ''
    } catch {
      detail = ''
    }

    throw new Error(
      detail
      || `Erreur HTTP ${response.status}`,
    )
  }

  return response.json() as Promise<T>
}


export async function getPendingPhysiologicalTests():
Promise<PhysiologicalTestProposal[]> {
  return request<
    PhysiologicalTestProposal[]
  >(
    '/api/coach/physiological-tests/pending',
  )
}


export async function acceptPhysiologicalTest(
  proposalId: string,
): Promise<PhysiologicalTestDecisionResult> {
  return request<
    PhysiologicalTestDecisionResult
  >(
    `/api/coach/physiological-tests/${proposalId}/accept`,
    {
      method: 'POST',
    },
  )
}


export async function declinePhysiologicalTest(
  proposalId: string,
): Promise<PhysiologicalTestDecisionResult> {
  return request<
    PhysiologicalTestDecisionResult
  >(
    `/api/coach/physiological-tests/${proposalId}/decline`,
    {
      method: 'POST',
    },
  )
}


export async function getPhysiologicalTestProtocolDetails(
  protocol: string,
): Promise<PhysiologicalTestProtocolDetails> {
  return request<
    PhysiologicalTestProtocolDetails
  >(
    (
      '/api/coach/'
      + 'physiological-tests/'
      + `protocols/${protocol}`
    ),
  )
}

