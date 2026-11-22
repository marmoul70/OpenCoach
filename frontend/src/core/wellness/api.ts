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
  provider: string
  start_date: string
  end_date: string
  days: number

  metrics: {
    hrv: WellnessMetricTrend
    hrv_baseline: WellnessMetricTrend
    resting_hr: WellnessMetricTrend
    avg_hr: WellnessMetricTrend
    min_hr: WellnessMetricTrend
    max_hr: WellnessMetricTrend
    stress_avg: WellnessMetricTrend
    sleep_score: WellnessMetricTrend
    sleep_seconds: WellnessMetricTrend
    sleep_deep_seconds: WellnessMetricTrend
    sleep_light_seconds: WellnessMetricTrend
    sleep_rem_seconds: WellnessMetricTrend
    sleep_awake_seconds: WellnessMetricTrend
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

export interface RecoveryMetricSummary {
  current: number | null
  average: number | null
  median: number | null
  sample_count: number
  coverage_days: number
  expected_days: number
}

export interface RecoveryWindow {
  days: number
  start_date: string
  end_date: string
  recorded_days: number
  coverage_ratio: number
  metrics: Record<string, RecoveryMetricSummary>
}

export interface RecoveryTimeSeriesMetric {
  metric: string
  unit: string | null
  current: number
  average: number
  median: number
  minimum: number
  maximum: number
  sample_count: number
  coverage_days: number
  first_measured_at: string
  last_measured_at: string
  statuses: string[]
  source_categories: string[]
}

export interface RecoverySubjective {
  date: string
  fatigue: number
  pain: number
  illness_status: string
  treatment_impact: string
  motivation: number
}

export interface RecoveryAssessment {
  date: string
  provider: string
  source_date: string | null
  data_age_days: number | null
  data_status: 'fresh' | 'stale' | 'unavailable' | string
  windows: RecoveryWindow[]
  time_series: RecoveryTimeSeriesMetric[]
  subjective: RecoverySubjective | null
}

export async function fetchRecoveryAssessment(): Promise<RecoveryAssessment> {
  const response = await fetch('/api/wellness/recovery')

  if (!response.ok) {
    throw new Error(
      `Impossible de charger les données Santé (${response.status}).`,
    )
  }

  return response.json() as Promise<RecoveryAssessment>
}
