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


export interface ActivityDetailResponse {
  id: string
  provider: string
  provider_activity_id: string
  name: string
  sport_type: string
  start_at: string
  start_at_local: string | null
  distance_m: number | null
  elapsed_time_seconds: number | null
  moving_time_seconds: number | null
  elevation_gain_m: number | null
  elevation_loss_m: number | null
  average_heart_rate: number | null
  max_heart_rate: number | null
  average_speed_mps: number | null
  average_power_w: number | null
  average_cadence: number | null
  average_stride_m: number | null
  calories: number | null
  training_load: number | null
  coros_detail: unknown
  coros_record: Record<string, unknown> | null
}

export async function fetchActivityDetail(
  activityId: string,
): Promise<ActivityDetailResponse> {
  const response = await fetch(
    `/api/activities/${encodeURIComponent(activityId)}/detail`,
  )

  if (!response.ok) {
    const message = await response.text()
    throw new Error(message || `Erreur HTTP ${response.status}`)
  }

  return response.json() as Promise<ActivityDetailResponse>
}
