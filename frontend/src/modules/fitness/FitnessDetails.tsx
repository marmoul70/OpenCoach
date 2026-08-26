import {
  Activity,
  BatteryCharging,
  HeartPulse,
  Moon,
  TriangleAlert,
} from 'lucide-react'
import {
  useEffect,
  useState,
} from 'react'

import {
  fetchLatestWellness,
  fetchWellnessTrends,
  type WellnessLatest,
  type WellnessMetricTrend,
  type WellnessTrends,
} from '../../core/wellness'
import {
  fetchTodayReadiness,
  type ReadinessMetricComparison,
  type ReadinessToday,
} from '../../core/readiness'


export function FitnessDetails() {
  const [
    wellness,
    setWellness,
  ] = useState<WellnessLatest | null>(
    null,
  )

  const [
    readiness,
    setReadiness,
  ] = useState<ReadinessToday | null>(
    null,
  )


  const [
    trends,
    setTrends,
  ] = useState<WellnessTrends | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )

  useEffect(() => {
    let mounted = true

    Promise.all([
      fetchLatestWellness(),
      fetchTodayReadiness(),
      fetchWellnessTrends(7),
    ])
      .then(
        ([
          wellnessResult,
          readinessResult,
          trendsResult,
        ]) => {
          if (!mounted) {
            return
          }

          setWellness(
            wellnessResult,
          )

          setReadiness(
            readinessResult,
          )

          setTrends(
            trendsResult,
          )
        },
      )
      .catch(
        (reason: unknown) => {
          if (!mounted) {
            return
          }

          setError(
            reason instanceof Error
              ? reason.message
              : (
                'Impossible de charger '
                + 'l’état de forme.'
              ),
          )
        },
      )
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  if (loading) {
    return (
      <div className="flex min-h-56 items-center justify-center">
        <span className="loading loading-spinner loading-lg text-success" />
      </div>
    )
  }

  if (
    error
    || !wellness
    || !readiness
    || !trends
  ) {
    return (
      <div className="alert alert-error">
        <TriangleAlert className="h-5 w-5" />

        <span>
          {error ?? 'Données indisponibles.'}
        </span>
      </div>
    )
  }

  const state =
    readiness.readiness

  return (
    <div className="space-y-4">
      <FitnessHeader
        score={state.score}
        level={state.level}
        date={readiness.date}
      />

      <section className="overflow-hidden rounded-xl border border-base-300">
        <div className="grid divide-y divide-base-300 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          <OverviewItem
            icon={Activity}
            label="CTL"
            value={formatNumber(
              state.fitness_ctl,
            )}
            description="Charge chronique"
          />

          <OverviewItem
            icon={BatteryCharging}
            label="ATL"
            value={formatNumber(
              state.fatigue_atl,
            )}
            description="Fatigue récente"
          />

          <OverviewItem
            icon={HeartPulse}
            label="Balance"
            value={formatNumber(
              state.training_balance,
            )}
            description="Équilibre actuel"
          />
        </div>
      </section>

      <section>
        <div className="mb-2">
          <h3 className="font-semibold text-base-content">
            Données physiologiques
          </h3>

          <p className="mt-0.5 text-xs text-base-content/45">
            Valeurs du jour comparées à vos références personnelles.
          </p>
        </div>

        <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-4">
          <MetricCard
            icon={Moon}
            label="Sommeil"
            value={
              wellness.sleep_score != null
                ? `${Math.round(wellness.sleep_score)} %`
                : '—'
            }
            detail={comparisonText(
              readiness.comparison.sleep_score,
            )}
          />

          <MetricCard
            icon={HeartPulse}
            label="HRV"
            value={
              wellness.hrv != null
                ? `${Math.round(wellness.hrv)} ms`
                : '—'
            }
            detail={comparisonText(
              readiness.comparison.hrv,
            )}
          />

          <MetricCard
            icon={HeartPulse}
            label="FC repos"
            value={
              wellness.resting_hr != null
                ? `${wellness.resting_hr} bpm`
                : '—'
            }
            detail={comparisonText(
              readiness.comparison.resting_hr,
            )}
          />

          <MetricCard
            icon={Moon}
            label="Durée sommeil"
            value={formatSleepDuration(
              wellness.sleep_seconds,
            )}
            detail={comparisonText(
              readiness.comparison.sleep_seconds,
            )}
          />
        </div>
      </section>

      <section className="border-t border-base-300 pt-5">
        <div className="mb-2">
          <h3 className="font-semibold text-base-content">
            Moyennes sur 7 jours
          </h3>

          <p className="mt-0.5 text-xs text-base-content/45">
            Comparaison de la dernière valeur disponible
            avec votre moyenne récente.
          </p>
        </div>

        <div className="overflow-hidden rounded-xl border border-base-300">
          <TrendRow
            label="Sommeil"
            trend={trends.metrics.sleep_score}
            formatValue={(value) => `${Math.round(value)} %`}
          />

          <TrendRow
            label="HRV"
            trend={trends.metrics.hrv}
            formatValue={(value) => `${Math.round(value)} ms`}
          />

          <TrendRow
            label="FC repos"
            trend={trends.metrics.resting_hr}
            formatValue={(value) => `${Math.round(value)} bpm`}
            inverse
          />

          <TrendRow
            label="CTL"
            trend={trends.metrics.fitness_ctl}
            formatValue={(value) => value.toFixed(1)}
            neutral
          />

          <TrendRow
            label="ATL"
            trend={trends.metrics.fatigue_atl}
            formatValue={(value) => value.toFixed(1)}
            inverse
          />
        </div>
      </section>

    </div>
  )
}


function TrendRow({
  label,
  trend,
  formatValue,
  inverse = false,
  neutral = false,
}: {
  label: string
  trend: WellnessMetricTrend
  formatValue: (
    value: number,
  ) => string
  inverse?: boolean
  neutral?: boolean
}) {
  const average =
    trend.average != null
      ? formatValue(
          trend.average,
        )
      : '—'

  const current =
    trend.current != null
      ? formatValue(
          trend.current,
        )
      : '—'

  const trendDisplay =
    getTrendDisplay(
      trend,
      inverse,
      neutral,
    )

  return (
    <div className="grid grid-cols-[1fr_auto_auto] items-center gap-3 border-b border-base-300 px-2 py-2 last:border-b-0">
      <div>
        <p className="text-sm font-semibold text-base-content">
          {label}
        </p>

      </div>

      <div className="text-right">
        <p className="text-xs text-base-content/40">
          Aujourd’hui
        </p>

        <p className="font-semibold text-base-content">
          {current}
        </p>
      </div>

      <div className="min-w-20 text-right">
        <p className="text-xs text-base-content/40">
          Moyenne 7 j
        </p>

        <p className="font-semibold text-base-content">
          {average}
        </p>

        <p className={`text-xs font-medium ${trendDisplay.className}`}>
          {trendDisplay.label}
        </p>
      </div>
    </div>
  )
}


function getTrendDisplay(
  trend: WellnessMetricTrend,
  inverse: boolean,
  neutral: boolean,
): {
  label: string
  className: string
} {
  if (
    trend.direction === 'unknown'
    || trend.change_percent == null
  ) {
    return {
      label: '—',
      className: 'text-base-content/40',
    }
  }

  if (
    trend.direction === 'stable'
  ) {
    return {
      label: '→ stable',
      className: 'text-base-content/50',
    }
  }

  const arrow =
    trend.direction === 'up'
      ? '↑'
      : '↓'

  const sign =
    trend.change_percent > 0
      ? '+'
      : ''

  const label = (
    `${arrow} ${sign}`
    + `${trend.change_percent.toFixed(1)} %`
  )

  if (neutral) {
    return {
      label,
      className: 'text-info',
    }
  }

  const normallyFavorable =
    trend.direction === 'up'

  const favorable =
    inverse
      ? !normallyFavorable
      : normallyFavorable

  return {
    label,
    className: favorable
      ? 'text-success'
      : 'text-warning',
  }
}



function FitnessHeader({
  score,
  level,
  date,
}: {
  score: number
  level: string
  date: string
}) {
  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <div className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-success/10 text-success">
          <HeartPulse size={20} />
        </div>

        <div>
          <p className="text-sm text-base-content/50">
            État de forme
          </p>

          <p className="text-lg font-semibold text-base-content">
            {formatReadinessLevel(
              level,
            )}
          </p>

          <p className="text-xs text-base-content/40">
            {formatDate(
              date,
            )}
          </p>
        </div>
      </div>

      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-bold text-success">
          {Math.round(
            score,
          )}
        </span>

        <span className="text-sm text-base-content/40">
          /100
        </span>
      </div>
    </div>
  )
}


