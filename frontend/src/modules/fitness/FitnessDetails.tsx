import { MetricTooltip } from '../../components/metrics/MetricTooltip'
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
        <span
          className="
            h-8
            w-8
            animate-spin
            rounded-full
            border-[2.5px]
            border-slate-200
            border-t-emerald-500
            dark:border-white/[0.10]
            dark:border-t-emerald-400
          "
          aria-hidden="true"
        />
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
      <div
        className="
          flex
          items-center
          gap-3
          rounded-[11px]
          border
          border-rose-500/15
          bg-rose-500/[0.05]
          px-4
          py-3
          text-[11px]
          font-medium
          text-rose-700
          dark:border-rose-400/15
          dark:bg-rose-400/[0.05]
          dark:text-rose-300
        "
      >
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

      <section className="rounded-xl border border-black/[0.06] dark:border-white/[0.07]">
        <div className="grid divide-y divide-black/[0.06] dark:divide-white/[0.07] sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          <OverviewItem
            icon={Activity}
            label={
              <MetricTooltip
                metric="ctl"
                label="CTL"
              />
            }
            value={formatNumber(
              state.fitness_ctl,
            )}
            description="Charge chronique"
          />

          <OverviewItem
            icon={BatteryCharging}
            label={
              <MetricTooltip
                metric="atl"
                label="ATL"
              />
            }
            value={formatNumber(
              state.fatigue_atl,
            )}
            description="Fatigue récente"
          />

          <OverviewItem
            icon={HeartPulse}
            label={
              <MetricTooltip
                metric="tsb"
                label="Balance"
              />
            }
            value={formatNumber(
              state.training_balance,
            )}
            description="Équilibre actuel"
          />
        </div>
      </section>

      <section>
        <div className="mb-2">
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">
            Données physiologiques
          </h3>

          <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">
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
            label={
              <MetricTooltip
                metric="hrv"
                label="HRV"
              />
            }
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

      <section className="border-t border-black/[0.06] dark:border-white/[0.07] pt-5">
        <div className="mb-2">
          <h3 className="font-semibold text-slate-800 dark:text-slate-100">
            Moyennes sur 7 jours
          </h3>

          <p className="mt-0.5 text-xs text-slate-400 dark:text-slate-500">
            Comparaison de la dernière valeur disponible
            avec votre moyenne récente.
          </p>
        </div>


        <div className="rounded-xl border border-black/[0.06] dark:border-white/[0.07]">
          <TrendRow
            label="Sommeil"
            trend={trends.metrics.sleep_score}
            formatValue={(value) => `${Math.round(value)} %`}
          />

          <TrendRow
            label={
              <MetricTooltip
                metric="hrv"
                label="HRV"
              />
            }
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
            label={
              <MetricTooltip
                metric="ctl"
                label="CTL"
              />
            }
            trend={trends.metrics.fitness_ctl}
            formatValue={(value) => value.toFixed(1)}
            neutral
          />

          <TrendRow
            label={
              <MetricTooltip
                metric="atl"
                label="ATL"
              />
            }
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
  label: React.ReactNode
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
    <div className="grid grid-cols-[1fr_auto_auto] items-center gap-3 border-b border-black/[0.06] dark:border-white/[0.07] px-2 py-2 last:border-b-0">
      <div>
        <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
          {label}
        </p>

      </div>

      <div className="text-right">
        <p className="text-xs text-slate-400 dark:text-slate-500">
          Aujourd’hui
        </p>

        <p className="font-semibold text-slate-800 dark:text-slate-100">
          {current}
        </p>
      </div>

      <div className="min-w-20 text-right">
        <p className="text-xs text-slate-400 dark:text-slate-500">
          Moyenne 7 j
        </p>

        <p className="font-semibold text-slate-800 dark:text-slate-100">
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
      className: 'text-slate-400 dark:text-slate-500',
    }
  }

  if (
    trend.direction === 'stable'
  ) {
    return {
      label: '→ stable',
      className: 'text-slate-500 dark:text-slate-400',
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
      className: 'text-sky-600 dark:text-sky-400',
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
      ? 'text-emerald-600 dark:text-emerald-400'
      : 'text-amber-600 dark:text-amber-400',
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
        <div className="
          flex
          size-10
          shrink-0
          items-center
          justify-center
          rounded-[11px]
          border
          border-emerald-500/10
          bg-emerald-500/[0.07]
          text-emerald-600
          dark:border-emerald-400/10
          dark:bg-emerald-400/[0.07]
          dark:text-emerald-400
        ">
          <HeartPulse size={20} />
        </div>

        <div>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            État de forme
          </p>

          <p className="text-lg font-semibold text-slate-800 dark:text-slate-100">
            {formatReadinessLevel(
              level,
            )}
          </p>

          <p className="text-xs text-slate-400 dark:text-slate-500">
            {formatDate(
              date,
            )}
          </p>
        </div>
      </div>

      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-bold text-emerald-600 dark:text-emerald-400">
          {Math.round(
            score,
          )}
        </span>

        <span className="text-sm text-slate-400 dark:text-slate-500">
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
  label: React.ReactNode
  value: string
  description: string
}) {
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <Icon
        size={17}
        className="shrink-0 text-slate-400 dark:text-slate-500"
      />

      <div>
        <div className="flex items-baseline gap-2">
          <span className="text-lg font-bold text-slate-800 dark:text-slate-100">
            {value}
          </span>

          <span className="text-xs font-medium text-slate-500 dark:text-slate-400">
            {label}
          </span>
        </div>

        <p className="text-xs text-slate-400 dark:text-slate-500">
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
  label: React.ReactNode
  value: string
  detail: string
}) {
  return (
    <div className="
      rounded-[11px]
      border
      border-black/[0.06]
      bg-white
      px-3
      py-2.5
      dark:border-white/[0.07]
      dark:bg-[#171d21]
    ">
      <div className="flex items-center gap-2 text-slate-400 dark:text-slate-500">
        <Icon size={15} />

        <span className="text-xs font-medium">
          {label}
        </span>
      </div>

      <p className="mt-1 text-lg font-bold text-slate-800 dark:text-slate-100">
        {value}
      </p>

      <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
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
