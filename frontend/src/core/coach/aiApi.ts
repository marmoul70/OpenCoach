export interface AIDataProposal {
  id: string
  field_key: string
  value: number | string | number[] | string[] | Record<string, string>
  existing_value: number | string | number[] | string[] | Record<string, string> | null
  unit: string
  status: 'pending' | 'confirmed' | 'rejected' | 'expired' | 'conflict'
  expires_at: string
}

export interface AIChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface AIRaceOption {
  race_id: string
  date: string
  name: string
  location: string | null
  race_type: string | null
  priority: string | null
  status: string | null
  distance_km: number | null
  elevation_gain_m: number | null
  target_time_minutes: number | null
}

export interface AIChatResponse {
  answer: string
  model: string
  context_used: boolean
  data_proposals: AIDataProposal[]
  race_options: AIRaceOption[]
}

async function readError(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: unknown }
    if (typeof body.detail === 'string') return body.detail
  } catch {
    // Fall through to the HTTP status.
  }
  return `Erreur HTTP ${response.status}`
}

export async function listPendingAIDataProposals(): Promise<AIDataProposal[]> {
  const response = await fetch('/api/ai/data-proposals', {
    headers: { Accept: 'application/json' },
  })
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<AIDataProposal[]>
}

export async function askAICoach(
  question: string,
  history: AIChatMessage[],
): Promise<AIChatResponse> {
  const response = await fetch('/api/ai/coach', {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question, history: history.slice(-8) }),
  })
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<AIChatResponse>
}

export async function confirmAIDataProposal(
  proposalId: string,
): Promise<AIDataProposal> {
  const response = await fetch(
    `/api/ai/data-proposals/${encodeURIComponent(proposalId)}/confirm`,
    { method: 'POST', headers: { Accept: 'application/json' } },
  )
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<AIDataProposal>
}

export async function rejectAIDataProposal(
  proposalId: string,
): Promise<AIDataProposal> {
  const response = await fetch(
    `/api/ai/data-proposals/${encodeURIComponent(proposalId)}/reject`,
    { method: 'POST', headers: { Accept: 'application/json' } },
  )
  if (!response.ok) throw new Error(await readError(response))
  return response.json() as Promise<AIDataProposal>
}
