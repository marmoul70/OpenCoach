import {
  Activity,
  CalendarDays,
  ChevronRight,
  Heart,
  Moon,
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
import { SidePanel } from '../../components/ui/SidePanel'
import { PageHeader } from '../../design-system/components/PageHeader'

type WindowSize = 7 | 14 | 30
type HealthSectionKey = 'cardio' | 'recovery' | 'sleep'

const HEALTH_SECTIONS = [
  { key: 'cardio', title: 'Cardio', description: 'Fréquence cardiaque et santé cardiovasculaire', icon: Heart, metrics: ['resting_hr', 'avg_hr', 'min_hr', 'max_hr', 'avg_sleeping_hr'], trends: ['resting_hr'] },
  { key: 'recovery', title: 'Récupération', description: 'HRV, stress et charge d’entraînement', icon: Activity, metrics: ['hrv', 'hrv_baseline', 'stress_avg', 'fitness_ctl', 'fatigue_atl'], trends: ['hrv', 'fitness_ctl', 'fatigue_atl', 'stress_avg'] },
  { key: 'sleep', title: 'Sommeil', description: 'Qualité, durée et phases du sommeil', icon: Moon, metrics: ['sleep_score', 'sleep_seconds', 'sleep_deep_seconds', 'sleep_light_seconds', 'sleep_rem_seconds', 'sleep_awake_seconds'], trends: ['sleep_score', 'sleep_seconds'] },
] as const

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
  const [selectedSection, setSelectedSection] = useState<HealthSectionKey | null>(null)

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
    <main className="oc-app-shell min-h-screen px-3 py-4 sm:px-5 lg:px-6">
      <div className="mx-auto max-w-[1440px] space-y-4">
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

            <section className="grid gap-3 lg:grid-cols-3">
              {HEALTH_SECTIONS.map((section) => {
                const Icon = section.icon
                const available = section.metrics
                  .map((key) => ({ key, metric: selectedWindow?.metrics[key] }))
                  .filter((item) => item.metric?.current != null)
                return (
                  <button
                    key={section.key}
                    type="button"
                    onClick={() => setSelectedSection(section.key)}
                    className="group min-w-0 rounded-2xl border border-[var(--oc-border)] bg-[var(--oc-surface)] p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-[var(--oc-accent)] hover:shadow-md"
                    aria-label={`Ouvrir le détail ${section.title}`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <div className="flex items-center gap-2.5">
                        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--oc-accent-soft)] text-[var(--oc-accent)]">
                          <Icon className="h-[18px] w-[18px]" />
                        </span>
                        <div>
                          <h2 className="font-semibold text-[var(--oc-text)]">{section.title}</h2>
                          <p className="text-xs text-[var(--oc-muted)]">{available.length} indicateurs disponibles</p>
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 shrink-0 text-[var(--oc-muted)] transition group-hover:translate-x-0.5 group-hover:text-[var(--oc-accent)]" />
                    </div>
                    <div className="mt-4 grid grid-cols-2 gap-x-4 gap-y-3">
                      {section.metrics.slice(0, 4).map((key) => {
                        const metric = selectedWindow?.metrics[key]
                        const definition = METRICS.find((item) => item.key === key)
                        return (
                          <div key={key} className="min-w-0">
                            <p className="truncate text-[11px] text-[var(--oc-muted)]">{definition?.label ?? key}</p>
                            <p className="mt-0.5 truncate text-base font-semibold tabular-nums text-[var(--oc-text)]">
                              {metric?.current == null ? '—' : formatMetric(metric.current, definition?.unit ?? '')}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                    <p className="mt-3 border-t border-[var(--oc-border)] pt-2 text-xs text-[var(--oc-muted)]">
                      {section.description}
                    </p>
                  </button>
                )
              })}
            </section>

            <section className="oc-surface flex flex-wrap items-center justify-between gap-3 p-3 sm:p-4">
              <div>
                <h2 className="text-sm font-semibold text-[var(--oc-text)]">Période d’analyse</h2>
                <p className="mt-0.5 text-xs text-[var(--oc-muted)]">
                  {selectedWindow ? `${selectedWindow.recorded_days}/${selectedWindow.days} jours couverts · ${Math.round(selectedWindow.coverage_ratio * 100)} %` : 'Données indisponibles'}
                </p>
              </div>
              <div className="inline-flex w-fit rounded-xl bg-[var(--oc-surface-muted)] p-1" aria-label="Période d’historique">
                {([7, 14, 30] as const).map((days) => (
                  <button
                    key={days}
                    type="button"
                    onClick={() => setWindowSize(days)}
                    aria-pressed={windowSize === days}
                    className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${windowSize === days ? 'bg-[var(--oc-surface)] text-emerald-700 shadow-sm ring-1 ring-[var(--oc-border)] dark:text-emerald-300' : 'text-[var(--oc-muted)] hover:text-[var(--oc-text)]'}`}
                  >
                    {days} j
                  </button>
                ))}
              </div>
            </section>

            <SidePanel
              open={selectedSection !== null}
              title={HEALTH_SECTIONS.find((section) => section.key === selectedSection)?.title ?? 'Détail santé'}
              eyebrow="Suivi physiologique"
              onClose={() => setSelectedSection(null)}
            >
              {selectedSection && selectedWindow && (() => {
                const section = HEALTH_SECTIONS.find((item) => item.key === selectedSection)!
                const sectionMetrics = section.metrics
                const trendKeys = section.trends
                return (
                  <div className="space-y-5">
                    <div>
                      <p className="text-sm text-[var(--oc-text-secondary)]">{section.description}</p>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs text-[var(--oc-muted)]">
                        <span className="rounded-lg bg-[var(--oc-surface-muted)] px-2.5 py-1">{windowSize} derniers jours</span>
                        <span className="rounded-lg bg-[var(--oc-surface-muted)] px-2.5 py-1">{selectedWindow.recorded_days}/{selectedWindow.days} jours couverts</span>
                      </div>
                    </div>

                    <section>
                      <h3 className="mb-2 text-sm font-semibold text-[var(--oc-text)]">Indicateurs détaillés</h3>
                      <div className="grid gap-2 sm:grid-cols-2">
                        {sectionMetrics.map((key) => {
                          const definition = METRICS.find((item) => item.key === key)!
                          return (
                            <MetricTile
                              key={key}
                              label={definition.label}
                              unit={definition.unit}
                              metric={selectedWindow.metrics[key]}
                            />
                          )
                        })}
                      </div>
                    </section>

                    <section>
                      <h3 className="mb-2 text-sm font-semibold text-[var(--oc-text)]">Évolution</h3>
                      <div className="space-y-3">
                        {trendKeys.map((key) => {
                          const trendTitle: Record<string, string> = {
                            hrv: 'HRV nocturne',
                            resting_hr: 'Fréquence cardiaque au repos',
                            sleep_score: 'Score de sommeil',
                            sleep_seconds: 'Durée du sommeil',
                            fitness_ctl: 'Charge chronique · CTL',
                            fatigue_atl: 'Charge aiguë · ATL',
                            stress_avg: 'Stress moyen',
                          }
                          const trendUnit: Record<string, string> = {
                            hrv: 'ms', resting_hr: 'bpm', sleep_score: '/100',
                            sleep_seconds: 'duration', fitness_ctl: 'load',
                            fatigue_atl: 'load', stress_avg: 'score',
                          }
                          const trend = trends.metrics[key as keyof typeof trends.metrics]
                          if (!trend) return null
                          return (
                            <TrendChart
                              key={key}
                              title={trendTitle[key] ?? key}
                              unit={trendUnit[key] ?? ''}
                              trend={trend}
                              days={windowSize}
                              endDate={trends.end_date}
                            />
                          )
                        })}
                      </div>
                    </section>

                    {assessment.time_series.filter((series) => {
                      if (selectedSection === 'cardio') return series.metric === 'heart_rate'
                      if (selectedSection === 'recovery') return series.metric === 'sleep_hrv' || series.metric === 'stress'
                      return series.metric === 'respiration_rate' || series.metric === 'temperature'
                    }).length > 0 && (
                      <section>
                        <h3 className="mb-2 text-sm font-semibold text-[var(--oc-text)]">Mesures détaillées COROS</h3>
                        <div className="space-y-2">
                          {assessment.time_series.filter((series) => {
                            if (selectedSection === 'cardio') return series.metric === 'heart_rate'
                            if (selectedSection === 'recovery') return series.metric === 'sleep_hrv' || series.metric === 'stress'
                            return series.metric === 'respiration_rate' || series.metric === 'temperature'
                          }).map((series) => (
                            <div key={series.metric} className="rounded-xl border border-[var(--oc-border)] p-3">
                              <div className="flex items-center justify-between gap-2">
                                <p className="text-sm font-semibold text-[var(--oc-text)]">{SERIES_LABELS[series.metric] ?? series.metric}</p>
                                <span className="text-xs text-[var(--oc-muted)]">{series.sample_count} mesures</span>
                              </div>
                              <p className="mt-2 text-xl font-bold text-[var(--oc-text)]">{formatNumber(series.current)} <span className="text-xs font-medium text-[var(--oc-muted)]">{series.unit ?? ''}</span></p>
                              <div className="mt-2 grid grid-cols-3 gap-2">
                                <MiniValue label="Moyenne" value={formatNumber(series.average)} />
                                <MiniValue label="Minimum" value={formatNumber(series.minimum)} />
                                <MiniValue label="Maximum" value={formatNumber(series.maximum)} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </section>
                    )}
                  </div>
                )
              })()}
            </SidePanel>

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
    <div className="relative min-w-0 overflow-hidden rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface-raised)] p-3 shadow-[var(--oc-shadow-card)]">
      <div aria-hidden="true" className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-emerald-500/80 via-teal-400/50 to-transparent" />
      <div className="flex items-center justify-between gap-3">
        <span className="oc-type-label font-semibold uppercase tracking-wide text-[var(--oc-muted)]">{label}</span>
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--oc-accent-soft)] text-[var(--oc-accent)] [&>svg]:h-4 [&>svg]:w-4">{icon}</span>
      </div>
      <p className="mt-2 break-words text-xl font-bold tracking-tight tabular-nums text-[var(--oc-text)]">{value}</p>
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
    <article className="min-w-0 rounded-lg border border-[var(--oc-border)] bg-[var(--oc-page)]/70 p-3 transition-colors hover:border-[var(--oc-border-strong)]">
      <div className="flex items-start justify-between gap-3">
        <p className="oc-type-body font-semibold leading-snug text-[var(--oc-text-secondary)]">{label}</p>
        <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-[var(--oc-accent)]" aria-hidden="true" />
      </div>
      <p className="mt-1.5 text-xl font-bold tracking-tight tabular-nums text-[var(--oc-text)]">
        {value == null ? '—' : formatMetric(value, unit)}
      </p>
      <div className="mt-2 grid grid-cols-3 gap-2 border-t border-[var(--oc-border)] pt-2">
        <div className="min-w-0">
          <p className="oc-type-caption">Moyenne</p>
          <p className="mt-0.5 truncate text-[11px] font-semibold tabular-nums text-[var(--oc-text-secondary)]">{metric?.average == null ? '—' : formatMetric(metric.average, unit)}</p>
        </div>
        <div className="min-w-0">
          <p className="oc-type-caption">Mesures</p>
          <p className="mt-0.5 truncate text-[11px] font-semibold tabular-nums text-[var(--oc-text-secondary)]">{metric?.sample_count ?? 0}</p>
        </div>
        <div className="min-w-0">
          <p className="oc-type-caption">Jours couverts</p>
          <p className="mt-0.5 truncate text-[11px] font-semibold tabular-nums text-[var(--oc-text-secondary)]">{metric?.coverage_days ?? 0}</p>
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


function statusLabel(status: string, age: number | null): string {
  if (status === 'fresh') return 'Données du jour disponibles'
  if (status === 'stale') return `Dernière donnée : J-${age ?? '?'}`
  return 'Aucune donnée quotidienne disponible'
}
