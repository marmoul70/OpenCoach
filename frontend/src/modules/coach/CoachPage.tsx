import { MetricTooltip } from '../../components/metrics/MetricTooltip'
import {
  Activity,
  Brain,
  CircleCheck,
  Clock,
  HeartPulse,
  Info,
  Sparkles,
  TriangleAlert,
} from 'lucide-react'

import {
  useCoachToday,
} from './useCoachToday'


export function CoachPage() {
  const {
    coach,
    loading,
    unavailable,
    error,
  } = useCoachToday()

  if (loading) {
    return (
      <PageContainer>
        <div className="flex min-h-80 items-center justify-center">
          <span className="loading loading-spinner loading-lg text-primary" />
        </div>
      </PageContainer>
    )
  }

  if (error) {
    return (
      <PageContainer>
        <div className="alert alert-error">
          <TriangleAlert className="h-5 w-5" />

          <div>
            <p className="font-semibold">
              Coach indisponible
            </p>

            <p className="text-sm">
              {error}
            </p>
          </div>
        </div>
      </PageContainer>
    )
  }

  if (
    unavailable
    || !coach
  ) {
    return (
      <PageContainer>
        <div className="card border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body items-center py-16 text-center">
            <Brain className="h-9 w-9 text-base-content/25" />

            <h2 className="mt-2 text-lg font-semibold">
              Analyse en préparation
            </h2>

            <p className="max-w-md text-sm text-base-content/50">
              OpenCoach n’a pas encore assez de données pour
              construire une analyse complète.
            </p>
          </div>
        </div>
      </PageContainer>
    )
  }

  const {
    readiness,
    recentLoadAssessment,
    sessionDecisions,
    weeklyAssessment,
    dataWarning,
  } = coach

  const attentionSignals = [
    ...readiness.signals.filter(
      (signal) =>
        signal.level !== 'normal',
    ),
    ...(
      recentLoadAssessment?.signals
      ?? []
    ),
  ]

  const todaySessions = (
    sessionDecisions.filter(
      (item) =>
        item.session !== null,
    )
  )

  const progressPercent = (
    weeklyAssessment.targetLoad
      ? Math.min(
          100,
          Math.max(
            0,
            (
              weeklyAssessment.actualLoadToDate
              / weeklyAssessment.targetLoad
            ) * 100,
          ),
        )
      : 0
  )

  const actualPercent = (
    weeklyAssessment.targetLoad
      ? percentageOfTarget(
          weeklyAssessment.actualLoadToDate,
          weeklyAssessment.targetLoad,
        )
      : undefined
  )

  const projectedPercent = (
    weeklyAssessment.targetLoad
      ? percentageOfTarget(
          weeklyAssessment.projectedWeekLoad,
          weeklyAssessment.targetLoad,
        )
      : undefined
  )

  return (
    <PageContainer>

      <PageHeader />

      {dataWarning && (
        <div className="alert alert-warning mb-5">
          <Info className="h-5 w-5" />
          <span>{dataWarning}</span>
        </div>
      )}

      <div className="space-y-5">

        {/* ==================================================
            SYNTHÈSE
        ================================================== */}

        <section className="card border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body gap-5 p-5 sm:p-6">

            <div className="flex items-start gap-3">

              <StatusIcon
                status={weeklyAssessment.status}
              />

              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-base-content/40">
                  Cette semaine
                </p>

                <h2 className="mt-1 text-xl font-bold sm:text-2xl">
                  {humanizeHeadline(
                    weeklyAssessment.status,
                  )}
                </h2>

                <p className="mt-2 max-w-3xl text-sm leading-relaxed text-base-content/65">
                  {humanizeWeeklySituation(
                    weeklyAssessment,
                    actualPercent,
                    projectedPercent,
                  )}
                </p>
              </div>

            </div>

            <div className="flex flex-wrap gap-2">

              <HumanMetric
                icon={
                  <HeartPulse className="h-4 w-4" />
                }
                label={
                  <MetricTooltip
                    metric="readiness"
                    label={`Forme ${Math.round(readiness.score)}/100`}
                  />
                }
              />

              <HumanMetric
                icon={
                  <Activity className="h-4 w-4" />
                }
                label={
                  actualPercent !== undefined
                    ? `Charge réalisée ${Math.round(actualPercent)} %`
                    : 'Charge en cours'
                }
              />

              <HumanMetric
                icon={
                  attentionSignals.length > 0
                    ? (
                        <TriangleAlert className="h-4 w-4" />
                      )
                    : (
                        <CircleCheck className="h-4 w-4" />
                      )
                }
                label={
                  attentionSignals.length === 0
                    ? 'Aucun signal préoccupant'
                    : (
                        `${attentionSignals.length} point${
                          attentionSignals.length > 1
                            ? 's'
                            : ''
                        } à surveiller`
                      )
                }
              />

            </div>

          </div>
        </section>


        {/* ==================================================
            CONSEIL DU COACH
        ================================================== */}

        <section className="card border border-primary/20 bg-primary/5 shadow-sm">
          <div className="card-body gap-4 p-5 sm:p-6">

            <div className="flex items-start gap-3">

              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                <Brain className="h-5 w-5" />
              </div>

              <div className="min-w-0">

                <p className="text-xs font-bold uppercase tracking-wide text-primary/70">
                  Conseil du Coach
                </p>

                <h2 className="mt-1 text-lg font-bold text-base-content">
                  {coachAdviceHeadline(
                    weeklyAssessment.status,
                    weeklyAssessment.adaptationOpportunity,
                  )}
                </h2>

              </div>

            </div>

            <p className="max-w-3xl text-sm leading-relaxed text-base-content/70">
              {weeklyAssessment.instruction}
            </p>

            <p className="max-w-3xl text-sm leading-relaxed text-base-content/55">
              {coachAdviceContext(
                weeklyAssessment.status,
                weeklyAssessment.adaptationOpportunity,
                weeklyAssessment.projectedGapPercent,
              )}
            </p>

          </div>
        </section>


        {/* ==================================================
            PROGRESSION HEBDOMADAIRE
        ================================================== */}

        <section className="card border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body gap-5 p-5 sm:p-6">

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-base-content/40">
                Où tu en es
              </p>

              <h2 className="mt-1 text-lg font-bold">
                Ta progression cette semaine
              </h2>
            </div>

            <div className="space-y-3">

              <div className="flex items-end justify-between gap-4">

                <div>
                  <p className="text-xs text-base-content/45">
                    Déjà réalisé
                  </p>

                  <p className="text-xl font-bold tabular-nums">
                    {actualPercent !== undefined
                      ? `${Math.round(actualPercent)} %`
                      : '—'}
                  </p>
                </div>

                <div className="text-right">
                  <p className="text-xs text-base-content/45">
                    Fin de semaine estimée
                  </p>

                  <p className="text-xl font-bold tabular-nums">
                    {projectedPercent !== undefined
                      ? `${Math.round(projectedPercent)} %`
                      : '—'}

                    {weeklyAssessment.targetLoad && (
                      <span className="ml-1 text-sm font-medium text-base-content/40">
                        / cible 100 %
                      </span>
                    )}
                  </p>
                </div>

              </div>

              <progress
                className="progress progress-primary h-3 w-full"
                value={progressPercent}
                max={100}
              />

              <p className="text-sm leading-relaxed text-base-content/60">
                {buildProgressSentence(
                  weeklyAssessment,
                )}
              </p>

            </div>

          </div>
        </section>


        {/* ==================================================
            AUJOURD'HUI
        ================================================== */}

        <section className="card border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body gap-4 p-5 sm:p-6">

            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-base-content/40">
                Aujourd’hui
              </p>

              <h2 className="mt-1 text-lg font-bold">
                Ce que tu as à faire
              </h2>
            </div>

            {todaySessions.length > 0 ? (
              <div className="space-y-3">

                {todaySessions.map(
                  (
                    item,
                    index,
                  ) => {
                    const session =
                      item.session

                    if (!session) {
                      return null
                    }

                    return (
                      <div
                        key={
                          session.id
                          ?? `${session.date}-${index}`
                        }
                        className="rounded-box border border-base-300 bg-base-200/30 p-4"
                      >

                        <div className="flex flex-wrap items-start justify-between gap-3">

                          <div className="min-w-0">

                            <p className="font-semibold text-base-content">
                              {session.title}
                            </p>

                            <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-base-content/50">

                              <span>
                                {humanizeSessionType(
                                  session.type,
                                )}
                              </span>

                              <span className="flex items-center gap-1">
                                <Clock className="h-3.5 w-3.5" />
                                {session.durationMinutes} min
                              </span>

                              <span>
                                {humanizeIntensity(
                                  session.intensity,
                                )}
                              </span>

                            </div>

                          </div>

                          <DecisionBadge
                            action={
                              item.decision.action
                            }
                          />

                        </div>

                        <p className="mt-3 text-sm leading-relaxed text-base-content/65">
                          {humanizeSessionDecision(
                            item.decision.action,
                            item.decision.reason,
                          )}
                        </p>

                        {(
                          item.decision.action === 'reduce'
                          && item.decision.recommendedDurationMinutes
                        ) && (
                          <div className="mt-3 flex flex-wrap gap-2">

                            <span className="badge badge-warning badge-outline">
                              Durée conseillée :
                              {' '}
                              {Math.round(
                                item.decision.recommendedDurationMinutes,
                              )}
                              {' min'}
                            </span>

                            {item.decision.recommendedIntensity && (
                              <span className="badge badge-warning badge-outline">
                                Intensité :
                                {' '}
                                {humanizeIntensity(
                                  item.decision.recommendedIntensity,
                                )}
                              </span>
                            )}

                          </div>
                        )}

                      </div>
                    )
                  },
                )}

              </div>
            ) : (
              <div className="flex items-start gap-3 rounded-box bg-success/5 p-4">

                <CircleCheck className="mt-0.5 h-5 w-5 shrink-0 text-success" />

                <div>
                  <p className="font-medium">
                    Journée de récupération
                  </p>

                  <p className="mt-1 text-sm text-base-content/55">
                    Aucune séance n’est prévue aujourd’hui.
                    Profite de cette journée pour récupérer
                    et préparer la suite de la semaine.
                  </p>
                </div>

              </div>
            )}

          </div>
        </section>


        {/* ==================================================
            FORME & RÉCUPÉRATION
        ================================================== */}

        <section className="card border border-base-300 bg-base-100 shadow-sm">
          <div className="card-body gap-5 p-5 sm:p-6">

            <div className="flex items-start justify-between gap-5">

              <div className="min-w-0">

                <p className="text-xs font-semibold uppercase tracking-wide text-base-content/40">
                  Forme & récupération
                </p>

                <h2 className="mt-1 text-lg font-bold">
                  {readinessHeadline(
                    readiness.score,
                  )}
                </h2>

                <p className="mt-1 max-w-2xl text-sm leading-relaxed text-base-content/55">
                  {readinessSummary(
                    readiness.score,
                    attentionSignals.length,
                  )}
                </p>

              </div>

              <div className="shrink-0 text-right">

                <div className="flex items-center justify-end gap-1">
                  <span className="text-xs text-base-content/40">
                    Forme
                  </span>

                  <MetricTooltip
                    metric="readiness"
                  />
                </div>

                <p className="mt-0.5 text-2xl font-bold tabular-nums">
                  {Math.round(readiness.score)}

                  <span className="text-sm font-medium text-base-content/35">
                    /100
                  </span>
                </p>

              </div>

            </div>



            {attentionSignals.length > 0 ? (
              <div className="space-y-3">

                <p className="text-xs font-semibold uppercase tracking-wide text-base-content/40">
                  À surveiller
                </p>

                <div className="space-y-2">

                  {attentionSignals.map(
                    (
                      signal,
                      index,
                    ) => (
                      <div
                        key={index}
                        className="flex items-start gap-3 rounded-box bg-warning/5 p-3.5"
                      >

                        <TriangleAlert className="mt-0.5 h-4 w-4 shrink-0 text-warning" />

                        <div className="min-w-0">

                          {'metric' in signal && signal.metric && (
                            <p className="mb-0.5 text-sm font-semibold">
                              {humanizeReadinessMetric(
                                signal.metric,
                              )}
                            </p>
                          )}

                          <p className="text-sm leading-relaxed text-base-content/65">
                            {signal.reason}
                          </p>

                        </div>

                      </div>
                    ),
                  )}

                </div>

                <div className="flex items-start gap-3 rounded-box bg-success/5 p-3.5">

                  <CircleCheck className="mt-0.5 h-4 w-4 shrink-0 text-success" />

                  <p className="text-sm leading-relaxed text-base-content/60">
                    {buildAttentionConclusion(
                      readiness.score,
                      attentionSignals.length,
                    )}
                  </p>

                </div>

              </div>
            ) : (
              <div className="flex items-start gap-3 rounded-box bg-success/5 p-4">

                <CircleCheck className="mt-0.5 h-5 w-5 shrink-0 text-success" />

                <div>

                  <p className="font-medium">
                    Rien de particulier à surveiller
                  </p>

                  <p className="mt-1 text-sm leading-relaxed text-base-content/55">
                    Les indicateurs disponibles sont cohérents
                    avec la poursuite normale du programme.
                  </p>

                </div>

              </div>
            )}

          </div>
        </section>


        {/* ==================================================
            APPRENTISSAGE OPENCOACH
        ================================================== */}

        {weeklyAssessment.historyConfidence < 1 && (
          <section className="rounded-box border border-base-300 bg-base-100 p-4 sm:p-5">

            <div className="flex items-start gap-3">

              <Sparkles className="mt-0.5 h-5 w-5 shrink-0 text-info" />

              <div className="min-w-0 flex-1">

                <div className="flex flex-wrap items-center justify-between gap-2">

                  <div>
                    <p className="font-semibold">
                      OpenCoach affine encore ta référence
                    </p>

                    <p className="mt-0.5 text-xs text-base-content/45">
                      Historique utilisé :
                      {' '}
                      {formatHistoryPeriod(
                        weeklyAssessment.historyWindowDays,
                      )}
                    </p>
                  </div>

                  <MetricTooltip
                    metric="reference_confidence"
                  />

                </div>

                <progress
                  className="progress progress-info mt-3 h-2 w-full"
                  value={
                    Math.min(
                      weeklyAssessment.historyWindowDays,
                      28,
                    )
                  }
                  max={28}
                />

                <p className="mt-3 text-sm leading-relaxed text-base-content/60">
                  {buildLearningSentence(
                    weeklyAssessment.historyWindowDays,
                    weeklyAssessment.historyConfidenceLevel,
                  )}
                </p>


              </div>

            </div>

          </section>
        )}


        {/* ==================================================
            DÉTAILS TECHNIQUES
        ================================================== */}

        <details className="collapse collapse-arrow border border-base-300 bg-base-100">

          <summary className="collapse-title font-medium">
            Voir les données détaillées
          </summary>

          <div className="collapse-content">

            <div className="grid gap-3 pt-2 sm:grid-cols-2 lg:grid-cols-4">

              <DetailMetric
                label="Charge réalisée"
                value={formatNumber(
                  weeklyAssessment.actualLoadToDate,
                )}
              />

              <DetailMetric
                label="Charge restante prévue"
                value={formatNumber(
                  weeklyAssessment.remainingPlannedLoad,
                )}
              />

              <DetailMetric
                label="Projection fin de semaine"
                value={formatNumber(
                  weeklyAssessment.projectedWeekLoad,
                )}
              />

              <DetailMetric
                label="Écart projeté"
                value={
                  weeklyAssessment.projectedGapPercent !== undefined
                    ? `${formatSigned(
                        weeklyAssessment.projectedGapPercent,
                      )} %`
                    : '—'
                }
              />

              <DetailMetric
                label="Jours restants"
                value={`${weeklyAssessment.remainingDays}`}
              />

              <DetailMetric
                label="Séances restantes"
                value={`${weeklyAssessment.remainingSessionsCount}`}
              />

              <DetailMetric
                label="Historique utilisé"
                value={
                  `${weeklyAssessment.historyWindowDays} jours`
                }
              />

              <DetailMetric
                label={
                  <MetricTooltip
                    metric="reference_confidence"
                    label="Confiance référence"
                  />
                }
                value={
                  formatConfidence(
                    weeklyAssessment.historyConfidenceLevel,
                  )
                }
              />

            </div>


          </div>
        </details>

      </div>

    </PageContainer>
  )
}


