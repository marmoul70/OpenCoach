import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, RefreshCw } from 'lucide-react'

interface LatencySummary {
  p50: number | null
  p95: number | null
  min: number | null
  max: number | null
}

interface AIObservabilitySnapshot {
  window_hours: number
  retention: string
  capacity: number
  sample_count: number
  total_count: number
  truncated: boolean
  summary: {
    count: number
    errors: number
    error_rate_percent: number
    latency_ms: LatencySummary
  }
  breakdown: Array<{
    event: string
    dimension: string
    count: number
    errors: number
    error_rate_percent: number
    latency_ms: LatencySummary
  }>
}

const WINDOWS = [
  { value: 1, label: '1 h' },
  { value: 24, label: '24 h' },
  { value: 168, label: '7 j' },
] as const

function formatLatency(value: number | null): string {
  if (value === null) return '—'
  return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(value) + ' ms'
}

function eventLabel(event: string): string {
  if (event === 'coach_router') return 'Routeur Python'
  if (event === 'ollama_generation') return 'Génération Ollama'
  if (event === 'tool_execution') return 'Outil Python'
  return event
}

export function AIObservabilityPanel() {
  const [windowHours, setWindowHours] = useState<number>(24)
  const [snapshot, setSnapshot] = useState<AIObservabilitySnapshot | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function loadMetrics(hours: number) {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(
        `/api/ai/observability?window_hours=${hours}`,
        { headers: { Accept: 'application/json' }, cache: 'no-store' },
      )
      if (!response.ok) {
        throw new Error(response.status === 503
          ? 'Le moteur IA est indisponible.'
          : `Impossible de charger les métriques (HTTP ${response.status}).`)
      }
      setSnapshot(await response.json() as AIObservabilitySnapshot)
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Erreur de lecture des métriques.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadMetrics(windowHours)
  }, [windowHours])

  return (
    <section className="mt-4 overflow-hidden rounded-[16px] border border-[var(--oc-border)] bg-[var(--oc-surface)] shadow-[0_1px_3px_rgba(15,23,42,0.03)]">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[var(--oc-border)] px-4 py-3 sm:px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/10 text-sky-600 dark:text-sky-400">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-[12px] font-semibold text-[var(--oc-text)] dark:text-white">Supervision IA</h2>
            <p className="text-[9px] text-[var(--oc-muted)]">Performances techniques du moteur local</p>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="flex rounded-lg border border-[var(--oc-border)] p-0.5">
            {WINDOWS.map((item) => (
              <button
                key={item.value}
                type="button"
                aria-pressed={windowHours === item.value}
                onClick={() => setWindowHours(item.value)}
                className={windowHours === item.value
                  ? 'rounded-md bg-[var(--oc-surface-muted)] px-2.5 py-1 text-[9px] font-semibold text-[var(--oc-text)] dark:text-white'
                  : 'rounded-md px-2.5 py-1 text-[9px] font-medium text-[var(--oc-muted)] hover:text-[var(--oc-text)]'}
              >
                {item.label}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={() => void loadMetrics(windowHours)}
            disabled={loading}
            aria-label="Actualiser les métriques IA"
            className="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-[var(--oc-border)] text-[var(--oc-muted)] hover:bg-[var(--oc-surface-muted)] disabled:opacity-50"
          >
            <RefreshCw className={loading ? 'h-3.5 w-3.5 animate-spin' : 'h-3.5 w-3.5'} />
          </button>
        </div>
      </div>

      <div className="p-4 sm:p-5">
        {error ? (
          <p role="alert" className="text-[10px] text-rose-600 dark:text-rose-400">{error}</p>
        ) : loading && !snapshot ? (
          <p className="text-[10px] text-[var(--oc-muted)]">Chargement des métriques…</p>
        ) : snapshot ? (
          <>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
              <Metric label="Requêtes" value={String(snapshot.summary.count)} />
              <Metric label="Latence p50" value={formatLatency(snapshot.summary.latency_ms.p50)} />
              <Metric label="Latence p95" value={formatLatency(snapshot.summary.latency_ms.p95)} />
              <Metric
                label="Taux d'erreur"
                value={snapshot.summary.error_rate_percent.toLocaleString('fr-FR') + ' %'}
                warning={snapshot.summary.error_rate_percent > 5}
              />
            </div>

            {snapshot.breakdown.length > 0 ? (
              <div className="mt-4 divide-y divide-[var(--oc-border)]">
                {snapshot.breakdown.map((item) => (
                  <div key={item.event + item.dimension} className="flex flex-wrap items-center justify-between gap-2 py-2 first:pt-0 last:pb-0">
                    <div className="min-w-0">
                      <p className="text-[10px] font-semibold text-[var(--oc-text)] dark:text-white">{eventLabel(item.event)}</p>
                      <p className="truncate text-[9px] text-[var(--oc-muted)]">{item.dimension}</p>
                    </div>
                    <div className="flex items-center gap-3 text-right">
                      <span className="text-[9px] text-[var(--oc-muted)]">{item.count} appel(s)</span>
                      <span className="text-[10px] font-semibold tabular-nums text-[var(--oc-text)] dark:text-white">p95 {formatLatency(item.latency_ms.p95)}</span>
                      {item.errors > 0 && <span className="inline-flex items-center gap-1 text-[9px] font-semibold text-rose-600"><AlertTriangle className="h-3 w-3" />{item.errors}</span>}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="mt-4 text-[10px] text-[var(--oc-muted)]">Aucun appel IA mesuré sur cette période.</p>
            )}

            <p className="mt-3 border-t border-[var(--oc-border)] pt-2 text-[8px] text-[var(--oc-muted)]">
              {snapshot.sample_count} échantillon(s) en mémoire · capacité {snapshot.capacity.toLocaleString('fr-FR')}
              {snapshot.truncated ? ' · les plus anciens échantillons ont été évincés' : ''}
              {loading ? ' · actualisation…' : ''}
            </p>
          </>
        ) : null}
      </div>
    </section>
  )
}

function Metric({
  label,
  value,
  warning = false,
}: {
  label: string
  value: string
  warning?: boolean
}) {
  return (
    <div className="rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface-muted)] p-3">
      <p className="text-[8px] font-bold uppercase tracking-[0.08em] text-[var(--oc-muted)]">{label}</p>
      <p className={warning ? 'mt-1 text-[17px] font-bold tabular-nums text-rose-600' : 'mt-1 text-[17px] font-bold tabular-nums text-[var(--oc-text)] dark:text-white'}>
        {value}
      </p>
    </div>
  )
}
