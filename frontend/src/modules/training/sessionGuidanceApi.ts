export interface SessionGuidanceIntensityTarget {
  reference: string
  label: string

  minimum: number
  maximum: number

  unit: string

  speed_min_kmh: number | null
  speed_max_kmh: number | null

  pace_fastest_seconds_per_km:
    number | null

  pace_slowest_seconds_per_km:
    number | null
}


export interface SessionGuidanceStep {
  title: string
  description: string

  duration_minutes: number | null

  intensity_target: string | null
  heart_rate_target: string | null

  intensity_targets:
    SessionGuidanceIntensityTarget[]

  repetitions: number | null

  work_distance_meters: number | null

  repetition_fast_seconds: number | null
  repetition_slow_seconds: number | null

  recovery_description:
    string | null
}


export interface SessionGuidance {
  session_type: string

  objective: string

  coach_rationale: string

  terrain_recommendation: string

  preparation: string[]

  warmup: SessionGuidanceStep[]

  main_set: SessionGuidanceStep[]

  cooldown: SessionGuidanceStep[]

  execution_advice: string[]

  warnings: string[]

  analysis_targets: string[]
}


export async function fetchSessionGuidance(
  sessionId: string,
): Promise<SessionGuidance> {
  const response = await fetch(
    (
      '/api/training-sessions/'
      + `${sessionId}/guidance`
    ),
  )

  if (!response.ok) {
    let message =
      'Impossible de charger '
      + 'les consignes de la séance.'

    try {
      const payload =
        await response.json()

      if (
        typeof payload?.detail
        === 'string'
      ) {
        message =
          payload.detail
      }
    } catch {
      // Réponse HTTP non JSON.
    }

    throw new Error(
      message
    )
  }

  return response.json() as Promise<
    SessionGuidance
  >
}