function PageContainer({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <main className="min-h-screen bg-base-200">
      <div className="mx-auto max-w-5xl px-4 py-5 sm:px-6 lg:py-6">
        {children}
      </div>
    </main>
  )
}


function PageHeader() {
  return (
    <header className="mb-6">

      <div className="flex items-center gap-3">

        <div className="flex h-11 w-11 items-center justify-center rounded-box bg-primary/10 text-primary">
          <Brain className="h-6 w-6" />
        </div>

        <div>
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Coach
          </h1>

          <p className="mt-0.5 text-sm text-base-content/50">
            L’essentiel pour savoir où tu en es et quoi faire.
          </p>
        </div>

      </div>

    </header>
  )
}


function StatusIcon({
  status,
}: {
  status: string
}) {
  if (status === 'aligned') {
    return (
      <CircleCheck className="mt-1 h-6 w-6 shrink-0 text-success" />
    )
  }

  return (
    <TriangleAlert className="mt-1 h-6 w-6 shrink-0 text-warning" />
  )
}


function HumanMetric({
  icon,
  label,
}: {
  icon: React.ReactNode
  label: React.ReactNode
}) {
  return (
    <div className="flex items-center gap-2 rounded-full bg-base-200 px-3 py-1.5 text-sm">

      <span className="text-base-content/45">
        {icon}
      </span>

      <span className="font-medium">
        {label}
      </span>

    </div>
  )
}


