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
  fetchWellnessTrends,
  type RecoveryAssessment,
  type RecoveryMetricSummary,
  type WellnessMetricTrend,
  type WellnessTrends,
} from '../../core/wellness'

import { LineChart } from '../../design-system/charts/LineChart'
import { PageHeader } from '../../design-system/components/PageHeader'

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
  const [trends, setTrends] = useState<WellnessTrends | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [windowSize, setWindowSize] = useState<WindowSize>(7)
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    let mounted = true
    setLoading(true)
    setError(null)

    fetchRecoveryAssessment()
      .then(async (assessmentResult) => {
        const trendsResult = await fetchWellnessTrends(
          30,
          assessmentResult.provider === 'intervals' ? 'intervals' : 'coros',
        )
        if (mounted) {
          setAssessment(assessmentResult)
          setTrends(trendsResult)
        }
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
    <main className="oc-app-shell min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-6">
        <PageHeader
          eyebrow={<><HeartPulse className="h-4 w-4" /> Santé & récupération</>}
          title="Suivi physiologique"
          description="Historique COROS, sommeil, fréquence cardiaque, HRV et charge d’entraînement."
          actions={
            <button
              type="button"
              onClick={() => setRefreshKey((value) => value + 1)}
              disabled={loading}
              className="inline-flex min-h-10 items-center justify-center gap-2 rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface)] px-4 text-sm font-semibold text-[var(--oc-text-secondary)] transition hover:bg-[var(--oc-surface-hover)] disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
              Actualiser
            </button>
          }
        />

        {loading && (
          <div className="flex min-h-64 items-center justify-center oc-surface">
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

        {!loading && !error && assessment && trends && (
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

            <section className="oc-surface p-4 sm:p-5">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="oc-type-section-title text-[var(--oc-text)]">
                    Historique quotidien
                  </h2>
                  <p className="mt-1 oc-type-secondary">
                    Valeur la plus récente disponible et statistiques sur la période.
                  </p>
                </div>
                <div className="inline-flex w-fit rounded-xl bg-[var(--oc-surface-muted)] p-1" aria-label="Période d’historique">
                  {([7, 14, 30] as const).map((days) => (
                    <button
                      key={days}
                      type="button"
                      onClick={() => setWindowSize(days)}
                      aria-pressed={windowSize === days}
                      className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${windowSize === days ? 'bg-[var(--oc-surface)] text-emerald-700 shadow-sm ring-1 ring-[var(--oc-border)] dark:text-emerald-300' : 'text-[var(--oc-muted)] hover:text-[var(--oc-text)]'}`}
                    >
                      {days} j
                    </button>
                  ))}
                </div>
              </div>

              {selectedWindow && (
                <>
                  <div className="mt-4 flex flex-wrap items-center justify-between gap-2 rounded-xl bg-[var(--oc-surface-muted)] px-3 py-3 oc-type-secondary">
                    <span className="text-[var(--oc-text-secondary)]">
                      {formatDate(selectedWindow.start_date)} – {formatDate(selectedWindow.end_date)}
                    </span>
                    <span className="font-semibold tabular-nums text-[var(--oc-text-secondary)]">
                      {selectedWindow.recorded_days}/{selectedWindow.days} jours couverts · {Math.round(selectedWindow.coverage_ratio * 100)} %
                    </span>
                  </div>

                  <div className="mt-5 space-y-6">
                    {GROUPS.map((group) => {
                      const items = METRICS.filter((metric) => metric.group === group)
                      return (
                        <section key={group} className="rounded-2xl border border-[var(--oc-border)] bg-[var(--oc-surface-raised)] p-4 shadow-sm sm:p-5">
                          <div className="mb-4 flex items-center justify-between gap-3">
                            <h3 className="oc-type-section-title font-semibold text-[var(--oc-text)]">{group}</h3>
                            <span className="rounded-full bg-[var(--oc-accent-soft)] px-2.5 py-1 text-[11px] font-semibold text-[var(--oc-accent)]">{items.length} indicateurs</span>
                          </div>
                          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-2">
                            {items.map((metric) => (
                              <MetricTile
                                key={metric.key}
                                label={metric.label}
                                unit={metric.unit}
                                metric={selectedWindow.metrics[metric.key]}
                              />
                            ))}
                          </div>
                        </section>
                      )
                    })}
                  </div>
                </>
              )}
            </section>


            <section className="oc-surface p-4 sm:p-5">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <h2 className="oc-type-section-title text-[var(--oc-text)]">Évolution des indicateurs</h2>
                  <p className="mt-1 oc-type-secondary">
                    Tendances quotidiennes issues du même fournisseur que les données Wellness.
                  </p>
                </div>
                <span className="text-xs text-[var(--oc-muted)]">
                  Source : {trends.provider.toUpperCase()} · {windowSize} derniers jours
                </span>
              </div>
              <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                <TrendChart title="HRV nocturne" unit="ms" trend={trends.metrics.hrv} days={windowSize} endDate={trends.end_date} />
                <TrendChart title="Fréquence cardiaque au repos" unit="bpm" trend={trends.metrics.resting_hr} days={windowSize} endDate={trends.end_date} />
                <TrendChart title="Score de sommeil" unit="/100" trend={trends.metrics.sleep_score} days={windowSize} endDate={trends.end_date} />
                <TrendChart title="Durée du sommeil" unit="duration" trend={trends.metrics.sleep_seconds} days={windowSize} endDate={trends.end_date} />
                <TrendChart title="Charge chronique · CTL" unit="load" trend={trends.metrics.fitness_ctl} days={windowSize} endDate={trends.end_date} />
                <TrendChart title="Charge aiguë · ATL" unit="load" trend={trends.metrics.fatigue_atl} days={windowSize} endDate={trends.end_date} />
                <TrendChart title="Stress moyen" unit="score" trend={trends.metrics.stress_avg} days={windowSize} endDate={trends.end_date} />
              </div>
            </section>

            <section className="oc-surface p-4 sm:p-5">
              <div className="flex items-center gap-2">
                <Waves className="h-5 w-5 text-sky-600 dark:text-sky-400" />
                <div>
                  <h2 className="oc-type-section-title text-[var(--oc-text)]">Séries physiologiques COROS</h2>
                  <p className="mt-1 oc-type-secondary">Statistiques calculées à partir des échantillons horodatés sur les 30 derniers jours.</p>
                </div>
              </div>

              {assessment.time_series.length === 0 ? (
                <p className="mt-4 rounded-xl p-4 oc-type-body text-[var(--oc-muted)] bg-[var(--oc-surface-muted)]">
                  Aucune série détaillée disponible sur cette période. Les données quotidiennes restent consultables ci-dessus.
                </p>
              ) : (
                <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {assessment.time_series.map((series) => (
                    <div key={`${series.metric}-${series.unit ?? 'none'}`} className="rounded-xl border border-[var(--oc-border)] p-4">
                      <div className="flex items-start justify-between gap-2">
                        <h3 className="oc-type-card-title text-[var(--oc-text)]">
                          {SERIES_LABELS[series.metric] ?? series.metric.replaceAll('_', ' ')}
                        </h3>
                        <span className="rounded-md bg-[var(--oc-surface-muted)] px-2 py-1 oc-type-caption font-semibold uppercase text-[var(--oc-muted)]">
                          {series.sample_count} mesures
                        </span>
                      </div>
                      <p className="mt-3 text-xl font-bold tabular-nums text-[var(--oc-text)]">
                        {formatNumber(series.current)} <span className="oc-type-caption font-medium text-[var(--oc-muted)]">{series.unit ?? ''}</span>
                      </p>
                      <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
                        <MiniValue label="Moyenne" value={formatNumber(series.average)} />
                        <MiniValue label="Minimum" value={formatNumber(series.minimum)} />
                        <MiniValue label="Maximum" value={formatNumber(series.maximum)} />
                      </div>
                      <p className="mt-3 text-[11px] text-[var(--oc-muted)]">
                        {series.coverage_days} jours couverts · {formatDateTime(series.first_measured_at)} au {formatDateTime(series.last_measured_at)}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {assessment.subjective && (
              <section className="oc-surface p-4">
                <h2 className="oc-type-card-title text-[var(--oc-text)]">Ressenti du jour</h2>
                <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-5">
                  <MiniValue label="Fatigue" value={String(assessment.subjective.fatigue) + '/5'} />
                  <MiniValue label="Douleur" value={String(assessment.subjective.pain) + '/5'} />
                  <MiniValue label="Motivation" value={String(assessment.subjective.motivation) + '/5'} />
                  <MiniValue label="État" value={assessment.subjective.illness_status} />
                  <MiniValue label="Traitement" value={assessment.subjective.treatment_impact} />
                </div>
              </section>
            )}

            <p className="text-xs leading-relaxed text-[var(--oc-muted)]">
              Les valeurs absentes sont affichées « — » et ne sont jamais remplacées par zéro. Ces indicateurs décrivent les mesures enregistrées ; ils ne constituent pas un diagnostic médical et ne modifient pas automatiquement le score Readiness.
            </p>
          </>
        )}
      </div>
    </main>
  )
}


function TrendChart({
  title,
  unit,
  trend,
  days,
  endDate,
}: {
  title: string
  unit: string
  trend: WellnessMetricTrend
  days: WindowSize
  endDate: string
}) {
  const end = new Date(`${endDate}T12:00:00`).getTime()
  const start = end - (days - 1) * 24 * 60 * 60 * 1000
  const points = trend.points.filter((point) => {
    const timestamp = new Date(`${point.date}T12:00:00`).getTime()
    return timestamp >= start && timestamp <= end
  })

  const values = points.map((point) => point.value)
  const average = values.length > 0
    ? values.reduce((total, value) => total + value, 0) / values.length
    : null
  const latest = points[points.length - 1]
  const pointByDate = new Map(points.map((point) => [point.date, point]))
  const chartPoints = Array.from({ length: days }, (_, index) => {
    const date = new Date(`${endDate}T12:00:00Z`)
    date.setUTCDate(date.getUTCDate() - (days - 1 - index))
    const dateKey = date.toISOString().slice(0, 10)
    const point = pointByDate.get(dateKey)
    return {
      id: dateKey,
      label: formatDate(dateKey),
      value: point?.value ?? null,
    }
  })


  return (
    <LineChart
      title={title}
      points={chartPoints}
      valueFormatter={(value) => formatMetric(value, unit)}
      latestValue={latest ? formatMetric(latest.value, unit) : '—'}
      averageValue={average == null ? '—' : formatMetric(average, unit)}
      startLabel={chartPoints[0].label}
      endLabel={chartPoints[chartPoints.length - 1].label}
      emptyMessage={`Aucune donnée sur ${days} jours`}
      ariaLabel={`Évolution de ${title} sur ${days} jours`}
      headerMeta={`${points.length} j`}
    />
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
    <div className="relative min-w-0 overflow-hidden rounded-2xl border border-[var(--oc-border)] bg-[var(--oc-surface-raised)] p-4 shadow-[var(--oc-shadow-card)]">
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-500/80 via-teal-400/50 to-transparent" />
      <div className="flex items-center justify-between gap-3">
        <span className="oc-type-label font-semibold uppercase tracking-wide text-[var(--oc-muted)]">{label}</span>
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--oc-accent-soft)] text-[var(--oc-accent)]">{icon}</span>
      </div>
      <p className="mt-4 break-words text-2xl font-bold tracking-tight tabular-nums text-[var(--oc-text)]">{value}</p>
      <p className="mt-1 oc-type-secondary leading-relaxed">{detail}</p>
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
    <article className="min-w-0 rounded-xl border border-[var(--oc-border)] bg-[var(--oc-page)]/70 p-3.5 transition-colors hover:border-[var(--oc-border-strong)] sm:p-4">
      <div className="flex items-start justify-between gap-3">
        <p className="oc-type-body font-semibold leading-snug text-[var(--oc-text-secondary)]">{label}</p>
        <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-[var(--oc-accent)]" aria-hidden="true" />
      </div>
      <p className="mt-2 text-2xl font-bold tracking-tight tabular-nums text-[var(--oc-text)]">
        {value == null ? '—' : formatMetric(value, unit)}
      </p>
      <div className="mt-3 grid grid-cols-3 gap-2 border-t border-[var(--oc-border)] pt-3">
        <div className="min-w-0">
          <p className="oc-type-caption">Moyenne</p>
          <p className="mt-1 truncate text-xs font-semibold tabular-nums text-[var(--oc-text-secondary)]">{metric?.average == null ? '—' : formatMetric(metric.average, unit)}</p>
        </div>
        <div className="min-w-0">
          <p className="oc-type-caption">Mesures</p>
          <p className="mt-1 truncate text-xs font-semibold tabular-nums text-[var(--oc-text-secondary)]">{metric?.sample_count ?? 0}</p>
        </div>
        <div className="min-w-0">
          <p className="oc-type-caption">Jours couverts</p>
          <p className="mt-1 truncate text-xs font-semibold tabular-nums text-[var(--oc-text-secondary)]">{metric?.coverage_days ?? 0}</p>
        </div>
      </div>
    </article>
  )
}

function MiniValue({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-[10px] text-[var(--oc-muted)]">{label}</p>
      <p className="mt-0.5 oc-type-body font-semibold text-[var(--oc-text-secondary)]">{value}</p>
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
