import {
  Activity,
  CalendarDays,
  CircleAlert,
  HeartPulse,
  RefreshCw,
  Waves,
} from 'lucide-react'
import {
  useEffect,
  useState,
} from 'react'

import {
  fetchRecoveryAssessment,
  type RecoveryAssessment,
  type RecoveryMetricSummary,
} from '../../core/wellness'

type WindowSize = 7 | 14 | 30

const METRICS = [
  { key: 'hrv', label: 'HRV nocturne', unit: 'ms', group: 'Récupération' },
  { key: 'hrv_baseline', label: 'Baseline HRV', unit: 'ms', group: 'Récupération' },
  { key: 'resting_hr', label: 'FC au repos', unit: 'bpm', group: 'Cardiaque' },
  { key: 'avg_hr', label: 'FC moyenne', unit: 'bpm', group: 'Cardiaque' },
  { key: 'min_hr', label: 'FC minimale', unit: 'bpm', group: 'Cardiaque' },
  { key: 'max_hr', label: 'FC maximale', unit: 'bpm', group: 'Cardiaque' },
  { key: 'avg_sleeping_hr', label: 'FC moyenne sommeil', unit: 'bpm', group: 'Cardiaque' },
  { key: 'sleep_score', label: 'Score sommeil', unit: '/100', group: 'Sommeil' },
  { key: 'sleep_seconds', label: 'Durée sommeil', unit: 'duration', group: 'Sommeil' },
  { key: 'sleep_deep_seconds', label: 'Sommeil profond', unit: 'duration', group: 'Sommeil' },
  { key: 'sleep_light_seconds', label: 'Sommeil léger', unit: 'duration', group: 'Sommeil' },
  { key: 'sleep_rem_seconds', label: 'Sommeil paradoxal', unit: 'duration', group: 'Sommeil' },
  { key: 'sleep_awake_seconds', label: 'Temps éveillé', unit: 'duration', group: 'Sommeil' },
  { key: 'stress_avg', label: 'Stress moyen', unit: 'score', group: 'Autres mesures' },
  { key: 'spo2', label: 'SpO₂', unit: '%', group: 'Autres mesures' },
  { key: 'steps', label: 'Pas', unit: 'pas', group: 'Autres mesures' },
  { key: 'fitness_ctl', label: 'CTL', unit: 'load', group: 'Charge' },
  { key: 'fatigue_atl', label: 'ATL', unit: 'load', group: 'Charge' },
] as const

const GROUPS = [
  'Récupération',
  'Cardiaque',
  'Sommeil',
  'Autres mesures',
  'Charge',
] as const

const SERIES_LABELS: Record<string, string> = {
  sleep_hrv: 'HRV nocturne',
  heart_rate: 'Fréquence cardiaque',
  stress: 'Stress',
  spo2: 'SpO₂',
  respiration_rate: 'Fréquence respiratoire',
  temperature: 'Température',
}