function DetailMetric({
  label,
  value,
}: {
  label: React.ReactNode
  value: string
}) {
  return (
    <div className="rounded-box bg-base-200/50 p-3">

      <p className="text-xs text-base-content/45">
        {label}
      </p>

      <p className="mt-1 font-semibold tabular-nums">
        {value}
      </p>

    </div>
  )
}


function DecisionBadge({
  action,
}: {
  action: string
}) {
  if (action === 'keep') {
    return (
      <span className="badge badge-success gap-1">
        <CircleCheck className="h-3.5 w-3.5" />
        À conserver
      </span>
    )
  }

  if (action === 'reduce') {
    return (
      <span className="badge badge-warning gap-1">
        ↘ À alléger
      </span>
    )
  }

  if (action === 'rest') {
    return (
      <span className="badge badge-info gap-1">
        Récupération
      </span>
    )
  }

  if (action === 'skip') {
    return (
      <span className="badge badge-error gap-1">
        À supprimer
      </span>
    )
  }

  return (
    <span className="badge badge-warning badge-outline">
      À adapter
    </span>
  )
}


function humanizeHeadline(
  status: string,
): string {
  if (status === 'aligned') {
    return 'Ta semaine est sur les rails'
  }

  if (status === 'under_target') {
    return 'Ta semaine est un peu plus légère que prévu'
  }

  if (status === 'over_target') {
    return 'Ta semaine est plus chargée que prévu'
  }

  return 'OpenCoach apprend encore ton rythme'
}


