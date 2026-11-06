import {
  AlertTriangle,
  CheckCircle2,
  CloudUpload,
  RefreshCw,
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

  const normalizedSport = session.sportType
    .trim()
    .toLowerCase()
    .replace(/[\\s_-]/g, '')

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

  async function sendToCoros(): Promise<void> {
    if (saving || alreadySynced || pendingInProgress) {
      return
    }

    if (needsConfirmation) {
      const confirmed = window.confirm(
        'Le résultat du précédent envoi est incertain. '
        + 'Vérifie d’abord dans le calendrier COROS que cette séance '
        + 'n’existe pas déjà. Confirme uniquement si elle est absente.',
      )
      if (!confirmed) {
        return
      }
    } else {
      const confirmed = window.confirm(
        `Ajouter « ${session.title} » le ${formatDate(session.date)} `
        + 'au calendrier COROS ? La montre recevra la séance après '
        + 'synchronisation avec l’application COROS.',
      )
      if (!confirmed) {
        return
      }
    }

    setSaving(true)
    try {
      const result = await pushTrainingSessionToCoros(
        session.id,
        needsConfirmation,
      )
      window.dispatchEvent(
        new Event(TRAINING_SESSION_UPDATED_EVENT),
      )
      toast({
        type: 'success',
        title: 'Séance envoyée à COROS',
        message: result.message,
      })
    } catch (error) {
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

  if (alreadySynced) {
    return (
      <div
        className="
          mt-2
          flex
          items-center
          gap-2
          rounded-[9px]
          border
          border-emerald-500/20
          bg-emerald-500/[0.055]
          px-3
          py-2
          text-[11px]
          font-semibold
          text-emerald-700
          dark:text-emerald-400
        "
      >
        <CheckCircle2 className="h-3.5 w-3.5" />
        <span>
          <span className="block">Séance envoyée à COROS</span>
          <span className="mt-0.5 block font-normal text-[10px] opacity-80">
            Toute modification ou annulation doit aussi être faite dans COROS.
          </span>
        </span>
      </div>
    )
  }

  return (
    <div className="mt-2">
      <button
        type="button"
        disabled={saving || pendingInProgress}
        onClick={() => void sendToCoros()}
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
        ) : session.corosSyncStatus === 'failed' ? (
          <RefreshCw className="h-3.5 w-3.5" />
        ) : (
          <CloudUpload className="h-3.5 w-3.5" />
        )}
        {saving || pendingInProgress
          ? 'Envoi COROS en cours…'
          : needsConfirmation
            ? 'Vérifier COROS puis réessayer'
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