function OverviewItem({
  icon: Icon,
  label,
  value,
  description,
}: {
  icon: typeof Activity
  label: string
  value: string
  description: string
}) {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <Icon
        size={17}
        className="shrink-0 text-base-content/40"
      />

      <div>
        <div className="flex items-baseline gap-2">
          <span className="text-lg font-bold text-base-content">
            {value}
          </span>

          <span className="text-xs font-medium text-base-content/55">
            {label}
          </span>
        </div>

        <p className="text-xs text-base-content/40">
          {description}
        </p>
      </div>
    </div>
  )
}


function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
}: {
  icon: typeof HeartPulse
  label: string
  value: string
  detail: string
}) {
  return (
    <div className="rounded-xl border border-base-300 px-3 py-2.5">
      <div className="flex items-center gap-2 text-base-content/45">
        <Icon size={15} />

        <span className="text-xs font-medium">
          {label}
        </span>
      </div>

      <p className="mt-1 text-lg font-bold text-base-content">
        {value}
      </p>

      <p className="mt-1 text-xs text-base-content/45">
        {detail}
      </p>
    </div>
  )
}


function comparisonText(
  comparison: ReadinessMetricComparison,
): string {
  if (
    !comparison.reliable
    || comparison.baseline == null
  ) {
    return 'Référence personnelle insuffisante'
  }

  if (
    comparison.percent_delta
    == null
  ) {
    return 'Référence personnelle disponible'
  }

  const delta =
    comparison.percent_delta

  const sign =
    delta > 0
      ? '+'
      : ''

  return (
    `${sign}${delta.toFixed(1)} % `
    + 'vs référence'
  )
}


function formatReadinessLevel(
  level: string,
): string {
  const labels: Record<
    string,
    string
  > = {
    excellent: 'Excellent',
    good: 'Bon',
    normal: 'Normal',
    moderate: 'À surveiller',
    low: 'Récupération recommandée',
    poor: 'Récupération prioritaire',
    critical: 'Vigilance élevée',
  }

  return labels[level]
    ?? level
}




function formatSleepDuration(
  seconds: number | null,
): string {
  if (seconds == null) {
    return '—'
  }

  const totalMinutes =
    Math.round(
      seconds / 60,
    )

  const hours =
    Math.floor(
      totalMinutes / 60,
    )

  const minutes =
    totalMinutes % 60

  return (
    `${hours} h `
    + minutes
      .toString()
      .padStart(
        2,
        '0',
      )
  )
}


function formatNumber(
  value: number | null,
): string {
  return value == null
    ? '—'
    : value.toFixed(1)
}


function formatDate(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  ).format(
    new Date(
      `${value}T12:00:00`,
    ),
  )
}
