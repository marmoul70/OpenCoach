import {
  Activity,
  CircleCheck,
  Info,
  Minus,
  TrendingDown,
  TrendingUp,
  TriangleAlert,
} from 'lucide-react'

import {
  useCoachToday,
} from './useCoachToday'


interface CoachTodayWidgetProps {
  onOpenCoach: () => void
}


export function CoachTodayWidget({
  onOpenCoach,
}: CoachTodayWidgetProps) {
  const {
    coach,
    loading,
    unavailable,
    error,
  } = useCoachToday()

  if (loading) {
    return (
      <div className="card w-full border border-base-300 bg-base-100 shadow-sm">
        <div className="card-body flex min-h-32 items-center justify-center p-4">
          <span className="loading loading-spinner loading-sm text-primary" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card w-full border border-error/30 bg-base-100 shadow-sm">
        <div className="card-body gap-3 p-4">
          <div className="flex items-center gap-2 text-error">
            <TriangleAlert className="h-4 w-4" />

            <p className="font-semibold">
              Coach indisponible
            </p>
          </div>

          <p className="text-sm text-base-content/60">
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
        <div className="card-body gap-2 p-4">
          <p className="text-xs font-medium uppercase tracking-wide text-base-content/50">
            Coach
          </p>

          <p className="font-semibold">
            Analyse en attente
          </p>

          <p className="text-sm text-base-content/55">
            Les données nécessaires ne sont pas encore disponibles.
          </p>
        </div>
      </div>
    )
  }

  const {
    readiness,
    recentLoad,
    recentLoadAssessment,
    dataWarning,
  } = coach

  const summary = buildWeeklySummary(
    recentLoadAssessment,
  )

  const guidance = buildCoachGuidance(
    coach,
  )

  const signalCount = (
    readiness.warningCount
    + readiness.criticalCount
  )

  const readinessTrend = (
    resolveReadinessTrend(
      readiness.score,
    )
  )

  const loadTrend = (
    resolveLoadTrend(
      recentLoad?.actualLoadTotal,
      recentLoad?.plannedLoadTotal,
    )
  )

  return (
    <div
      role="button"
      tabIndex={0}
      className={[
        'card w-full cursor-pointer',
        'border border-base-300 bg-base-100 shadow-sm',
        'transition-all duration-150',
        'hover:border-primary/30 hover:shadow-md',
        'focus:outline-none focus-visible:ring-2',
        'focus-visible:ring-primary/40',
      ].join(' ')}
      onClick={onOpenCoach}
      onKeyDown={(event) => {
        if (
          event.key === 'Enter'
          || event.key === ' '
        ) {
          event.preventDefault()
          onOpenCoach()
        }
      }}
      aria-label="Ouvrir le Coach"
    >
      <div className="card-body gap-4 p-4 sm:p-5">

        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-xs font-medium uppercase tracking-wide text-base-content/45">
              Coach
            </p>

            <div className="mt-1 flex items-center gap-2">
              {summary.level === 'good' ? (
                <CircleCheck className="h-5 w-5 shrink-0 text-success" />
              ) : summary.level === 'warning' ? (
                <TriangleAlert className="h-5 w-5 shrink-0 text-warning" />
              ) : (
                <Info className="h-5 w-5 shrink-0 text-info" />
              )}

              <h2 className="truncate text-lg font-bold">
                {summary.title}
              </h2>
            </div>
          </div>

          <Activity className="h-5 w-5 shrink-0 text-base-content/25" />
        </div>

        <div className="grid grid-cols-3 divide-x divide-base-300 rounded-box border border-base-300 bg-base-200/40">
          <Metric
            label="Forme"
            value={`${Math.round(readiness.score)}/100`}
            trend={readinessTrend}
          />

          <Metric
            label="Charge 7 j"
            value={
              recentLoad
                ? formatNumber(
                    recentLoad.actualLoadTotal,
                  )
                : '—'
            }
            trend={loadTrend}
          />

          <Metric
            label="Signaux"
            value={`${signalCount}`}
          />
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-base-content/40">
              Analyse
            </p>

            <p className="mt-1 text-sm leading-relaxed text-base-content/70">
              {guidance.analysis}
            </p>
          </div>

          <div className="rounded-box bg-primary/5 px-3.5 py-3">
            <p className="text-xs font-semibold uppercase tracking-wide text-primary/70">
              Consigne du coach
            </p>

            <p className="mt-1 text-sm font-medium leading-relaxed text-base-content">
              {guidance.instruction}
            </p>
          </div>
        </div>

        {dataWarning && (
          <p className="text-xs text-warning">
            {dataWarning}
          </p>
        )}

      </div>
    </div>
  )
}


