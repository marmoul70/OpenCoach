import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  Flame,
  Footprints,
  Gauge,
  HeartPulse,
  Mountain,
  Timer,
  TrendingUp,
  Zap,
} from 'lucide-react'

import {
  fetchActivityDetail,
  type ActivityDetailResponse,
} from '../../core/activities'

interface Props {
  provider: string
  providerActivityId: string
}

type Metric = {
  label: string
  value: string
  icon: React.ReactNode
}

function collectText(value: unknown): string {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) return value.map(collectText).filter(Boolean).join('\n')
  if (value && typeof value === 'object') {
    const object = value as Record<string, unknown>
    if (typeof object.text === 'string') return object.text
    return Object.values(object).map(collectText).filter(Boolean).join('\n')
  }
  return ''
}

function capture(text: string, pattern: RegExp): string | null {
  return text.match(pattern)?.[1]?.trim() ?? null
}

function formatDuration(seconds: number | null): string {
  if (seconds == null || !Number.isFinite(seconds)) return '—'
  const total = Math.round(seconds)
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const secs = total % 60
  return hours > 0
    ? `${hours} h ${String(minutes).padStart(2, '0')} min`
    : `${minutes} min ${String(secs).padStart(2, '0')} s`
}

function formatNumber(value: number | null | undefined, digits = 0): string {
  if (value == null || !Number.isFinite(value)) return '—'
  return value.toLocaleString('fr-FR', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })
}

function DetailMetric({ label, value, icon }: Metric) {
  return (
    <div className="rounded-xl border border-black/[0.06] bg-white p-3 dark:border-white/[0.07] dark:bg-white/[0.025]">
      <div className="flex items-center gap-2 text-slate-400 dark:text-slate-500">
        <span className="text-emerald-600 dark:text-emerald-400">{icon}</span>
        <span className="text-[9px] font-semibold uppercase tracking-[0.08em]">{label}</span>
      </div>
      <p className="mt-2 text-[19px] font-bold tabular-nums text-slate-800 dark:text-slate-100">{value}</p>
    </div>
  )
}

