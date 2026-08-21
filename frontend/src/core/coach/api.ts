import type {
  CoachToday,
  RecentLoadSignalKind,
  RecentLoadSignalLevel,
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

    signals: Array<{
      metric: string
      level: string
      reason: string

      current_value: number | null
      reference_value: number | null
    }>

    source_date: string
    data_age_days: number
    data_status: 'fresh' | 'stale'
  }

  decision: {
    action:
      | 'keep'
      | 'reduce'
      | 'replace'
      | 'rest'

    reason: string

    original_duration_minutes:
      number | null

    recommended_duration_minutes:
      number | null

    duration_factor:
      number | null

    intensity_factor:
      number | null

    original_intensity:
      string | null

    recommended_intensity:
      string | null

    constraints: string[]
  }

  recent_load: {
    analyzed_days: number

    planned_load_total: number
    actual_load_total: number

    load_delta_total: number
    load_ratio: number | null

    above_plan_days: number
    below_plan_days: number
    on_plan_days: number

    broken_rest_days: number
    respected_rest_days: number

    has_training_history: boolean
  } | null

  recent_load_assessment: {
    has_warning: boolean
    has_critical: boolean
    has_overload: boolean
    has_broken_rest: boolean

    signals: Array<{
      kind: RecentLoadSignalKind
      level: RecentLoadSignalLevel
      reason: string
    }>
  } | null

  data_warning: string | null
}


export class CoachTodayUnavailableError
  extends Error {
  constructor(
    message = (
      'Les données nécessaires au coach '
      + 'ne sont pas disponibles.'
    ),
  ) {
    super(message)

    this.name =
      'CoachTodayUnavailableError'
  }
}


export async function fetchCoachToday():
Promise<CoachToday> {
  const response = await fetch(
    '/api/coach/today',
    {
      headers: {
        Accept: 'application/json',
      },
    },
  )

  if (response.status === 404) {
    const detail =
      await readErrorDetail(
        response,
      )

    throw new CoachTodayUnavailableError(
      detail
      ?? (
        'Les données nécessaires au coach '
        + 'ne sont pas disponibles.'
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
      ?? (
        'Impossible de charger '
        + 'la recommandation du coach.'
      ),
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
      sourceDate:
        data.readiness.source_date,

      dataAgeDays:
        data.readiness.data_age_days,

      dataStatus:
        data.readiness.data_status,
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

    recentLoad:
      data.recent_load
        ? {
            analyzedDays:
              data.recent_load
                .analyzed_days,

            plannedLoadTotal:
              data.recent_load
                .planned_load_total,

            actualLoadTotal:
              data.recent_load
                .actual_load_total,

            loadDeltaTotal:
              data.recent_load
                .load_delta_total,

            loadRatio:
              data.recent_load
                .load_ratio
              ?? undefined,

            abovePlanDays:
              data.recent_load
                .above_plan_days,

            belowPlanDays:
              data.recent_load
                .below_plan_days,

            onPlanDays:
              data.recent_load
                .on_plan_days,

            brokenRestDays:
              data.recent_load
                .broken_rest_days,

            respectedRestDays:
              data.recent_load
                .respected_rest_days,

            hasTrainingHistory:
              data.recent_load
                .has_training_history,
          }
        : null,

    recentLoadAssessment:
      data.recent_load_assessment
        ? {
            hasWarning:
              data.recent_load_assessment
                .has_warning,

            hasCritical:
              data.recent_load_assessment
                .has_critical,

            hasOverload:
              data.recent_load_assessment
                .has_overload,

            hasBrokenRest:
              data.recent_load_assessment
                .has_broken_rest,

            signals:
              data.recent_load_assessment
                .signals
                .map(
                  (signal) => ({
                    kind:
                      signal.kind,

                    level:
                      signal.level,

                    reason:
                      signal.reason,
                  }),
                ),
          }
        : null,

    dataWarning:
      data.data_warning
      ?? undefined
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