function Metric({
  label,
  value,
  trend,
}: {
  label: string
  value: string
  trend?: 'up' | 'down' | 'stable'
}) {
  return (
    <div className="px-3 py-2.5 text-center">
      <p className="text-[11px] font-medium text-base-content/45">
        {label}
      </p>

      <div className="mt-0.5 flex items-center justify-center gap-1.5">
        {trend && (
          <TrendIcon
            trend={trend}
          />
        )}

        <p className="font-bold tabular-nums text-base-content">
          {value}
        </p>
      </div>
    </div>
  )
}


function TrendIcon({
  trend,
}: {
  trend: 'up' | 'down' | 'stable'
}) {
  if (trend === 'up') {
    return (
      <TrendingUp
        className="h-4 w-4 text-success"
        aria-label="En hausse"
      />
    )
  }

  if (trend === 'down') {
    return (
      <TrendingDown
        className="h-4 w-4 text-warning"
        aria-label="En baisse"
      />
    )
  }

  return (
    <Minus
      className="h-4 w-4 text-base-content/35"
      aria-label="Stable"
    />
  )
}


function buildWeeklySummary(
  assessment: {
    hasWarning: boolean
    hasCritical: boolean
    hasOverload: boolean
    hasBrokenRest: boolean
  } | null,
): {
  title: string
  level: 'good' | 'warning' | 'info'
} {
  if (!assessment) {
    return {
      title: 'Semaine en cours',
      level: 'info',
    }
  }

  if (assessment.hasCritical) {
    return {
      title: 'Semaine à surveiller',
      level: 'warning',
    }
  }

  if (
    assessment.hasWarning
    || assessment.hasOverload
    || assessment.hasBrokenRest
  ) {
    return {
      title: 'Quelques points à surveiller',
      level: 'warning',
    }
  }

  return {
    title: 'Semaine sous contrôle',
    level: 'good',
  }
}


