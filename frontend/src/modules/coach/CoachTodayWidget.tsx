import {
  Activity,
  CircleGauge,
  Clock3,
  ShieldCheck,
} from 'lucide-react'

import type {
  CoachAction,
} from './types'

import {
  useCoachToday,
} from './useCoachToday'


export function CoachTodayWidget() {
  const {
    coach,
    loading,
    unavailable,
    error,
  } = useCoachToday()

  if (loading) {
    return (
      <div className="card border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body flex min-h-56 items-center justify-center">
          <span className="loading loading-spinner loading-md text-primary" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card border border-error/30 bg-base-100 shadow-sm">
        <div className="card-body">
          <p className="font-semibold text-error">
            Coach indisponible
          </p>

          <p className="mt-1 text-sm text-base-content/60">
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
      <div className="card border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body p-5">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-base-200 p-3">
              <ShieldCheck className="h-5 w-5" />
            </div>

            <div>
              <p className="text-sm text-base-content/60">
                Coach du jour
              </p>

              <h2 className="text-xl font-bold">
                Aucune recommandation
              </h2>
            </div>
          </div>

          <p className="mt-4 text-sm text-base-content/60">
            Aucune séance planifiée n&apos;est actuellement
            disponible pour aujourd&apos;hui.
          </p>
        </div>
      </div>
    )
  }

  const {
    session,
    readiness,
    decision,
  } = coach

  return (
    <div className="card border border-base-300 bg-base-100 shadow-sm">
      <div className="card-body p-5 sm:p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <p className="text-sm font-medium text-base-content/60">
              Coach du jour
            </p>

            <h2 className="mt-1 text-2xl font-bold">
              {session.title}
            </h2>

            <p className="mt-1 text-sm text-base-content/50">
              {session.description}
            </p>
          </div>

          <DecisionBadge
            action={decision.action}
          />
        </div>

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <Metric
            icon={
              <CircleGauge className="h-4 w-4" />
            }
            label="Readiness"
            value={`${readiness.score}/100`}
            detail={formatReadinessLevel(
              readiness.level,
            )}
          />

          <Metric
            icon={
              <Clock3 className="h-4 w-4" />
            }
            label="Durée"
            value={
              decision.recommendedDurationMinutes
                !== undefined
                ? `${decision.recommendedDurationMinutes} min`
                : 'Repos'
            }
            detail={
              decision.recommendedDurationMinutes
                !== undefined
                ? `${decision.originalDurationMinutes} min prévues`
                : `${decision.originalDurationMinutes} min annulées`
            }
          />

          <Metric
            icon={
              <Activity className="h-4 w-4" />
            }
            label="Intensité"
            value={
              formatIntensity(
                decision.recommendedIntensity,
              )
            }
            detail={
              `Prévue : ${decision.originalIntensity}`
            }
          />
        </div>

        <div className="mt-5 rounded-xl bg-base-200 p-4">
          <p className="text-xs font-semibold uppercase tracking-wide text-base-content/50">
            Recommandation OpenCoach
          </p>

          <p className="mt-2 font-medium text-base-content">
            {decision.reason}
          </p>
        </div>

        {decision.constraints.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2">
            {decision.constraints.map(
              (constraint) => (
                <span
                  key={constraint}
                  className="badge badge-outline"
                >
                  {formatConstraint(
                    constraint,
                  )}
                </span>
              ),
            )}
          </div>
        )}
      </div>
    </div>
  )
}


function DecisionBadge({
  action,
}: {
  action: CoachAction
}) {
  const label = {
    keep: 'Maintenir',
    reduce: 'Réduire',
    replace: 'Remplacer',
    rest: 'Repos',
  }[action]

  const className = {
    keep: 'badge-success',
    reduce: 'badge-warning',
    replace: 'badge-info',
    rest: 'badge-error',
  }[action]

  return (
    <span
      className={`badge ${className} badge-lg`}
    >
      {label}
    </span>
  )
}


interface MetricProps {
  icon: React.ReactNode
  label: string
  value: string
  detail: string
}


function Metric({
  icon,
  label,
  value,
  detail,
}: MetricProps) {
  return (
    <div className="rounded-xl bg-base-200 p-4">
      <div className="flex items-center gap-2 text-base-content/50">
        {icon}

        <span className="text-xs">
          {label}
        </span>
      </div>

      <p className="mt-2 text-lg font-bold">
        {value}
      </p>

      <p className="mt-1 text-xs text-base-content/50">
        {detail}
      </p>
    </div>
  )
}


function formatReadinessLevel(
  level: string,
): string {
  const labels: Record<string, string> = {
    high: 'Très bonne disponibilité',
    good: 'Bonne disponibilité',
    moderate: 'Disponibilité modérée',
    low: 'Disponibilité faible',
    very_low: 'Disponibilité très faible',
  }

  return labels[level] ?? level
}


function formatIntensity(
  intensity?: string,
): string {
  if (!intensity) {
    return 'Aucune'
  }

  const labels: Record<string, string> = {
    easy: 'Facile',
    recovery: 'Récupération',
  }

  return labels[intensity] ?? intensity
}


function formatConstraint(
  constraint: string,
): string {
  const labels: Record<string, string> = {
    avoid_high_intensity:
      'Éviter haute intensité',
    prefer_recovery_or_rest:
      'Récupération / repos',
    reduce_duration:
      'Réduire la durée',
    avoid_pain_aggravation:
      'Ne pas aggraver la douleur',
    consider_low_motivation:
      'Motivation basse',
    monitor_intensity:
      'Surveiller l’intensité',
    monitor_recovery:
      'Surveiller la récupération',
    reduce_training_load:
      'Réduire la charge',
  }

  return labels[constraint]
    ?? constraint
}
