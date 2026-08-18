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
