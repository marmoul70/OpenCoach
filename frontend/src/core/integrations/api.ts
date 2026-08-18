export interface IntervalsConnection {
  provider: 'intervals'
  configured: boolean
  enabled: boolean
  athlete_id: string | null
  api_key_configured: boolean
}

export interface IntervalsConnectionUpdate {
  athlete_id: string
  api_key: string | null
  enabled: boolean
}

export interface IntervalsConnectionTestResult {
  provider: 'intervals'
  connected: boolean
  athlete_id: string
}

async function request<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(input, init)

  if (!response.ok) {
    let message = `Erreur HTTP ${response.status}`

    try {
      const payload = await response.json() as {
        detail?: string
      }

      if (payload.detail) {
        message = payload.detail
      }
    } catch {
      // Réponse non JSON : on conserve le message HTTP.
    }

    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export function fetchIntervalsConnection():
Promise<IntervalsConnection> {
  return request<IntervalsConnection>(
    '/api/integrations/intervals/connection',
  )
}

export function saveIntervalsConnection(
  payload: IntervalsConnectionUpdate,
): Promise<IntervalsConnection> {
  return request<IntervalsConnection>(
    '/api/integrations/intervals/connection',
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    },
  )
}

export function testIntervalsConnection(
  athleteId: string,
  apiKey: string,
): Promise<IntervalsConnectionTestResult> {
  return request<IntervalsConnectionTestResult>(
    '/api/integrations/intervals/connection/test',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        athlete_id: athleteId,
        api_key: apiKey,
      }),
    },
  )
}

export function testSavedIntervalsConnection():
Promise<IntervalsConnectionTestResult> {
  return request<IntervalsConnectionTestResult>(
    '/api/integrations/intervals/connection/test-saved',
    {
      method: 'POST',
    },
  )
}
