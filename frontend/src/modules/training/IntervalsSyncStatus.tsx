import {
  CheckCircle2,
  Clock3,
  RefreshCw,
  TriangleAlert,
} from 'lucide-react'

import type {
  TrainingSession,
} from './types'


interface IntervalsSyncStatusProps {
  session: TrainingSession
  compact?: boolean
  header?: boolean
}


interface SyncPresentation {
  label: string
  detail?: string
  icon:
    typeof CheckCircle2
  className: string
}


export function IntervalsSyncStatus({
  session,
  compact = false,
  header = false,
}: IntervalsSyncStatusProps) {
  const presentation =
    getSyncPresentation(
      session,
    )

  if (!presentation) {
    return null
  }

  const Icon = presentation.icon

  if (header) {
    return (
      <div
        className="
          flex
          min-w-0
          items-center
          gap-1.5
          text-[10.5px]
        "
      >
        <Icon
          className={[
            'h-3.5 w-3.5 shrink-0 ',
            presentation.className,
          ].join(' ')}
        />

        <span
          className={[
            'font-medium ',
            presentation.className,
          ].join(' ')}
        >
          {presentation.label}
        </span>

        {presentation.detail && (
          <>
            <span
              className="
                text-slate-300
                dark:text-slate-700
              "
            >
              ·
            </span>

            <span
              className="
                truncate
                text-slate-400
                dark:text-slate-500
              "
            >
              {presentation.detail}
            </span>
          </>
        )}
      </div>
    )
  }

  if (compact) {
    return (
      <span
        className={[
          'mt-1 flex items-center gap-1 ',
          'text-[10.5px] font-medium ',
          presentation.className,
        ].join(' ')}
      >
        <Icon
          className="h-3 w-3 shrink-0"
        />

        <span>
          {presentation.label}
        </span>
      </span>
    )
  }

  return (
    <div
      className={[
        'mt-2.5 flex items-start gap-2.5 ',
        'rounded-[10px] border ',
        'border-black/[0.06] ',
        'bg-slate-50/70 px-3 py-2.5 ',
        'dark:border-white/[0.065] ',
        'dark:bg-white/[0.025]',
      ].join(' ')}
    >
      <Icon
        className={[
          'mt-0.5 h-4 w-4 shrink-0 ',
          presentation.className,
        ].join(' ')}
      />

      <div className="min-w-0">
        <p
          className={[
            'text-[11.5px] font-semibold ',
            presentation.className,
          ].join(' ')}
        >
          {presentation.label}
        </p>

        {presentation.detail && (
          <p
            className="
              mt-0.5
              text-[10.5px]
              leading-4
              text-slate-400
              dark:text-slate-500
            "
          >
            {presentation.detail}
          </p>
        )}

        {(
          session.intervalsSyncStatus
          === 'failed'
          && session.intervalsSyncError
        ) && (
          <p
            className="
              mt-1
              text-[10px]
              leading-4
              text-red-500
              dark:text-red-400
            "
          >
            {session.intervalsSyncError}
          </p>
        )}
      </div>
    </div>
  )
}


function getSyncPresentation(
  session: TrainingSession,
): SyncPresentation | null {
  switch (
    session.intervalsSyncStatus
  ) {
    case 'synced':
      return {
        label: 'Intervals.icu synchronisé',
        detail:
          formatLastSyncedAt(
            session.intervalsLastSyncedAt,
          ),
        icon: CheckCircle2,
        className:
          'text-emerald-600 dark:text-emerald-400',
      }

    case 'pending':
      return {
        label: 'Intervals.icu · En attente',
        detail:
          'La séance sera envoyée à Intervals.icu.',
        icon: Clock3,
        className:
          'text-slate-500 dark:text-slate-400',
      }

    case 'update_required':
      return {
        label:
          'Intervals.icu · Mise à jour nécessaire',
        detail:
          'La séance a changé depuis la dernière synchronisation.',
        icon: RefreshCw,
        className:
          'text-amber-600 dark:text-amber-400',
      }

    case 'failed':
      return {
        label:
          'Intervals.icu · Échec de synchronisation',
        detail:
          'La séance reste enregistrée dans OpenCoach.',
        icon: TriangleAlert,
        className:
          'text-red-600 dark:text-red-400',
      }

    case 'deleted':
      return {
        label:
          'Intervals.icu · Séance retirée',
        detail:
          session.intervalsLastSyncedAt
            ? formatLastSyncedAt(
                session.intervalsLastSyncedAt,
              )
            : undefined,
        icon: CheckCircle2,
        className:
          'text-slate-400 dark:text-slate-500',
      }

    default:
      return null
  }
}


function formatLastSyncedAt(
  value?: string,
): string | undefined {
  if (!value) {
    return undefined
  }

  /*
   * Les timestamps backend peuvent être sérialisés
   * sans suffixe de fuseau alors qu'ils représentent
   * une heure UTC.
   *
   * Sans cette normalisation, JavaScript interprète
   * une valeur telle que 2026-09-05T19:31:25
   * comme une heure locale.
   */
  const normalizedValue =
    hasExplicitTimezone(value)
      ? value
      : `${value}Z`

  const date =
    new Date(normalizedValue)

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return undefined
  }

  const elapsedMilliseconds =
    Math.max(
      0,
      Date.now() - date.getTime(),
    )

  const elapsedSeconds =
    Math.floor(
      elapsedMilliseconds / 1000,
    )

  if (elapsedSeconds < 60) {
    return 'À l\'instant'
  }

  const elapsedMinutes =
    Math.floor(
      elapsedSeconds / 60,
    )

  if (elapsedMinutes < 60) {
    return `Il y a ${elapsedMinutes} min`
  }

  const elapsedHours =
    Math.floor(
      elapsedMinutes / 60,
    )

  if (elapsedHours < 24) {
    return `Il y a ${elapsedHours} h`
  }

  const elapsedDays =
    Math.floor(
      elapsedHours / 24,
    )

  if (elapsedDays < 7) {
    return `Il y a ${elapsedDays} j`
  }

  if (elapsedDays < 30) {
    const weeks =
      Math.floor(
        elapsedDays / 7,
      )

    return `Il y a ${weeks} sem`
  }

  if (elapsedDays < 365) {
    const months =
      Math.floor(
        elapsedDays / 30,
      )

    return `Il y a ${months} mois`
  }

  const years =
    Math.floor(
      elapsedDays / 365,
    )

  return (
    `Il y a ${years} `
    + (
      years === 1
        ? 'an'
        : 'ans'
    )
  )
}


function hasExplicitTimezone(
  value: string,
): boolean {
  return (
    /Z$/i.test(value)
    || /[+-]\d{2}:?\d{2}$/.test(value)
  )
}
