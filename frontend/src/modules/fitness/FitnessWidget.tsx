import { useEffect, useState } from 'react'
import {
  Footprints,
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
  const [data, setData] = useState<WellnessLatest | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)

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

  return (
    <button
      type="button"
      onClick={onClick}
      className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="card-body p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-success/10">
              <HeartPulse className="h-5 w-5 text-success" />
            </div>

            <div>
              <p className="text-sm font-medium text-base-content/60">
                État de forme
              </p>

              <p className="mt-1 text-sm text-base-content/40">
                {data
                  ? formatDate(data.date)
                  : 'Dernières données disponibles'}
              </p>
            </div>
          </div>

          {loading && (
            <span className="loading loading-spinner loading-sm" />
          )}
        </div>

        {!loading && error && (
          <div className="mt-5 text-sm text-error">
            Données indisponibles
          </div>
        )}

        {!loading && !error && data && (
          <>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <Metric
                icon={<Moon className="h-4 w-4" />}
                label="Sommeil"
                value={
                  data.sleep_score != null
                    ? `${Math.round(data.sleep_score)}/100`
                    : '—'
                }
              />

              <Metric
                icon={<HeartPulse className="h-4 w-4" />}
                label="HRV"
                value={
                  data.hrv != null
                    ? `${Math.round(data.hrv)} ms`
                    : '—'
                }
              />

              <Metric
                icon={<HeartPulse className="h-4 w-4" />}
                label="FC repos"
                value={
                  data.resting_hr != null
                    ? `${data.resting_hr} bpm`
                    : '—'
                }
              />

              <Metric
                icon={<Footprints className="h-4 w-4" />}
                label="Pas"
                value={
                  data.steps != null
                    ? data.steps.toLocaleString('fr-FR')
                    : '—'
                }
              />
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2">
              <SmallMetric
                label="CTL"
                value={formatNumber(data.fitness_ctl)}
              />

              <SmallMetric
                label="ATL"
                value={formatNumber(data.fatigue_atl)}
              />

              <SmallMetric
                label="Ramp"
                value={formatRamp(data.ramp_rate)}
              />
            </div>

            <div className="mt-4 flex items-center justify-between">
              <span className="text-xs text-base-content/50">
                SpO₂ {formatSpo2(data.spo2)}
              </span>

              <span className="text-sm font-medium text-success">
                Voir →
              </span>
            </div>
          </>
        )}
      </div>
    </button>
  )
}


interface MetricProps {
  icon: React.ReactNode
  label: string
  value: string
}


function Metric({
  icon,
  label,
  value,
}: MetricProps) {
  return (
    <div className="rounded-xl bg-base-200 p-3">
      <div className="flex items-center gap-1.5 text-base-content/50">
        {icon}

        <span className="text-xs">
          {label}
        </span>
      </div>

      <p className="mt-1 text-lg font-semibold text-base-content">
        {value}
      </p>
    </div>
  )
}


function SmallMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-lg border border-base-300 p-2 text-center">
      <p className="text-xs text-base-content/50">
        {label}
      </p>

      <p className="mt-1 font-semibold">
        {value}
      </p>
    </div>
  )
}


function formatDate(value: string): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  ).format(new Date(`${value}T12:00:00`))
}


function formatNumber(
  value: number | null,
): string {
  return value == null
    ? '—'
    : value.toFixed(1)
}


function formatRamp(
  value: number | null,
): string {
  if (value == null) {
    return '—'
  }

  return `${value > 0 ? '+' : ''}${value.toFixed(1)}`
}


function formatSpo2(
  value: number | null,
): string {
  return value == null
    ? '—'
    : `${Math.round(value)} %`
}