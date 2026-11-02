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
  type CorosConnection,
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
  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true
    fetchCorosConnection()
      .then(result => {
        if (mounted) setConnection(result)
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
      const popup = window.open(result.login_url, '_blank', 'noopener,noreferrer')
      if (!popup) {
        throw new Error('Autorise les fenêtres contextuelles pour ouvrir COROS.')
      }

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
      <div className="flex items-center gap-2 p-5 text-sm text-slate-500">
        <LoaderCircle className="h-4 w-4 animate-spin" />
        Chargement de la configuration COROS…
      </div>
    )
  }

  if (!connection) {
    return <p className="p-5 text-sm text-red-600">{error || 'Configuration COROS indisponible.'}</p>
  }

  return (
    <div className="space-y-5 p-4 sm:p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-slate-100 text-slate-700 dark:bg-white/10 dark:text-white">
            <Watch className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-semibold text-slate-900 dark:text-white">Connexion COROS</h2>
            <p className="mt-1 max-w-xl text-xs leading-5 text-slate-500">
              Importe tes activités et tes données de récupération dans OpenCoach via le serveur officiel COROS MCP.
            </p>
          </div>
        </div>
        <div className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${connection.connected ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-400' : 'bg-slate-100 text-slate-600 dark:bg-white/10 dark:text-slate-300'}`}>
          {connection.connected ? <CheckCircle2 className="h-3.5 w-3.5" /> : <CircleAlert className="h-3.5 w-3.5" />}
          {connection.connected ? 'Connecté' : 'Non connecté'}
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 p-4 dark:border-white/10">
        <div className="flex items-start gap-3">
          <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
          <div>
            <p className="text-sm font-medium text-slate-800 dark:text-slate-100">Connexion sécurisée</p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
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
      </div>

      <div className="space-y-3">
        <div>
          <h3 className="text-sm font-semibold text-slate-900 dark:text-white">Données à importer</h3>
          <p className="mt-1 text-xs text-slate-500">Tu peux activer ou désactiver chaque famille indépendamment.</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-2">
          {Object.entries(CATEGORY_LABELS).map(([key, label]) => (
            <label key={key} className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 px-3 py-3 text-xs text-slate-700 dark:border-white/10 dark:text-slate-200">
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
          <span className="mb-1.5 block text-xs font-medium text-slate-700 dark:text-slate-200">Synchronisation automatique</span>
          <select
            value={connection.sync_interval_hours}
            onChange={event => setConnection(current => current ? { ...current, sync_interval_hours: Number(event.target.value) } : current)}
            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-xs text-slate-800 dark:border-white/10 dark:bg-[#10171b] dark:text-white"
          >
            <option value={0}>Désactivée</option>
            <option value={6}>Toutes les 6 heures</option>
            <option value={12}>Toutes les 12 heures</option>
            <option value={24}>Toutes les 24 heures</option>
          </select>
        </label>
        <div className="rounded-lg bg-slate-50 px-3 py-2.5 dark:bg-white/[0.04]">
          <span className="block text-xs font-medium text-slate-700 dark:text-slate-200">Historique initial</span>
          <span className="mt-1 block text-sm font-semibold text-slate-900 dark:text-white">6 derniers mois</span>
          <span className="mt-1 block text-[11px] text-slate-500">Fenêtre fixe pour le premier import.</span>
        </div>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4 dark:border-white/10">
        <p className="text-[11px] text-slate-500">
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
      {error && <p role="alert" className="rounded-lg bg-red-50 p-3 text-xs text-red-700 dark:bg-red-500/10 dark:text-red-300">{error}</p>}
      {!connection.connected && <p className="text-[11px] text-slate-500">Les préférences seront enregistrables après connexion. L’import des données sera activé dans la prochaine étape.</p>}
    </div>
  )
}