function humanizeWeeklySituation(
  weekly: {
    status: string
    projectedGapPercent?: number
  },
  actualPercent?: number,
  projectedPercent?: number,
): string {
  if (
    weekly.status === 'aligned'
    && actualPercent !== undefined
    && projectedPercent !== undefined
  ) {
    return (
      `Tu as réalisé ${Math.round(actualPercent)} % `
      + `de la charge prévue pour cette semaine. `
      + `En suivant le programme restant, tu devrais terminer `
      + `autour de ${Math.round(projectedPercent)} % de ta cible. `
      + `La trajectoire est bonne, rien à modifier pour le moment.`
    )
  }

  if (
    weekly.status === 'under_target'
    && actualPercent !== undefined
    && projectedPercent !== undefined
  ) {
    return (
      `Tu as réalisé ${Math.round(actualPercent)} % `
      + `de ta charge cible. `
      + `Avec les séances encore prévues, la semaine devrait `
      + `terminer autour de ${Math.round(projectedPercent)} %.`
    )
  }

  if (
    weekly.status === 'over_target'
    && actualPercent !== undefined
    && projectedPercent !== undefined
  ) {
    return (
      `Tu as déjà réalisé ${Math.round(actualPercent)} % `
      + `de ta charge cible. `
      + `La projection atteint actuellement environ `
      + `${Math.round(projectedPercent)} %, `
      + `donc la fin de semaine mérite d’être surveillée.`
    )
  }

  if (
    weekly.status === 'aligned'
    && weekly.projectedGapPercent !== undefined
  ) {
    return (
      `Ta semaine devrait terminer très proche de la cible prévue. `
      + `L’écart estimé est seulement de `
      + `${Math.abs(
        weekly.projectedGapPercent,
      ).toFixed(1)} %.`
    )
  }

  return (
    'OpenCoach consolide encore les données nécessaires '
    + 'pour situer précisément ta semaine.'
  )
}


