import {
  CheckCircle2,
  CircleAlert,
  Link2,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  Watch,
} from 'lucide-react'
import { useEffect, useState } from 'react'

import {
  fetchCorosConnection,
  pollCorosOAuth,
  saveCorosSettings,
  startCorosOAuth,
  syncCorosHistory,
  waitForCorosSync,
  testCorosConnection,
  type CorosConnection,
  type CorosAvailableTool,
} from '../../core/integrations'

const CATEGORY_LABELS: Record<string, string> = {
  activities: 'Activités sportives',
  activity_details: 'Détails et tours',
  fit_files: 'Fichiers FIT (données détaillées)',
  sleep: 'Sommeil et phases',
  hrv: 'Variabilité cardiaque (HRV)',
  heart_rate: 'Fréquence cardiaque',
  stress: 'Stress',
  daily_health: 'Santé quotidienne (pas, SpO₂…)',
  training_load: 'Charge et forme',
}

function errorMessage(reason: unknown): string {
  return reason instanceof Error
    ? reason.message
    : 'Une erreur inattendue est survenue.'
}

export function CorosSection() {
  const [connection, setConnection] = useState<CorosConnection | null>(null)
  const [loading, setLoading] = useState(true)
  const [connecting, setConnecting] = useState(false)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)
  const [availableTools, setAvailableTools] = useState<CorosAvailableTool[]>([])
  const [availableToolsCount, setAvailableToolsCount] = useState<number | null>(null)

  useEffect(() => {
    let mounted = true
    fetchCorosConnection()
      .then(result => {
        if (mounted) setConnection(result)
        const activeJob = result.sync_job
        if (activeJob && ['pending', 'running'].includes(activeJob.status)) {
          setSyncing(true)
          waitForCorosSync(activeJob.job_id)
            .then(syncResult => {
              if (!mounted) return
              const total = Object.values(syncResult.imported_snapshots).reduce((sum, count) => sum + count, 0)
              const activities = syncResult.imported_snapshots.activities ?? 0
              const skipped = syncResult.skipped.length ? ` Éléments ignorés : ${syncResult.skipped.join(', ')}.` : ''
              setMessage(`Import terminé : ${activities} activité(s) et ${total} instantanés enregistrés (${syncResult.start_date} → ${syncResult.end_date}).${skipped}`)
              return fetchCorosConnection().then(refreshed => {
                if (mounted) setConnection(refreshed)
              })
            })
            .catch(reason => {
              if (mounted) setError(errorMessage(reason))
            })
            .finally(() => {
              if (mounted) setSyncing(false)
            })
        }
      })
      .catch(reason => {
        if (mounted) setError(errorMessage(reason))
      })
      .finally(() => {
        if (mounted) setLoading(false)
      })
    return () => { mounted = false }
  }, [])

  async function handleConnect() {
    setConnecting(true)
    setError(null)
    setMessage(null)

    try {
      const result = await startCorosOAuth()
      const popup = window.open(result.login_url, '_blank')
      if (!popup) {
        throw new Error('Autorise les fenêtres contextuelles pour ouvrir COROS.')
      }
      // Conserve la référence retournée par window.open pour détecter le blocage,
      // puis coupe immédiatement l'accès à window.opener pour éviter le reverse tabnabbing.
      popup.opener = null

      const startedAt = Date.now()
      while (Date.now() - startedAt < 5 * 60 * 1000) {
        await new Promise(resolve => window.setTimeout(resolve, 2500))
        const status = await pollCorosOAuth()
        if (status.connected) {
          const refreshed = await fetchCorosConnection()
          setConnection(refreshed)
          setMessage('Compte COROS connecté. Tu peux maintenant configurer les imports.')
          return
        }
      }

      throw new Error('Délai dépassé. Relance la connexion et termine l’autorisation COROS.')
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setConnecting(false)
    }
  }


  async function handleTestConnection() {
    setTesting(true)
    setError(null)
    setMessage(null)
    try {
      const result = await testCorosConnection()
      setAvailableTools(Array.isArray(result.available_tools) ? result.available_tools : [])
      setAvailableToolsCount(Number.isFinite(result.available_tools_count) ? result.available_tools_count : null)
      setMessage(`Connexion MCP opérationnelle : ${result.available_tools_count} outils COROS disponibles.`)
      const refreshed = await fetchCorosConnection()
      setConnection(refreshed)
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setTesting(false)
    }
  }


  async function handleSyncHistory() {
    setSyncing(true)
    setError(null)
    setMessage(null)
    try {
      const result = await syncCorosHistory()
      const total = Object.values(result.imported_snapshots).reduce((sum, count) => sum + count, 0)
      const activities = result.imported_snapshots.activities ?? 0
      const skipped = result.skipped.length ? ` Éléments ignorés : ${result.skipped.join(', ')}.` : ''
      setMessage(`Import terminé : ${activities} activité(s) et ${total} instantanés enregistrés (${result.start_date} → ${result.end_date}).${skipped}`)
      const refreshed = await fetchCorosConnection()
      setConnection(refreshed)
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setSyncing(false)
    }
  }

  function updateCategory(key: string, checked: boolean) {
    setConnection(current => current
      ? {
          ...current,
          categories: {
            ...current.categories,
            [key]: checked,
          },
        }
      : current)
  }

  async function handleSave() {
    if (!connection) return
    setSaving(true)
    setError(null)
    setMessage(null)
    try {
      const result = await saveCorosSettings({
        enabled: connection.enabled,
        sync_interval_hours: connection.sync_interval_hours,
        categories: connection.categories,
      })
      setConnection(current => current ? { ...current, ...result } : current)
      setMessage('Préférences COROS enregistrées.')
    } catch (reason) {
      setError(errorMessage(reason))
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center gap-2 p-5 text-sm text-[var(--oc-muted)]">
        <LoaderCircle className="h-4 w-4 animate-spin" />
        Chargement de la configuration COROS…
      </div>
    )
  }

  if (!connection) {
    return <p className="p-5 text-sm text-red-600">{error || 'Configuration COROS indisponible.'}</p>
  }

  return (
    <>
      {syncing && (
        <div
          role="status"
          aria-live="polite"
          className="fixed right-5 top-5 z-[100] flex max-w-sm items-start gap-3 rounded-xl border border-emerald-500/30 bg-[#111b1a] px-4 py-3 text-white shadow-2xl"
        >
          <LoaderCircle className="mt-0.5 h-5 w-5 shrink-0 animate-spin text-emerald-400" />
          <div>
            <p className="text-sm font-semibold">Import COROS en cours</p>
            <p className="mt-1 text-xs leading-5 text-[var(--oc-muted-soft)]">
              Récupération de ton historique et de tes données de récupération. Cela peut prendre quelques minutes.
            </p>
          </div>
        </div>
      )}
      <div className="space-y-5 p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--oc-surface-muted)] text-[var(--oc-text-secondary)] dark:bg-[var(--oc-surface-muted)] dark:text-white">
            <Watch className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-[var(--oc-text)] dark:text-white">Connexion COROS</h2>
            <p className="mt-1 max-w-xl text-xs leading-5 text-[var(--oc-muted)]">
              Importe tes activités et tes données de récupération dans OpenCoach via le serveur officiel COROS MCP.
            </p>
          </div>
        </div>
        <div className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${connection.connected ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-[var(--oc-surface-muted)] text-[var(--oc-text-secondary)] dark:bg-[var(--oc-surface-muted)] dark:text-[var(--oc-muted-soft)]'}`}>
          {connection.connected ? <CheckCircle2 className="h-3.5 w-3.5" /> : <CircleAlert className="h-3.5 w-3.5" />}
          {connection.connected ? 'Connecté' : 'Non connecté'}
        </div>
      </div>

      <div className="rounded-xl border border-[var(--oc-border)] p-4 dark:border-[var(--oc-border)]">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
          <div>
            <p className="text-sm font-medium text-[var(--oc-text-secondary)] dark:text-[var(--oc-text)]">Connexion sécurisée</p>
            <p className="mt-1 text-xs leading-5 text-[var(--oc-muted)]">
              L’autorisation se fait sur COROS. OpenCoach ne te demande jamais ton mot de passe COROS ; les jetons sont conservés chiffrés côté serveur.
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleConnect}
          disabled={connecting}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3.5 py-2.5 text-xs font-semibold text-white hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-emerald-600 dark:hover:bg-emerald-500"
        >
          {connecting ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <Link2 className="h-4 w-4" />}
          {connecting ? 'En attente de l’autorisation COROS…' : connection.connected ? 'Reconnecter COROS' : 'Connecter mon compte COROS'}
        </button>
        {connection.connected && (
          <button
            type="button"
            onClick={handleTestConnection}
            disabled={testing || connecting}
            className="mt-4 ml-2 inline-flex items-center gap-2 rounded-lg border border-slate-300 px-3.5 py-2.5 text-xs font-semibold text-[var(--oc-text-secondary)] hover:bg-slate-50 disabled:opacity-60 dark:border-white/15 dark:text-[var(--oc-text-secondary)] dark:hover:bg-white/5"
          >
            {testing ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {testing ? 'Test en cours…' : 'Tester la connexion MCP'}
          </button>
        )}
      </div>

      {connection.connected && (
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 dark:border-emerald-500/20 dark:bg-emerald-500/5">
          <div>
            <p className="text-sm font-semibold text-[var(--oc-text)] dark:text-white">Importer l’historique COROS</p>
            <p className="mt-1 text-xs text-[var(--oc-muted)]">Import initial sur six mois, puis mise à jour des données disponibles.</p>
          </div>
          <button type="button" onClick={handleSyncHistory} disabled={syncing || testing} className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50">
            {syncing ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            {syncing ? 'Import en cours…' : 'Lancer l’import'}
          </button>
        </div>
      )}

      <div className="space-y-3">
        <div>
          <h3 className="text-sm font-semibold text-[var(--oc-text)] dark:text-white">Données à importer</h3>
          <p className="mt-1 text-xs text-[var(--oc-muted)]">Tu peux activer ou désactiver chaque famille indépendamment.</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
            <label key={key} className="flex cursor-pointer items-center gap-3 rounded-lg border border-[var(--oc-border)] px-3 py-3 text-xs text-[var(--oc-text-secondary)] dark:border-[var(--oc-border)] dark:text-[var(--oc-text-secondary)]">
              <input
                type="checkbox"
                checked={Boolean(connection.categories[key])}
                onChange={event => updateCategory(key, event.target.checked)}
                className="h-4 w-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500"
              />
              {label}
            </label>
          ))}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1.5 block text-xs font-medium text-[var(--oc-text-secondary)] dark:text-[var(--oc-text-secondary)]">Fréquence souhaitée</span>
          <select
            value={connection.sync_interval_hours}
            onChange={event => setConnection(current => current ? { ...current, sync_interval_hours: Number(event.target.value) } : current)}
            className="w-full rounded-lg border border-[var(--oc-border)] bg-white px-3 py-2.5 text-xs text-[var(--oc-text-secondary)] dark:border-[var(--oc-border)] dark:bg-[#10171b] dark:text-white"
          >
            <option value={0}>Désactivée</option>
            <option value={6}>Toutes les 6 heures</option>
            <option value={12}>Toutes les 12 heures</option>
            <option value={24}>Toutes les 24 heures</option>
          </select>
          <span className="mt-1.5 block text-[11px] text-[var(--oc-muted)]">Le service vérifie les échéances toutes les 15 minutes et lance l’import lorsque la fréquence est atteinte.</span>
        </label>
        <div className="rounded-lg bg-slate-50 px-3 py-2.5 dark:bg-white/[0.04]">
          <span className="block text-xs font-medium text-[var(--oc-text-secondary)] dark:text-[var(--oc-text-secondary)]">Historique initial</span>
          <span className="mt-1 block text-sm font-semibold text-[var(--oc-text)] dark:text-white">6 derniers mois</span>
          <span className="mt-1 block text-[11px] text-[var(--oc-muted)]">Fenêtre cible du premier import.</span>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4 dark:border-[var(--oc-border)]">
        <p className="text-[11px] text-[var(--oc-muted)]">
          {connection.last_synced_at
            ? `Dernière synchronisation : ${new Date(connection.last_synced_at).toLocaleString('fr-FR')}`
            : 'Aucune synchronisation effectuée.'}
        </p>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving || !connection.connected}
          className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2.5 text-xs font-semibold text-white hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {saving ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Enregistrer les préférences
        </button>
      </div>

      {message && <p role="status" className="text-xs text-emerald-700 dark:text-emerald-400">{message}</p>}
      {availableToolsCount !== null && (
        <section aria-label="Diagnostic des outils COROS" className="rounded-lg border border-emerald-500/20 bg-emerald-500/5 p-3">
          <h3 className="text-xs font-semibold text-[var(--oc-text-secondary)] dark:text-[var(--oc-text)]">Outils COROS reçus : {availableToolsCount}</h3>
          {availableTools.length > 0 ? (
            <ul className="mt-3 grid gap-2 sm:grid-cols-2">
              {availableTools.map(tool => (
                <li key={tool.name} className="rounded-lg border border-[var(--oc-border)] p-3 dark:border-[var(--oc-border)]">
                  <p className="font-mono text-[11px] font-semibold text-[var(--oc-text-secondary)] dark:text-[var(--oc-text)]">{tool.name}</p>
                  {tool.description && <p className="mt-1 text-[11px] text-[var(--oc-muted)]">{tool.description}</p>}
                  <p className="mt-2 text-[10px] font-semibold uppercase tracking-wide text-[var(--oc-muted)]">Paramètres attendus</p>
                  {Object.entries(tool.input_schema?.properties ?? {}).length > 0 ? (
                    <ul className="mt-1 space-y-1">
                      {Object.entries(tool.input_schema.properties ?? {}).map(([name, definition]) => (
                        <li key={name} className="text-[11px] text-[var(--oc-text-secondary)] dark:text-[var(--oc-muted-soft)]">
                          <span className="font-mono font-medium">{name}</span>
                          <span className="text-slate-400"> · {Array.isArray(definition.type) ? definition.type.join(' | ') : definition.type ?? 'type non précisé'}</span>
                          {tool.input_schema.required?.includes(name) && <span className="ml-1 text-amber-600">obligatoire</span>}
                          {definition.description && <span className="block text-[var(--oc-muted)]">{definition.description}</span>}
                        </li>
                      ))}
                    </ul>
                  ) : <p className="mt-1 text-[11px] text-[var(--oc-muted)]">Aucun paramètre déclaré.</p>}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-xs text-amber-700 dark:text-amber-300">Le serveur annonce {availableToolsCount} outils, mais n'a transmis aucun nom. La réponse API est incomplète.</p>
          )}
        </section>
      )}
      {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-xs text-red-700 dark:bg-red-500/10 dark:text-red-300">{error}</p>}
      {!connection.connected && <p className="text-[11px] text-[var(--oc-muted)]">Connecte COROS pour activer les synchronisations automatiques. Tu peux aussi lancer un import manuel à tout moment.</p>}
      </div>
    </>
  )
}