function buildCoachGuidance(
  coach: {
    readiness: {
      score: number
      warningCount: number
      criticalCount: number
      signals: Array<{
        level: string
        reason: string
      }>
    }

    recentLoad: {
      actualLoadTotal: number
      plannedLoadTotal: number
    } | null

    recentLoadAssessment: {
      hasWarning: boolean
      hasCritical: boolean
      hasOverload: boolean
      hasBrokenRest: boolean
      signals: Array<{
        level: string
        reason: string
      }>
    } | null
  },
): {
  analysis: string
  instruction: string
} {
  const {
    readiness,
    recentLoad,
    recentLoadAssessment,
  } = coach

  const loadAssessment =
    recentLoadAssessment

  const actualLoad =
    recentLoad?.actualLoadTotal

  const plannedLoad =
    recentLoad?.plannedLoadTotal

  const loadIsAbovePlan = (
    actualLoad !== undefined
    && plannedLoad !== undefined
    && plannedLoad > 0
    && actualLoad > plannedLoad * 1.15
  )

  // --------------------------------------------------------
  // Situation critique
  // --------------------------------------------------------

  if (
    readiness.criticalCount > 0
    || loadAssessment?.hasCritical
  ) {
    return {
      analysis:
        'Un signal important de récupération ou de charge '
        + 'est actuellement présent. La priorité est de ne '
        + 'pas accentuer la fatigue avant de poursuivre la progression.',

      instruction:
        'N’ajoute aucune charge supplémentaire. '
        + 'Privilégie la récupération et suis uniquement '
        + 'les adaptations proposées par OpenCoach.',
    }
  }

  // --------------------------------------------------------
  // Repos programmé non respecté
  // --------------------------------------------------------

  if (loadAssessment?.hasBrokenRest) {
    return {
      analysis:
        'Une période de repos prévue n’a pas été totalement '
        + 'respectée. Cette charge supplémentaire doit être '
        + 'prise en compte dans la récupération actuelle.',

      instruction:
        'N’essaie pas de compenser avec davantage '
        + 'd’entraînement. Respecte les prochaines séances '
        + 'faciles et les périodes de récupération prévues.',
    }
  }

  // --------------------------------------------------------
  // Charge élevée + readiness encore bon
  // --------------------------------------------------------

  if (
    (
      loadAssessment?.hasOverload
      || loadIsAbovePlan
    )
    && readiness.score >= 80
  ) {
    return {
      analysis:
        'Ta disponibilité reste très bonne, mais la charge '
        + 'récente est supérieure au programme prévu. '
        + 'Aucun signal critique de fatigue n’est détecté pour le moment.',

      instruction:
        'Garde le programme prévu sans ajouter de charge '
        + 'supplémentaire. Sois attentif aux sensations '
        + 'et à la qualité de récupération.',
    }
  }

  // --------------------------------------------------------
  // Charge élevée + readiness moyen
  // --------------------------------------------------------

  if (
    loadAssessment?.hasOverload
    || loadIsAbovePlan
  ) {
    return {
      analysis:
        'La charge récente est élevée alors que ta '
        + 'disponibilité n’est pas optimale. Le cumul '
        + 'mérite davantage de prudence.',

      instruction:
        'Évite toute séance supplémentaire et reste '
        + 'strictement sur le programme prévu. '
        + 'Réévalue tes sensations avant les efforts exigeants.',
    }
  }

  // --------------------------------------------------------
  // Readiness élevé
  // --------------------------------------------------------

  if (
    readiness.score >= 80
    && readiness.warningCount === 0
  ) {
    return {
      analysis:
        'Ta disponibilité est très bonne aujourd’hui. '
        + 'Les indicateurs de récupération sont favorables '
        + 'et aucun signal majeur de charge n’est détecté.',

      instruction:
        'Conserve le programme prévu. Il n’est pas '
        + 'nécessaire d’ajouter du volume ou de '
        + 'l’intensité pour le moment.',
    }
  }

  // --------------------------------------------------------
  // Readiness élevé avec vigilance
  // --------------------------------------------------------

  if (readiness.score >= 80) {
    return {
      analysis:
        'Ta disponibilité générale est bonne, malgré '
        + 'un signal de vigilance isolé. À lui seul, '
        + 'il ne justifie pas de modifier la séance prévue.',

      instruction:
        'Conserve le programme prévu, mais surveille '
        + 'tes sensations pendant l’échauffement et '
        + 'réduis l’effort si elles se dégradent.',
    }
  }

  // --------------------------------------------------------
  // Readiness intermédiaire
  // --------------------------------------------------------

  if (readiness.score >= 60) {
    return {
      analysis:
        'Ta disponibilité est correcte sans être optimale. '
        + 'La séance reste envisageable, mais la réponse '
        + 'à l’effort doit guider son exécution.',

      instruction:
        'Respecte strictement l’intensité prévue et '
        + 'n’ajoute pas de travail supplémentaire. '
        + 'Ralentis si les sensations sont moins bonnes que prévu.',
    }
  }

  // --------------------------------------------------------
  // Readiness faible
  // --------------------------------------------------------

  return {
    analysis:
      'Ta disponibilité est réduite aujourd’hui. '
      + 'Les indicateurs suggèrent de privilégier '
      + 'la récupération plutôt que la charge supplémentaire.',

    instruction:
      'Évite d’augmenter la charge et privilégie '
      + 'une séance allégée ou la récupération selon '
      + 'les adaptations proposées par OpenCoach.',
  }
}


function resolveReadinessTrend(
  score: number,
): 'up' | 'down' | 'stable' {
  if (score >= 80) {
    return 'up'
  }

  if (score < 60) {
    return 'down'
  }

  return 'stable'
}


function resolveLoadTrend(
  actualLoad: number | undefined,
  plannedLoad: number | undefined,
): 'up' | 'down' | 'stable' | undefined {
  if (
    actualLoad === undefined
    || plannedLoad === undefined
  ) {
    return undefined
  }

  if (plannedLoad <= 0) {
    return actualLoad > 0
      ? 'up'
      : 'stable'
  }

  const ratio = (
    actualLoad
    / plannedLoad
  )

  if (ratio > 1.15) {
    return 'up'
  }

  if (ratio < 0.85) {
    return 'down'
  }

  return 'stable'
}


function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    'fr-FR',
    {
      maximumFractionDigits: 0,
    },
  ).format(value)
}