function buildProgressSentence(
  weekly: {
    projectedGapPercent?: number
    remainingDays: number
    remainingSessionsCount: number
  },
): string {
  let sentence = (
    `Il reste ${weekly.remainingDays} jour${
      weekly.remainingDays > 1
        ? 's'
        : ''
    } et ${weekly.remainingSessionsCount} séance${
      weekly.remainingSessionsCount > 1
        ? 's'
        : ''
    } prévue${
      weekly.remainingSessionsCount > 1
        ? 's'
        : ''
    }.`
  )

  if (
    weekly.projectedGapPercent
    !== undefined
  ) {
    sentence += (
      ` À ce rythme, l’écart final serait de `
      + `${Math.abs(
        weekly.projectedGapPercent,
      ).toFixed(1)} %.`
    )
  }

  return sentence
}


function coachAdviceHeadline(
  status: string,
  adaptationOpportunity: boolean,
): string {
  if (
    status === 'aligned'
    && !adaptationOpportunity
  ) {
    return 'Continue comme prévu'
  }

  if (
    status === 'under_target'
    && adaptationOpportunity
  ) {
    return 'Une adaptation peut être utile'
  }

  if (
    status === 'over_target'
    && adaptationOpportunity
  ) {
    return 'La fin de semaine mérite d’être allégée'
  }

  if (status === 'under_target') {
    return 'Ne cherche pas à rattraper artificiellement'
  }

  if (status === 'over_target') {
    return 'N’ajoute pas de charge supplémentaire'
  }

  return 'Conserve le programme actuel'
}


