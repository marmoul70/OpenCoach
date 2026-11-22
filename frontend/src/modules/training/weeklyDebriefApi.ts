export interface WeeklyDebriefHistory {
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
