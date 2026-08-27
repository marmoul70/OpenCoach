import {
  useEffect,
  useState,
} from 'react'

import {
  HeartPulse,
  Moon,
} from 'lucide-react'

import {
  fetchLatestWellness,
  type WellnessLatest,
} from '../../core/wellness'


interface FitnessWidgetProps {
  onClick: () => void
}


export function FitnessWidget({
  onClick,
}: FitnessWidgetProps) {
  const [
    data,
    setData,
  ] = useState<WellnessLatest | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    error,
    setError,
  ] = useState(false)

  useEffect(() => {
    let mounted = true

    fetchLatestWellness()
      .then((wellness) => {
        if (mounted) {
          setData(wellness)
        }
      })
      .catch(() => {
        if (mounted) {
          setError(true)
        }
      })
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
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body flex min-h-28 items-center justify-center p-4">
          <span className="loading loading-spinner loading-sm text-success" />
        </div>
      </div>
    )
  }

  if (
    error
    || !data
  ) {
    return (
      <button
        type="button"
        onClick={onClick}
        className="card w-full border border-error/30 bg-base-100 text-left shadow-sm"
      >
        <div className="card-body p-4">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-error">
                État de forme
              </p>

              <p className="mt-1 font-semibold text-error">
                Données indisponibles
              </p>
            </div>

            <HeartPulse className="h-4 w-4 text-error" />
          </div>
        </div>
      </button>
    )
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="card-body gap-3 p-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
              État de forme
            </p>

            <p className="mt-1 truncate text-sm text-base-content/50">
              {formatDate(
                data.date,
              )}
            </p>
          </div>

          <HeartPulse className="h-4 w-4 shrink-0 text-success" />
        </div>

        <div className="flex flex-wrap items-center gap-x-5 gap-y-2">
          <InlineMetric
            icon={
              <Moon className="h-3.5 w-3.5" />
            }
            label="Sommeil"
            value={
              data.sleep_score != null
                ? `${Math.round(data.sleep_score)}/100`
                : '—'
            }
          />

          <InlineMetric
            icon={
              <HeartPulse className="h-3.5 w-3.5" />
            }
            label="HRV"
            value={
              data.hrv != null
                ? `${Math.round(data.hrv)} ms`
                : '—'
            }
          />

          <InlineMetric
            label="FC repos"
            value={
              data.resting_hr != null
                ? `${data.resting_hr} bpm`
                : '—'
            }
          />

          <InlineMetric
            label="CTL"
            value={
              formatNumber(
                data.fitness_ctl,
              )
            }
          />
        </div>
      </div>
    </button>
  )
}


function InlineMetric({
  icon,
  label,
  value,
}: {
  icon?: React.ReactNode
  label: React.ReactNode
  value: string
}) {
  return (
    <div className="flex items-center gap-1.5 text-sm">
      {icon && (
        <span className="text-base-content/40">
          {icon}
        </span>
      )}

      <span className="text-xs text-base-content/45">
        {label}
      </span>

      <span className="font-semibold text-base-content">
        {value}
      </span>
    </div>
  )
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


function formatNumber(
  value: number | null,
): string {
  return value == null
    ? '—'
    : value.toFixed(1)
}