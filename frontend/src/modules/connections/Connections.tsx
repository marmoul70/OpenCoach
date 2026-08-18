import { useEffect, useState } from 'react'
import {
  Activity,
  CheckCircle2,
  MessageCircle,
  Radio,
  Watch,
} from 'lucide-react'

import {
  fetchIntervalsConnection,
  saveIntervalsConnection,
  testIntervalsConnection,
  testSavedIntervalsConnection,
  type IntervalsConnection,
} from '../../core/integrations'


export function Connections() {
  const [connection, setConnection] =
    useState<IntervalsConnection | null>(null)

  const [athleteId, setAthleteId] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [enabled, setEnabled] = useState(true)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [testing, setTesting] = useState(false)

  const [connectionTested, setConnectionTested] =
    useState(false)

  const [error, setError] = useState<string | null>(null)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    let mounted = true

    fetchIntervalsConnection()
      .then((result) => {
        if (!mounted) {
          return
        }

        setConnection(result)
        setAthleteId(result.athlete_id ?? '')
        setEnabled(result.enabled)
      })
      .catch((reason: unknown) => {
        if (!mounted) {
          return
        }

        setError(
          getErrorMessage(reason),
        )
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

  async function handleTest() {
    setTesting(true)
    setError(null)
    setMessage(null)
    setConnectionTested(false)

    try {
      const normalizedAthleteId =
        athleteId.trim()

      const normalizedApiKey =
        apiKey.trim()

      if (!normalizedAthleteId) {
        throw new Error(
          "L'identifiant athlète est obligatoire.",
        )
      }

      if (normalizedApiKey) {
        await testIntervalsConnection(
          normalizedAthleteId,
          normalizedApiKey,
        )
      } else {
        if (!connection?.api_key_configured) {
          throw new Error(
            'Saisissez une clé API pour tester la connexion.',
          )
        }

        await testSavedIntervalsConnection()
      }

      setConnectionTested(true)

      setMessage(
        'Connexion à Intervals.icu réussie. Vous pouvez maintenant enregistrer.',
      )
    } catch (reason) {
      setConnectionTested(false)

      setError(
        getErrorMessage(reason),
      )
    } finally {
      setTesting(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    setError(null)
    setMessage(null)

    try {
      const result = await saveIntervalsConnection({
        athlete_id: athleteId.trim(),
        api_key: apiKey.trim() || null,
        enabled,
      })

      setConnection(result)
      setApiKey('')
      setConnectionTested(false)

      setMessage(
        'Connexion Intervals.icu enregistrée.',
      )
    } catch (reason) {
      setError(
        getErrorMessage(reason),
      )
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-base-200">
        <span className="loading loading-spinner loading-lg text-primary" />
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-base-200">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-base-content">
            Connexions
          </h1>

          <p className="mt-1 text-sm text-base-content/60">
            Configurez les services externes utilisés par OpenCoach.
          </p>
        </header>

        <div className="space-y-4">
          <section className="collapse collapse-arrow border border-base-300 bg-base-100 shadow-sm">
            <input
              type="checkbox"
              defaultChecked
            />

            <div className="collapse-title">
              <div className="flex flex-wrap items-center justify-between gap-4 pr-6">
                <div className="flex items-center gap-3">
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10">
                    <Activity className="h-5 w-5 text-primary" />
                  </div>

                  <div>
                    <h2 className="font-semibold text-base-content">
                      Intervals.icu
                    </h2>

                    <p className="text-sm text-base-content/60">
                      Activités, charge d&apos;entraînement et récupération.
                    </p>
                  </div>
                </div>

                <ConnectionBadge
                  connected={
                    connection?.configured === true &&
                    connection.enabled
                  }
                />
              </div>
            </div>

            <div className="collapse-content">
              <div className="border-t border-base-300 pt-5">
                <div className="grid gap-5 sm:grid-cols-2">
                  <fieldset className="fieldset">
                    <label className="fieldset-legend">
                      Athlete ID
                    </label>

                    <input
                      value={athleteId}
                      onChange={(event) => {
                        setAthleteId(
                          event.target.value,
                        )

                        setConnectionTested(false)
                        setMessage(null)
                      }}
                      placeholder="i123456"
                      className="input input-bordered w-full"
                    />
                  </fieldset>

                  <fieldset className="fieldset">
                    <label className="fieldset-legend">
                      API Key
                    </label>

                    <input
                      type="password"
                      value={apiKey}
                      onChange={(event) => {
                        setApiKey(
                          event.target.value,
                        )

                        setConnectionTested(false)
                        setMessage(null)
                      }}
                      placeholder={
                        connection?.api_key_configured
                          ? 'Clé déjà configurée'
                          : 'Votre clé API Intervals.icu'
                      }
                      autoComplete="off"
                      className="input input-bordered w-full"
                    />

                    {connection?.api_key_configured && (
                      <p className="mt-1 text-xs text-base-content/50">
                        Laissez vide pour conserver la clé actuelle.
                      </p>
                    )}
                  </fieldset>
                </div>

                <div className="mt-5 flex items-center justify-between gap-4 rounded-xl bg-base-200 p-4">
                  <div>
                    <p className="font-medium text-base-content">
                      Connexion activée
                    </p>

                    <p className="mt-1 text-xs text-base-content/50">
                      Autorise OpenCoach à utiliser cette intégration.
                    </p>
                  </div>

                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={(event) => {
                      setEnabled(
                        event.target.checked,
                      )
                    }}
                    className="toggle toggle-primary"
                  />
                </div>

                {error && (
                  <div className="alert alert-error mt-4">
                    <span>
                      {error}
                    </span>
                  </div>
                )}

                {message && (
                  <div className="alert alert-success mt-4">
                    <CheckCircle2 className="h-5 w-5" />

                    <span>
                      {message}
                    </span>
                  </div>
                )}

                <div className="mt-6 flex flex-wrap justify-end gap-3 border-t border-base-300 pt-5">
                  <button
                    type="button"
                    onClick={handleTest}
                    disabled={
                      testing ||
                      saving
                    }
                    className="btn btn-outline"
                  >
                    {testing && (
                      <span className="loading loading-spinner loading-sm" />
                    )}

                    Tester
                  </button>

                  <button
                    type="button"
                    onClick={handleSave}
                    disabled={
                      saving ||
                      testing ||
                      !connectionTested
                    }
                    className="btn btn-primary"
                  >
                    {saving && (
                      <span className="loading loading-spinner loading-sm" />
                    )}

                    Enregistrer
                  </button>
                </div>

                {!connectionTested && apiKey.trim() && (
                  <p className="mt-3 text-right text-xs text-base-content/50">
                    Testez la connexion avant de pouvoir enregistrer.
                  </p>
                )}
              </div>
            </div>
          </section>

          <ComingSoonConnection
            icon={
              <Radio className="h-5 w-5" />
            }
            name="Strava"
            description="Synchronisation des activités et segments."
          />

          <ComingSoonConnection
            icon={
              <MessageCircle className="h-5 w-5" />
            }
            name="Telegram"
            description="Notifications et échanges avec OpenCoach."
          />

          <ComingSoonConnection
            icon={
              <Watch className="h-5 w-5" />
            }
            name="Suunto"
            description="Connexion directe à l'écosystème Suunto."
          />
        </div>
      </div>
    </main>
  )
}


function ConnectionBadge({
  connected,
}: {
  connected: boolean
}) {
  return (
    <div
      className={[
        'badge gap-2',
        connected
          ? 'badge-success'
          : 'badge-ghost',
      ].join(' ')}
    >
      <span className="size-2 rounded-full bg-current" />

      {connected
        ? 'Connecté'
        : 'Non connecté'}
    </div>
  )
}


function ComingSoonConnection({
  icon,
  name,
  description,
}: {
  icon: React.ReactNode
  name: string
  description: string
}) {
  return (
    <section className="collapse collapse-arrow border border-base-300 bg-base-100 shadow-sm">
      <input
        type="checkbox"
      />

      <div className="collapse-title">
        <div className="flex items-center justify-between gap-4 pr-6">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-base-200 text-base-content/60">
              {icon}
            </div>

            <div>
              <h2 className="font-semibold text-base-content">
                {name}
              </h2>

              <p className="text-sm text-base-content/50">
                {description}
              </p>
            </div>
          </div>

          <span className="badge badge-ghost">
            Bientôt
          </span>
        </div>
      </div>

      <div className="collapse-content">
        <div className="border-t border-base-300 pt-5">
          <p className="text-sm text-base-content/60">
            Cette connexion sera configurable dans une prochaine version d&apos;OpenCoach.
          </p>
        </div>
      </div>
    </section>
  )
}


function getErrorMessage(
  reason: unknown,
): string {
  return reason instanceof Error
    ? reason.message
    : 'Une erreur inattendue est survenue.'
}