export interface WeeklyDebriefHistory {
  coros_time_series: Array<{
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
  }>
  wellness_days: Array<{
    date: string
    provider: string
    resting_hr: number | null
    avg_hr: number | null
    min_hr: number | null
    max_hr: number | null
    hrv: number | null
    hrv_baseline: number | null
    stress_avg: number | null
    sleep_seconds: number | null
    sleep_score: number | null
    sleep_quality: number | null
    sleep_deep_seconds: number | null
    sleep_light_seconds: number | null
    sleep_rem_seconds: number | null
    sleep_awake_seconds: number | null
    avg_sleeping_hr: number | null
    spo2: number | null
    steps: number | null
  }>
  heart_rate_activities: Array<{
    activity_name: string
    started_at: string
    average_bpm: number | null
    maximum_bpm: number | null
    sample_count: number
    samples: Array<{ time_seconds: number; bpm: number }>
  }>
  id: string
  facts: Record<string, number | string | null>
  debrief: {
    week_start: string
    week_end: string
    verdict: string
    overall_score: number | null
    headline: string
    analysis: string
    strengths: string[]
    warnings: string[]
    completion_ratio: number | null
    duration_ratio: number | null
    load_ratio: number | null
  }
  adaptation: {
    direction: string
    reason: string
    load_factor: number
    volume_factor: number
    maximum_progression_rate: number
    intensity_policy: string
    long_run_policy: string
    strength_policy: string
    guardrails: string[]
  }
  generated_at: string
  planning_updated: boolean
}

export async function fetchWeeklyDebrief(
  weekStart: string,
): Promise<WeeklyDebriefHistory> {
  const params = new URLSearchParams({ week_start: weekStart })
  const response = await fetch(
    `/api/coach/weekly-debrief?${params.toString()}`,
  )
  if (!response.ok) {
    throw new Error(
      response.status === 404
        ? 'Aucun bilan enregistré pour cette semaine.'
        : `Impossible de charger le bilan (${response.status}).`,
    )
  }
  return await response.json() as WeeklyDebriefHistory
}

export async function applyWeeklyDebrief(
  weekStart: string,
): Promise<void> {
  const params = new URLSearchParams({ week_start: weekStart })
  const response = await fetch(
    `/api/coach/weekly-debrief/apply?${params.toString()}`,
    { method: 'POST' },
  )
  if (!response.ok) {
    const payload = await response.json().catch(() => null) as { detail?: string } | null
    throw new Error(payload?.detail ?? `Impossible d'appliquer la proposition (${response.status}).`)
  }
}
