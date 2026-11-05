import {
  Activity,
  Check,
  CircleAlert,
  KeyRound,
  Link2,
  LoaderCircle,
  Pencil,
  RefreshCw,
  UserRound,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import {
  fetchInitialSyncStatus,
  fetchIntervalsConnection,
  saveIntervalsConnection,
  startInitialSync,
  syncIntervals,
  testIntervalsConnection,
  testSavedIntervalsConnection,
  type IntervalsConnection,
} from '../../core/integrations'


export function IntervalsSection() {
  const {
    toast,
    dismissToast,
  } = useToast()

  const [
    connection,
    setConnection,
  ] = useState<
    IntervalsConnection | null
  >(null)

  const [
    athleteId,
    setAthleteId,
  ] = useState('')

  const [
    apiKey,
    setApiKey,
  ] = useState('')

  const [
    enabled,
    setEnabled,
  ] = useState(true)

  const [
    editing,
    setEditing,
  ] = useState(false)

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    testing,
    setTesting,
  ] = useState(false)

  const [
    syncing,
    setSyncing,
  ] = useState(false)

  const [
    connectionTested,
    setConnectionTested,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null)

  const [
    message,
    setMessage,
  ] = useState<
    string | null
  >(null)


  useEffect(() => {
    let mounted = true

    fetchIntervalsConnection()
      .then(result => {
        if (!mounted) {
          return
        }

        setConnection(result)

        setAthleteId(
          result.athlete_id
          ?? '',
        )

        setEnabled(
          result.enabled,
        )
      })
      .catch(
        (reason: unknown) => {
          if (!mounted) {
            return
          }

          setError(
            getErrorMessage(
              reason,
            ),
          )
        },
      )
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

      if (
        !normalizedAthleteId
      ) {
        throw new Error(
          "L'identifiant athlète "
          + 'est obligatoire.',
        )
      }

      if (normalizedApiKey) {
        await testIntervalsConnection(
          normalizedAthleteId,
          normalizedApiKey,
        )
      } else {
        if (
          !connection
            ?.api_key_configured
        ) {
          throw new Error(
            'Saisissez une clé API '
            + 'pour tester la connexion.',
          )
        }

        await testSavedIntervalsConnection()
      }

      setConnectionTested(true)

      setMessage(
        'Connexion testée avec succès.',
      )
    } catch (reason) {
      setConnectionTested(false)

      setError(
        getErrorMessage(
          reason,
        ),
      )
    } finally {
      setTesting(false)
    }
  }


  async function waitForInitialSync(
    jobId: string,
  ) {
    const startedAt =
      Date.now()

    const timeoutMs =
      15 * 60 * 1000

    while (true) {
      const status =
        await fetchInitialSyncStatus(
          jobId,
        )

      if (
        status.status === 'success'
      ) {
        return status
      }

      if (
        status.status === 'error'
      ) {
        throw new Error(
          status.error
          || (
            'La synchronisation initiale '
            + 'a échoué.'
          ),
        )
      }

      if (
        Date.now() - startedAt
        > timeoutMs
      ) {
        throw new Error(
          'La synchronisation initiale '
          + 'dépasse 15 minutes.',
        )
      }

      await new Promise<void>(
        resolve => {
          window.setTimeout(
            resolve,
            2000,
          )
        },
      )
    }
  }


  async function handleSave() {
    setSaving(true)
    setError(null)
    setMessage(null)

    const requiresInitialSync =
      connection?.last_synced_at == null

    try {
      const result =
        await saveIntervalsConnection({
          athlete_id:
            athleteId.trim(),

          api_key:
            apiKey.trim()
            || null,

          enabled,
        })

      setConnection(result)
      setApiKey('')
      setConnectionTested(false)
      setEditing(false)

      if (
        requiresInitialSync
        && result.enabled
      ) {
        const loadingToastId =
          toast({
            type: 'info',
            title:
              'Chargement des activités',
          message:
            'OpenCoach récupère jusqu’à '
            + '3 mois de données Intervals.icu. '
            + 'Cette première synchronisation '
            + 'peut prendre plusieurs minutes.',
          duration: null,
        })

        setSyncing(true)

        try {
          const job =
            await startInitialSync()

          const syncResult =
            await waitForInitialSync(
              job.job_id,
            )

          const refreshedConnection =
            await fetchIntervalsConnection()

          setConnection(
            refreshedConnection,
          )

          dismissToast(
            loadingToastId,
          )

          toast({
            type: 'success',
            title:
              'Historique chargé',
            message: [
              (
                `${syncResult.synced_activities} `
                + 'activité(s)'
              ),
              (
                `${syncResult.synced_wellness_days} `
                + 'jour(s) Wellness'
              ),
              (
                `${syncResult.days} jours importés`
              ),
            ].join(' · '),
          })
        } catch (reason) {
          dismissToast(
            loadingToastId,
          )

          toast({
            type: 'error',
            title:
              'Import initial incomplet',
            message:
              getErrorMessage(
                reason,
              ),
            duration: null,
          })
        } finally {
          setSyncing(false)
        }

        return
      }

      setMessage(
        'Configuration enregistrée.',
      )

      window.setTimeout(
        () => setMessage(null),
        2000,
      )
    } catch (reason) {
      setError(
        getErrorMessage(
          reason,
        ),
      )
    } finally {
      setSaving(false)
    }
  }


  async function handleSync() {
    if (
      !connection?.configured
      || !connection.enabled
    ) {
      return
    }

    setSyncing(true)

    try {
      const result =
        await syncIntervals(7)

      setConnection(
        current => {
          if (!current) {
            return current
          }

          return {
            ...current,

            last_synced_at:
              result.synced_at,
          }
        },
      )

      toast({
        type: 'info',
        title:
          'Synchronisation terminée',

        message: [
          (
            `${result.synced_activities} `
            + 'activité(s)'
          ),
          (
            `${result.synced_wellness_days} `
            + 'jour(s) Wellness'
          ),
        ].join(' · '),
      })
    } catch (reason) {
      toast({
        type: 'error',

        title:
          'Échec de la synchronisation',

        message:
          getErrorMessage(
            reason,
          ),

        duration: null,
      })
    } finally {
      setSyncing(false)
    }
  }


  function handleCancel() {
    setAthleteId(
      connection?.athlete_id
      ?? '',
    )

    setEnabled(
      connection?.enabled
      ?? true,
    )

    setApiKey('')
    setError(null)
    setMessage(null)
    setConnectionTested(false)
    setEditing(false)
  }


  if (loading) {
    return (
      <div
        className="
          flex
          min-h-[180px]
          items-center
          justify-center
          rounded-[12px]
          border
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]
          dark:border-white/[0.065]
          dark:bg-[var(--oc-surface)]
        "
      >
        <div
          className="
            flex
            items-center
            gap-2
            text-[10.5px]
            text-[var(--oc-muted-soft)]
          "
        >
          <LoaderCircle
            className="
              h-4
              w-4
              animate-spin
              text-emerald-500
            "
          />

          Chargement d’Intervals.icu…
        </div>
      </div>
    )
  }


  const connected =
    connection?.configured
    === true
    && connection.enabled


  return (
    <div
      className="
        overflow-hidden
        rounded-[12px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]
        dark:border-white/[0.065]
        dark:bg-[var(--oc-surface)]
      "
    >

      {/* SERVICE HERO */}

      <div
        className="
          relative
          overflow-hidden
          px-4
          py-4
        "
      >
        <div
          className="
            pointer-events-none
            absolute
            -right-16
            -top-20
            h-44
            w-44
            rounded-full
            bg-emerald-500/[0.05]
            blur-3xl
          "
        />

        <div
          className="
            relative
            flex
            items-start
            justify-between
            gap-3
          "
        >
          <div
            className="
              flex
              min-w-0
              items-start
              gap-3
            "
          >
            <div
              className="
                flex
                h-10
                w-10
                shrink-0
                items-center
                justify-center
                rounded-[11px]
                bg-emerald-50
                text-emerald-600
                dark:bg-emerald-500/[0.08]
                dark:text-emerald-400
              "
            >
              <Activity
                className="
                  h-[18px]
                  w-[18px]
                "
              />
            </div>

            <div className="min-w-0">
              <div
                className="
                  flex
                  items-center
                  gap-2
                "
              >
                <h3
                  className="
                    text-[15px]
                    font-bold
                    tracking-[-0.02em]
                    text-[var(--oc-text)]
                    dark:text-white
                  "
                >
                  Intervals.icu
                </h3>

                <ConnectionStatus
                  connected={
                    connected
                  }
                />
              </div>

              <p
                className="
                  mt-1
                  text-[10px]
                  text-[var(--oc-muted-soft)]
                  dark:text-[var(--oc-muted)]
                "
              >
                Activités, récupération
                et charge d'entraînement.
              </p>
            </div>
          </div>


          {!editing && (
            <button
              type="button"
              onClick={() =>
                setEditing(true)
              }
              className="
                flex
                h-8
                shrink-0
                items-center
                gap-1.5
                rounded-[8px]
                border
                border-[var(--oc-border)]
                px-2.5
                text-[10px]
                font-semibold
                text-[var(--oc-muted)]
                transition
                hover:bg-[var(--oc-surface-muted)]
                hover:text-[var(--oc-text)]
                dark:border-white/[0.065]
                dark:text-[var(--oc-muted-soft)]
                dark:hover:bg-[var(--oc-surface-hover)]
                dark:hover:text-white
              "
            >
              <Pencil
                className="
                  h-3
                  w-3
                "
              />

              <span className="hidden sm:inline">
                Configuration
              </span>
            </button>
          )}
        </div>
      </div>


      {editing ? (

        /* CONFIGURATION */

        <div
          className="
            border-t
            border-[var(--oc-border)]
            px-4
            py-4
            dark:border-white/[0.06]
          "
        >
          <div
            className="
              grid
              gap-3
              sm:grid-cols-2
            "
          >
            <ConnectionField
              icon={UserRound}
              label="Athlete ID"
              value={athleteId}
              placeholder="i123456"
              onChange={value => {
                setAthleteId(value)
                setConnectionTested(false)
                setMessage(null)
              }}
            />

            <ConnectionField
              icon={KeyRound}
              label="API Key"
              value={apiKey}
              type="password"
              placeholder={
                connection
                  ?.api_key_configured
                  ? 'Clé déjà configurée'
                  : 'Votre clé API'
              }
              onChange={value => {
                setApiKey(value)
                setConnectionTested(false)
                setMessage(null)
              }}
            />
          </div>


          {connection
            ?.api_key_configured
            && (
              <p
                className="
                  mt-2
                  text-[9px]
                  text-[var(--oc-muted-soft)]
                  dark:text-[var(--oc-muted)]
                "
              >
                Laisse la clé vide pour
                conserver la clé actuelle.
              </p>
            )}


          <div
            className="
              mt-3
              flex
              items-center
              justify-between
              gap-4
              rounded-[10px]
              bg-[var(--oc-surface-muted)]
              px-3
              py-2.5
              dark:bg-[var(--oc-surface-muted)]
            "
          >
            <div>
              <p
                className="
                  text-[10.5px]
                  font-semibold
                  text-[var(--oc-text-secondary)]
                  dark:text-[var(--oc-text-secondary)]
                "
              >
                Intégration active
              </p>

              <p
                className="
                  mt-0.5
                  text-[9px]
                  text-[var(--oc-muted-soft)]
                "
              >
                Autorise OpenCoach à
                utiliser cette connexion.
              </p>
            </div>

            <ModernToggle
              checked={enabled}
              onChange={setEnabled}
            />
          </div>


          {error && (
            <StatusMessage
              error
              message={error}
            />
          )}

          {message && (
            <StatusMessage
              message={message}
            />
          )}


          <div
            className="
              mt-4
              flex
              flex-wrap
              items-center
              justify-end
              gap-2
              border-t
              border-[var(--oc-border)]
              pt-3
              dark:border-white/[0.06]
            "
          >
            <button
              type="button"
              onClick={handleCancel}
              className="
                h-8
                rounded-[8px]
                px-3
                text-[10px]
                font-semibold
                text-[var(--oc-muted-soft)]
                hover:bg-[var(--oc-surface-muted)]
                hover:text-[var(--oc-text-secondary)]
                dark:hover:bg-[var(--oc-surface-hover)]
              "
            >
              Annuler
            </button>

            <button
              type="button"
              disabled={
                testing
                || saving
                || syncing
              }
              onClick={() =>
                void handleTest()
              }
              className="
                flex
                h-8
                items-center
                gap-1.5
                rounded-[8px]
                border
                border-[var(--oc-border)]
                px-3
                text-[10px]
                font-semibold
                text-[var(--oc-text-secondary)]
                transition
                hover:bg-[var(--oc-surface-muted)]
                disabled:opacity-40
                dark:border-white/[0.07]
                dark:text-[var(--oc-text-secondary)]
                dark:hover:bg-[var(--oc-surface-hover)]
              "
            >
              {testing && (
                <LoaderCircle
                  className="
                    h-3
                    w-3
                    animate-spin
                  "
                />
              )}

              Tester
            </button>

            <button
              type="button"
              disabled={
                saving
                || testing
                || syncing
                || !connectionTested
              }
              onClick={() =>
                void handleSave()
              }
              className="
                flex
                h-8
                items-center
                gap-1.5
                rounded-[8px]
                bg-emerald-600
                px-3
                text-[10px]
                font-semibold
                text-white
                transition
                hover:bg-emerald-700
                disabled:cursor-not-allowed
                disabled:bg-[var(--oc-surface-muted)]
                disabled:text-[var(--oc-muted-soft)]
                dark:disabled:bg-[var(--oc-surface-muted)]
                dark:disabled:text-[var(--oc-text-secondary)]
              "
            >
              {saving && (
                <LoaderCircle
                  className="
                    h-3
                    w-3
                    animate-spin
                  "
                />
              )}

              Enregistrer
            </button>
          </div>


          {!connectionTested
            && apiKey.trim()
            && (
              <p
                className="
                  mt-2
                  text-right
                  text-[9px]
                  text-[var(--oc-muted-soft)]
                "
              >
                Teste la connexion avant
                l'enregistrement.
              </p>
            )}
        </div>

      ) : (

        /* SERVICE DASHBOARD */

        <>
          <div
            className="
              grid
              grid-cols-2
              border-t
              border-[var(--oc-border)]
              dark:border-white/[0.06]
              sm:grid-cols-3
            "
          >
            <ServiceMetric
              label="Athlete ID"
              value={
                connection
                  ?.athlete_id
                || '—'
              }
              icon={UserRound}
            />

            <ServiceMetric
              label="Clé API"
              value={
                connection
                  ?.api_key_configured
                  ? 'Configurée'
                  : 'Absente'
              }
              icon={KeyRound}
            />

            <ServiceMetric
              label="État"
              value={
                connected
                  ? 'Actif'
                  : (
                      connection
                        ?.configured
                        ? 'Désactivé'
                        : 'Non configuré'
                    )
              }
              icon={Link2}
              className="
                col-span-2
                border-t
                border-[var(--oc-border)]
                dark:border-white/[0.06]
                sm:col-span-1
                sm:border-t-0
              "
            />
          </div>


          <div
            className="
              flex
              flex-col
              gap-3
              border-t
              border-[var(--oc-border)]
              bg-[var(--oc-surface-muted)]
              px-4
              py-3
              dark:border-white/[0.06]
              dark:bg-[var(--oc-surface-muted)]
              sm:flex-row
              sm:items-center
              sm:justify-between
            "
          >
            <div>
              <p
                className="
                  text-[9px]
                  font-semibold
                  uppercase
                  tracking-[0.08em]
                  text-[var(--oc-muted-soft)]
                  dark:text-[var(--oc-muted)]
                "
              >
                Dernière synchronisation
              </p>

              <p
                className="
                  mt-1
                  text-[11px]
                  font-semibold
                  text-[var(--oc-text-secondary)]
                  dark:text-[var(--oc-text-secondary)]
                "
              >
                {
                  connection
                    ?.last_synced_at
                    ? (
                        formatRelativeSyncTime(
                          connection
                            .last_synced_at,
                        )
                      )
                    : (
                        'Aucune synchronisation'
                      )
                }
              </p>
            </div>


            <button
              type="button"
              onClick={() =>
                void handleSync()
              }
              disabled={
                syncing
                || saving
                || testing
                || !connected
              }
              className="
                flex
                h-8
                items-center
                justify-center
                gap-1.5
                rounded-[8px]
                border
                border-[var(--oc-border)]
                bg-[var(--oc-surface)]
                px-3
                text-[10px]
                font-semibold
                text-[var(--oc-text-secondary)]
                transition
                hover:border-emerald-500/20
                hover:text-emerald-700
                disabled:cursor-not-allowed
                disabled:opacity-40
                dark:border-white/[0.07]
                dark:bg-[var(--oc-surface-muted)]
                dark:text-[var(--oc-text-secondary)]
              "
            >
              {
                syncing
                  ? (
                      <LoaderCircle
                        className="
                          h-3
                          w-3
                          animate-spin
                        "
                      />
                    )
                  : (
                      <RefreshCw
                        className="
                          h-3
                          w-3
                        "
                      />
                    )
              }

              {
                syncing
                  ? 'Synchronisation…'
                  : 'Synchroniser'
              }
            </button>
          </div>


          {message && (
            <div className="px-4 pb-3">
              <StatusMessage
                message={message}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}


function ConnectionStatus({
  connected,
}: {
  connected: boolean
}) {
  return (
    <span
      className={[
        (
          'inline-flex items-center '
          + 'gap-1 rounded-full '
          + 'px-1.5 py-0.5 '
          + 'text-[8.5px] '
          + 'font-semibold'
        ),
        connected
          ? (
              'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/[0.08] '
              + 'dark:text-emerald-400'
            )
          : (
              'bg-[var(--oc-surface-muted)] '
              + 'text-[var(--oc-muted-soft)] '
              + 'dark:bg-[var(--oc-surface-muted)] '
              + 'dark:text-[var(--oc-muted)]'
            ),
      ].join(' ')}
    >
      <span
        className={[
          (
            'h-1.5 w-1.5 '
            + 'rounded-full'
          ),
          connected
            ? 'bg-emerald-500'
            : 'bg-[var(--oc-muted-soft)]',
        ].join(' ')}
      />

      {
        connected
          ? 'Connecté'
          : 'Non connecté'
      }
    </span>
  )
}


function ServiceMetric({
  label,
  value,
  icon: Icon,
  className = '',
}: {
  label: string
  value: string
  icon: typeof Activity
  className?: string
}) {
  return (
    <div
      className={[
        (
          'px-4 py-3 '
          + 'sm:not-last:border-r '
          + 'sm:not-last:border-[var(--oc-border)] '
          + 'dark:sm:not-last:border-white/[0.06]'
        ),
        className,
      ].join(' ')}
    >
      <div
        className="
          flex
          items-center
          gap-1.5
          text-[var(--oc-muted-soft)]
        "
      >
        <Icon
          className="
            h-3
            w-3
          "
        />

        <span
          className="
            text-[8.5px]
            font-semibold
            uppercase
            tracking-[0.07em]
          "
        >
          {label}
        </span>
      </div>

      <p
        className="
          mt-1.5
          truncate
          text-[11px]
          font-semibold
          text-[var(--oc-text-secondary)]
          dark:text-[var(--oc-text-secondary)]
        "
      >
        {value}
      </p>
    </div>
  )
}


function ConnectionField({
  label,
  value,
  onChange,
  placeholder,
  icon: Icon,
  type = 'text',
}: {
  label: string
  value: string
  onChange:
    (value: string) => void
  placeholder?: string
  icon: typeof Activity
  type?: string
}) {
  return (
    <label>
      <span
        className="
          mb-1.5
          block
          text-[9px]
          font-semibold
          uppercase
          tracking-[0.07em]
          text-[var(--oc-muted-soft)]
          dark:text-[var(--oc-muted)]
        "
      >
        {label}
      </span>

      <div
        className="
          flex
          h-10
          items-center
          rounded-[9px]
          border
          border-[var(--oc-border)]
          bg-[var(--oc-surface-muted)]
          px-3
          focus-within:border-emerald-500/40
          focus-within:ring-2
          focus-within:ring-emerald-500/[0.08]
          dark:border-white/[0.07]
          dark:bg-[var(--oc-surface-muted)]
        "
      >
        <Icon
          className="
            mr-2
            h-3.5
            w-3.5
            shrink-0
            text-[var(--oc-muted-soft)]
            dark:text-[var(--oc-text-secondary)]
          "
        />

        <input
          type={type}
          value={value}
          placeholder={placeholder}
          autoComplete="off"
          onChange={
            event =>
              onChange(
                event.target.value,
              )
          }
          className="
            min-w-0
            flex-1
            bg-transparent
            text-[11px]
            font-medium
            text-[var(--oc-text)]
            outline-none
            placeholder:text-[var(--oc-muted-soft)]
            dark:text-[var(--oc-text)]
            dark:placeholder:text-[var(--oc-text-secondary)]
          "
        />
      </div>
    </label>
  )
}


function ModernToggle({
  checked,
  onChange,
}: {
  checked: boolean
  onChange:
    (value: boolean) => void
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={
        checked
          ? 'Désactiver l’intégration'
          : 'Activer l’intégration'
      }
      onClick={() =>
        onChange(!checked)
      }
      className={[
        (
          'relative inline-flex '
          + 'h-[24px] w-[42px] '
          + 'shrink-0 items-center '
          + 'rounded-full border '
          + 'transition-all duration-200 '
          + 'focus-visible:outline-none '
          + 'focus-visible:ring-2 '
          + 'focus-visible:ring-emerald-500/20'
        ),
        checked
          ? (
              'border-emerald-600 '
              + 'bg-emerald-600 '
              + 'shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]'
            )
          : (
              'border-[var(--oc-border)] '
              + 'bg-[var(--oc-surface-muted)] '
              + 'dark:border-white/[0.08] '
              + 'dark:bg-[var(--oc-surface-muted)]'
            ),
      ].join(' ')}
    >
      <span
        className={[
          (
            'absolute left-[3px] '
            + 'h-[16px] w-[16px] '
            + 'rounded-full bg-[var(--oc-surface)] '
            + 'shadow-[0_1px_3px_rgba(15,23,42,0.20)] '
            + 'transition-transform duration-200'
          ),
          checked
            ? 'translate-x-[18px]'
            : 'translate-x-0',
        ].join(' ')}
      />

      <span
        aria-hidden="true"
        className={[
          (
            'absolute h-[4px] w-[4px] '
            + 'rounded-full transition-opacity'
          ),
          checked
            ? (
                'left-[8px] '
                + 'bg-white/80 '
                + 'opacity-100'
              )
            : (
                'right-[8px] '
                + 'bg-slate-400/50 '
                + 'opacity-70 '
                + 'dark:bg-white/25'
              ),
        ].join(' ')}
      />
    </button>
  )
}


function StatusMessage({
  message,
  error = false,
}: {
  message: string
  error?: boolean
}) {
  return (
    <div
      className={[
        (
          'mt-3 flex items-start '
          + 'gap-2 rounded-[8px] '
          + 'px-2.5 py-2 '
          + 'text-[9.5px]'
        ),
        error
          ? (
              'bg-red-50 '
              + 'text-red-600 '
              + 'dark:bg-red-500/[0.06] '
              + 'dark:text-red-400'
            )
          : (
              'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/[0.07] '
              + 'dark:text-emerald-400'
            ),
      ].join(' ')}
    >
      {
        error
          ? (
              <CircleAlert
                className="
                  mt-px
                  h-3
                  w-3
                  shrink-0
                "
              />
            )
          : (
              <Check
                className="
                  mt-px
                  h-3
                  w-3
                  shrink-0
                "
              />
            )
      }

      {message}
    </div>
  )
}


function formatRelativeSyncTime(
  value: string,
): string {
  const normalizedValue =
    hasTimezoneInformation(
      value,
    )
      ? value
      : `${value}Z`

  const date =
    new Date(
      normalizedValue,
    )

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return 'Date inconnue'
  }

  const elapsedMilliseconds =
    Date.now()
    - date.getTime()

  const elapsedMinutes =
    Math.max(
      0,
      Math.floor(
        elapsedMilliseconds
        / 60_000,
      ),
    )

  if (elapsedMinutes < 1) {
    return "À l'instant"
  }

  if (elapsedMinutes < 60) {
    return (
      `Il y a ${
        elapsedMinutes
      } min`
    )
  }

  const elapsedHours =
    Math.floor(
      elapsedMinutes / 60,
    )

  if (elapsedHours < 24) {
    return (
      elapsedHours === 1
        ? 'Il y a 1 h'
        : (
            `Il y a ${
              elapsedHours
            } h`
          )
    )
  }

  const elapsedDays =
    Math.floor(
      elapsedHours / 24,
    )

  return (
    elapsedDays === 1
      ? 'Il y a 1 jour'
      : (
          `Il y a ${
            elapsedDays
          } jours`
        )
  )
}


function hasTimezoneInformation(
  value: string,
): boolean {
  return (
    value.endsWith('Z')
    || /[+-]\d{2}:\d{2}$/.test(
      value,
    )
  )
}


function getErrorMessage(
  reason: unknown,
): string {
  return (
    reason instanceof Error
      ? reason.message
      : (
          'Une erreur inattendue '
          + 'est survenue.'
        )
  )
}
