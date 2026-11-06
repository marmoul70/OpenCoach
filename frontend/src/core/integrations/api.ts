export interface IntervalsConnection {
  provider: 'intervals'
  configured: boolean
  enabled: boolean
  athlete_id: string | null
  api_key_configured: boolean
  web_cookie_configured: boolean
  web_cookie_hint: string | null
  last_synced_at: string | null
}

export interface IntervalsConnectionUpdate {
  athlete_id: string
  api_key: string | null
  web_cookie: string | null
  enabled: boolean
}

export interface IntervalsConnectionTestResult {
  provider: 'intervals'
  connected: boolean
  athlete_id: string
}

export interface IntervalsSyncResult {
  provider: 'intervals'
  synced_activities: number
  synced_wellness_days: number
  days: number
  synced_at: string
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
  webCookie?: string,
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
        web_cookie: webCookie?.trim() || null,
      }),
    },
  )
}

export function testSavedIntervalsConnection(
  webCookie?: string,
): Promise<IntervalsConnectionTestResult> {
  return request<IntervalsConnectionTestResult>(
    '/api/integrations/intervals/connection/test-saved',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        web_cookie: webCookie?.trim() || null,
      }),
    },
  )
}

export interface IntervalsInitialSyncJob {
  job_id: string
  status:
    | 'pending'
    | 'running'
    | 'success'
    | 'error'
}


export interface IntervalsInitialSyncStatus
  extends IntervalsInitialSyncJob {
  synced_activities: number
  synced_wellness_days: number
  days: number
  error: string | null
}


export function startInitialSync():
Promise<IntervalsInitialSyncJob> {
  return request<IntervalsInitialSyncJob>(
    '/api/integrations/intervals/sync/initial/start',
    {
      method: 'POST',
    },
  )
}


export function fetchInitialSyncStatus(
  jobId: string,
): Promise<IntervalsInitialSyncStatus> {
  return request<IntervalsInitialSyncStatus>(
    (
      '/api/integrations/intervals/'
      + `sync/initial/status/${jobId}`
    ),
  )
}


export function syncIntervals(
  days = 7,
): Promise<IntervalsSyncResult> {
  return request<IntervalsSyncResult>(
    `/api/integrations/intervals/sync?days=${days}`,
    {
      method: 'POST',
    },
  )
}