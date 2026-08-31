export interface ActivitySummary {
  id?: string

  provider: string
  provider_activity_id: string

  name: string
  sport_type: string

  start_at: string
  start_at_local?: string | null

  moving_time_seconds?: number | null
  elapsed_time_seconds?: number | null

  distance_m?: number | null
  elevation_gain_m?: number | null
}

export async function fetchActivities(): Promise<ActivitySummary[]> {
  const response = await fetch('/api/activities')

  if (!response.ok) {
    const message = await response.text()

    throw new Error(
      message || `Erreur HTTP ${response.status}`,
    )
  }

  return response.json() as Promise<ActivitySummary[]>
}
