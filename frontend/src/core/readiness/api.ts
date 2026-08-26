export interface ReadinessMetricBaseline {
  median: number | null
  sample_count: number
  reliable: boolean
}

export interface ReadinessMetricComparison {
  current: number | null
  baseline: number | null
  absolute_delta: number | null
  percent_delta: number | null
  reliable: boolean
}

export interface ReadinessSignal {
  metric: string
  level: string
  reason: string
  current_value: number | null
  reference_value: number | null
}

export interface ReadinessToday {
  date: string
  provider: string

  baseline: {
    start_date: string
    end_date: string

    hrv: ReadinessMetricBaseline
    resting_hr: ReadinessMetricBaseline
    sleep_seconds: ReadinessMetricBaseline
    sleep_score: ReadinessMetricBaseline
  }

  comparison: {
    hrv: ReadinessMetricComparison
    resting_hr: ReadinessMetricComparison
    sleep_seconds: ReadinessMetricComparison
    sleep_score: ReadinessMetricComparison
  }

  readiness: {
    score: number
    level: string

    warning_count: number
    critical_count: number

    training_constraints: string[]

    fitness_ctl: number | null
    fatigue_atl: number | null
    training_balance: number | null

    signals: ReadinessSignal[]
  }
}

export async function fetchTodayReadiness(): Promise<ReadinessToday> {
  const response = await fetch(
    '/api/readiness/today',
  )

  if (!response.ok) {
    throw new Error(
      `Impossible de charger le Readiness (${response.status}).`,
    )
  }

  return response.json() as Promise<ReadinessToday>
}
