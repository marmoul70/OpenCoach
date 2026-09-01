import {
  Activity,
  HeartPulse,
  Moon,
  TrendingUp,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

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
      <div
        className="
          flex
          min-h-48
          items-center
          justify-center
          rounded-2xl
          border
          border-black/[0.07]
          bg-white
          dark:border-white/[0.08]
          dark:bg-[#141a1e]
        "
      >
        <span
          className="
            loading
            loading-spinner
            loading-sm
            text-emerald-500
          "
        />
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
        className="
          w-full
          rounded-2xl
          border
          border-red-500/20
          bg-white
          p-5
          text-left
          dark:bg-[#141a1e]
        "
      >
        <p
          className="
            text-sm
            font-semibold
            text-red-500
          "
        >
          Données de forme indisponibles
        </p>
      </button>
    )
  }


  return (
    <button
      type="button"
      onClick={onClick}
      className="
        group
        w-full
        rounded-2xl
        border
        border-black/[0.07]
        bg-white
        p-5
        text-left
        shadow-[0_1px_2px_rgba(15,23,42,0.025)]
        transition
        duration-200
        hover:-translate-y-0.5
        hover:shadow-[0_12px_35px_rgba(15,23,42,0.055)]
        dark:border-white/[0.08]
        dark:bg-[#141a1e]
      "
    >
      <div
        className="
          flex
          items-center
          justify-between
          gap-4
        "
      >
        <div>
          <p
            className="
              text-xs
              font-semibold
              uppercase
              tracking-[0.14em]
              text-slate-400
              dark:text-slate-500
            "
          >
            Dernière mesure
          </p>

          <p
            className="
              mt-1
              text-sm
              font-medium
              text-slate-600
              dark:text-slate-300
            "
          >
            {formatDate(
              data.date,
            )}
          </p>
        </div>

        <div
          className="
            flex h-10 w-10
            items-center
            justify-center
            rounded-xl
            bg-emerald-50
            text-emerald-600
            dark:bg-emerald-500/10
            dark:text-emerald-400
          "
        >
          <Activity
            className="h-5 w-5"
          />
        </div>
      </div>


      <div
        className="
          mt-5
          grid
          grid-cols-2
          gap-x-4
          gap-y-5
        "
      >
        <Metric
          icon={
            <Moon className="h-4 w-4" />
          }
          label="Sommeil"
          value={
            data.sleep_score != null
              ? `${Math.round(
                  data.sleep_score,
                )}`
              : '—'
          }
          unit={
            data.sleep_score != null
              ? '/100'
              : undefined
          }
        />

        <Metric
          icon={
            <HeartPulse
              className="h-4 w-4"
            />
          }
          label="HRV"
          value={
            data.hrv != null
              ? `${Math.round(
                  data.hrv,
                )}`
              : '—'
          }
          unit={
            data.hrv != null
              ? 'ms'
              : undefined
          }
        />

        <Metric
          icon={
            <HeartPulse
              className="h-4 w-4"
            />
          }
          label="FC repos"
          value={
            data.resting_hr != null
              ? `${data.resting_hr}`
              : '—'
          }
          unit={
            data.resting_hr != null
              ? 'bpm'
              : undefined
          }
        />

        <Metric
          icon={
            <TrendingUp
              className="h-4 w-4"
            />
          }
          label="CTL"
          value={
            formatNumber(
              data.fitness_ctl,
            )
          }
        />
      </div>


      <div
        className="
          mt-5
          border-t
          border-black/[0.06]
          pt-4
          dark:border-white/[0.07]
        "
      >
        <span
          className="
            text-xs
            font-semibold
            text-emerald-600
            dark:text-emerald-400
          "
        >
          Voir les tendances →
        </span>
      </div>
    </button>
  )
}


function Metric({
  icon,
  label,
  value,
  unit,
}: {
  icon: React.ReactNode
  label: string
  value: string
  unit?: string
}) {
  return (
    <div>
      <div
        className="
          flex
          items-center
          gap-1.5
          text-xs
          font-medium
          text-slate-400
          dark:text-slate-500
        "
      >
        <span
          className="
            text-emerald-600
            dark:text-emerald-400
          "
        >
          {icon}
        </span>

        {label}
      </div>

      <div
        className="
          mt-1
          flex
          items-baseline
          gap-1
        "
      >
        <span
          className="
            text-2xl
            font-bold
            tracking-[-0.04em]
            tabular-nums
            text-slate-950
            dark:text-white
          "
        >
          {value}
        </span>

        {unit && (
          <span
            className="
              text-xs
              font-medium
              text-slate-400
            "
          >
            {unit}
          </span>
        )}
      </div>
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
