import {
  useState,
} from 'react'

import {
  Eye,
} from 'lucide-react'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  CoachTodayDetails,
} from './CoachTodayDetails'

import type {
  CoachAction,
  CoachToday,
} from './types'

import {
  useCoachToday,
} from './useCoachToday'


export function CoachTodayWidget() {
  const [
    detailsOpen,
    setDetailsOpen,
  ] = useState(false)

  const {
    coach,
    loading,
    unavailable,
    error,
  } = useCoachToday()

  if (loading) {
    return (
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body flex min-h-28 items-center justify-center p-4">
          <span className="loading loading-spinner loading-sm text-primary" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card w-full border border-error/30 bg-base-100 shadow-sm">
        <div className="card-body p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-error">
            Coach du jour
          </p>

          <p className="mt-1 font-semibold text-error">
            Indisponible
          </p>

          <p className="mt-2 text-sm text-base-content/60">
            {error}
          </p>
        </div>
      </div>
    )
  }

  if (
    unavailable
    || !coach
  ) {
    return (
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
            Coach du jour
          </p>

          <p className="mt-1 font-semibold">
            Données indisponibles
          </p>

          <p className="mt-1 text-sm text-base-content/50">
            Les données nécessaires au coach
            ne sont pas encore disponibles.
          </p>
        </div>
      </div>
    )
  }

  const summary =
    buildCoachSummary(
      coach,
    )

  return (
    <>
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body gap-4 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
                Coach du jour
              </p>

              <div className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                <h2 className="text-lg font-bold">
                  Forme du jour
                </h2>

                <FormBadge
                  level={
                    summary.formLevel
                  }
                  label={
                    summary.formLabel
                  }
                />
              </div>

              <p className="mt-1 text-sm text-base-content/50">
                Readiness{' '}
                <span className="font-semibold text-base-content">
                  {Math.round(
                    coach.readiness.score,
                  )}/100
                </span>
              </p>
            </div>

            <button
              type="button"
              className="btn btn-ghost btn-sm btn-circle shrink-0"
              onClick={() =>
                setDetailsOpen(true)
              }
              aria-label="Voir le détail du coach"
              title="Voir le détail"
            >
              <Eye className="h-4 w-4" />
            </button>
          </div>

          <div>
            <p className="font-semibold text-base-content">
              {summary.headline}
            </p>

            <p className="mt-1 text-sm leading-relaxed text-base-content/60">
              {summary.context}
            </p>
          </div>

          {summary.sessionsLabel && (
            <div className="rounded-lg bg-base-200/60 px-3 py-2">
              <p className="text-sm font-medium text-base-content">
                {summary.sessionsLabel}
              </p>
            </div>
          )}

          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-base-content/45">
              Conseil
            </p>

            <p className="mt-1 text-sm leading-relaxed text-base-content/70">
              {summary.advice}
            </p>
          </div>
        </div>
      </div>

      <Modal
        title="Coach du jour"
        open={detailsOpen}
        onClose={() =>
          setDetailsOpen(false)
        }
      >
        <CoachTodayDetails
          coach={coach}
        />
      </Modal>
    </>
  )
}


interface CoachSummary {
  formLevel:
    | 'good'
    | 'moderate'
    | 'low'

  formLabel: string

  headline: string
  context: string
  advice: string

  sessionsLabel:
    string | null
}