export function ActivityDetailPanel({ provider, providerActivityId }: Props) {
  const [detail, setDetail] = useState<ActivityDetailResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setLoading(true)
    setError(null)
    fetchActivityDetail(provider, providerActivityId)
      .then(value => {
        if (active) setDetail(value)
      })
      .catch(reason => {
        if (active) setError(reason instanceof Error ? reason.message : 'Impossible de charger le détail.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [provider, providerActivityId])

  const parsed = useMemo(() => {
    if (!detail) return null
    const text = collectText(detail.coros_detail)
    const elevation = capture(text, /Elevation Gain\s*\/\s*Loss\s*:\s*([\d.]+\s*m\s*\/\s*[\d.]+\s*m)/i)
    const elevationParts = elevation?.match(/([\d.]+)\s*m\s*\/\s*([\d.]+)\s*m/i)
    const speedPace = capture(text, /Average Pace\s*:\s*([\d:]+\s*\/km)/i)
    const movingPace = capture(text, /Moving Average Pace\s*:\s*([\d:]+\s*\/km)/i)
    const adjustedPace = capture(text, /Adjusted Pace\s*:\s*([\d:]+\s*\/km)/i)
    const bestKm = capture(text, /Best Kilometer\s*:\s*([\d:]+\s*\/km)/i)
    const avgHr = capture(text, /Average Heart Rate\s*:\s*(\d+)\s*bpm/i)
    const maxHr = capture(text, /Max(?:imum)? Heart Rate\s*:\s*(\d+)\s*bpm/i)
    const cadence = capture(text, /Average Cadence\s*:\s*([\d.]+)\s*spm/i)
    const stride = capture(text, /Average Stride Length\s*:\s*([\d.]+)\s*m/i)
    const power = capture(text, /Average Power\s*:\s*([\d.]+)\s*W/i)
    const calories = capture(text, /Calories\s*:\s*(\d+)\s*kcal/i)
    const load = capture(text, /Training Load\s*:\s*([\d.]+)/i)
    const aerobic = capture(text, /Aerobic TE\s*:\s*([\d.]+)/i)
    const anaerobic = capture(text, /Anaerobic TE\s*:\s*([\d.]+)/i)
    const focus = capture(text, /Training Focus\s*:\s*([^\r\n]+)/i)
    const effort = capture(text, /Perceived Effort\s*:\s*([^\r\n]+)/i)
    return {
      text,
      elevationGain: elevationParts ? Number(elevationParts[1]) : detail.elevation_gain_m,
      elevationLoss: elevationParts ? Number(elevationParts[2]) : detail.elevation_loss_m,
      averagePace: speedPace,
      movingPace,
      adjustedPace,
      bestKm,
      averageHeartRate: avgHr ?? (detail.average_heart_rate != null ? `${Math.round(detail.average_heart_rate)} bpm` : null),
      maxHeartRate: maxHr,
      cadence: cadence ? `${cadence} ppm` : (detail.average_cadence != null ? `${Math.round(detail.average_cadence)} ppm` : null),
      stride: stride ? `${stride}` : (detail.average_stride_m != null ? formatNumber(detail.average_stride_m, 2) : null),
      power: power ? `${power} W` : (detail.average_power_w != null ? `${Math.round(detail.average_power_w)} W` : null),
      calories: calories ? `${calories} kcal` : (detail.calories != null ? `${detail.calories} kcal` : null),
      load: load ?? (detail.training_load != null ? formatNumber(detail.training_load) : null),
      aerobic,
      anaerobic,
      focus,
      effort,
    }
  }, [detail])

  if (loading) return <div className="flex min-h-48 items-center justify-center text-sm text-slate-400">Chargement des données COROS…</div>
  if (error) return <div className="rounded-xl border border-red-500/20 bg-red-500/[0.06] p-4 text-sm text-red-500">{error}</div>
  if (!detail) return null

  const dateValue = detail.start_at_local ?? detail.start_at
  const metrics: Metric[] = [
    { label: 'Distance', value: detail.distance_m != null ? `${formatNumber(detail.distance_m / 1000, 2)} km` : '—', icon: <Footprints className="h-3.5 w-3.5" /> },
    { label: 'Durée', value: formatDuration(detail.moving_time_seconds ?? detail.elapsed_time_seconds), icon: <Timer className="h-3.5 w-3.5" /> },
    { label: 'Allure moyenne', value: parsed?.averagePace ?? '—', icon: <Gauge className="h-3.5 w-3.5" /> },
    { label: 'Allure ajustée', value: parsed?.adjustedPace ?? '—', icon: <TrendingUp className="h-3.5 w-3.5" /> },
    { label: 'Dénivelé positif', value: parsed?.elevationGain != null ? `${formatNumber(parsed.elevationGain)} m` : '—', icon: <Mountain className="h-3.5 w-3.5" /> },
    { label: 'Dénivelé négatif', value: parsed?.elevationLoss != null ? `${formatNumber(parsed.elevationLoss)} m` : '—', icon: <Mountain className="h-3.5 w-3.5" /> },
    { label: 'FC moyenne', value: parsed?.averageHeartRate ?? '—', icon: <HeartPulse className="h-3.5 w-3.5" /> },
    { label: 'FC maximale', value: parsed?.maxHeartRate ?? '—', icon: <HeartPulse className="h-3.5 w-3.5" /> },
    { label: 'Puissance moyenne', value: parsed?.power ?? '—', icon: <Zap className="h-3.5 w-3.5" /> },
    { label: 'Cadence', value: parsed?.cadence ?? '—', icon: <Activity className="h-3.5 w-3.5" /> },
    { label: 'Longueur de foulée', value: parsed?.stride ? `${parsed.stride} m` : '—', icon: <Footprints className="h-3.5 w-3.5" /> },
    { label: 'Calories', value: parsed?.calories ?? '—', icon: <Flame className="h-3.5 w-3.5" /> },
    { label: 'Charge COROS', value: parsed?.load ?? '—', icon: <TrendingUp className="h-3.5 w-3.5" /> },
    { label: 'Meilleur km', value: parsed?.bestKm ?? '—', icon: <Gauge className="h-3.5 w-3.5" /> },
  ]

  return (
    <div className="space-y-4 pb-6">
      <section className="rounded-2xl border border-emerald-500/15 bg-emerald-500/[0.045] p-4">
        <p className="text-[9px] font-bold uppercase tracking-[0.12em] text-emerald-600 dark:text-emerald-400">{detail.provider.toUpperCase()} · {detail.sport_type}</p>
        <h3 className="mt-1 text-xl font-bold text-slate-900 dark:text-white">{detail.name}</h3>
        <p className="mt-1 text-xs text-slate-500">{new Intl.DateTimeFormat('fr-FR', { dateStyle: 'full', timeStyle: 'short' }).format(new Date(dateValue))}</p>
      </section>

      <section>
        <div className="mb-2 flex items-center justify-between">
          <h4 className="text-xs font-bold uppercase tracking-[0.1em] text-slate-500">Indicateurs de la séance</h4>
          {detail.coros_detail != null && <span className="rounded-full bg-emerald-500/10 px-2 py-1 text-[9px] font-semibold text-emerald-600 dark:text-emerald-400">Détail COROS</span>}
        </div>
        <div className="grid grid-cols-2 gap-2">
          {metrics.map(metric => <DetailMetric key={metric.label} {...metric} />)}
        </div>
      </section>

      {(parsed?.movingPace || parsed?.aerobic || parsed?.anaerobic || parsed?.focus || parsed?.effort) && (
        <section className="rounded-xl border border-black/[0.06] bg-white p-4 dark:border-white/[0.07] dark:bg-white/[0.025]">
          <h4 className="text-xs font-bold uppercase tracking-[0.1em] text-slate-500">Analyse de l'effort</h4>
          <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
            {parsed.movingPace && <div><p className="text-slate-400">Allure en mouvement</p><p className="mt-1 font-semibold text-slate-800 dark:text-slate-200">{parsed.movingPace}</p></div>}
            {parsed.aerobic && <div><p className="text-slate-400">Effet aérobie</p><p className="mt-1 font-semibold text-slate-800 dark:text-slate-200">{parsed.aerobic}</p></div>}
            {parsed.anaerobic && <div><p className="text-slate-400">Effet anaérobie</p><p className="mt-1 font-semibold text-slate-800 dark:text-slate-200">{parsed.anaerobic}</p></div>}
            {parsed.focus && <div><p className="text-slate-400">Objectif physiologique</p><p className="mt-1 font-semibold text-slate-800 dark:text-slate-200">{parsed.focus}</p></div>}
            {parsed.effort && <div><p className="text-slate-400">Effort perçu</p><p className="mt-1 font-semibold text-slate-800 dark:text-slate-200">{parsed.effort}</p></div>}
          </div>
        </section>
      )}

      {!detail.coros_detail && (
        <p className="rounded-xl border border-amber-500/20 bg-amber-500/[0.06] p-3 text-xs text-amber-700 dark:text-amber-300">
          Les données générales sont disponibles, mais COROS n'a pas fourni de fiche détaillée pour cette activité lors de l'import.
        </p>
      )}
    </div>
  )
}
