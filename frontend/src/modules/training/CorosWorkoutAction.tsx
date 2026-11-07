import {
  AlertTriangle,
  CheckCircle2,
  CloudUpload,
  RefreshCw,
  ShieldAlert,
  X,
} from 'lucide-react'

import {
  useState,
} from 'react'

import {
  pushTrainingSessionToCoros,
} from '../../core/training/api'

import {
  TRAINING_SESSION_UPDATED_EVENT,
} from '../../core/events'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import type {
  TrainingSession,
} from './types'


interface CorosWorkoutActionProps {
  session: TrainingSession
}


export function CorosWorkoutAction({
  session,
}: CorosWorkoutActionProps) {
  const { toast } = useToast()
  const [saving, setSaving] = useState(false)
  const [confirmationOpen, setConfirmationOpen] = useState(false)
  const [confirmedNoDuplicate, setConfirmedNoDuplicate] = useState(false)

  const normalizedSport = session.sportType
    .trim()
    .toLowerCase()
    .replace(/[\s_-]/g, '')

  const supportedSport = [
    'run',
    'running',
    'trailrun',
    'trailrunning',
    'ride',
    'cycling',
    'bike',
  ].includes(normalizedSport)

  if (
    session.status !== 'planned'
    || session.type === 'rest'
    || !supportedSport
  ) {
    return null
  }

  if (!session.prescription) {
    return (
      <div
        className="
          mt-2
          rounded-[9px]
          border
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]/[0.025]
          px-3
          py-2
          text-[10px]
          leading-4
          text-[var(--oc-muted)]
        "
      >
        Envoi COROS indisponible : cette séance n’a pas de prescription
        structurée. Les séances saisies manuellement ne contiennent pas
        encore les phases et les cibles nécessaires à la montre.
      </div>
    )
  }

  const pendingInProgress = (
    session.corosSyncStatus === 'pending'
    && Boolean(session.corosSyncStartedAt)
    && Date.now() - new Date(
      session.corosSyncStartedAt as string,
    ).getTime() < 5 * 60 * 1000
  )

  const needsConfirmation = (
    session.corosSyncStatus === 'unknown'
    || (
      session.corosSyncStatus === 'pending'
      && !pendingInProgress
    )
  )

  const alreadySynced = (
    session.corosSyncStatus === 'synced'
  )

  function openConfirmation(): void {
    if (saving || pendingInProgress) {
      return
    }
    setConfirmedNoDuplicate(false)
    setConfirmationOpen(true)
  }

  async function sendToCoros(): Promise<void> {
    if (saving || pendingInProgress) {
      return
    }
    if (needsConfirmation && !confirmedNoDuplicate) {
      return
    }

    setSaving(true)
    try {
      const result = await pushTrainingSessionToCoros(
        session.id,
        needsConfirmation,
      )
      setConfirmationOpen(false)
      window.dispatchEvent(
        new Event(TRAINING_SESSION_UPDATED_EVENT),
      )
      toast({
        type: 'success',
        title: alreadySynced
          ? 'Vérification COROS terminée'
          : 'Séance envoyée à COROS',
        message: result.message,
      })
    } catch (error) {
      setConfirmationOpen(false)
      toast({
        type: 'error',
        title: 'Envoi COROS impossible',
        message: error instanceof Error
          ? error.message
          : 'Une erreur inattendue est survenue.',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="mt-2">
      <button
        type="button"
        disabled={saving || pendingInProgress}
        onClick={openConfirmation}
        title={session.corosSyncError ?? undefined}
        className="
          inline-flex
          min-h-9
          w-full
          items-center
          justify-center
          gap-2
          rounded-[9px]
          border
          border-sky-500/20
          bg-sky-500/[0.055]
          px-3
          text-[11px]
          font-semibold
          text-sky-700
          transition
          hover:border-sky-500/35
          hover:bg-sky-500/[0.09]
          disabled:cursor-not-allowed
          disabled:opacity-45
          dark:text-sky-300
        "
      >
        {saving || pendingInProgress ? (
          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
        ) : needsConfirmation ? (
          <AlertTriangle className="h-3.5 w-3.5" />
        ) : session.corosSyncStatus === 'failed' || alreadySynced ? (
          <RefreshCw className="h-3.5 w-3.5" />
        ) : (
          <CloudUpload className="h-3.5 w-3.5" />
        )}
        {saving || pendingInProgress
          ? 'Envoi COROS en cours…'
          : needsConfirmation
            ? 'Vérifier COROS puis réessayer'
            : alreadySynced
              ? 'Mettre à jour dans COROS'
              : session.corosSyncStatus === 'failed'
                ? 'Réessayer l’envoi COROS'
                : 'Envoyer vers COROS'}
      </button>
      {session.corosSyncError && (
        <p
          className="
            mt-1.5
            px-1
            text-[10px]
            leading-4
            text-[var(--oc-text-secondary)]
          "
        >
          {session.corosSyncError}
        </p>
      )}

      {confirmationOpen && (
        <div
          className="
            fixed inset-0 z-[100]
            flex items-center justify-center
            bg-slate-950/45
            px-4 py-6
            backdrop-blur-[3px]
          "
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !saving) {
              setConfirmationOpen(false)
            }
          }}
        >
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="coros-confirm-title"
            className="
              w-full max-w-[420px]
              overflow-hidden rounded-2xl
              border border-[var(--oc-border)]
              bg-[var(--oc-surface-raised)]
              shadow-2xl
            "
          >
            <header className="flex items-start gap-3 border-b border-[var(--oc-border)] px-5 py-4">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-sky-500/10 text-sky-600 dark:text-sky-300">
                {needsConfirmation
                  ? <ShieldAlert className="h-5 w-5" />
                  : <CloudUpload className="h-5 w-5" />}
              </span>
              <div className="min-w-0 flex-1">
                <h2 id="coros-confirm-title" className="text-sm font-semibold text-[var(--oc-text)]">
                  {needsConfirmation
                    ? 'Vérification avant nouvel envoi'
                    : alreadySynced
                      ? 'Mettre à jour la séance COROS'
                      : 'Envoyer la séance vers COROS'}
                </h2>
                <p className="mt-1 text-xs leading-5 text-[var(--oc-text-secondary)]">
                  {session.title} · {formatDate(session.date)}
                </p>
              </div>
              <button
                type="button"
                aria-label="Fermer"
                disabled={saving}
                onClick={() => setConfirmationOpen(false)}
                className="rounded-lg p-1.5 text-[var(--oc-text-secondary)] transition hover:bg-[var(--oc-surface-hover)]"
              >
                <X className="h-4 w-4" />
              </button>
            </header>

            <div className="space-y-3 px-5 py-4">
              {needsConfirmation ? (
                <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.06] p-3">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
                    <div>
                      <p className="text-xs font-semibold text-[var(--oc-text)]">
                        Le résultat du précédent envoi est incertain.
                      </p>
                      <p className="mt-1 text-xs leading-5 text-[var(--oc-text-secondary)]">
                        Consulte le calendrier COROS à cette date. Ne relance l’envoi que si cette séance est absente.
                      </p>
                    </div>
                  </div>
                  <label className="mt-3 flex cursor-pointer items-start gap-2 border-t border-amber-500/15 pt-3 text-xs leading-5 text-[var(--oc-text)]">
                    <input
                      type="checkbox"
                      checked={confirmedNoDuplicate}
                      onChange={(event) => setConfirmedNoDuplicate(event.target.checked)}
                      className="mt-1 accent-amber-600"
                    />
                    <span>J’ai vérifié le calendrier COROS et confirmé que cette séance n’y figure pas.</span>
                  </label>
                </div>
              ) : (
                <>
                  <p className="text-xs leading-5 text-[var(--oc-text-secondary)]">
                    {alreadySynced
                      ? 'La version actuelle de la séance sera comparée à celle de COROS. Si elle a changé, la séance existante sera mise à jour sans en créer une seconde.'
                      : 'Cette séance sera ajoutée à ton calendrier COROS. Elle sera ensuite transférable vers ta montre après synchronisation avec l’application COROS.'}
                  </p>
                  <div className="flex items-center justify-between rounded-xl border border-[var(--oc-border)] bg-[var(--oc-surface-muted)] px-3 py-2.5">
                    <span className="text-xs text-[var(--oc-text-secondary)]">Durée prévue</span>
                    <span className="text-sm font-semibold tabular-nums text-[var(--oc-text)]">{session.durationMinutes} min</span>
                  </div>
                </>
              )}
            </div>

            <footer className="flex justify-end gap-2 border-t border-[var(--oc-border)] bg-[var(--oc-surface-muted)]/60 px-5 py-3">
              <button
                type="button"
                disabled={saving}
                onClick={() => setConfirmationOpen(false)}
                className="rounded-lg px-3 py-2 text-xs font-medium text-[var(--oc-text-secondary)] transition hover:bg-[var(--oc-surface-hover)]"
              >
                Annuler
              </button>
              <button
                type="button"
                disabled={saving || (needsConfirmation && !confirmedNoDuplicate)}
                onClick={() => void sendToCoros()}
                className="inline-flex items-center gap-2 rounded-lg bg-sky-600 px-3.5 py-2 text-xs font-semibold text-white transition hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-40"
              >
                {saving
                  ? <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  : <CheckCircle2 className="h-3.5 w-3.5" />}
                {saving
                  ? 'Envoi en cours…'
                  : needsConfirmation
                    ? 'Confirmer et réessayer'
                    : alreadySynced
                      ? 'Vérifier et mettre à jour'
                      : 'Confirmer l’envoi'}
              </button>
            </footer>
          </section>
        </div>
      )}
    </div>
  )
}


function formatDate(value: string): string {
  return new Date(
    `${value}T12:00:00`,
  ).toLocaleDateString(
    'fr-FR',
    {
      day: 'numeric',
      month: 'long',
    },
  )
}