function coachAdviceContext(
  status: string,
  adaptationOpportunity: boolean,
  projectedGapPercent?: number,
): string {
  if (
    status === 'aligned'
    && projectedGapPercent !== undefined
  ) {
    return (
      `La projection reste très proche de la cible `
      + `avec un écart estimé à `
      + `${Math.abs(projectedGapPercent).toFixed(1)} %. `
      + `Le programme restant suffit pour terminer la semaine correctement.`
    )
  }

  if (
    status === 'under_target'
    && adaptationOpportunity
  ) {
    return (
      'Il reste encore assez de marge dans la semaine '
      + 'pour envisager un ajustement raisonnable. '
      + 'Aucune séance ne sera modifiée sans ta validation.'
    )
  }

  if (
    status === 'over_target'
    && adaptationOpportunity
  ) {
    return (
      'Réduire légèrement la charge restante permettrait '
      + 'de revenir vers la zone prévue sans toucher '
      + 'à la semaine suivante.'
    )
  }

  if (status === 'under_target') {
    return (
      'Le temps restant ne justifie pas de forcer un rattrapage. '
      + 'La semaine suivante repartira sur sa propre trajectoire.'
    )
  }

  if (status === 'over_target') {
    return (
      'La charge est déjà élevée. '
      + 'La priorité est de ne pas accentuer davantage le dépassement.'
    )
  }

  return (
    'OpenCoach consolide encore ta référence avant '
    + 'de proposer des ajustements plus précis.'
  )
}


function humanizeReadinessMetric(
  metric: string,
): string {
  const labels: Record<
    string,
    string
  > = {
    hrv: 'HRV',
    resting_hr: 'Fréquence cardiaque au repos',
    sleep_duration: 'Durée de sommeil',
    sleep_score: 'Qualité du sommeil',
    training_load: 'Charge récente',
    fitness_ctl: 'Charge chronique',
    fatigue_atl: 'Fatigue récente',
    training_balance: 'Équilibre de charge',
  }

  return (
    labels[metric]
    ?? metric.replaceAll('_', ' ')
  )
}


function readinessHeadline(
  score: number,
): string {
  if (score >= 80) {
    return 'Bonne forme aujourd’hui'
  }

  if (score >= 60) {
    return 'Forme correcte aujourd’hui'
  }

  return 'Récupération à privilégier'
}


function readinessSummary(
  score: number,
  signalCount: number,
): string {
  if (
    score >= 80
    && signalCount === 0
  ) {
    return (
      'Tes indicateurs sont favorables et cohérents '
      + 'avec le programme prévu.'
    )
  }

  if (score >= 80) {
    return (
      'Ta forme générale reste bonne malgré quelques '
      + 'éléments à surveiller.'
    )
  }

  if (score >= 60) {
    return (
      'La situation reste correcte, mais tes sensations '
      + 'devront guider les séances du jour.'
    )
  }

  return (
    'Plusieurs indicateurs invitent à réduire la contrainte '
    + 'et à favoriser la récupération.'
  )
}


