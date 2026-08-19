import type {
  CoachToday,
} from '../../modules/coach/types'


interface CoachTodayApiResponse {
  date: string

  session: {
    id: string | null

    date: string
    type: string
    sport_type: string

    title: string
    description: string

    duration_minutes: number

    distance_km: number | null
    elevation_gain_m: number | null

    intensity: string
    heart_rate_zone: string | null

    status: string
  } | null

  readiness: {
    score: number
    level: string

    warning_count: number
    critical_count: number

    training_constraints: string[]

    signals: {
      metric: string
      level: string
      reason: string

      current_value: number | null
      reference_value: number | null
    }[]
  }

  decision: {
    action:
      | 'keep'
      | 'reduce'
      | 'replace'
      | 'rest'

    reason: string

    original_duration_minutes: number | null
    recommended_duration_minutes: number | null

    duration_factor: number | null
    intensity_factor: number | null

    original_intensity: string | null
    recommended_intensity: string | null

    constraints: string[]
  }
}


export class CoachTodayUnavailableError
  extends Error {
  constructor(
    message: string,
  ) {
    super(message)

    this.name =
      'CoachTodayUnavailableError'
  }
}


export async function fetchCoachToday(): Promise<CoachToday> {
  const response =
    await fetch(
      '/api/coach/today',
    )

  if (response.status === 404) {
    const detail =
      await readErrorDetail(
        response,
      )

    throw new CoachTodayUnavailableError(
      detail
      ?? (
        'Les données nécessaires au Coach '
        + 'ne sont pas disponibles aujourd’hui.'
      ),
    )
  }

  if (!response.ok) {
    const detail =
      await readErrorDetail(
        response,
      )

    throw new Error(
      detail
      ?? `Erreur HTTP ${response.status}`,
    )
  }

  const data = (
    await response.json()
  ) as CoachTodayApiResponse

  return {
    date:
      data.date,

    session:
      data.session
        ? {
            id:
              data.session.id
              ?? undefined,

            date:
              data.session.date,

            type:
              data.session.type,

            sportType:
              data.session.sport_type,

            title:
              data.session.title,

            description:
              data.session.description,

            durationMinutes:
              data.session.duration_minutes,

            distanceKm:
              data.session.distance_km
              ?? undefined,

            elevationGainM:
              data.session.elevation_gain_m
              ?? undefined,

            intensity:
              data.session.intensity,

            heartRateZone:
              data.session.heart_rate_zone
              ?? undefined,

            status:
              data.session.status,
          }
        : null,

    readiness: {
      score:
        data.readiness.score,

      level:
        data.readiness.level,

      warningCount:
        data.readiness.warning_count,

      criticalCount:
        data.readiness.critical_count,

      trainingConstraints:
        data.readiness
          .training_constraints,

      signals:
        data.readiness.signals.map(
          (signal) => ({
            metric:
              signal.metric,

            level:
              signal.level,

            reason:
              signal.reason,

            currentValue:
              signal.current_value
              ?? undefined,

            referenceValue:
              signal.reference_value
              ?? undefined,
          }),
        ),
    },

    decision: {
      action:
        data.decision.action,

      reason:
        data.decision.reason,

      originalDurationMinutes:
        data.decision
          .original_duration_minutes
        ?? undefined,

      recommendedDurationMinutes:
        data.decision
          .recommended_duration_minutes
        ?? undefined,

      durationFactor:
        data.decision.duration_factor
        ?? undefined,

      intensityFactor:
        data.decision.intensity_factor
        ?? undefined,

      originalIntensity:
        data.decision.original_intensity
        ?? undefined,

      recommendedIntensity:
        data.decision
          .recommended_intensity
        ?? undefined,

      constraints:
        data.decision.constraints,
    },
  }
}


async function readErrorDetail(
  response: Response,
): Promise<string | null> {
  try {
    const payload =
      (await response.json()) as {
        detail?: unknown
      }

    if (
      typeof payload.detail
      === 'string'
    ) {
      return payload.detail
    }

    return null
  } catch {
    return null
  }
}