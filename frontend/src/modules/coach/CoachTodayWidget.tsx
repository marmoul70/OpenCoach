import {
  Activity,
  ArrowRight,
  CircleCheck,
  Minus,
  ShieldCheck,
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
      <div
        className="
          flex
          min-h-64
          w-full
          items-center
          justify-center
          rounded-2xl
          border
          border-black/[0.07]
          bg-white
          dark:border-white/[0.08]
          dark:bg-[#141a1e]
        "
      >
        <span
          className="
            loading
            loading-spinner
            loading-sm
            text-emerald-500
          "
        />
      </div>
    )
  }


  if (error) {
    return (
      <div
        className="
          w-full
          rounded-2xl
          border
          border-red-500/20
          bg-white
          p-5
          dark:bg-[#141a1e]
        "
      >
        <div
          className="
            flex
            items-center
            gap-2
            text-red-500
          "
        >
          <TriangleAlert
            className="h-5 w-5"
          />

          <p className="font-semibold">
            Coach indisponible
          </p>
        </div>

        <p
          className="
            mt-2
            text-sm
            leading-6
            text-slate-500
            dark:text-slate-400
          "
        >
          {error}
        </p>
      </div>
    )
  }


  if (
    unavailable
    || !coach
  ) {
    return (
      <button
        type="button"
        onClick={onOpenCoach}
        className="
          group
          w-full
          rounded-2xl
          border
          border-black/[0.07]
          bg-white
          p-5
          text-left
          transition
          hover:border-emerald-500/20
          dark:border-white/[0.08]
          dark:bg-[#141a1e]
        "
      >
        <div
          className="
            flex
            h-10
            w-10
            items-center
            justify-center
            rounded-xl
            bg-slate-50
            text-slate-400
            dark:bg-white/[0.05]
          "
        >
          <Activity
            className="h-5 w-5"
          />
        </div>

        <h3
          className="
            mt-4
            text-lg
            font-bold
            tracking-[-0.02em]
            text-slate-950
            dark:text-white
          "
        >
          Analyse en attente
        </h3>

        <p
          className="
            mt-1
            text-sm
            leading-6
            text-slate-500
            dark:text-slate-400
          "
        >
          Les données nécessaires ne
          sont pas encore disponibles.
        </p>

        <div
          className="
            mt-5
            flex
            items-center
            justify-end
          "
        >
          <ArrowRight
            className="
              h-4
              w-4
              text-slate-300
              transition-transform
              group-hover:translate-x-1
            "
          />
        </div>
      </button>
    )
  }


  const {
    readiness,
    recentLoad,
    recentLoadAssessment,
    dataWarning,
  } = coach

  const summary =
    buildWeeklySummary(
      recentLoadAssessment,
    )

  const guidance =
    buildCoachGuidance(
      coach,
    )

  const signalCount = (
    readiness.warningCount
    + readiness.criticalCount
  )

  const readinessTrend =
    resolveReadinessTrend(
      readiness.score,
    )

  const loadTrend =
    resolveLoadTrend(
      recentLoad?.actualLoadTotal,
      recentLoad?.plannedLoadTotal,
    )

  const readinessPresentation =
    getReadinessPresentation(
      readiness.score,
      readiness.criticalCount,
      readiness.warningCount,
    )


  return (
    <button
      type="button"
      onClick={onOpenCoach}
      className="
        group
        relative
        w-full
        overflow-hidden
        rounded-2xl
        border
        border-black/[0.07]
        bg-white
        p-0
        text-left
        shadow-[0_1px_2px_rgba(15,23,42,0.025)]
        transition
        duration-200
        hover:-translate-y-0.5
        hover:shadow-[0_12px_35px_rgba(15,23,42,0.055)]
        focus-visible:outline-none
        focus-visible:ring-2
        focus-visible:ring-emerald-500/40
        dark:border-white/[0.08]
        dark:bg-[#141a1e]
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          -right-16
          -top-20
          h-48
          w-48
          rounded-full
          bg-emerald-500/[0.05]
          blur-3xl
        "
      />

      <div
        className="
          relative
          p-5
          sm:p-6
        "
      >
        {/* -------------------------------------------
            État principal
           ------------------------------------------- */}

        <div
          className="
            flex
            items-start
            justify-between
            gap-5
          "
        >
          <div className="min-w-0">
            <div
              className="
                flex
                flex-wrap
                items-center
                gap-2
              "
            >
              <span
                className={[
                  (
                    'inline-flex items-center '
                    + 'gap-1.5 rounded-full '
                    + 'px-2.5 py-1 '
                    + 'text-[10px] '
                    + 'font-bold uppercase '
                    + 'tracking-[0.12em]'
                  ),
                  readinessPresentation.badgeClass,
                ].join(' ')}
              >
                <ShieldCheck
                  className="h-3.5 w-3.5"
                />

                {readinessPresentation.label}
              </span>

              <span
                className="
                  text-[11px]
                  font-medium
                  text-slate-400
                "
              >
                Analyse du jour
              </span>
            </div>

            <h3
              className="
                mt-3
                text-xl
                font-bold
                tracking-[-0.03em]
                text-slate-950
                sm:text-2xl
                dark:text-white
              "
            >
              {summary.title}
            </h3>

            <p
              className="
                mt-2
                max-w-2xl
                text-sm
                leading-6
                text-slate-500
                dark:text-slate-400
              "
            >
              {guidance.analysis}
            </p>
          </div>


          <div
            className="
              hidden
              shrink-0
              sm:block
            "
          >
            <ReadinessScore
              score={
                readiness.score
              }
            />
          </div>
        </div>


        {/* -------------------------------------------
            Score mobile
           ------------------------------------------- */}

        <div
          className="
            mt-5
            sm:hidden
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              rounded-xl
              bg-slate-50
              px-4
              py-3
              dark:bg-white/[0.04]
            "
          >
            <div>
              <p
                className="
                  text-[10px]
                  font-semibold
                  uppercase
                  tracking-wide
                  text-slate-400
                "
              >
                Disponibilité
              </p>

              <p
                className="
                  mt-0.5
                  text-xs
                  text-slate-500
                  dark:text-slate-400
                "
              >
                Score du jour
              </p>
            </div>

            <div
              className="
                flex
                items-baseline
                gap-1
              "
            >
              <span
                className="
                  text-2xl
                  font-bold
                  tracking-[-0.04em]
                  text-slate-950
                  dark:text-white
                "
              >
                {Math.round(
                  readiness.score,
                )}
              </span>

              <span
                className="
                  text-xs
                  text-slate-400
                "
              >
                /100
              </span>
            </div>
          </div>
        </div>


        {/* -------------------------------------------
            Métriques
           ------------------------------------------- */}

        <div
          className="
            mt-5
            grid
            grid-cols-3
            divide-x
            divide-black/[0.06]
            border-y
            border-black/[0.06]
            py-4
            dark:divide-white/[0.07]
            dark:border-white/[0.07]
          "
        >
          <Metric
            label="Forme"
            value={
              `${Math.round(
                readiness.score,
              )}`
            }
            unit="/100"
            trend={
              readinessTrend
            }
          />

          <Metric
            label="Charge 7 j"
            value={
              recentLoad
                ? formatNumber(
                    recentLoad
                      .actualLoadTotal,
                  )
                : '—'
            }
            trend={
              loadTrend
            }
          />

          <Metric
            label="Signaux"
            value={
              `${signalCount}`
            }
            state={
              signalCount === 0
                ? 'good'
                : 'warning'
            }
          />
        </div>


        {/* -------------------------------------------
            Consigne
           ------------------------------------------- */}

        <div
          className="
            mt-5
            rounded-xl
            border
            border-emerald-500/10
            bg-emerald-50/60
            p-4
            dark:border-emerald-500/10
            dark:bg-emerald-500/[0.055]
          "
        >
          <div
            className="
              flex
              items-start
              gap-3
            "
          >
            <div
              className="
                mt-0.5
                flex
                h-7
                w-7
                shrink-0
                items-center
                justify-center
                rounded-lg
                bg-emerald-100
                text-emerald-600
                dark:bg-emerald-500/10
                dark:text-emerald-400
              "
            >
              <CircleCheck
                className="h-4 w-4"
              />
            </div>

            <div>
              <p
                className="
                  text-[10px]
                  font-bold
                  uppercase
                  tracking-[0.13em]
                  text-emerald-700
                  dark:text-emerald-400
                "
              >
                Consigne du coach
              </p>

              <p
                className="
                  mt-1.5
                  text-sm
                  font-medium
                  leading-6
                  text-slate-800
                  dark:text-slate-200
                "
              >
                {guidance.instruction}
              </p>
            </div>
          </div>
        </div>


        {dataWarning && (
          <div
            className="
              mt-4
              flex
              items-start
              gap-2
              text-xs
              leading-5
              text-amber-600
              dark:text-amber-400
            "
          >
            <TriangleAlert
              className="
                mt-0.5
                h-3.5
                w-3.5
                shrink-0
              "
            />

            {dataWarning}
          </div>
        )}


        <div
          className="
            mt-5
            flex
            items-center
            justify-end
          "
        >
          <span
            className="
              flex
              items-center
              gap-2
              text-xs
              font-semibold
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Voir l’analyse complète

            <ArrowRight
              className="
                h-4
                w-4
                transition-transform
                group-hover:translate-x-1
              "
            />
          </span>
        </div>
      </div>
    </button>
  )
}


function ReadinessScore({
  score,
}: {
  score: number
}) {
  const normalized =
    Math.max(
      0,
      Math.min(
        100,
        Math.round(score),
      ),
    )

  return (
    <div
      className="
        relative
        flex
        h-24
        w-24
        items-center
        justify-center
      "
    >
      <svg
        viewBox="0 0 100 100"
        className="
          absolute
          inset-0
          h-full
          w-full
          -rotate-90
        "
      >
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke="currentColor"
          strokeWidth="7"
          className="
            text-slate-100
            dark:text-white/[0.06]
          "
        />

        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke="currentColor"
          strokeWidth="7"
          strokeLinecap="round"
          pathLength="100"
          strokeDasharray="100"
          strokeDashoffset={
            100 - normalized
          }
          className="text-emerald-500"
        />
      </svg>

      <div className="text-center">
        <p
          className="
            text-2xl
            font-bold
            tracking-[-0.05em]
            text-slate-950
            dark:text-white
          "
        >
          {normalized}
        </p>

        <p
          className="
            text-[9px]
            font-semibold
            uppercase
            tracking-wide
            text-slate-400
          "
        >
          Forme
        </p>
      </div>
    </div>
  )
}


function Metric({
  label,
  value,
  unit,
  trend,
  state,
}: {
  label: string
  value: string
  unit?: string
  trend?: 'up' | 'down' | 'stable'
  state?: 'good' | 'warning'
}) {
  return (
    <div
      className="
        min-w-0
        px-3
        first:pl-0
        last:pr-0
        sm:px-4
      "
    >
      <p
        className="
          truncate
          text-[10px]
          font-semibold
          uppercase
          tracking-wide
          text-slate-400
        "
      >
        {label}
      </p>

      <div
        className="
          mt-1
          flex
          items-center
          gap-1.5
        "
      >
        {trend && (
          <TrendIcon
            trend={trend}
          />
        )}

        <span
          className={[
            (
              'truncate '
              + 'text-lg '
              + 'font-bold '
              + 'tabular-nums '
              + 'tracking-[-0.03em]'
            ),
            state === 'good'
              ? (
                  'text-emerald-600 '
                  + 'dark:text-emerald-400'
                )
              : state === 'warning'
                ? (
                    'text-amber-500'
                  )
                : (
                    'text-slate-900 '
                    + 'dark:text-white'
                  ),
          ].join(' ')}
        >
          {value}
        </span>

        {unit && (
          <span
            className="
              hidden
              text-[10px]
              text-slate-400
              sm:inline
            "
          >
            {unit}
          </span>
        )}
      </div>
    </div>
  )
}


function TrendIcon({
  trend,
}: {
  trend:
    | 'up'
    | 'down'
    | 'stable'
}) {
  if (trend === 'up') {
    return (
      <TrendingUp
        className="
          h-4
          w-4
          shrink-0
          text-emerald-500
        "
      />
    )
  }

  if (trend === 'down') {
    return (
      <TrendingDown
        className="
          h-4
          w-4
          shrink-0
          text-amber-500
        "
      />
    )
  }

  return (
    <Minus
      className="
        h-4
        w-4
        shrink-0
        text-slate-300
      "
    />
  )
}


function getReadinessPresentation(
  score: number,
  criticalCount: number,
  warningCount: number,
): {
  label: string
  badgeClass: string
} {
  if (
    criticalCount > 0
    || score < 50
  ) {
    return {
      label:
        'Récupération prioritaire',
      badgeClass:
        (
          'bg-red-50 '
          + 'text-red-600 '
          + 'dark:bg-red-500/10 '
          + 'dark:text-red-400'
        ),
    }
  }

  if (
    warningCount > 0
    || score < 70
  ) {
    return {
      label:
        'À surveiller',
      badgeClass:
        (
          'bg-amber-50 '
          + 'text-amber-600 '
          + 'dark:bg-amber-500/10 '
          + 'dark:text-amber-400'
        ),
    }
  }

  return {
    label:
      'Prêt à s’entraîner',
    badgeClass:
      (
        'bg-emerald-50 '
        + 'text-emerald-700 '
        + 'dark:bg-emerald-500/10 '
        + 'dark:text-emerald-400'
      ),
  }
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
  level:
    | 'good'
    | 'warning'
    | 'info'
} {
  if (!assessment) {
    return {
      title:
        'Semaine en cours',
      level:
        'info',
    }
  }

  if (
    assessment.hasCritical
  ) {
    return {
      title:
        'Semaine à surveiller',
      level:
        'warning',
    }
  }

  if (
    assessment.hasWarning
    || assessment.hasOverload
    || assessment.hasBrokenRest
  ) {
    return {
      title:
        'Quelques points à surveiller',
      level:
        'warning',
    }
  }

  return {
    title:
      'Semaine sous contrôle',
    level:
      'good',
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
    && actualLoad
      > plannedLoad * 1.15
  )


  if (
    readiness.criticalCount > 0
    || loadAssessment?.hasCritical
  ) {
    return {
      analysis:
        (
          'Un signal important de récupération '
          + 'ou de charge est actuellement présent. '
          + 'La priorité est de ne pas accentuer '
          + 'la fatigue avant de poursuivre '
          + 'la progression.'
        ),

      instruction:
        (
          'N’ajoute aucune charge supplémentaire. '
          + 'Privilégie la récupération et suis '
          + 'uniquement les adaptations proposées '
          + 'par OpenCoach.'
        ),
    }
  }


  if (
    loadAssessment
      ?.hasBrokenRest
  ) {
    return {
      analysis:
        (
          'Une période de repos prévue n’a pas '
          + 'été totalement respectée. Cette '
          + 'charge supplémentaire doit être '
          + 'prise en compte dans la récupération.'
        ),

      instruction:
        (
          'N’essaie pas de compenser avec davantage '
          + 'd’entraînement. Respecte les prochaines '
          + 'séances faciles et les périodes '
          + 'de récupération prévues.'
        ),
    }
  }


  if (
    (
      loadAssessment
        ?.hasOverload
      || loadIsAbovePlan
    )
    && readiness.score >= 80
  ) {
    return {
      analysis:
        (
          'Ta disponibilité reste très bonne, '
          + 'mais la charge récente est supérieure '
          + 'au programme prévu. Aucun signal '
          + 'critique de fatigue n’est détecté.'
        ),

      instruction:
        (
          'Garde le programme prévu sans ajouter '
          + 'de charge supplémentaire. Sois attentif '
          + 'aux sensations et à la récupération.'
        ),
    }
  }


  if (
    loadAssessment?.hasOverload
    || loadIsAbovePlan
  ) {
    return {
      analysis:
        (
          'La charge récente est élevée alors que '
          + 'ta disponibilité n’est pas optimale. '
          + 'Le cumul mérite davantage de prudence.'
        ),

      instruction:
        (
          'Évite toute séance supplémentaire et '
          + 'reste strictement sur le programme prévu. '
          + 'Réévalue tes sensations avant les efforts '
          + 'exigeants.'
        ),
    }
  }


  if (
    readiness.score >= 80
    && readiness.warningCount === 0
  ) {
    return {
      analysis:
        (
          'Ta disponibilité est très bonne aujourd’hui. '
          + 'Les indicateurs de récupération sont '
          + 'favorables et aucun signal majeur '
          + 'de charge n’est détecté.'
        ),

      instruction:
        (
          'Conserve le programme prévu. Il n’est '
          + 'pas nécessaire d’ajouter du volume '
          + 'ou de l’intensité.'
        ),
    }
  }


  if (
    readiness.score >= 80
  ) {
    return {
      analysis:
        (
          'Ta disponibilité générale est bonne, '
          + 'malgré un signal de vigilance isolé. '
          + 'À lui seul, il ne justifie pas '
          + 'de modifier la séance prévue.'
        ),

      instruction:
        (
          'Conserve le programme prévu, mais surveille '
          + 'tes sensations pendant l’échauffement '
          + 'et réduis l’effort si elles se dégradent.'
        ),
    }
  }


  if (
    readiness.score >= 60
  ) {
    return {
      analysis:
        (
          'Ta disponibilité est correcte sans être '
          + 'optimale. La séance reste envisageable, '
          + 'mais la réponse à l’effort doit guider '
          + 'son exécution.'
        ),

      instruction:
        (
          'Respecte strictement l’intensité prévue '
          + 'et n’ajoute pas de travail supplémentaire. '
          + 'Ralentis si les sensations sont moins '
          + 'bonnes que prévu.'
        ),
    }
  }


  return {
    analysis:
      (
        'Ta disponibilité est réduite aujourd’hui. '
        + 'Les indicateurs suggèrent de privilégier '
        + 'la récupération plutôt que la charge '
        + 'supplémentaire.'
      ),

    instruction:
      (
        'Évite d’augmenter la charge et privilégie '
        + 'une séance allégée ou la récupération '
        + 'selon les adaptations proposées '
        + 'par OpenCoach.'
      ),
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
):
  | 'up'
  | 'down'
  | 'stable'
  | undefined {
  if (
    actualLoad === undefined
    || plannedLoad === undefined
  ) {
    return undefined
  }

  if (
    plannedLoad <= 0
  ) {
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
