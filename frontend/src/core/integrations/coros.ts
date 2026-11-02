export interface CorosConnection {
  provider: 'coros'
  configured: boolean
  connected: boolean
  enabled: boolean
  last_synced_at: string | null
  sync_interval_hours: number
  categories: Record<string, boolean>
  initial_import_months: 6
}

export interface CorosSettingsUpdate {
  enabled: boolean
  sync_interval_hours: number
  categories: Record<string, boolean>
}

async function corosRequest<T>(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(input, init)

  if (!response.ok) {
    let message = `Erreur HTTP ${response.status}`
    try {
      const payload = await response.json() as { detail?: string }
      if (payload.detail) message = payload.detail
    } catch {
      // Keep the HTTP fallback.
    }
    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export function fetchCorosConnection(): Promise<CorosConnection> {
  return corosRequest<CorosConnection>(
    '/api/integrations/coros/connection',
  )
}

export function startCorosOAuth(): Promise<{ login_url: string; status: string }> {
  return corosRequest(
    '/api/integrations/coros/oauth/start',
    { method: 'POST' },
  )
}

export function pollCorosOAuth(): Promise<{ connected: boolean; status: string }> {
  return corosRequest(
    '/api/integrations/coros/oauth/poll',
    { method: 'POST' },
  )
}

export function saveCorosSettings(
  payload: CorosSettingsUpdate,
): Promise<Pick<CorosConnection, 'enabled' | 'sync_interval_hours' | 'categories'>> {
  return corosRequest(
    '/api/integrations/coros/settings',
    {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    },
  )
}


export interface CorosConnectionTest {
  connected: boolean
  mcp_reachable: boolean
  available_tools: string[]
  available_tools_count: number
}

export function testCorosConnection(): Promise<CorosConnectionTest> {
  return corosRequest('/api/integrations/coros/test', { method: 'POST' })
}


export interface CorosSyncResult {
  status: string
  start_date: string
  end_date: string
  imported_snapshots: Record<string, number>
  skipped: string[]
}

export function syncCorosHistory(): Promise<CorosSyncResult> {
  return corosRequest('/api/integrations/coros/sync', { method: 'POST' })
}