function buildAttentionConclusion(
  readinessScore: number,
  signalCount: number,
): string {
  if (
    readinessScore >= 80
    && signalCount === 1
  ) {
    return (
      'Ce signal reste isolé et ne remet pas en cause '
      + 'le programme prévu pour le moment.'
    )
  }

  if (readinessScore >= 80) {
    return (
      'Ta forme générale reste bonne, mais garde ces '
      + 'signaux en tête pendant les prochaines séances.'
    )
  }

  return (
    'Ces signaux méritent d’être réévalués avant '
    + 'les prochaines séances exigeantes.'
  )
}


function formatHistoryPeriod(
  historyWindowDays: number,
): string {
  const weeks = Math.max(
    1,
    Math.round(
      historyWindowDays / 7,
    ),
  )

  if (weeks === 1) {
    return '1 semaine'
  }

  return `${weeks} semaines`
}


function buildLearningSentence(
  historyWindowDays: number,
  confidenceLevel: string,
): string {
  if (
    historyWindowDays <= 7
    || confidenceLevel === 'low'
  ) {
    return (
      'La référence est encore jeune. '
      + 'Les prochaines semaines permettront à OpenCoach '
      + 'de mieux distinguer ta charge habituelle, ta récupération '
      + 'et ta capacité réelle à progresser.'
    )
  }

  if (
    historyWindowDays <= 14
    || confidenceLevel === 'moderate'
  ) {
    return (
      'La référence commence à se stabiliser. '
      + 'OpenCoach dispose déjà de davantage de recul '
      + 'pour interpréter ta charge et tes réactions à l’entraînement.'
    )
  }

  if (
    historyWindowDays < 28
    || confidenceLevel === 'good'
  ) {
    return (
      'La référence devient solide. '
      + 'Les recommandations s’appuient maintenant '
      + 'sur plusieurs semaines d’entraînement.'
    )
  }

  return (
    'OpenCoach dispose désormais d’un historique suffisamment '
    + 'large pour utiliser une référence hebdomadaire stable.'
  )
}


function humanizeSessionType(
  type: string,
): string {
  const labels: Record<
    string,
    string
  > = {
    aerobic_easy: 'Endurance fondamentale',
    threshold: 'Seuil',
    speed_development: 'Développement de la vitesse',
    strength_lower_body: 'Renforcement jambes',
    long_endurance: 'Sortie longue',
  }

  return (
    labels[type]
    ?? type.replaceAll('_', ' ')
  )
}


function humanizeIntensity(
  intensity: string,
): string {
  const labels: Record<
    string,
    string
  > = {
    easy: 'Facile',
    moderate: 'Modérée',
    hard: 'Soutenue',
    very_hard: 'Très soutenue',
    high: 'Soutenue',
  }

  return (
    labels[intensity]
    ?? intensity
  )
}


function humanizeSessionDecision(
  action: string,
  reason: string,
): string {
  if (action === 'keep') {
    return (
      'Cette séance est cohérente avec ton état actuel '
      + 'et peut être réalisée comme prévu.'
    )
  }

  if (action === 'reduce') {
    return (
      'OpenCoach recommande d’alléger cette séance. '
      + reason
    )
  }

  if (action === 'rest') {
    return (
      'La récupération est prioritaire aujourd’hui. '
      + reason
    )
  }

  return reason
}


function percentageOfTarget(
  value: number,
  target: number,
): number {
  if (target <= 0) {
    return 0
  }

  return (
    value
    / target
    * 100
  )
}


function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    'fr-FR',
    {
      maximumFractionDigits: 1,
    },
  ).format(value)
}


function formatSigned(
  value: number,
): string {
  if (value > 0) {
    return `+${formatNumber(value)}`
  }

  return formatNumber(value)
}


function formatConfidence(
  level: string,
): string {
  if (level === 'low') {
    return 'encore faible'
  }

  if (level === 'moderate') {
    return 'moyenne'
  }

  if (level === 'good') {
    return 'bonne'
  }

  return 'élevée'
}
