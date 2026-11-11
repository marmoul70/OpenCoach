import { useEffect, useState } from 'react'
import { RotateCcw, Save, Sparkles } from 'lucide-react'

type Personality = 'balanced' | 'demanding' | 'severe' | 'motivating' | 'benevolent'
type ResponseStyle = 'concise' | 'detailed' | 'analytical'

interface CoachPreferences {
  personality: Personality
  firmness: number
  motivation: number
  response_style: ResponseStyle
  custom_prompt: string
}

const DEFAULTS: CoachPreferences = {
  personality: 'balanced',
  firmness: 3,
  motivation: 3,
  response_style: 'detailed',
  custom_prompt: '',
}

const fieldClass = 'mt-1.5 w-full rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface)] px-3 py-2.5 text-sm text-[var(--oc-text)] outline-none transition focus:border-emerald-500 dark:text-white'
const labelClass = 'text-xs font-semibold text-[var(--oc-text)] dark:text-white'

export function AISettingsSection() {
  const [preferences, setPreferences] = useState<CoachPreferences>(DEFAULTS)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function loadPreferences() {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch('/api/ai/preferences', {
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
        cache: 'no-store',
      })
      if (!response.ok) throw new Error(`Chargement impossible (HTTP ${response.status}).`)
      setPreferences({ ...DEFAULTS, ...await response.json() as CoachPreferences })
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Impossible de charger les préférences.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadPreferences()
  }, [])

  function update<K extends keyof CoachPreferences>(key: K, value: CoachPreferences[K]) {
    setPreferences(current => ({ ...current, [key]: value }))
    setMessage(null)
  }

  async function savePreferences() {
    setSaving(true)
    setMessage(null)
    setError(null)
    try {
      const response = await fetch('/api/ai/preferences', {
        method: 'PUT',
        credentials: 'same-origin',
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences),
      })
      const payload = await response.json() as CoachPreferences | { detail?: string }
      if (!response.ok) {
        throw new Error('detail' in payload && payload.detail ? payload.detail : `Enregistrement impossible (HTTP ${response.status}).`)
      }
      setPreferences(payload as CoachPreferences)
      setMessage('Préférences enregistrées.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Erreur lors de l’enregistrement.')
    } finally {
      setSaving(false)
    }
  }

  async function resetPreferences() {
    setSaving(true)
    setMessage(null)
    setError(null)
    try {
      const response = await fetch('/api/ai/preferences/reset', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { Accept: 'application/json' },
      })
      const payload = await response.json() as CoachPreferences | { detail?: string }
      if (!response.ok) {
        throw new Error('detail' in payload && payload.detail ? payload.detail : `Réinitialisation impossible (HTTP ${response.status}).`)
      }
      setPreferences(payload as CoachPreferences)
      setMessage('Réglages par défaut restaurés.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Erreur lors de la réinitialisation.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return <p className="text-xs text-[var(--oc-muted)]">Chargement des préférences du coach…</p>
  }

  return (
    <div className="space-y-5">
      <div className="flex items-start gap-3 rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface-muted)] p-3.5">
        <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" />
        <div>
          <p className="text-sm font-semibold text-[var(--oc-text)] dark:text-white">Personnalise ton coach IA</p>
          <p className="mt-1 text-xs leading-5 text-[var(--oc-muted)]">Ces préférences modifient le ton et la présentation des réponses. Les règles de fiabilité, de sécurité et de lecture seule restent prioritaires.</p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="block">
          <span className={labelClass}>Personnalité</span>
          <select className={fieldClass} value={preferences.personality} onChange={event => update('personality', event.target.value as Personality)}>
            <option value="balanced">Équilibrée</option>
            <option value="demanding">Exigeante</option>
            <option value="severe">Sévère et directe</option>
            <option value="motivating">Motivante</option>
            <option value="benevolent">Bienveillante</option>
          </select>
        </label>
        <label className="block">
          <span className={labelClass}>Style de réponse</span>
          <select className={fieldClass} value={preferences.response_style} onChange={event => update('response_style', event.target.value as ResponseStyle)}>
            <option value="concise">Concis</option>
            <option value="detailed">Détaillé</option>
            <option value="analytical">Analytique et structuré</option>
          </select>
        </label>
      </div>

      <div className="grid gap-5 sm:grid-cols-2">
        <label className="block">
          <span className="flex items-center justify-between gap-2">
            <span className={labelClass}>Fermeté</span>
            <span className="text-xs font-semibold tabular-nums text-emerald-700 dark:text-emerald-400">{preferences.firmness}/5</span>
          </span>
          <input className="mt-3 w-full accent-emerald-600" type="range" min="1" max="5" step="1" value={preferences.firmness} onChange={event => update('firmness', Number(event.target.value))} />
          <span className="mt-1 flex justify-between text-[10px] text-[var(--oc-muted)]"><span>Souple</span><span>Très ferme</span></span>
        </label>
        <label className="block">
          <span className="flex items-center justify-between gap-2">
            <span className={labelClass}>Motivation</span>
            <span className="text-xs font-semibold tabular-nums text-emerald-700 dark:text-emerald-400">{preferences.motivation}/5</span>
          </span>
          <input className="mt-3 w-full accent-emerald-600" type="range" min="1" max="5" step="1" value={preferences.motivation} onChange={event => update('motivation', Number(event.target.value))} />
          <span className="mt-1 flex justify-between text-[10px] text-[var(--oc-muted)]"><span>Neutre</span><span>Très stimulant</span></span>
        </label>
      </div>

      <label className="block">
        <span className={labelClass}>Consignes personnalisées</span>
        <textarea
          className={fieldClass + ' min-h-32 resize-y leading-5'}
          value={preferences.custom_prompt}
          maxLength={6000}
          onChange={event => update('custom_prompt', event.target.value)}
          placeholder="Ex. : privilégie les analyses concrètes, explique les choix de charge et challenge-moi lorsque je manque de régularité…"
          rows={5}
        />
        <span className="mt-1 block text-right text-[10px] text-[var(--oc-muted)]">{preferences.custom_prompt.length}/6000 caractères</span>
      </label>

      {error && <p role="alert" className="rounded-lg bg-rose-500/10 p-3 text-xs text-rose-600 dark:text-rose-300">{error}</p>}
      {message && <p role="status" className="rounded-lg bg-emerald-500/10 p-3 text-xs text-emerald-700 dark:text-emerald-300">{message}</p>}

      <div className="flex flex-wrap items-center justify-between gap-2 border-t border-[var(--oc-border)] pt-4">
        <button type="button" disabled={saving} onClick={() => void resetPreferences()} className="inline-flex min-h-10 items-center gap-2 rounded-xl border border-[var(--oc-border)] px-3 py-2 text-xs font-semibold text-[var(--oc-muted)] transition hover:bg-[var(--oc-surface-muted)] disabled:opacity-50">
          <RotateCcw className="h-3.5 w-3.5" /> Réinitialiser
        </button>
        <button type="button" disabled={saving} onClick={() => void savePreferences()} className="inline-flex min-h-10 items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50">
          <Save className="h-3.5 w-3.5" /> {saving ? 'Enregistrement…' : 'Enregistrer'}
        </button>
      </div>
    </div>
  )
}
