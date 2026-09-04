import './TrainingDetailsV3.css'

import {
  Check,
  Star,
  X,
} from 'lucide-react'

import {
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  fetchTrainingSessionActivityCandidates,
  fetchTrainingSessionDebrief,
  type SessionExecutionDebrief,
  type TrainingActivityCandidate,
} from '../../core/training/api'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import type {
  TrainingSession,
} from './types'

import {
  fetchSessionGuidance,
} from './sessionGuidanceApi'

import type {
  SessionGuidance,
} from './sessionGuidanceApi'

import {
  SidePanelSection,
} from '../../components/ui/SidePanelSection'

import {
  SessionGuidancePanel,
} from './SessionGuidancePanel'
import {
  TrainingSessionActions,
} from './TrainingSessionActions'
import {
  formatTrainingIntensity,
} from './intensity'

interface TrainingDetailsProps {
  session: TrainingSession

  onValidateSession: (
    activityId: string,
  ) => Promise<SessionExecutionDebrief>

  onSkipSession?: () => Promise<void>

  onMoveSession?: (
    targetDate: string,
  ) => Promise<void>
}


export function TrainingDetails({
  session,
  onValidateSession,
  onSkipSession,
  onMoveSession,
}: TrainingDetailsProps) {
  const {
    toast,
  } = useToast()

  const [
    openSection,
    setOpenSection,
  ] = useState<string | null>(
    session.status === 'completed'
      ? 'debrief'
      : 'training',
  )

  const debriefRef =
    useRef<HTMLDivElement | null>(
      null,
    )
  const [
    activities,
    setActivities,
  ] = useState<
    TrainingActivityCandidate[]
  >([])

  const [
    loadingActivities,
    setLoadingActivities,
  ] = useState(true)

  const [
    activityError,
    setActivityError,
  ] = useState<string | null>(
    null,
  )

  const [
    selectedActivityId,
    setSelectedActivityId,
  ] = useState<string | null>(
    session.activityId ?? null,
  )

  const [
    validating,
    setValidating,
  ] = useState(false)

  const [
    validationError,
    setValidationError,
  ] = useState<string | null>(
    null,
  )

  const [
    debrief,
    setDebrief,
  ] = useState<
    SessionExecutionDebrief
    | null
  >(null)

  const [
    loadingDebrief,
    setLoadingDebrief,
  ] = useState(
    session.status === 'completed',
  )


  const [
    guidance,
    setGuidance,
  ] = useState<
    SessionGuidance
    | null
  >(null)

  const [
    loadingGuidance,
    setLoadingGuidance,
  ] = useState(true)

  const [
    guidanceError,
    setGuidanceError,
  ] = useState<string | null>(
    null,
  )

  useEffect(() => {
    setSelectedActivityId(
      session.activityId ?? null,
    )
  }, [
    session.activityId,
  ])


  useEffect(() => {
    setOpenSection(
      session.status === 'completed'
        ? 'debrief'
        : 'training',
    )
  }, [
    session.id,
    session.status,
  ])


  useEffect(() => {
    let mounted = true

    setLoadingGuidance(true)
    setGuidanceError(null)

    fetchSessionGuidance(
      session.id,
    )
      .then((result) => {
        if (!mounted) {
          return
        }

        setGuidance(
          result,
        )
      })
      .catch((reason: unknown) => {
        if (!mounted) {
          return
        }

        setGuidance(
          null,
        )

        setGuidanceError(
          reason instanceof Error
            ? reason.message
            : (
                'Impossible de charger '
                + 'les consignes.'
              ),
        )
      })
      .finally(() => {
        if (mounted) {
          setLoadingGuidance(
            false,
          )
        }
      })

    return () => {
      mounted = false
    }
  }, [
    session.id,
  ])


  useEffect(() => {
    if (
      session.status !== 'completed'
    ) {
      setDebrief(null)
      setLoadingDebrief(false)
      return
    }

    let mounted = true

    setLoadingDebrief(true)

    fetchTrainingSessionDebrief(
      session.id,
    )
      .then((result) => {
        if (!mounted) {
          return
        }

        setDebrief(
          result,
        )
      })
      .catch(() => {
        if (!mounted) {
          return
        }

        setDebrief(null)
      })
      .finally(() => {
        if (mounted) {
          setLoadingDebrief(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [
    session.id,
    session.status,
  ])


  useEffect(() => {
    if (
      session.type === 'rest'
    ) {
      setLoadingActivities(false)
      setActivities([])
      return
    }

    let mounted = true

    setLoadingActivities(true)
    setActivityError(null)

    fetchTrainingSessionActivityCandidates(
      session.id,
    )
      .then((result) => {
        if (!mounted) {
          return
        }

        setActivities(result)
      })
      .catch((reason: unknown) => {
        if (!mounted) {
          return
        }

        setActivityError(
          reason instanceof Error
            ? reason.message
            : 'Impossible de rechercher les activités.',
        )
      })
      .finally(() => {
        if (mounted) {
          setLoadingActivities(
            false,
          )
        }
      })

    return () => {
      mounted = false
    }
  }, [
    session.id,
    session.type,
  ])


  function handleActivitySelect(
    activityId: string,
  ) {
    if (
      session.status === 'completed'
    ) {
      return
    }

    setValidationError(null)

    setSelectedActivityId(
      current =>
        current === activityId
          ? null
          : activityId,
    )
  }


  async function handleValidateSession() {
    if (!selectedActivityId) {
      setValidationError(
        'Sélectionnez une activité réalisée.',
      )
      return
    }

    setValidationError(null)
    setValidating(true)

    try {
      const result =
        await onValidateSession(
          selectedActivityId,
        )

      setDebrief(
        result,
      )

      toast({
        type: 'success',
        title: 'Séance analysée',
        message: (
          'Le débriefing du coach '
          + 'est disponible.'
        ),
        duration: 8000,
        actionLabel:
          'Voir le débriefing',
        onAction: () => {
          window.requestAnimationFrame(
            () => {
              debriefRef.current
                ?.scrollIntoView({
                  behavior: 'smooth',
                  block: 'start',
                })
            },
          )
        },
      })
    } catch (reason) {
      setValidationError(
        reason instanceof Error
          ? reason.message
          : (
              'Impossible de valider '
              + 'la séance.'
            ),
      )
    } finally {
      setValidating(false)
    }
  }




  return (
    <div
      className="
        training-details-v3
        space-y-3
      "
    >
      <section
        className="
          border-b
          border-black/[0.06]
          pb-3
          dark:border-white/[0.07]
        "
      >
        <SessionHeader
          session={session}
        />

        <SessionSummary
          session={session}
          guidance={guidance}
        />
      </section>


      {(
        onSkipSession
        && onMoveSession
      ) && (
        <TrainingSessionActions
          session={session}
          onRealized={() => {
            setOpenSection(
              'activity',
            )
          }}
          onSkipped={
            onSkipSession
          }
          onMoved={
            onMoveSession
          }
        />
      )}


      {session.status === 'completed' && (
        <SidePanelSection
          sectionId="debrief"
          eyebrow="Analyse"
          title="Débriefing OpenCoach"
          open={
            openSection === 'debrief'
          }
          onOpenChange={
            setOpenSection
          }
        >
          <div
            ref={debriefRef}
            className="
              scroll-mt-4
            "
          >
            {loadingDebrief ? (
              <SectionLoader />
            ) : debrief ? (
              <DebriefSection
                loading={false}
                debrief={debrief}
              />
            ) : (
              <p
                className="
                  text-[11.5px]
                  leading-5
                  text-slate-400
                  dark:text-slate-500
                "
              >
                Le débriefing est en cours
                de préparation.
              </p>
            )}
          </div>
        </SidePanelSection>
      )}


      {session.status !== 'completed' && (
        <SidePanelSection
          sectionId="training"
          eyebrow="Plan"
          title="Entraînement prévu"
          badge={
            session.type === 'rest'
              ? null
              : `${session.durationMinutes} min`
          }
          open={
            openSection === 'training'
          }
          onOpenChange={
            setOpenSection
          }
        >
          <TrainingGuidanceContent
            loading={loadingGuidance}
            guidance={guidance}
            error={guidanceError}
          />
        </SidePanelSection>
      )}


      {session.type !== 'rest' && (
        <SidePanelSection
          sectionId="activity"
          eyebrow="Réalisation"
          title={
            session.status === 'completed'
              ? 'Activité associée'
              : 'Activité réalisée'
          }
          badge={
            session.status === 'completed'
              ? (
                  selectedActivityId
                    ? '1 activité associée'
                    : 'Aucune activité associée'
                )
              : (
                  selectedActivityId
                    ? '1 activité sélectionnée'
                    : null
                )
          }
          open={
            openSection === 'activity'
          }
          onOpenChange={
            setOpenSection
          }
        >
          <ActivitySection
            session={session}
            activities={activities}
            loading={loadingActivities}
            error={activityError}
            selectedActivityId={
              selectedActivityId
            }
            validating={validating}
            validationError={
              validationError
            }
            onActivitySelect={
              handleActivitySelect
            }
            onValidate={() =>
              void handleValidateSession()
            }
          />
        </SidePanelSection>
      )}


      {session.status === 'completed' && (
        <SidePanelSection
          sectionId="training"
          eyebrow="Plan"
          title="Entraînement prévu"
          badge={
            session.type === 'rest'
              ? null
              : `${session.durationMinutes} min`
          }
          open={
            openSection === 'training'
          }
          onOpenChange={
            setOpenSection
          }
        >
          <TrainingGuidanceContent
            loading={loadingGuidance}
            guidance={guidance}
            error={guidanceError}
          />
        </SidePanelSection>
      )}
    </div>
  )
}


function SectionLoader() {
  return (
    <div
      className="
        flex
        min-h-20
        items-center
        justify-center
      "
    >
      <span
        className="
          size-4
          animate-spin
          rounded-full
          border-2
          border-slate-200
          border-t-emerald-500
          dark:border-white/15
          dark:border-t-emerald-400
        "
      />
    </div>
  )
}


function TrainingGuidanceContent({
  loading,
  guidance,
  error,
}: {
  loading: boolean
  guidance: SessionGuidance | null
  error: string | null
}) {
  if (loading) {
    return (
      <SectionLoader />
    )
  }

  if (guidance) {
    return (
      <SessionGuidancePanel
        guidance={guidance}
      />
    )
  }

  if (error) {
    return (
      <div
        className="
          rounded-[10px]
          border
          border-amber-500/20
          bg-amber-500/[0.05]
          px-3
          py-2.5
          text-[11px]
          leading-5
          text-amber-700
          dark:border-amber-400/20
          dark:bg-amber-400/[0.055]
          dark:text-amber-300
        "
      >
        {error}
      </div>
    )
  }

  return null
}


function SessionHeader({
  session,
}: {
  session: TrainingSession
}) {
  return (
    <div
      className="
        flex
        items-start
        justify-between
        gap-3
      "
    >
      <div
        className="
          flex
          flex-wrap
          items-center
          gap-1.5
        "
      >
        <span
          className="
            text-[10.5px]
            font-medium
            text-slate-400
            dark:text-slate-500
          "
        >
          {formatDate(
            session.date,
          )}
        </span>

        <span
          className="
            text-slate-300
            dark:text-slate-600
          "
        >
          ·
        </span>

        <span
          className="
            text-[10.5px]
            text-slate-500
            dark:text-slate-400
          "
        >
          {formatSportType(
            session.sportType,
          )}
        </span>

        {session.type === 'supplementary' && (
          <span
            className="
              rounded-full
              border
              border-black/[0.07]
              px-1.5
              py-0.5
              text-[9px]
              font-semibold
              text-slate-500
              dark:border-white/[0.07]
              dark:text-slate-400
            "
          >
            Supplémentaire
          </span>
        )}
      </div>

      <StatusBadge
        status={
          session.status
        }
      />
    </div>
  )
}

function SessionSummary({
  session,
  guidance,
}: {
  session: TrainingSession
  guidance: SessionGuidance | null
}) {
  const estimatedDistance =
    estimateSessionDistance(
      session.durationMinutes,
      guidance,
    )

  const distanceLabel =
    session.distanceKm !== undefined
      ? `${
          formatNumber(
            session.distanceKm,
          )
        } km`
      : (
          estimatedDistance
            ? `≈ ${estimatedDistance}`
            : '—'
        )

  return (
    <div
      className="
        mt-3
        grid
        grid-cols-2
        overflow-hidden
        rounded-[12px]
        border
        border-black/[0.065]
        bg-white
        dark:border-white/[0.065]
        dark:bg-white/[0.02]
      "
    >
      <SessionMetric
        value={
          session.type === 'rest'
            ? 'Repos'
            : `${session.durationMinutes} min`
        }
        label="Durée"
      />

      <SessionMetric
        value={
          distanceLabel
        }
        label="Distance"
        left
      />

      <SessionMetric
        value={
          session.intensity
            ? formatTrainingIntensity(
                session.intensity,
              )
            : formatSessionType(
                session.type,
              )
        }
        label="Intensité"
        top
      />

      <SessionMetric
        value={
          session.heartRateZone
            ? formatHeartRateZone(
                session.heartRateZone,
              )
            : '—'
        }
        label="Zone FC"
        left
        top
      />

      {session.elevationGainM !== undefined && (
        <div
          className="
            col-span-2
            border-t
            border-black/[0.06]
            dark:border-white/[0.06]
          "
        >
          <SessionMetric
            value={
              `+${
                Math.round(
                  session.elevationGainM,
                )
              } m`
            }
            label="Dénivelé positif"
          />
        </div>
      )}
    </div>
  )
}


function SessionMetric({
  value,
  label,
  left = false,
  top = false,
}: {
  value: string
  label: string
  left?: boolean
  top?: boolean
}) {
  return (
    <div
      className={[
        (
          'flex min-h-[58px] flex-col '
          + 'items-center justify-center '
          + 'px-2.5 py-2 text-center'
        ),
        left
          ? (
              'border-l border-black/[0.06] '
              + 'dark:border-white/[0.06]'
            )
          : '',
        top
          ? (
              'border-t border-black/[0.06] '
              + 'dark:border-white/[0.06]'
            )
          : '',
      ].join(' ')}
    >
      <p
        className="
          text-[14px]
          font-semibold
          leading-tight
          text-slate-900
          dark:text-slate-100
        "
      >
        {value}
      </p>

      <p
        className="
          mt-0.5
          text-[9px]
          font-semibold
          uppercase
          tracking-[0.08em]
          text-slate-400
          dark:text-slate-500
        "
      >
        {label}
      </p>
    </div>
  )
}


function estimateSessionDistance(
  durationMinutes: number,
  guidance: SessionGuidance | null,
): string | null {
  if (
    !guidance
    || durationMinutes <= 0
  ) {
    return null
  }

  const allSteps = [
    ...guidance.warmup,
    ...guidance.main_set,
    ...guidance.cooldown,
  ]

  const target = allSteps
    .flatMap(
      step =>
        step.intensity_targets,
    )
    .find(
      intensity =>
        intensity.speed_min_kmh != null
        && intensity.speed_max_kmh != null,
    )

  if (
    !target
    || target.speed_min_kmh == null
    || target.speed_max_kmh == null
  ) {
    return null
  }

  const averageSpeed = (
    target.speed_min_kmh
    + target.speed_max_kmh
  ) / 2

  const distanceKm = (
    averageSpeed
    * durationMinutes
    / 60
  )

  const roundedKm =
    Math.round(
      distanceKm * 2,
    ) / 2

  return `${formatNumber(
    roundedKm,
  )} km`
}


function isFutureTrainingSession(
  sessionDate: string,
): boolean {
  const today = new Date()

  const year =
    today.getFullYear()

  const month =
    String(
      today.getMonth() + 1,
    ).padStart(
      2,
      '0',
    )

  const day =
    String(
      today.getDate(),
    ).padStart(
      2,
      '0',
    )

  const todayIso =
    `${year}-${month}-${day}`

  return sessionDate > todayIso
}


function formatHeartRateZone(
  value: string,
): string {
  const compact = value
    .replace(
      /^Fréquence cardiaque individualisée\s*:\s*/i,
      '',
    )
    .replace(
      /^Fréquence cardiaque\s*:\s*/i,
      '',
    )
    .trim()

  return `FC ${compact}`
}


function formatSessionType(
  type: string,
): string {
  switch (type) {
    case 'aerobic_easy':
      return 'Endurance facile'

    case 'threshold':
      return 'Seuil'

    case 'long_run':
      return 'Sortie longue'

    case 'intervals':
      return 'Intervalles'

    case 'recovery':
      return 'Récupération'

    case 'rest':
      return 'Repos'

    case 'supplementary':
      return 'Supplémentaire'

    default:
      return type
        .replaceAll('_', ' ')
  }
}


interface ActivitySectionProps {
  session:
    TrainingSession

  activities:
    TrainingActivityCandidate[]

  loading: boolean

  error:
    string | null

  selectedActivityId:
    string | null

  validating: boolean

  validationError:
    string | null

  onActivitySelect: (
    activityId: string,
  ) => void

  onValidate: () => void
}


function ActivitySection({
  session,
  activities,
  loading,
  error,
  selectedActivityId,
  validating,
  validationError,
  onActivitySelect,
  onValidate,
}: ActivitySectionProps) {
  const completed =
    session.status === 'completed'

  const futureSession =
    isFutureTrainingSession(
      session.date,
    )


  if (futureSession) {
    return (
      <div
        className="
          flex
          items-center
          justify-between
          gap-3
          py-1
        "
      >
        <div>
          <p
            className="
              text-[11.5px]
              font-medium
              text-slate-600
              dark:text-slate-300
            "
          >
            Association disponible
            le jour de la séance.
          </p>
        </div>

        <span
          className="
            shrink-0
            rounded-full
            border
            border-slate-200
            bg-slate-50
            px-2
            py-0.5
            text-[9px]
            font-semibold
            text-slate-500
            dark:border-white/[0.08]
            dark:bg-white/[0.04]
            dark:text-slate-400
          "
        >
          À venir
        </span>
      </div>
    )
  }


  return (
    <div
      className="
        space-y-2.5
      "
    >
      {loading && (
        <div
          className="
            flex
            items-center
            gap-2
            py-2
          "
        >
          <span
            className="
              size-4
              shrink-0
              animate-spin
              rounded-full
              border-2
              border-slate-200
              border-t-emerald-500
              dark:border-white/15
              dark:border-t-emerald-400
            "
            aria-hidden="true"
          />

          <span
            className="
              text-[11px]
              text-slate-500
              dark:text-slate-400
            "
          >
            Recherche des activités…
          </span>
        </div>
      )}


      {!loading && error && (
        <div
          className="
            rounded-[10px]
            border
            border-rose-500/20
            bg-rose-500/[0.05]
            px-3
            py-2.5
            text-[11px]
            text-rose-600
            dark:border-rose-400/20
            dark:bg-rose-400/[0.05]
            dark:text-rose-400
          "
        >
          {error}
        </div>
      )}


      {!loading
        && !error
        && activities.length === 0 && (
          <div
            className="
              py-1
            "
          >
            <p
              className="
                text-[11.5px]
                font-medium
                text-slate-600
                dark:text-slate-300
              "
            >
              Aucune activité détectée
            </p>

            <p
              className="
                mt-1
                text-[10.5px]
                leading-4
                text-slate-400
                dark:text-slate-500
              "
            >
              Une prochaine synchronisation
              Intervals.icu peut faire
              apparaître l&apos;activité.
            </p>
          </div>
        )}


      {!loading
        && !error
        && activities.length > 0 && (
          <div className="space-y-2">
            {activities.map(
              (activity) => (
                <ActivityRow
                  key={
                    activity.id
                  }
                  activity={
                    activity
                  }
                  selected={
                    selectedActivityId
                    === activity.id
                  }
                  disabled={
                    completed
                    || validating
                  }
                  onClick={() =>
                    onActivitySelect(
                      activity.id,
                    )
                  }
                />
              ),
            )}
          </div>
        )}


      {validationError && (
        <div
          className="
            rounded-[10px]
            border
            border-rose-500/20
            bg-rose-500/[0.05]
            px-3
            py-2.5
            text-[11px]
            text-rose-600
            dark:border-rose-400/20
            dark:bg-rose-400/[0.05]
            dark:text-rose-400
          "
        >
          {validationError}
        </div>
      )}


      {!completed
        && activities.length > 0 && (
          <div
            className="
              flex
              justify-end
              pt-1
            "
          >
            <button
              type="button"
              className="
                workout-activity-validate-button
                inline-flex
                min-h-9
                items-center
                justify-center
                gap-2
                rounded-[9px]
                bg-emerald-600
                px-3
                py-1.5
                text-[11px]
                font-semibold
                text-white
                transition
                hover:bg-emerald-700
                disabled:pointer-events-none
                disabled:opacity-45
                dark:bg-emerald-500
                dark:hover:bg-emerald-400
              "
              disabled={
                !selectedActivityId
                || validating
              }
              onClick={
                onValidate
              }
            >
              {validating && (
                <span
                  className="
                    size-3.5
                    shrink-0
                    animate-spin
                    rounded-full
                    border-2
                    border-white/35
                    border-t-white
                  "
                  aria-hidden="true"
                />
              )}

              Valider la séance
            </button>
          </div>
        )}
    </div>
  )
}



interface ActivityRowProps {
  activity:
    TrainingActivityCandidate

  selected: boolean

  disabled: boolean

  onClick: () => void
}


function ActivityRow({
  activity,
  selected,
  disabled,
  onClick,
}: ActivityRowProps) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={[
        (
          'workout-activity-card '
          + 'w-full rounded-[10px] '
          + 'border px-3 py-2.5 '
          + 'text-left transition'
        ),
        selected
          ? (
              'workout-activity-card--selected '
              + 'border-emerald-500/30 '
              + 'bg-emerald-500/[0.035] '
              + 'ring-1 ring-emerald-500/10 '
              + 'dark:border-emerald-400/25 '
              + 'dark:bg-emerald-400/[0.04] '
              + 'dark:ring-emerald-400/10'
            )
          : (
              'border-black/[0.06] '
              + 'hover:border-black/[0.09] '
              + 'hover:bg-slate-50/70 '
              + 'dark:border-white/[0.07] '
              + 'dark:bg-white/[0.02] '
              + 'dark:hover:border-white/[0.10] '
              + 'dark:hover:bg-white/[0.035]'
            ),
      ].join(' ')}
    >
      <div
        className="
          flex
          items-start
          justify-between
          gap-3
        "
      >
        <div className="min-w-0">
          <div
            className="
              flex
              flex-wrap
              items-center
              gap-1.5
            "
          >
            <p
              className="
                truncate
                text-[12.5px]
                font-semibold
                text-slate-800
                dark:text-slate-100
              "
            >
              {activity.name}
            </p>

            {activity.bestMatch && (
              <span
                className="
                  rounded-[5px]
                  bg-emerald-500/[0.08]
                  px-1.5
                  py-0.5
                  text-[8.5px]
                  font-bold
                  uppercase
                  tracking-[0.03em]
                  text-emerald-700
                  dark:bg-emerald-400/[0.08]
                  dark:text-emerald-400
                "
              >
                Meilleur choix
              </span>
            )}
          </div>

          <p
            className="
              mt-0.5
              text-[10.5px]
              text-slate-400
              dark:text-slate-500
            "
          >
            {formatSportType(
              activity.sportType,
            )}

            {activity.startAtLocal
              ? (
                  ` · ${formatActivityTime(
                    activity.startAtLocal,
                  )}`
                )
              : ''}
          </p>
        </div>


        <span
          className={[
            (
              'shrink-0 rounded-[6px] '
              + 'border px-1.5 py-0.5 '
              + 'text-[9px] font-bold'
            ),
            getMatchBadgeClass(
              activity.matchScore,
            ),
          ].join(' ')}
        >
          {Math.round(
            activity.matchScore,
          )} %
        </span>
      </div>


      <div
        className="
          mt-2
          flex
          flex-wrap
          items-center
          gap-x-2
          gap-y-1.5
        "
      >
        {activity.movingTimeSeconds
          !== undefined && (
            <ActivityMetric
              label="Durée"
              value={
                formatDuration(
                  activity
                    .movingTimeSeconds,
                )
              }
            />
          )}

        {activity.distanceM
          !== undefined && (
            <ActivityMetric
              label="Distance"
              value={
                formatDistance(
                  activity.distanceM,
                )
              }
            />
          )}

        {activity.elevationGainM
          !== undefined && (
            <ActivityMetric
              label="D+"
              value={
                `${
                  Math.round(
                    activity
                      .elevationGainM,
                  )
                } m`
              }
            />
          )}

        {activity.feel
          !== undefined && (
            <div
              className="
                inline-flex
                items-center
                gap-1.5
                whitespace-nowrap
              "
            >
              <span
                className="
                  rounded-[5px]
                  bg-slate-100
                  px-1.5
                  py-0.5
                  text-[8.5px]
                  font-bold
                  uppercase
                  tracking-[0.03em]
                  text-slate-500
                  dark:bg-white/[0.055]
                  dark:text-slate-400
                "
              >
                Ressenti
              </span>

              <FeelStars
                feel={
                  activity.feel
                }
              />

              <span
                className="
                  text-[9.5px]
                  text-slate-400
                  dark:text-slate-500
                "
              >
                {formatFeelLabel(
                  activity.feel,
                )}
              </span>
            </div>
          )}
      </div>


      {selected && !disabled && (
        <p
          className="
            mt-2
            text-[9.5px]
            text-emerald-600
            dark:text-emerald-400
          "
        >
          Sélectionnée · cliquer pour désélectionner
        </p>
      )}
    </button>
  )
}


function ActivityMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        inline-flex
        items-center
        gap-1.5
        whitespace-nowrap
      "
    >
      <span
        className="
          rounded-[5px]
          bg-slate-100
          px-1.5
          py-0.5
          text-[8.5px]
          font-bold
          uppercase
          tracking-[0.03em]
          text-slate-500
          dark:bg-white/[0.055]
          dark:text-slate-400
        "
      >
        {label}
      </span>

      <span
        className="
          text-[10.5px]
          font-semibold
          text-slate-700
          dark:text-slate-200
        "
      >
        {value}
      </span>
    </div>
  )
}

interface DebriefSectionProps {
  loading: boolean

  debrief:
    SessionExecutionDebrief
    | null
}


function DebriefSection({
  loading,
  debrief,
}: DebriefSectionProps) {
  if (loading) {
    return (
      <div
        className="
          flex
          items-center
          gap-2
          py-2
          text-[11px]
          text-slate-500
          dark:text-slate-400
        "
      >
        <span
          className="
            size-3.5
            shrink-0
            animate-spin
            rounded-full
            border-2
            border-slate-200
            border-t-emerald-500
            dark:border-white/15
            dark:border-t-emerald-400
          "
          aria-hidden="true"
        />

        Chargement du débriefing…
      </div>
    )
  }


  if (!debrief) {
    return null
  }


  return (
    <div
      className="
        space-y-3
      "
    >
      <div
        className="
          flex
          items-start
          justify-between
          gap-3
        "
      >
        <div className="min-w-0">
          <p
            className="
              text-[12.5px]
              font-semibold
              leading-5
              text-slate-800
              dark:text-slate-100
            "
          >
            {debrief.objective}
          </p>
        </div>

        <span
          className={[
            (
              'shrink-0 rounded-full border '
              + 'px-2 py-0.5 '
              + 'text-[9px] '
              + 'font-semibold'
            ),
            getDebriefBadgeClass(
              debrief.overallStatus,
            ),
          ].join(' ')}
        >
          {formatDebriefStatus(
            debrief.overallStatus,
          )}
        </span>
      </div>


      <p
        className="
          text-[11.5px]
          leading-5
          text-slate-600
          dark:text-slate-300
        "
      >
        {debrief.debriefing}
      </p>


      {debrief.strengths.length > 0 && (
        <div
          className="
            border-t
            border-black/[0.055]
            pt-2.5
            dark:border-white/[0.06]
          "
        >
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Points forts
          </p>

          <ul
            className="
              mt-1.5
              space-y-1.5
              text-[11px]
              leading-5
              text-slate-600
              dark:text-slate-300
            "
          >
            {debrief.strengths.map(
              (strength) => (
                <li
                  key={strength}
                  className="
                    flex
                    items-start
                    gap-2
                  "
                >
                  <Check
                    size={13}
                    className="
                      mt-1
                      shrink-0
                      text-emerald-600
                      dark:text-emerald-400
                    "
                  />

                  <span>
                    {strength}
                  </span>
                </li>
              ),
            )}
          </ul>
        </div>
      )}


      {debrief.attentionPoints.length > 0 && (
        <div
          className="
            border-t
            border-black/[0.055]
            pt-2.5
            dark:border-white/[0.06]
          "
        >
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-amber-600
              dark:text-amber-400
            "
          >
            Points d&apos;attention
          </p>

          <ul
            className="
              mt-1.5
              space-y-1.5
              text-[11px]
              leading-5
              text-slate-600
              dark:text-slate-300
            "
          >
            {debrief.attentionPoints.map(
              (point) => (
                <li
                  key={point}
                  className="
                    flex
                    items-start
                    gap-2
                  "
                >
                  <span
                    className="
                      mt-[7px]
                      size-1.5
                      shrink-0
                      rounded-full
                      bg-amber-500
                      dark:bg-amber-400
                    "
                  />

                  <span>
                    {point}
                  </span>
                </li>
              ),
            )}
          </ul>
        </div>
      )}
    </div>
  )
}



function getDebriefBadgeClass(
  status: string,
): string {
  switch (status) {
    case 'compliant':
      return 'border-emerald-500/20 bg-emerald-500/[0.08] text-emerald-600 dark:text-emerald-400'

    case 'partial':
      return 'border-amber-500/20 bg-amber-500/[0.08] text-amber-600 dark:text-amber-400'

    case 'non_compliant':
      return 'border-rose-500/20 bg-rose-500/[0.08] text-rose-600 dark:text-rose-400'

    default:
      return 'border-slate-200 bg-slate-50 text-slate-500 dark:border-white/[0.08] dark:bg-white/[0.04] dark:text-slate-400'
  }
}


function formatDebriefStatus(
  status: string,
): string {
  switch (status) {
    case 'compliant':
      return 'Objectif respecté'

    case 'partial':
      return 'Partiellement respecté'

    case 'non_compliant':
      return 'Objectif non respecté'

    default:
      return status
  }
}


function StatusBadge({
  status,
}: {
  status:
    TrainingSession['status']
}) {
  if (
    status === 'completed'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          border
          border-emerald-500/20
          bg-emerald-500/[0.08]
          px-2
          py-0.5
          text-[10.5px]
          font-semibold
          text-emerald-600
          dark:text-emerald-400
        "
      >
        <Check
          size={12}
        />

        Réalisée
      </span>
    )
  }

  if (
    status === 'skipped'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          border
          border-rose-500/20
          bg-rose-500/[0.08]
          px-2
          py-0.5
          text-[10.5px]
          font-semibold
          text-rose-600
          dark:text-rose-400
        "
      >
        <X
          size={12}
        />

        Non réalisée
      </span>
    )
  }

  return (
    <span
      className="
        inline-flex
        items-center
        rounded-full
        border
        border-amber-500/20
        bg-amber-500/[0.08]
        px-2
        py-0.5
        text-[10.5px]
        font-semibold
        text-amber-600
        dark:text-amber-400
      "
    >
      À faire
    </span>
  )
}


