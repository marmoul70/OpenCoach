export interface CorosConnection {
  provider: 'coros'
  configured: boolean
  connected: boolean
  enabled: boolean
  last_synced_at: string | null
  sync_interval_hours: number
  categories: Record<string, boolean>
  initial_import_months: 6
  sync_job: {
    job_id: string
    status: 'pending' | 'running' | 'success' | 'error' | 'interrupted'
    created_at: string | null
    finished_at: string | null
    result: CorosSyncResult | null
    error: string | null
    progress?: { category: string | null; next_date: string | null }
  } | null
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


export interface CorosToolProperty {
  type?: string | string[]
  description?: string
  enum?: Array<string | number | boolean>
  default?: unknown
}

export interface CorosAvailableTool {
  name: string
  description: string
  input_schema: {
    type?: string
    required?: string[]
    properties?: Record<string, CorosToolProperty>
  }
}

export interface CorosConnectionTest {
  connected: boolean
  mcp_reachable: boolean
  available_tools: CorosAvailableTool[]
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

export async function waitForCorosSync(jobId: string): Promise<CorosSyncResult> {
  const deadline = Date.now() + 10 * 60 * 1000
  while (Date.now() < deadline) {
    await new Promise(resolve => window.setTimeout(resolve, 2000))
    const job = await corosRequest<{
      status: string
      result: CorosSyncResult | null
      error: string | null
    }>(`/api/integrations/coros/sync/status/${jobId}`)
    if (job.status === 'success' && job.result) return job.result
    if (job.status === 'error') throw new Error(job.error || 'L’import COROS a échoué.')
    if (job.status === 'interrupted') throw new Error('L’import COROS a été interrompu. Relance-le pour reprendre au dernier point sauvegardé.')
  }
  throw new Error('L’import COROS est toujours en cours. Vérifie son état avant de le relancer.')
}

export async function syncCorosHistory(): Promise<CorosSyncResult> {
  const started = await corosRequest<{ job_id: string; status: string }>(
    '/api/integrations/coros/sync/start',
    { method: 'POST' },
  )
  return waitForCorosSync(started.job_id)
}
