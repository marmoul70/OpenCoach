export interface WellnessLatest {
  provider: string
  date: string

  fitness_ctl: number | null
  fatigue_atl: number | null
  ramp_rate: number | null

  resting_hr: number | null
  hrv: number | null

  sleep_seconds: number | null
  sleep_score: number | null
  sleep_quality: number | null
  avg_sleeping_hr: number | null

  spo2: number | null
  steps: number | null

  provider_updated_at: string | null
}

export async function fetchLatestWellness(): Promise<WellnessLatest> {
  const response = await fetch('/api/wellness/latest')

  if (!response.ok) {
    throw new Error(
      `Impossible de charger le Wellness (${response.status}).`,
    )
  }

  return response.json() as Promise<WellnessLatest>
}

export type WellnessTrendDirection =
  | 'up'
  | 'down'
  | 'stable'
  | 'unknown'

export interface WellnessTrendPoint {
  date: string
  value: number
}

export interface WellnessMetricTrend {
  current: number | null
  average: number | null
  change_percent: number | null
  direction: WellnessTrendDirection
  sample_count: number
  points: WellnessTrendPoint[]
}

export interface WellnessTrends {
  start_date: string
  end_date: string
  days: number

  metrics: {
    hrv: WellnessMetricTrend
    resting_hr: WellnessMetricTrend
    sleep_score: WellnessMetricTrend
    sleep_seconds: WellnessMetricTrend
    fitness_ctl: WellnessMetricTrend
    fatigue_atl: WellnessMetricTrend
  }
}

export async function fetchWellnessTrends(
  days = 7,
): Promise<WellnessTrends> {
  const response = await fetch(
    `/api/wellness/trends?days=${days}`,
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger les tendances Wellness (${response.status}).`,
    )
  }

  return response.json() as Promise<WellnessTrends>
}