function FeelStars({
  feel,
}: {
  feel: number
}) {
  const normalizedFeel =
    Math.min(
      5,
      Math.max(
        1,
        Math.round(
          feel,
        ),
      ),
    )

  const stars =
    6 - normalizedFeel

  return (
    <div
      className="
        flex items-center
        gap-0.5
      "
      aria-label={
        `${stars} étoiles sur 5`
      }
    >
      {Array.from(
        {
          length: 5,
        },
        (
          _,
          index,
        ) => (
          <Star
            key={index}
            className={[
              'h-3.5 w-3.5',
              index < stars
                ? (
                  'fill-current '
                  + 'text-amber-600 dark:text-amber-400'
                )
                : (
                  'text-slate-300 dark:text-slate-700'
                ),
            ].join(' ')}
          />
        ),
      )}
    </div>
  )
}


function getMatchBadgeClass(
  score: number,
): string {
  if (score >= 85) {
    return 'border-emerald-500/20 bg-emerald-500/[0.08] text-emerald-600 dark:text-emerald-400'
  }

  if (score >= 65) {
    return 'border-amber-500/20 bg-amber-500/[0.08] text-amber-600 dark:text-amber-400'
  }

  return 'border-rose-500/20 bg-rose-500/[0.08] text-rose-600 dark:text-rose-400'
}


