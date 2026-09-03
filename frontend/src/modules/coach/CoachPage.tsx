import {
  Brain,
  Clock,
  Info,
} from 'lucide-react'

import {
  useState,
} from 'react'

import {
  SidePanel,
} from '../../components/ui/SidePanel'

import {
  useCoachToday,
} from './useCoachToday'

import {
  TrainingDetails,
} from '../training/TrainingDetails'

import {
  useTrainingSessions,
} from '../training/trainingStore'



export function CoachPage() {
  const {
    sessions: trainingSessions,
    validateSession,
  } = useTrainingSessions()

  const [
    selectedSessionId,
    setSelectedSessionId,
  ] = useState<string | null>(
    null,
  )

  const selectedTrainingSession =
    selectedSessionId
      ? (
          trainingSessions.find(
            item =>
              item.id
              === selectedSessionId,
          )
          ?? null
        )
      : null

  const {
    coach,
    loading,
    unavailable,
    error,
  } = useCoachToday()

  if (loading) {
    return (
      <PageContainer>
        <div className="flex min-h-[420px] items-center justify-center">
          <div className="flex items-center gap-2 text-[13px] text-slate-400">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-500" />
            Analyse de ta situation…
          </div>
        </div>
      </PageContainer>
    )
  }

  if (error || unavailable || !coach) {
    return (
      <PageContainer>
        <div className="flex min-h-[420px] items-center justify-center">
          <div className="max-w-md text-center">
            <Brain className="mx-auto h-6 w-6 text-slate-300" />
            <h2 className="mt-3 text-[15px] font-semibold text-slate-900 dark:text-white">
              Analyse indisponible
            </h2>
            <p className="mt-1 text-[10.5px] leading-5 text-slate-400">
              {error ?? 'OpenCoach prépare encore ton analyse.'}
            </p>
          </div>
        </div>
      </PageContainer>
    )
  }

  const {
    readiness,
    recentLoad,
    recentLoadAssessment,
    sessionDecisions,
    weeklyAssessment,
    weeklyPlan,
    dataWarning,
  } = coach

  const todayItem =
    sessionDecisions.find(item => item.session !== null)

  const session = todayItem?.session ?? null

  const attentionSignals = [
    ...readiness.signals.filter(signal => signal.level !== 'normal'),
    ...(recentLoadAssessment?.signals ?? []),
  ]

  const tone = resolveReadinessTone(
    readiness.score,
    readiness.criticalCount,
    readiness.warningCount,
  )

  const actualPercent =
    weeklyAssessment.targetLoad
      ? percentageOfTarget(
          weeklyAssessment.actualLoadToDate,
          weeklyAssessment.targetLoad,
        )
      : 0

  const projectedPercent =
    weeklyAssessment.targetLoad
      ? percentageOfTarget(
          weeklyAssessment.projectedWeekLoad,
          weeklyAssessment.targetLoad,
        )
      : 0

  return (
    <PageContainer>
      <header className="mb-4 flex items-end justify-between gap-4">
        <div>
          <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-600 dark:text-emerald-400">
            OpenCoach
          </p>

          <h1 className="mt-0.5 text-[30px] font-bold tracking-[-0.04em] text-slate-950 dark:text-white">
            Coach
          </h1>

          <p className="mt-1 text-[13px] text-slate-400 dark:text-slate-500">
            Ton briefing d'entraînement du jour.
          </p>
        </div>

        <div className="hidden text-right sm:block">
          <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-slate-300 dark:text-slate-600">
            Aujourd'hui
          </p>

          <p className="mt-0.5 text-[10px] font-semibold text-slate-500 dark:text-slate-400">
            {new Intl.DateTimeFormat('fr-FR', {
              weekday: 'short',
              day: '2-digit',
              month: 'short',
            }).format(new Date())}
          </p>
        </div>
      </header>

      {dataWarning && (
        <div className="mb-3 flex items-center gap-2 rounded-[10px] border border-amber-500/15 bg-amber-50/70 px-3 py-2 text-[9px] text-amber-700 dark:bg-amber-500/[0.05] dark:text-amber-400">
          <Info className="h-3.5 w-3.5 shrink-0" />
          {dataWarning}
        </div>
      )}

      <div className="overflow-hidden rounded-[16px] border border-black/[0.07] bg-white shadow-[0_1px_3px_rgba(15,23,42,0.03)] dark:border-white/[0.07] dark:bg-[#151b1f]">

        {/* ==================================================
            HERO / DECISION
            ================================================== */}

        <div className="grid lg:grid-cols-[minmax(0,1fr)_270px]">

          <section className="relative min-w-0 p-5 sm:p-6 lg:p-7">

            <div className="pointer-events-none absolute -left-24 -top-32 h-72 w-72 rounded-full bg-emerald-500/[0.045] blur-3xl" />

            <div className="relative">
              <div className="flex items-center gap-2">
                <span
                  className={[
                    'h-2 w-2 rounded-full',
                    tone === 'critical'
                      ? 'bg-red-500'
                      : tone === 'warning'
                        ? 'bg-amber-500'
                        : 'bg-emerald-500',
                  ].join(' ')}
                />

                <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                  Recommandation du jour
                </span>
              </div>

              <h2 className="mt-4 max-w-[720px] text-[27px] font-bold leading-[1.1] tracking-[-0.045em] text-slate-950 dark:text-white sm:text-[30px]">
                {buildDailyDecisionHeadline(
                  readiness.score,
                  readiness.criticalCount,
                  readiness.warningCount,
                  recentLoadAssessment?.hasCritical ?? false,
                  recentLoadAssessment?.hasOverload ?? false,
                )}
              </h2>

              <p className="mt-3 max-w-[680px] text-[14px] leading-[1.7] text-slate-500 dark:text-slate-400">
                {readinessSummary(
                  readiness.score,
                  attentionSignals.length,
                )}
              </p>

              {session ? (
                <div
                  className="
                    mt-6
                    overflow-hidden
                    rounded-[13px]
                    border
                    border-white/[0.07]
                    bg-[#141917]
                    shadow-[0_12px_35px_rgba(4,12,8,0.10)]
                  "
                >
                  <div
                    className="
                      relative
                      overflow-hidden
                      px-4
                      py-4
                      sm:px-5
                    "
                  >
                    <div
                      className="
                        pointer-events-none
                        absolute
                        -right-20
                        -top-24
                        h-44
                        w-44
                        rounded-full
                        bg-emerald-500/[0.08]
                        blur-3xl
                      "
                    />

                    <div
                      className="
                        relative
                        flex
                        flex-col
                        gap-4
                        sm:flex-row
                        sm:items-end
                        sm:justify-between
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
                            className="
                              text-[10px]
                              font-bold
                              uppercase
                              tracking-[0.11em]
                              text-emerald-400
                            "
                          >
                            Séance du jour
                          </span>

                          {todayItem && (
                            <CockpitDecisionPill
                              action={
                                todayItem
                                  .decision
                                  .action
                              }
                            />
                          )}
                        </div>

                        <h3
                          className="
                            mt-2
                            text-[19px]
                            font-bold
                            tracking-[-0.025em]
                            text-white
                          "
                        >
                          {session.title}
                        </h3>

                        <div
                          className="
                            mt-2.5
                            flex
                            flex-wrap
                            items-center
                            gap-x-4
                            gap-y-2
                            text-[12px]
                            font-medium
                            text-white/55
                          "
                        >
                          <span
                            className="
                              flex
                              items-center
                              gap-1.5
                            "
                          >
                            <Clock
                              className="
                                h-3.5
                                w-3.5
                                text-emerald-400
                              "
                            />

                            {
                              session
                                .durationMinutes
                            } min
                          </span>

                          <span>
                            {
                              humanizeIntensity(
                                session.intensity,
                              )
                            }
                          </span>

                          {
                            session
                              .heartRateZone
                            && (
                              <span>
                                {
                                  session
                                    .heartRateZone
                                }
                              </span>
                            )
                          }

                          <span>
                            {
                              humanizeSessionType(
                                session.type,
                              )
                            }
                          </span>
                        </div>
                      </div>


                      <button
                        type="button"
                        disabled={!session.id}
                        onClick={() => {
                          if (!session.id) {
                            return
                          }

                          setSelectedSessionId(
                            session.id,
                          )
                        }}
                        className="
                          inline-flex
                          h-8
                          shrink-0
                          items-center
                          justify-center
                          rounded-[8px]
                          border
                          border-emerald-400/25
                          bg-emerald-400/[0.09]
                          px-3
                          text-[10px]
                          font-semibold
                          text-emerald-300
                          transition
                          hover:border-emerald-400/40
                          hover:bg-emerald-400/[0.14]
                          hover:text-emerald-200
                          disabled:cursor-not-allowed
                          disabled:opacity-40
                        "
                      >
                        Voir la séance

                        <span
                          className="
                            ml-1.5
                            text-emerald-400
                          "
                        >
                          →
                        </span>
                      </button>
                    </div>


                    {todayItem && (
                      <div
                        className="
                          relative
                          mt-4
                          border-t
                          border-white/[0.065]
                          pt-3
                        "
                      >
                        <p
                          className="
                            max-w-[680px]
                            text-[12px]
                            leading-[1.65]
                            text-white/45
                          "
                        >
                          {
                            humanizeSessionDecision(
                              todayItem
                                .decision
                                .action,
                              todayItem
                                .decision
                                .reason,
                            )
                          }
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="mt-6 border-t border-black/[0.06] pt-4 dark:border-white/[0.06]">
                  <p className="text-[10px] font-bold uppercase tracking-[0.1em] text-emerald-600 dark:text-emerald-400">
                    Aujourd'hui
                  </p>

                  <p className="mt-1.5 text-[15px] font-semibold text-slate-800 dark:text-slate-200">
                    Journée de récupération
                  </p>

                  <p className="mt-1 text-[9.5px] text-slate-400">
                    Aucune séance prévue. La récupération fait partie du plan.
                  </p>
                </div>
              )}
            </div>
          </section>


          {/* ================================================
              RIGHT RAIL
              ================================================ */}

          <aside className="border-t border-black/[0.06] bg-[#fafbfa] p-5 dark:border-white/[0.06] dark:bg-white/[0.018] lg:border-l lg:border-t-0">

            <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
              État du jour
            </p>

            <div className="mt-5 flex items-end gap-2">
              <span className="text-[54px] font-bold leading-none tracking-[-0.07em] text-slate-950 dark:text-white">
                {Math.round(readiness.score)}
              </span>

              <span className="mb-1 text-[11px] font-semibold text-slate-300 dark:text-slate-600">
                /100
              </span>
            </div>

            <p
              className={[
                'mt-2 text-[12px] font-bold uppercase tracking-[0.08em]',
                tone === 'critical'
                  ? 'text-red-500'
                  : tone === 'warning'
                    ? 'text-amber-500'
                    : 'text-emerald-600 dark:text-emerald-400',
              ].join(' ')}
            >
              {readinessStateLabel(
                readiness.score,
                readiness.criticalCount,
                readiness.warningCount,
              )}
            </p>

            <div className="mt-5 space-y-3">
              <RailMetric
                label="Récupération"
                value={
                  readiness.criticalCount > 0
                    ? 'Faible'
                    : readiness.warningCount > 0
                      ? 'À surveiller'
                      : 'Bonne'
                }
                tone={
                  readiness.criticalCount > 0
                    ? 'critical'
                    : readiness.warningCount > 0
                      ? 'warning'
                      : 'good'
                }
              />

              <RailMetric
                label="Charge"
                value={
                  recentLoadAssessment?.hasCritical
                    ? 'Critique'
                    : recentLoadAssessment?.hasOverload
                      ? 'Élevée'
                      : 'Maîtrisée'
                }
                tone={
                  recentLoadAssessment?.hasCritical
                    ? 'critical'
                    : recentLoadAssessment?.hasOverload
                      ? 'warning'
                      : 'good'
                }
              />

              <RailMetric
                label="Alertes"
                value={
                  attentionSignals.length === 0
                    ? 'Aucune'
                    : String(attentionSignals.length)
                }
                tone={
                  attentionSignals.length === 0
                    ? 'good'
                    : 'warning'
                }
              />
            </div>

            <div className="mt-5 border-t border-black/[0.06] pt-3 dark:border-white/[0.06]">
              <div className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                <span className="text-[8.5px] font-medium text-slate-400">
                  Données disponibles
                </span>
              </div>
            </div>
          </aside>
        </div>


        {/* ==================================================
            WEEK TRAJECTORY
            ================================================== */}

        <section className="border-t border-black/[0.06] px-5 py-5 dark:border-white/[0.06] sm:px-6 lg:px-7">

          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                Cette semaine
              </p>

              <h3 className="mt-1 text-[17px] font-semibold tracking-[-0.02em] text-slate-800 dark:text-slate-200">
                Trajectoire d'entraînement
              </h3>
            </div>

            <WeeklyStatusPill status={weeklyAssessment.status} />
          </div>

          <div className="mt-5 grid grid-cols-3 gap-5">
            <TrajectoryMetric
              value={formatNumber(weeklyAssessment.actualLoadToDate)}
              label="réalisé"
            />

            <TrajectoryMetric
              value={
                weeklyAssessment.targetLoad
                  ? formatNumber(weeklyAssessment.targetLoad)
                  : '—'
              }
              label="cible"
            />

            <TrajectoryMetric
              value={formatNumber(weeklyAssessment.projectedWeekLoad)}
              label="projeté"
              align="right"
            />
          </div>

          <CockpitTrajectory
            actual={actualPercent}
            projected={projectedPercent}
          />

          <div className="mt-4 flex flex-wrap items-center justify-between gap-2 text-[8.5px] font-medium text-slate-400 dark:text-slate-500">
            <span>
              {weeklyPlan
                ? `${humanizeTrainingPhaseV2(weeklyPlan.phase)} · semaine ${weeklyPlan.phaseWeekIndex}`
                : 'Plan en cours'}
            </span>

            <span>
              {weeklyAssessment.remainingSessionsCount} séance
              {weeklyAssessment.remainingSessionsCount > 1 ? 's' : ''} restante
              {weeklyAssessment.remainingSessionsCount > 1 ? 's' : ''}
            </span>
          </div>
        </section>


        {/* ==================================================
            DECISION FACTORS
            ================================================== */}

        <section className="border-t border-black/[0.06] px-5 py-5 dark:border-white/[0.06] sm:px-6 lg:px-7">

          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-400 dark:text-slate-500">
                Analyse
              </p>

              <h3 className="mt-1 text-[17px] font-semibold tracking-[-0.02em] text-slate-800 dark:text-slate-200">
                Pourquoi cette décision ?
              </h3>
            </div>

            <Brain className="h-4 w-4 text-emerald-500" />
          </div>

          <div className="mt-4 grid gap-x-8 gap-y-1 md:grid-cols-2">
            {readiness.signals.length > 0 ? (
              readiness.signals.slice(0, 4).map((signal, index) => (
                <DecisionFactor
                  key={`${signal.metric}-${index}`}
                  label={humanizeReadinessMetric(signal.metric)}
                  detail={signal.reason}
                  level={signal.level}
                />
              ))
            ) : (
              <>
                <DecisionFactor
                  label="Récupération"
                  detail="Aucun signal défavorable détecté"
                  level="normal"
                />

                <DecisionFactor
                  label="Charge récente"
                  detail={
                    recentLoad
                      ? `${formatNumber(recentLoad.actualLoadTotal)} sur les 7 derniers jours`
                      : 'Charge compatible avec le programme'
                  }
                  level={
                    recentLoadAssessment?.hasOverload
                      ? 'warning'
                      : 'normal'
                  }
                />
              </>
            )}

            {(recentLoadAssessment?.signals ?? []).slice(0, 2).map(
              (signal, index) => (
                <DecisionFactor
                  key={`load-${index}`}
                  label="Charge"
                  detail={signal.reason}
                  level={signal.level}
                />
              ),
            )}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-black/[0.055] pt-3 dark:border-white/[0.06]">
            <p className="max-w-2xl text-[11px] leading-5 text-slate-400 dark:text-slate-500">
              {weeklyAssessment.instruction}
            </p>

            <details className="group relative">
              <summary className="cursor-pointer list-none text-[8.5px] font-semibold text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 [&::-webkit-details-marker]:hidden">
                Détails de l'analyse
              </summary>

              <div className="mt-3 grid min-w-[260px] gap-2 sm:grid-cols-2 lg:grid-cols-4">
                <CockpitDetail
                  label="Charge restante"
                  value={formatNumber(weeklyAssessment.remainingPlannedLoad)}
                />

                <CockpitDetail
                  label="Écart projeté"
                  value={
                    weeklyAssessment.projectedGapPercent !== undefined
                      ? `${formatSigned(weeklyAssessment.projectedGapPercent)} %`
                      : '—'
                  }
                />

                <CockpitDetail
                  label="Historique"
                  value={`${weeklyAssessment.historyWindowDays} jours`}
                />

                <CockpitDetail
                  label="Confiance"
                  value={formatConfidence(weeklyAssessment.historyConfidenceLevel)}
                />
              </div>
            </details>
          </div>
        </section>
      </div>

      <SidePanel
        open={
          Boolean(
            selectedTrainingSession,
          )
        }
        eyebrow="Coach"
        title={
          selectedTrainingSession?.title
          ?? 'Détail de la séance'
        }
        onClose={() => {
          setSelectedSessionId(
            null,
          )
        }}
      >
        {selectedTrainingSession && (
          <TrainingDetails
            session={
              selectedTrainingSession
            }
            onValidateSession={async (
              activityId,
            ) => {
              return validateSession(
                selectedTrainingSession.id,
                activityId,
              )
            }}
          />
        )}
      </SidePanel>

    </PageContainer>
  )
}


/* ============================================================
   COACH COCKPIT V3 UI
   ============================================================ */

function CockpitDecisionPill({
  action,
}: {
  action: string
}) {
  const config =
    action === 'keep'
      ? ['Maintenir', 'text-emerald-600 bg-emerald-500/[0.07] dark:text-emerald-400']
      : action === 'reduce'
        ? ['Alléger', 'text-amber-600 bg-amber-500/[0.08] dark:text-amber-400']
        : action === 'rest'
          ? ['Récupération', 'text-sky-600 bg-sky-500/[0.08] dark:text-sky-400']
          : ['Adapter', 'text-slate-500 bg-slate-500/[0.07]']

  return (
    <span className={`rounded-full px-2 py-0.5 text-[7.5px] font-bold uppercase tracking-[0.06em] ${config[1]}`}>
      {config[0]}
    </span>
  )
}


function RailMetric({
  label,
  value,
  tone,
}: {
  label: string
  value: string
  tone: 'good' | 'warning' | 'critical'
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-[11px] text-slate-400 dark:text-slate-500">
        {label}
      </span>

      <div className="flex items-center gap-1.5">
        <span
          className={[
            'h-1.5 w-1.5 rounded-full',
            tone === 'critical'
              ? 'bg-red-500'
              : tone === 'warning'
                ? 'bg-amber-500'
                : 'bg-emerald-500',
          ].join(' ')}
        />

        <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
          {value}
        </span>
      </div>
    </div>
  )
}


function TrajectoryMetric({
  value,
  label,
  align = 'left',
}: {
  value: string
  label: string
  align?: 'left' | 'right'
}) {
  return (
    <div className={align === 'right' ? 'text-right' : ''}>
      <p className="text-[22px] font-bold tracking-[-0.035em] tabular-nums text-slate-850 dark:text-slate-200">
        {value}
      </p>

      <p className="mt-0.5 text-[8px] font-medium uppercase tracking-[0.07em] text-slate-400">
        {label}
      </p>
    </div>
  )
}


function CockpitTrajectory({
  actual,
  projected,
}: {
  actual: number
  projected: number
}) {
  const a = Math.max(0, Math.min(100, actual))
  const p = Math.max(0, Math.min(100, projected))

  return (
    <div className="mt-4">
      <div className="relative h-[6px] rounded-full bg-slate-100 dark:bg-white/[0.055]">
        <div
          className="absolute inset-y-0 left-0 rounded-full bg-emerald-500"
          style={{ width: `${a}%` }}
        />

        <span
          className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-[3px] border-white bg-emerald-500 shadow-sm dark:border-[#151b1f]"
          style={{ left: `${a}%` }}
        />

        <span
          className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-slate-500 bg-white dark:border-slate-300 dark:bg-[#151b1f]"
          style={{ left: `${p}%` }}
        />

        <span className="absolute right-0 top-1/2 h-3.5 w-[2px] -translate-y-1/2 bg-slate-300 dark:bg-slate-600" />
      </div>

      <div className="relative mt-2 h-3 text-[7px] font-medium text-slate-300 dark:text-slate-600">
        <span
          className="absolute -translate-x-1/2"
          style={{ left: `${a}%` }}
        >
          maintenant
        </span>

        <span className="absolute right-0">
          cible
        </span>
      </div>
    </div>
  )
}


function DecisionFactor({
  label,
  detail,
  level,
}: {
  label: string
  detail: string
  level: string
}) {
  const warning = level === 'warning'
  const critical = level === 'critical'

  return (
    <div className="grid grid-cols-[18px_105px_minmax(0,1fr)] items-start gap-2 border-b border-black/[0.045] py-2.5 last:border-b-0 dark:border-white/[0.045]">
      <div
        className={[
          'mt-[2px] flex h-4 w-4 items-center justify-center rounded-full text-[9px] font-bold',
          critical
            ? 'bg-red-500/[0.08] text-red-500'
            : warning
              ? 'bg-amber-500/[0.08] text-amber-500'
              : 'bg-emerald-500/[0.08] text-emerald-600 dark:text-emerald-400',
        ].join(' ')}
      >
        {critical || warning ? '!' : '✓'}
      </div>

      <span className="text-[11px] font-semibold text-slate-700 dark:text-slate-300">
        {label}
      </span>

      <span className="text-[11px] leading-5 text-slate-400 dark:text-slate-500">
        {detail}
      </span>
    </div>
  )
}


function CockpitDetail({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-[8px] bg-slate-50 px-3 py-2 dark:bg-white/[0.025]">
      <p className="text-[7.5px] font-medium uppercase tracking-[0.06em] text-slate-400">
        {label}
      </p>

      <p className="mt-1 text-[10px] font-semibold tabular-nums text-slate-700 dark:text-slate-300">
        {value}
      </p>
    </div>
  )
}


function readinessStateLabel(
  score: number,
  criticalCount: number,
  warningCount: number,
): string {
  if (criticalCount > 0 || score < 50) {
    return 'Faible'
  }

  if (warningCount > 0 || score < 70) {
    return 'À surveiller'
  }

  if (score >= 85) {
    return 'Excellente'
  }

  return 'Très bonne'
}



/* ============================================================
   COACH COCKPIT V3 - PRESENTATION HELPERS
   ============================================================ */

function resolveReadinessTone(
  score: number,
  criticalCount: number,
  warningCount: number,
):
  | 'good'
  | 'warning'
  | 'critical' {
  if (
    criticalCount > 0
    || score < 50
  ) {
    return 'critical'
  }

  if (
    warningCount > 0
    || score < 70
  ) {
    return 'warning'
  }

  return 'good'
}


function buildDailyDecisionHeadline(
  score: number,
  criticalCount: number,
  warningCount: number,
  loadCritical: boolean,
  loadOverload: boolean,
): string {
  if (
    criticalCount > 0
    || loadCritical
    || score < 50
  ) {
    return (
      'Aujourd’hui, la récupération '
      + 'passe avant la charge'
    )
  }

  if (
    loadOverload
    && score < 80
  ) {
    return (
      'Reste strictement sur '
      + 'le programme prévu'
    )
  }

  if (
    score >= 80
    && warningCount === 0
  ) {
    return (
      'Garde la séance prévue'
    )
  }

  if (score >= 70) {
    return (
      'Le programme reste adapté '
      + 'à ton état du jour'
    )
  }

  return (
    'Adapte l’effort à tes '
    + 'sensations aujourd’hui'
  )
}


function WeeklyStatusPill({
  status,
}: {
  status: string
}) {
  const config =
    status === 'aligned'
      ? {
          label:
            'Sous contrôle',

          className:
            (
              'bg-emerald-500/[0.07] '
              + 'text-emerald-700 '
              + 'dark:text-emerald-400'
            ),
        }
      : status === 'over_target'
        ? {
            label:
              'Charge élevée',

            className:
              (
                'bg-amber-500/[0.08] '
                + 'text-amber-700 '
                + 'dark:text-amber-400'
              ),
          }
        : status === 'under_target'
          ? {
              label:
                'Sous la cible',

              className:
                (
                  'bg-sky-500/[0.08] '
                  + 'text-sky-700 '
                  + 'dark:text-sky-400'
                ),
            }
          : {
              label:
                'Analyse en cours',

              className:
                (
                  'bg-slate-500/[0.07] '
                  + 'text-slate-500 '
                  + 'dark:text-slate-400'
                ),
            }

  return (
    <span
      className={[
        (
          'rounded-full '
          + 'px-2 py-1 '
          + 'text-[7.5px] '
          + 'font-bold '
          + 'uppercase '
          + 'tracking-[0.06em]'
        ),
        config.className,
      ].join(' ')}
    >
      {config.label}
    </span>
  )
}


function humanizeTrainingPhaseV2(
  phase: string,
): string {
  const labels: Record<
    string,
    string
  > = {
    foundation:
      'Fondation',

    base:
      'Base',

    build:
      'Développement',

    specific:
      'Spécifique',

    taper:
      'Affûtage',

    recovery:
      'Récupération',

    return_to_training:
      'Retour entraînement',
  }

  return (
    labels[phase]
    ?? phase.replaceAll(
      '_',
      ' ',
    )
  )
}


function PageContainer({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <main
      className="
        min-h-screen
        bg-[#f5f7f6]
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          mx-auto
          max-w-[1180px]
          px-3
          py-4
          sm:px-5
          lg:px-5
          lg:py-[18px]
        "
      >
        {children}
      </div>
    </main>
  )
}


export function PageHeader() {
  return (
    <header className="mb-4">
      <p
        className="
          text-[10px]
          font-bold
          uppercase
          tracking-[0.13em]
          text-emerald-600
          dark:text-emerald-400
        "
      >
        Analyse
      </p>

      <h1
        className="
          mt-1
          text-[24px]
          font-bold
          tracking-[-0.035em]
          text-slate-950
          dark:text-white
        "
      >
        Coach
      </h1>

      <p
        className="
          mt-1
          max-w-2xl
          text-[11.5px]
          text-slate-400
          dark:text-slate-500
        "
      >
        Décision quotidienne basée sur ta
        récupération, ta charge et ton plan.
      </p>
    </header>
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

    resting_hr:
      'Fréquence cardiaque au repos',

    sleep_duration:
      'Durée de sommeil',

    sleep_score:
      'Qualité du sommeil',

    training_load:
      'Charge récente',

    fitness_ctl:
      'Charge chronique',

    fatigue_atl:
      'Fatigue récente',

    training_balance:
      'Équilibre de charge',
  }

  return (
    labels[metric]
    ?? metric.replaceAll(
      '_',
      ' ',
    )
  )
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
