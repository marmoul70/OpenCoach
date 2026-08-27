import {
  Activity,
  CircleGauge,
  Clock3,
  HeartPulse,
  ShieldAlert,
} from 'lucide-react'

import type {
  CoachAction,
  CoachToday,
} from './types'


interface CoachTodayDetailsProps {
  coach: CoachToday
}
import {
  formatTrainingIntensity,
} from '../training/intensity'

export function CoachTodayDetails({
  coach,
}: CoachTodayDetailsProps) {
  const {
    sessionDecisions,
    readiness,
    recentLoad,
    recentLoadAssessment,
    dataWarning,
  } = coach

  return (
    <div className="space-y-6">
      <section>
        <p className="text-xs font-semibold uppercase tracking-wide text-base-content/50">
          Décisions OpenCoach
        </p>

        <div className="mt-3 flex flex-wrap items-center gap-3">
          <span className="badge badge-outline">
            Readiness {Math.round(readiness.score)}/100
          </span>

          <span className="text-sm text-base-content/60">
            {sessionDecisions.length}{' '}
            décision
            {sessionDecisions.length > 1
              ? 's'
              : ''}
            {' '}pour aujourd’hui
          </span>
        </div>
      </section>

      {dataWarning && (
        <div
          className="
            rounded-xl
            border border-warning/30
            bg-warning/10
            p-4
          "
        >
          <div className="flex items-start gap-3">
            <ShieldAlert
              className="
                mt-0.5
                h-5 w-5
                shrink-0
                text-warning
              "
            />

            <div>
              <p className="font-semibold text-base-content">
                Données de récupération non actualisées
              </p>

              <p
                className="
                  mt-1
                  text-sm
                  leading-relaxed
                  text-base-content/65
                "
              >
                {dataWarning}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="divider my-0" />

      <section>
        <h3 className="font-semibold text-base-content">
          État de récupération
        </h3>

        <div className="mt-3 grid gap-3 sm:grid-cols-3">
          <InfoCard
            icon={
              <CircleGauge className="h-4 w-4" />
            }
            label="Readiness"
            value={`${Math.round(readiness.score)}/100`}
            detail={formatReadinessLevel(
              readiness.level,
            )}
          />

          <InfoCard
            icon={
              <ShieldAlert className="h-4 w-4" />
            }
            label="Alertes"
            value={
              `${readiness.warningCount} attention`
            }
            detail={
              `${readiness.criticalCount} critique`
            }
          />

          <InfoCard
            icon={
              <HeartPulse className="h-4 w-4" />
            }
            label="Contraintes"
            value={
              String(
                readiness.trainingConstraints.length,
              )
            }
            detail="Règles actives"
          />
        </div>
        <p className="mt-2 text-xs text-base-content/45">
          Données de récupération :{' '}
          {formatReadinessFreshness(
            readiness.sourceDate,
            readiness.dataAgeDays,
          )}
        </p>
      </section>

      {recentLoad && (
        <>
          <div className="divider my-0" />

          <section>
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="font-semibold text-base-content">
                  Charge récente
                </h3>

                <p className="mt-1 text-sm text-base-content/50">
                  Comparaison entre le programme OpenCoach et
                  l&apos;entraînement réellement effectué sur les{' '}
                  {recentLoad.analyzedDays} derniers jours.
                </p>
              </div>

              {recentLoadAssessment && (
                <RecentLoadBadge
                  assessment={recentLoadAssessment}
                />
              )}
            </div>

            <div className="mt-3 grid gap-3 sm:grid-cols-3">
              <InfoCard
                icon={
                  <Activity className="h-4 w-4" />
                }
                label="Charge prévue"
                value={formatTrainingLoad(
                  recentLoad.plannedLoadTotal,
                )}
                detail={`${recentLoad.analyzedDays} jours analysés`}
              />

              <InfoCard
                icon={
                  <Activity className="h-4 w-4" />
                }
                label="Charge réalisée"
                value={formatTrainingLoad(
                  recentLoad.actualLoadTotal,
                )}
                detail={formatLoadRatio(
                  recentLoad.loadRatio,
                )}
              />

              <InfoCard
                icon={
                  <CircleGauge className="h-4 w-4" />
                }
                label="Écart"
                value={formatLoadDelta(
                  recentLoad.loadDeltaTotal,
                )}
                detail={formatLoadDeltaDetail(
                  recentLoad.loadDeltaTotal,
                )}
              />
            </div>

            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border border-base-300 p-4">
                <p className="text-xs text-base-content/50">
                  Respect du programme
                </p>

                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="badge badge-warning badge-outline">
                    {recentLoad.abovePlanDays} au-dessus
                  </span>

                  <span className="badge badge-success badge-outline">
                    {recentLoad.onPlanDays} conformes
                  </span>

                  <span className="badge badge-info badge-outline">
                    {recentLoad.belowPlanDays} en dessous
                  </span>
                </div>
              </div>

              <div className="rounded-xl border border-base-300 p-4">
                <p className="text-xs text-base-content/50">
                  Journées de repos
                </p>

                <p className="mt-2 font-semibold">
                  {recentLoad.brokenRestDays} non respecté
                  {recentLoad.brokenRestDays > 1 ? 's' : ''}
                </p>

                <p className="mt-1 text-xs text-base-content/50">
                  {recentLoad.respectedRestDays} repos respecté
                  {recentLoad.respectedRestDays > 1 ? 's' : ''}
                </p>
              </div>
            </div>

            {recentLoadAssessment
              && recentLoadAssessment.signals.length > 0 && (
                <div className="mt-3 divide-y divide-base-300 overflow-hidden rounded-xl border border-base-300">
                  {recentLoadAssessment.signals.map(
                    (signal) => (
                      <RecentLoadSignalRow
                        key={signal.kind}
                        signal={signal}
                      />
                    ),
                  )}
                </div>
              )}
          </section>
        </>
      )}

      {readiness.signals.length > 0 && (
        <>
          <div className="divider my-0" />

          <section>
            <h3 className="font-semibold text-base-content">
              Signaux du jour
            </h3>

            <p className="mt-1 text-sm text-base-content/50">
              Données prises en compte dans le calcul du Readiness.
            </p>

            <div className="mt-3 divide-y divide-base-300 overflow-hidden rounded-xl border border-base-300">
              {readiness.signals.map(
                (signal) => (
                  <ReadinessSignalRow
                    key={signal.metric}
                    signal={signal}
                  />
                ),
              )}
            </div>
          </section>
        </>
      )}

      <div className="divider my-0" />

      <section>
        <h3 className="font-semibold text-base-content">
          Séances du jour
        </h3>

        <p className="mt-1 text-sm text-base-content/50">
          Détail du planning et recommandation
          pour chaque activité.
        </p>

        <div className="mt-4 space-y-4">
          {sessionDecisions.map(
            (
              item,
              index,
            ) => {
              const session =
                item.session

              const decision =
                item.decision

              if (!session) {
                return (
                  <div
                    key={`rest-${index}`}
                    className="rounded-xl border border-base-300 bg-base-200/50 p-4"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <DecisionBadge
                        action={
                          decision.action
                        }
                      />

                      <span className="font-semibold">
                        Journée de repos
                      </span>
                    </div>

                    <p className="mt-3 text-sm leading-relaxed text-base-content/60">
                      {decision.reason}
                    </p>
                  </div>
                )
              }

              return (
                <div
                  key={
                    session.id
                    ?? `${session.date}-${session.type}-${index}`
                  }
                  className="rounded-xl border border-base-300 p-4"
                >
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                    <div className="min-w-0">
                      <p className="font-semibold">
                        {session.title}
                      </p>

                      <p className="mt-1 text-sm text-base-content/60">
                        {session.description}
                      </p>
                    </div>

                    <div className="flex shrink-0 flex-wrap gap-2">
                      <span className="badge badge-outline">
                        {session.sportType}
                      </span>

                      <DecisionBadge
                        action={
                          decision.action
                        }
                      />
                    </div>
                  </div>

                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    <InfoCard
                      icon={
                        <Clock3 className="h-4 w-4" />
                      }
                      label="Durée prévue"
                      value={`${session.durationMinutes} min`}
                      detail={
                        session.distanceKm !== undefined
                          ? `${session.distanceKm} km`
                          : 'Distance non renseignée'
                      }
                    />

                    <InfoCard
                      icon={
                        <Activity className="h-4 w-4" />
                      }
                      label="Intensité prévue"
                      value={
                        formatIntensity(
                          session.intensity,
                        )
                      }
                      detail={
                        session.heartRateZone
                        ?? 'Zone cardiaque non renseignée'
                      }
                    />

                    <InfoCard
                      icon={
                        <Clock3 className="h-4 w-4" />
                      }
                      label="Durée recommandée"
                      value={
                        decision.recommendedDurationMinutes
                          !== undefined
                          ? (
                              `${decision.recommendedDurationMinutes} min`
                            )
                          : 'Repos'
                      }
                      detail={
                        formatDurationChange(
                          decision.originalDurationMinutes,
                          decision.recommendedDurationMinutes,
                        )
                      }
                    />

                    <InfoCard
                      icon={
                        <Activity className="h-4 w-4" />
                      }
                      label="Intensité recommandée"
                      value={
                        formatIntensity(
                          decision.recommendedIntensity,
                        )
                      }
                      detail={
                        decision.originalIntensity
                          ? (
                              'Initialement : '
                              + formatIntensity(
                                decision.originalIntensity,
                              )
                            )
                          : 'Aucune intensité initiale'
                      }
                    />
                  </div>

                  <div className="mt-4 rounded-xl bg-base-200 p-4">
                    <p className="text-xs font-medium uppercase tracking-wide text-base-content/45">
                      Analyse du coach
                    </p>

                    <p className="mt-2 text-sm leading-relaxed text-base-content/70">
                      {decision.reason}
                    </p>
                  </div>

                  {decision.constraints.length > 0 && (
                    <div className="mt-4">
                      <p className="text-xs font-medium text-base-content/50">
                        Garde-fous actifs
                      </p>

                      <div className="mt-2 flex flex-wrap gap-2">
                        {decision.constraints.map(
                          (
                            constraint:
                              string,
                          ) => (
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
                    </div>
                  )}
                </div>
              )
            },
          )}
        </div>
      </section>

      <div className="divider my-0" />

      <div className="rounded-xl bg-base-200 p-4 text-sm text-base-content/60">
        Cette recommandation est informative. La séance
        enregistrée dans votre planning n&apos;est pas
        modifiée automatiquement.
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
    rest: 'badge-neutral',
  }[action]

  return (
    <span
      className={`badge ${className} badge-lg`}
    >
      {label}
    </span>
  )
}


interface InfoCardProps {
  icon: React.ReactNode
  label: string
  value: string
  detail: string
}


function InfoCard({
  icon,
  label,
  value,
  detail,
}: InfoCardProps) {
  return (
    <div className="rounded-xl bg-base-200 p-4">
      <div className="flex items-center gap-2 text-base-content/50">
        {icon}

        <span className="text-xs">
          {label}
        </span>
      </div>

      <p className="mt-2 font-semibold text-base-content">
        {value}
      </p>

      <p className="mt-1 text-xs text-base-content/50">
        {detail}
      </p>
    </div>
  )
}


function ReadinessSignalRow({
  signal,
}: {
  signal: CoachToday['readiness']['signals'][number]
}) {
  return (
    <div className="flex items-start justify-between gap-4 px-4 py-3">
      <div className="min-w-0">
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium">
            {formatSignalMetric(
              signal.metric,
            )}
          </span>

          <SignalBadge
            level={signal.level}
          />
        </div>

        <p className="mt-1 text-sm text-base-content/55">
          {signal.reason}
        </p>
      </div>

      {signal.currentValue !== undefined && (
        <div className="shrink-0 text-right text-sm">
          <p className="font-semibold">
            {formatSignalValue(
              signal.metric,
              signal.currentValue,
            )}
          </p>

          {signal.referenceValue !== undefined && (
            <p className="text-xs text-base-content/40">
              réf.{' '}
              {formatSignalValue(
                signal.metric,
                signal.referenceValue,
              )}
            </p>
          )}
        </div>
      )}
    </div>
  )
}


function SignalBadge({
  level,
}: {
  level: string
}) {
  const label = {
    normal: 'Normal',
    warning: 'Attention',
    critical: 'Critique',
    unavailable: 'Indisponible',
  }[level] ?? level

  const className = {
    normal: 'badge-success',
    warning: 'badge-warning',
    critical: 'badge-error',
    unavailable: 'badge-ghost',
  }[level] ?? 'badge-ghost'

  return (
    <span
      className={`badge badge-sm ${className}`}
    >
      {label}
    </span>
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
  intensity: string | null | undefined,
): string {
  return formatTrainingIntensity(
    intensity,
  )
}


function formatDurationChange(
  original?: number,
  recommended?: number,
): string {
  if (
    original === undefined
    && recommended === undefined
  ) {
    return 'Journée de repos planifiée'
  }

  if (
    original !== undefined
    && recommended === undefined
  ) {
    return `${original} min supprimées`
  }

  if (
    recommended !== undefined
    && recommended === original
  ) {
    return 'Durée inchangée'
  }

  if (
    original !== undefined
    && recommended !== undefined
  ) {
    const difference =
      original - recommended

    return `${difference} min de moins`
  }

  return 'Aucune modification'
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

    recent_overload:
      'Surcharge récente',

    repeated_overload:
      'Surcharge répétée',

    broken_rest:
      'Repos non respecté',

    repeated_broken_rest:
      'Repos répétés non respectés',
  }

  return labels[constraint]
    ?? constraint
}


function formatSignalMetric(
  metric: string,
): string {
  const labels: Record<string, string> = {
    hrv: 'HRV',
    resting_hr: 'FC repos',
    sleep_duration: 'Sommeil',
    sleep_score: 'Score sommeil',
    training_load: 'Charge',
    subjective_fatigue: 'Fatigue',
    pain: 'Douleur',
    illness: 'Santé',
    treatment_impact: 'Traitement',
    motivation: 'Motivation',
  }

  return labels[metric]
    ?? metric
}


function formatSignalValue(
  metric: string,
  value: number,
): string {
  if (metric === 'hrv') {
    return `${Math.round(value)} ms`
  }

  if (metric === 'resting_hr') {
    return `${Math.round(value)} bpm`
  }

  if (metric === 'sleep_duration') {
    return formatSleepDuration(
      value,
    )
  }

  if (metric === 'sleep_score') {
    return `${Math.round(value)}/100`
  }

  if (metric === 'subjective_fatigue') {
    return `${Math.round(value)}/5`
  }

  if (metric === 'pain') {
    return `${Math.round(value)}/10`
  }

  if (metric === 'training_load') {
    return value.toFixed(1)
  }

  return value.toFixed(1)
}


function formatSleepDuration(
  seconds: number,
): string {
  const totalMinutes =
    Math.round(
      seconds / 60,
    )

  const hours =
    Math.floor(
      totalMinutes / 60,
    )

  const minutes =
    totalMinutes % 60

  return `${hours}h${String(
    minutes,
  ).padStart(2, '0')}`
}

function RecentLoadBadge({
  assessment,
}: {
  assessment:
    CoachToday['recentLoadAssessment']
}) {
  if (!assessment) {
    return null
  }

  if (assessment.hasCritical) {
    return (
      <span className="badge badge-error">
        Charge critique
      </span>
    )
  }

  if (assessment.hasWarning) {
    return (
      <span className="badge badge-warning">
        À surveiller
      </span>
    )
  }

  return (
    <span className="badge badge-success">
      Charge maîtrisée
    </span>
  )
}


function RecentLoadSignalRow({
  signal,
}: {
  signal: NonNullable<
    CoachToday['recentLoadAssessment']
  >['signals'][number]
}) {
  return (
    <div className="flex items-start justify-between gap-4 px-4 py-3">
      <div>
        <div className="flex flex-wrap items-center gap-2">
          <span className="font-medium">
            {formatRecentLoadSignal(
              signal.kind,
            )}
          </span>

          <SignalBadge
            level={signal.level}
          />
        </div>

        <p className="mt-1 text-sm text-base-content/55">
          {signal.reason}
        </p>
      </div>
    </div>
  )
}


function formatTrainingLoad(
  value: number,
): string {
  return value.toFixed(1)
}


function formatLoadDelta(
  value: number,
): string {
  const prefix =
    value > 0
      ? '+'
      : ''

  return `${prefix}${value.toFixed(1)}`
}


function formatLoadDeltaDetail(
  value: number,
): string {
  if (value > 0) {
    return 'Charge supérieure au programme'
  }

  if (value < 0) {
    return 'Charge inférieure au programme'
  }

  return 'Charge conforme au programme'
}


function formatLoadRatio(
  ratio?: number,
): string {
  if (ratio === undefined) {
    return 'Aucune charge prévue'
  }

  const percent =
    Math.round(
      (ratio - 1) * 100,
    )

  if (percent > 0) {
    return `+${percent} % vs programme`
  }

  if (percent < 0) {
    return `${percent} % vs programme`
  }

  return 'Conforme au programme'
}


function formatRecentLoadSignal(
  kind: string,
): string {
  const labels: Record<string, string> = {
    recent_overload:
      'Surcharge récente',

    repeated_overload:
      'Surcharge répétée',

    broken_rest:
      'Repos non respecté',

    repeated_broken_rest:
      'Repos régulièrement non respectés',
  }

  return labels[kind]
    ?? kind
}

function formatReadinessFreshness(
  sourceDate: string,
  ageDays: number,
): string {
  if (ageDays === 0) {
    return "aujourd'hui"
  }

  const formattedDate =
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
      },
    ).format(
      new Date(
        `${sourceDate}T12:00:00`,
      ),
    )

  if (ageDays === 1) {
    return `${formattedDate} · il y a 1 jour`
  }

  return (
    `${formattedDate} · `
    + `il y a ${ageDays} jours`
  )
}