export function HealthPage() {
  const [assessment, setAssessment] = useState<RecoveryAssessment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [windowSize, setWindowSize] = useState<WindowSize>(7)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(null)

    fetchRecoveryAssessment()
      .then((result) => {
        if (mounted) setAssessment(result)
      })
      .catch((reason: unknown) => {
        if (mounted) {
          setError(
            reason instanceof Error
              ? reason.message
              : 'Impossible de charger les données Santé.',
          )
        }
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })

    return () => {
      mounted = false
    }
  }, [refreshKey])

  const selectedWindow = assessment?.windows.find(
    (item) => item.days === windowSize,
  )

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <div className="flex items-center gap-2 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
              <HeartPulse className="h-4 w-4" />
              SANTÉ & RÉCUPÉRATION
            </div>
            <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-950 dark:text-white sm:text-3xl">
              Suivi physiologique
            </h1>
            <p className="mt-1 max-w-2xl text-sm text-slate-500 dark:text-slate-400">
              Historique COROS, sommeil, fréquence cardiaque, HRV et charge d’entraînement.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setRefreshKey((value) => value + 1)}
            disabled={loading}
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-[#141a1e] dark:text-slate-200 dark:hover:bg-white/5"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Actualiser
          </button>
        </header>

        {loading && (
          <div className="flex min-h-64 items-center justify-center rounded-2xl border border-slate-200 bg-white dark:border-white/10 dark:bg-[#141a1e]">
            <RefreshCw className="h-7 w-7 animate-spin text-emerald-500" />
          </div>
        )}

        {!loading && error && (
          <div className="flex items-start gap-3 rounded-2xl border border-rose-500/20 bg-rose-500/5 p-5 text-sm text-rose-700 dark:text-rose-300">
            <CircleAlert className="mt-0.5 h-5 w-5 shrink-0" />
            <div>
              <p className="font-semibold">Données Santé indisponibles</p>
              <p className="mt-1">{error}</p>
              <p className="mt-2 text-xs opacity-80">
                Vérifie la connexion et l’authentification à l’API OpenCoach.
              </p>
            </div>
          </div>
        )}

        {!loading && !error && assessment && (
          <>
            <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              <StatusCard
                label="Source"
                value={assessment.provider.toUpperCase()}
                detail="Fournisseur des données quotidiennes"
                icon={<Activity className="h-5 w-5" />}
              />
              <StatusCard
                label="Dernière journée"
                value={assessment.source_date ? formatDate(assessment.source_date) : 'Aucune'}
                detail={statusLabel(assessment.data_status, assessment.data_age_days)}
                icon={<CalendarDays className="h-5 w-5" />}
              />
              <StatusCard
                label="Jours enregistrés · 30 j"
                value={String(assessment.windows.find((item) => item.days === 30)?.recorded_days ?? 0)}
                detail="Journées avec au moins une mesure"
                icon={<HeartPulse className="h-5 w-5" />}
              />
              <StatusCard
                label="Mesures détaillées"
                value={String(assessment.time_series.reduce((total, item) => total + item.sample_count, 0))}
                detail="Échantillons COROS sur 30 jours"
                icon={<Waves className="h-5 w-5" />}
              />
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#141a1e] sm:p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                    Historique quotidien
                  </h2>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                    Valeur la plus récente disponible et statistiques sur la période.
                  </p>
                </div>
                <div className="inline-flex w-fit rounded-xl bg-slate-100 p-1 dark:bg-white/5" aria-label="Période d’historique">
                  {([7, 14, 30] as const).map((days) => (
                    <button
                      key={days}
                      type="button"
                      onClick={() => setWindowSize(days)}
                      aria-pressed={windowSize === days}
                      className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${windowSize === days ? 'bg-white text-emerald-700 shadow-sm dark:bg-[#263238] dark:text-emerald-300' : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'}`}
                    >
                      {days} j
                    </button>
                  ))}
                </div>
              </div>

              {selectedWindow && (
                <>
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-3 text-xs dark:bg-white/[0.035]">
                    <span className="text-slate-600 dark:text-slate-300">
                      {formatDate(selectedWindow.start_date)} – {formatDate(selectedWindow.end_date)}
                    </span>
                    <span className="font-semibold tabular-nums text-slate-700 dark:text-slate-200">
                      {selectedWindow.recorded_days}/{selectedWindow.days} jours couverts · {Math.round(selectedWindow.coverage_ratio * 100)} %
                    </span>
                  </div>

                  <div className="mt-5 space-y-6">
                    {GROUPS.map((group) => {
                      const items = METRICS.filter((metric) => metric.group === group)
                      return (
                        <div key={group}>
                          <h3 className="mb-3 text-sm font-semibold text-slate-700 dark:text-slate-200">{group}</h3>
                          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-3">
                            {items.map((metric) => (
                              <MetricTile
                                key={metric.key}
                                label={metric.label}
                                unit={metric.unit}
                                metric={selectedWindow.metrics[metric.key]}
                              />
                            ))}
                          </div>
                        </div>
                      )
                    })}
                  </div>
                </>
              )}
            </section>

            <section className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#141a1e] sm:p-5">
              <div className="flex items-center gap-2">
                <Waves className="h-5 w-5 text-sky-600 dark:text-sky-400" />
                <div>
                  <h2 className="text-lg font-semibold text-slate-900 dark:text-white">Séries physiologiques COROS</h2>
                  <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Statistiques calculées à partir des échantillons horodatés sur les 30 derniers jours.</p>
                </div>
              </div>

              {assessment.time_series.length === 0 ? (
                <p className="mt-4 rounded-xl bg-slate-50 p-4 text-sm text-slate-500 dark:bg-white/[0.035] dark:text-slate-400">
                  Aucune série détaillée disponible sur cette période. Les données quotidiennes restent consultables ci-dessus.
                </p>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {assessment.time_series.map((series) => (
                    <div key={`${series.metric}-${series.unit ?? 'none'}`} className="rounded-xl border border-slate-200 p-4 dark:border-white/10">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                          {SERIES_LABELS[series.metric] ?? series.metric.replaceAll('_', ' ')}
                        </h3>
                        <span className="rounded-md bg-slate-100 px-2 py-1 text-[10px] font-semibold uppercase text-slate-500 dark:bg-white/5 dark:text-slate-400">
                          {series.sample_count} mesures
                        </span>
                      </div>
                      <p className="mt-3 text-2xl font-bold tabular-nums text-slate-950 dark:text-white">
                        {formatNumber(series.current)} <span className="text-xs font-medium text-slate-400">{series.unit ?? ''}</span>
                      </p>
                      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                        <MiniValue label="Moyenne" value={formatNumber(series.average)} />
                        <MiniValue label="Minimum" value={formatNumber(series.minimum)} />
                        <MiniValue label="Maximum" value={formatNumber(series.maximum)} />
                      </div>
                      <p className="mt-3 text-[11px] text-slate-400 dark:text-slate-500">
                        {series.coverage_days} jours couverts · {formatDateTime(series.first_measured_at)} au {formatDateTime(series.last_measured_at)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {assessment.subjective && (
              <section className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#141a1e]">
                <h2 className="text-base font-semibold text-slate-900 dark:text-white">Ressenti du jour</h2>
                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-5">
                  <MiniValue label="Fatigue" value={String(assessment.subjective.fatigue) + '/5'} />
                  <MiniValue label="Douleur" value={String(assessment.subjective.pain) + '/5'} />
                  <MiniValue label="Motivation" value={String(assessment.subjective.motivation) + '/5'} />
                  <MiniValue label="État" value={assessment.subjective.illness_status} />
                  <MiniValue label="Traitement" value={assessment.subjective.treatment_impact} />
                </div>
              </section>
            )}

            <p className="text-xs leading-relaxed text-slate-400 dark:text-slate-500">
              Les valeurs absentes sont affichées « — » et ne sont jamais remplacées par zéro. Ces indicateurs décrivent les mesures enregistrées ; ils ne constituent pas un diagnostic médical et ne modifient pas automatiquement le score Readiness.
            </p>
          </>
        )}
      </div>
    </main>
  )
}

function StatusCard({
  label,
  value,
  detail,
  icon,
}: {
  label: string
  value: string
  detail: string
  icon: React.ReactNode
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-white/10 dark:bg-[#141a1e]">
      <div className="flex items-center justify-between text-slate-400">
        <span className="text-xs font-medium">{label}</span>
        {icon}
      </div>
      <p className="mt-3 truncate text-xl font-bold text-slate-950 dark:text-white">{value}</p>
      <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{detail}</p>
    </div>
  )
}

function MetricTile({
  label,
  unit,
  metric,
}: {
  label: string
  unit: string
  metric: RecoveryMetricSummary | undefined
}) {
  const value = metric?.current
  return (
    <div className="rounded-xl border border-slate-200 p-3 dark:border-white/10">
      <p className="text-xs font-medium text-slate-500 dark:text-slate-400">{label}</p>
      <p className="mt-1 text-xl font-bold tabular-nums text-slate-950 dark:text-white">
        {value == null ? '—' : formatMetric(value, unit)}
      </p>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-slate-400 dark:text-slate-500">
        <span>Moy. {metric?.average == null ? '—' : formatMetric(metric.average, unit)}</span>
        <span>{metric?.sample_count ?? 0} mesures</span>
        <span>{metric?.coverage_days ?? 0} j couverts</span>
      </div>
    </div>
  )
}

function MiniValue({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-slate-400 dark:text-slate-500">{label}</p>
      <p className="mt-0.5 text-sm font-semibold text-slate-700 dark:text-slate-200">{value}</p>
    </div>
  )
}

function formatMetric(value: number, unit: string): string {
  if (unit === 'duration') return formatDuration(value)
  if (unit === 'pas') return Math.round(value).toLocaleString('fr-FR')
  if (unit === 'load') return value.toFixed(1)
  return `${Number.isInteger(value) ? value : value.toFixed(1)} ${unit}`.trim()
}

function formatDuration(seconds: number): string {
  const totalMinutes = Math.round(seconds / 60)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours} h ${String(minutes).padStart(2, '0')}`
}

function formatNumber(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(1)
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(`${value}T12:00:00`))
}

function formatDateTime(value: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function statusLabel(status: string, age: number | null): string {
  if (status === 'fresh') return 'Données du jour disponibles'
  if (status === 'stale') return `Dernière donnée : J-${age ?? '?'}`
  return 'Aucune donnée quotidienne disponible'
}