function buildCoachSummary(
  coach: CoachToday,
): CoachSummary {
  const readiness =
    coach.readiness.score

  const sessionItems =
    coach.sessionDecisions.filter(
      (item) =>
        item.session !== null,
    )

  const activeItems =
    sessionItems.filter(
      (item) =>
        item.session?.status
        === 'planned',
    )

  const actions =
    activeItems.map(
      (item) =>
        item.decision.action,
    )

  const hasRest =
    actions.includes('rest')

  const hasReplace =
    actions.includes('replace')

  const hasReduce =
    actions.includes('reduce')

  const hasCriticalLoad =
    coach.recentLoadAssessment
      ?.hasCritical
    ?? false

  const hasLoadWarning =
    coach.recentLoadAssessment
      ?.hasWarning
    ?? false

  const hasCriticalReadiness =
    coach.readiness.criticalCount > 0

  const hasReadinessWarning =
    coach.readiness.warningCount > 0

  const sessionsLabel =
    buildSessionsLabel(
      sessionItems,
    )

  if (
    readiness < 40
    || hasRest
    || hasCriticalReadiness
    || hasCriticalLoad
  ) {
    return {
      formLevel: 'low',
      formLabel: 'Faible',

      headline:
        'Priorité récupération.',

      context:
        (
          'Les signaux du jour indiquent '
          + 'que la charge prévue doit être '
          + 'fortement adaptée.'
        ),

      advice:
        buildLowFormAdvice(
          activeItems.map(
            (item) =>
              item.decision.action,
          ),
        ),

      sessionsLabel,
    }
  }

  if (
    readiness < 70
    || hasReduce
    || hasReplace
    || hasReadinessWarning
    || hasLoadWarning
  ) {
    return {
      formLevel: 'moderate',
      formLabel: 'Moyenne',

      headline:
        'Journée à gérer avec prudence.',

      context:
        (
          'La récupération ou la charge '
          + 'récente demande quelques '
          + 'ajustements aujourd’hui.'
        ),

      advice:
        buildModerateFormAdvice(
          activeItems.map(
            (item) =>
              item.decision.action,
          ),
          activeItems.length,
        ),

      sessionsLabel,
    }
  }

  if (activeItems.length === 0) {
    return {
      formLevel: 'good',
      formLabel: 'Bonne',

      headline:
        'Profite de la récupération.',

      context:
        (
          'Aucune séance n’est actuellement '
          + 'à réaliser aujourd’hui.'
        ),

      advice:
        (
          'Garde cette journée légère '
          + 'et profite-en pour récupérer.'
        ),

      sessionsLabel,
    }
  }

  return {
    formLevel: 'good',
    formLabel: 'Bonne',

    headline:
      'Bonne journée pour s’entraîner.',

    context:
      (
        'La récupération est bonne '
        + 'et le programme prévu peut '
        + 'être suivi aujourd’hui.'
      ),

    advice:
      buildGoodFormAdvice(
        activeItems.length,
      ),

    sessionsLabel,
  }
}


function buildGoodFormAdvice(
  sessionCount: number,
): string {
  if (sessionCount > 1) {
    return (
      'Tu peux réaliser les séances prévues. '
      + 'Garde néanmoins de la marge sur la '
      + 'deuxième pour éviter une fatigue inutile.'
    )
  }

  return (
    'Tu peux suivre la séance prévue '
    + 'dans les conditions planifiées.'
  )
}


function buildModerateFormAdvice(
  actions: CoachAction[],
  sessionCount: number,
): string {
  if (
    actions.includes('replace')
  ) {
    return (
      'Privilégie la séance de remplacement '
      + 'proposée et évite de chercher '
      + 'de l’intensité supplémentaire.'
    )
  }

  if (
    actions.includes('reduce')
  ) {
    if (sessionCount > 1) {
      return (
        'Réduis les séances concernées '
        + 'et conserve la deuxième activité '
        + 'facile pour limiter la charge totale.'
      )
    }

    return (
      'Respecte la réduction proposée '
      + 'et ne compense pas par davantage '
      + 'd’intensité.'
    )
  }

  return (
    'Reste attentif aux sensations '
    + 'et garde une marge sur la séance.'
  )
}


function buildLowFormAdvice(
  actions: CoachAction[],
): string {
  if (
    actions.includes('rest')
  ) {
    return (
      'Le repos est recommandé aujourd’hui. '
      + 'Évite d’ajouter une séance non prévue.'
    )
  }

  return (
    'Réduis fortement la charge du jour '
    + 'et privilégie la récupération.'
  )
}


function buildSessionsLabel(
  items:
    CoachToday['sessionDecisions'],
): string | null {
  const sessions =
    items
      .map(
        (item) =>
          item.session,
      )
      .filter(
        (
          session,
        ): session is NonNullable<
          typeof session
        > =>
          session !== null,
      )

  if (sessions.length === 0) {
    return null
  }

  const activityNames =
    sessions.map(
      (session) =>
        formatActivityType(
          session.sportType,
          session.type,
        ),
    )

  return (
    `${sessions.length} séance`
    + (
      sessions.length > 1
        ? 's'
        : ''
    )
    + ' · '
    + activityNames.join(' + ')
  )
}


function FormBadge({
  level,
  label,
}: {
  level:
    CoachSummary['formLevel']

  label: string
}) {
  const className = {
    good: 'badge-success',
    moderate: 'badge-warning',
    low: 'badge-error',
  }[level]

  return (
    <span
      className={`badge badge-sm ${className}`}
    >
      {label}
    </span>
  )
}


function formatActivityType(
  sportType: string,
  type: string,
): string {
  const value =
    sportType.toLowerCase()

  const labels:
    Record<string, string> = {
      run: 'Course',
      running: 'Course',
      trailrunning: 'Trail',
      trail_running: 'Trail',
      strength: 'Renforcement',
      strength_training: 'Renforcement',
      bike: 'Vélo',
      cycling: 'Vélo',
      walking: 'Marche',
      hiking: 'Randonnée',
      swimming: 'Natation',
    }

  return (
    labels[value]
    ?? sportType
    ?? type
  )
}