function formatFeelLabel(
  feel: number,
): string {
  switch (
    Math.round(
      feel,
    )
  ) {
    case 1:
      return 'Excellent'

    case 2:
      return 'Bon'

    case 3:
      return 'Moyen'

    case 4:
      return 'Difficile'

    case 5:
      return 'Très difficile'

    default:
      return 'Non défini'
  }
}


function formatDistance(
  distanceM: number,
): string {
  return (
    `${
      (
        distanceM / 1000
      ).toFixed(2)
    } km`
  )
}


function formatDuration(
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

  if (hours === 0) {
    return `${minutes} min`
  }

  if (minutes === 0) {
    return `${hours} h`
  }

  return (
    `${hours} h ${minutes} min`
  )
}


function formatActivityTime(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(
    new Date(
      dateString,
    ),
  )
}


function formatSportType(
  sportType: string,
): string {
  const labels:
    Record<string, string> = {
      Run:
        'Course à pied',
      TrailRun:
        'Trail',
      Ride:
        'Cyclisme',
      VirtualRide:
        'Cyclisme virtuel',
      Walk:
        'Marche',
      Hike:
        'Randonnée',
      Swim:
        'Natation',
      StrengthTraining:
        'Renforcement',
      WeightTraining:
        'Renforcement',
      Other:
        'Autre',
    }

  return (
    labels[sportType]
    ?? sportType
  )
}


function formatDate(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  ).format(
    new Date(
      `${dateString}T12:00:00`,
    ),
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
  ).format(
    value,
  )
}
