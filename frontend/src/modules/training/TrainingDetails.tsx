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
  type ReactNode,
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
  SessionGuidancePanel,
} from './SessionGuidancePanel'
import {
  formatTrainingIntensity,
} from './intensity'

interface TrainingDetailsProps {
  session: TrainingSession

  onValidateSession: (
    activityId: string,
  ) => Promise<SessionExecutionDebrief>
}


export function TrainingDetails({
  session,
  onValidateSession,
}: TrainingDetailsProps) {
  const {
    toast,
  } = useToast()

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
    <div className="training-details-v3">
      <div className="training-details-v3__hero">
        <SessionHeader
          session={session}
        />

        <SessionSummary
          session={session}
          guidance={guidance}
        />
      </div>


      <CollapseSection
        title="Débriefing"
        subtitle={
          debrief
            ? 'Analyse du coach disponible'
            : 'Séance non réalisée'
        }
        preferredOpen={
          Boolean(debrief)
        }
      >
        <div
          ref={
            debriefRef
          }
          className="
            scroll-mt-4
          "
        >
          {loadingDebrief ? (
            <div
              className="
                flex
                min-h-24
                items-center
                justify-center
              "
            >
              <span
                className="
                  h-5
                  w-5
                  animate-spin
                  rounded-full
                  border-2
                  border-slate-200
                  border-t-emerald-500
                  dark:border-white/[0.08]
                  dark:border-t-emerald-400
                "
              />
            </div>
          ) : debrief ? (
            <DebriefSection
              loading={false}
              debrief={debrief}
            />
          ) : (
            <div
              className="
                rounded-[10px]
                border
                border-black/[0.055]
                bg-slate-50
                px-3
                py-2.5
                dark:border-white/[0.055]
                dark:bg-white/[0.025]
              "
            >
              <p
                className="
                  text-[12px]
                  font-semibold
                  text-slate-700
                  dark:text-slate-300
                "
              >
                Séance non réalisée
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
                Le débriefing du coach sera
                disponible après validation
                de l’activité réalisée.
              </p>
            </div>
          )}
        </div>
      </CollapseSection>


      <CollapseSection
        title="Entraînement"
        subtitle="Échauffement · Cœur · Retour au calme"
        preferredOpen={
          session.status !== 'completed'
        }
      >
        {loadingGuidance && (
          <div
            className="
              flex
              min-h-28
              items-center
              justify-center
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
            />
          </div>
        )}

        {!loadingGuidance
          && guidance && (
            <SessionGuidancePanel
              guidance={guidance}
            />
          )}

        {!loadingGuidance
          && guidanceError && (
            <div
              className="
                rounded-[10px]
                border
                border-amber-500/15
                bg-amber-50
                px-3
                py-2.5
                text-[11px]
                font-medium
                text-amber-700
                dark:bg-amber-500/[0.07]
                dark:text-amber-400
              "
            >
              {guidanceError}
            </div>
          )}
      </CollapseSection>


      {session.type !== 'rest' && (
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
      )}
    </div>
  )
}


function CollapseSection({
  title,
  subtitle,
  preferredOpen,
  children,
}: {
  title: string
  subtitle?: string
  preferredOpen: boolean
  children: ReactNode
}) {
  const [
    open,
    setOpen,
  ] = useState(
    preferredOpen,
  )

  useEffect(() => {
    setOpen(
      preferredOpen,
    )
  }, [
    preferredOpen,
  ])

  return (
    <details
      open={open}
      onToggle={(event) => {
        setOpen(
          event.currentTarget.open,
        )
      }}
      className="
        group
        overflow-hidden
        rounded-[12px]
        border
        border-black/[0.065]
        bg-white
        dark:border-white/[0.07]
        dark:bg-white/[0.018]
      "
    >
      <summary
        className="
          cursor-pointer
          list-none
          px-3.5
          py-3
        "
      >
        <div
          className="
            flex
            items-center
            justify-between
            gap-3
          "
        >
          <span
            className="
              text-[12.5px]
              font-semibold
              text-slate-900
              dark:text-slate-100
            "
          >
            {title}
          </span>

          {subtitle && (
            <span
              className="
                truncate
                text-[10px]
                text-slate-400
                dark:text-slate-500
              "
            >
              {subtitle}
            </span>
          )}
        </div>
      </summary>

      <div
        className="
          border-t
          border-black/[0.06]
          p-3.5
          dark:border-white/[0.065]
        "
      >
        {children}
      </div>
    </details>
  )
}


function SessionHeader({
  session,
}: {
  session: TrainingSession
}) {
  return (
    <div
      className="
        flex flex-col
        gap-3
        sm:flex-row
        sm:items-start
        sm:justify-between
      "
    >
      <div className="min-w-0">
        <div
          className="
            flex flex-wrap
            items-center
            gap-2
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

          {session.type
            === 'supplementary' && (
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

        <h2
          className="
            mt-1
            text-[18px]
            font-bold
            tracking-[-0.025em]
            text-slate-950
            dark:text-white
          "
        >
          {session.title}
        </h2>

        <p
          className="
            mt-1
            text-[10.5px]
            text-slate-400
            dark:text-slate-500
          "
        >
          {formatSportType(
            session.sportType,
          )}
        </p>
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

  return (
    <div
      className="
        flex
        flex-wrap
        gap-2
      "
    >
      <span
        className="
          rounded-[8px]
          border
          border-black/[0.065]
          bg-slate-50
          px-2
          py-1
          text-[10px]
          font-medium
          text-slate-600
          dark:border-white/[0.065]
          dark:bg-white/[0.025]
          dark:text-slate-400
        "
      >
        {session.type === 'rest'
          ? 'Repos'
          : `${session.durationMinutes} min`}
      </span>

      {estimatedDistance && (
        <span
          className="
            inline-flex
            items-center
            rounded-full
            border
            px-2.5
            py-1
            text-[10.5px]
            font-semibold
          "
        >
          ≈ {estimatedDistance}
        </span>
      )}

      {session.distanceKm !== undefined && (
        <span
          className="
            inline-flex
            items-center
            rounded-full
            border
            px-2.5
            py-1
            text-[10.5px]
            font-semibold
          "
        >
          {
            formatNumber(
              session.distanceKm,
            )
          } km
        </span>
      )}

      {session.elevationGainM !== undefined && (
        <span
          className="
            inline-flex
            items-center
            rounded-full
            border
            px-2.5
            py-1
            text-[10.5px]
            font-semibold
          "
        >
          +{
            Math.round(
              session.elevationGainM,
            )
          } m
        </span>
      )}

      <span
        className="
          rounded-[8px]
          border
          border-emerald-500/15
          bg-emerald-50
          px-2
          py-1
          text-[10px]
          font-semibold
          text-emerald-700
          dark:bg-emerald-500/[0.07]
          dark:text-emerald-400
        "
      >
        {
          formatSessionType(
            session.type,
          )
        }
      </span>

      {session.intensity && (
        <span
          className="
            inline-flex
            items-center
            rounded-full
            border
            px-2.5
            py-1
            text-[10.5px]
            font-semibold
          "
        >
          {
            formatTrainingIntensity(
              session.intensity,
            )
          }
        </span>
      )}

      {session.heartRateZone && (
        <span
          className="
            inline-flex
            items-center
            rounded-full
            border
            border-violet-500/20
            bg-violet-500/[0.06]
            px-2.5
            py-1
            text-[10.5px]
            font-semibold
            text-violet-600
            dark:text-violet-400
          "
        >
          {
            formatHeartRateZone(
              session.heartRateZone,
            )
          }
        </span>
      )}
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

  const [
    expanded,
    setExpanded,
  ] = useState(
    !completed,
  )

  useEffect(() => {
    if (completed) {
      setExpanded(false)
    }
  }, [
    completed,
  ])


  const futureSession =
    isFutureTrainingSession(
      session.date,
    )

  if (futureSession) {
    return (
      <section
        className="
          training-details-v3__activity
        "
      >
        <div
          className="
            flex
            items-center
            justify-between
            gap-3
            rounded-xl
            border
            border-black/[0.06] dark:border-white/[0.07]
            bg-white dark:bg-[#141a1e]
            px-4 py-3
          "
        >
          <div>
            <p
              className="
                font-semibold
                text-slate-800 dark:text-slate-100
              "
            >
              Activité réalisée
            </p>

            <p
              className="
                mt-0.5
                text-xs
                text-slate-400 dark:text-slate-500
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
              px-2.5 py-1
              text-[10.5px]
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
      </section>
    )
  }


  const selectedCount =
    selectedActivityId
      ? 1
      : 0

  const selectionLabel =
    completed
      ? (
        selectedCount > 0
          ? '1 activité associée'
          : 'Aucune activité associée'
      )
      : (
        `${selectedCount} activité`
        + (
          selectedCount > 1
            ? 's'
            : ''
        )
        + ' sélectionnée'
        + (
          selectedCount > 1
            ? 's'
            : ''
        )
      )

  return (
    <section
      className="
        border-t
        border-black/[0.06] dark:border-white/[0.07]
        pt-5
      "
    >
      <details
        open={
          expanded
        }
        onToggle={(event) => {
          setExpanded(
            event.currentTarget.open,
          )
        }}
        className="
          workout-activity-panel
          overflow-hidden
          rounded-xl
          border
          border-black/[0.06] dark:border-white/[0.07]
          bg-white dark:bg-[#141a1e]
        "
      >
        <summary
          className="
            cursor-pointer
            list-none
            px-4 py-3
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              gap-3
            "
          >
            <div className="min-w-0">
              <p
                className="
                  font-semibold
                  text-slate-800 dark:text-slate-100
                "
              >
                Activité réalisée
              </p>

              {!completed && (
                <p
                  className="
                    mt-0.5
                    text-xs
                    text-slate-400 dark:text-slate-500
                  "
                >
                  Associer l&apos;activité
                  Intervals.icu correspondante.
                </p>
              )}
            </div>

            <span
              className={[
                (
                  'shrink-0 rounded-full border '
                  + 'px-2.5 py-1 text-[10.5px] '
                  + 'font-semibold'
                ),
                completed
                  ? (
                      'border-emerald-500/20 '
                      + 'bg-emerald-500/[0.06] '
                      + 'text-emerald-600 '
                      + 'dark:text-emerald-400'
                    )
                  : (
                    selectedCount > 0
                      ? (
                          'border-emerald-500/20 '
                          + 'bg-emerald-500/10 '
                          + 'text-emerald-700 '
                          + 'dark:text-emerald-300'
                        )
                      : (
                          'border-slate-200 '
                          + 'bg-slate-50 '
                          + 'text-slate-500 '
                          + 'dark:border-white/[0.08] '
                          + 'dark:bg-white/[0.04] '
                          + 'dark:text-slate-400'
                        )
                  ),
              ].join(' ')}
            >
              {selectionLabel}
            </span>
          </div>
        </summary>

        <div
          className="
            border-t
            border-black/[0.06] dark:border-white/[0.07]
            px-4 py-4
          "
        >
          {loading && (
            <div
              className="
                flex
                items-center
                gap-2
                rounded-xl
                bg-slate-50 dark:bg-white/[0.035]
                px-4 py-3
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
                  text-sm
                  text-slate-500 dark:text-slate-400
                "
              >
                Recherche des activités…
              </span>
            </div>
          )}

          {!loading
            && error && (
              <div
                className="
                  rounded-xl
                  border
                  border-rose-500/20 dark:border-rose-400/20
                  bg-rose-500/[0.05] dark:bg-rose-400/[0.05]
                  px-4 py-3
                  text-sm
                  text-rose-600 dark:text-rose-400
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
                  rounded-xl
                  bg-slate-50 dark:bg-white/[0.035]
                  px-4 py-3
                "
              >
                <p
                  className="
                    text-sm
                    font-medium
                    text-slate-600 dark:text-slate-300
                  "
                >
                  Aucune activité détectée
                </p>

                <p
                  className="
                    mt-1
                    text-xs
                    text-slate-400 dark:text-slate-500
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
                mt-3
                rounded-xl
                border
                border-rose-500/20 dark:border-rose-400/20
                bg-rose-500/[0.05] dark:bg-rose-400/[0.05]
                px-4 py-3
                text-sm
                text-rose-600 dark:text-rose-400
              "
            >
              {validationError}
            </div>
          )}

          {!completed
            && activities.length > 0 && (
              <div
                className="
                  mt-4
                  flex
                  justify-end
                "
              >
                <button
                  type="button"
                  className="
                    workout-activity-validate-button
                    inline-flex
                    min-h-10
                    items-center
                    justify-center
                    gap-2
                    rounded-[10px]
                    bg-emerald-600
                    px-4 py-2
                    text-sm
                    font-semibold
                    text-white
                    shadow-sm
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
                        size-4
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
      </details>
    </section>
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
          + 'w-full rounded-xl '
          + 'border px-4 py-3 '
          + 'text-left transition'
        ),
        selected
          ? (
              'workout-activity-card--selected '
              + 'border-emerald-500/35 dark:border-emerald-400/30 '
            + 'bg-emerald-500/[0.05] dark:bg-emerald-400/[0.055] '
            + 'ring-1 '
            + 'ring-emerald-500/15 dark:ring-emerald-400/15'
          )
          : (
            'border-black/[0.06] dark:border-white/[0.07] '
            + 'hover:bg-slate-50/80 dark:bg-white/[0.025]'
          ),
      ].join(' ')}
    >
      <div
        className="
          flex flex-col
          gap-3
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div className="min-w-0">
          <div
            className="
              flex flex-wrap
              items-center
              gap-2
            "
          >
            <p
              className="
                truncate
                font-semibold
                text-slate-800 dark:text-slate-100
              "
            >
              {activity.name}
            </p>

            {activity.bestMatch && (
              <span
                className="
                  rounded-full
                  border
                  border-emerald-500/20
                  bg-emerald-500/[0.08]
                  px-2 py-0.5
                  text-[10px]
                  font-semibold
                  text-emerald-600
                  dark:text-emerald-400
                "
              >
                Meilleur choix
              </span>
            )}
          </div>

          <p
            className="
              mt-1 text-xs
              text-slate-500 dark:text-slate-400
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


        <div
          className="
            flex flex-wrap
            items-center
            gap-3
            text-sm
            text-slate-500 dark:text-slate-400
          "
        >
          {activity.movingTimeSeconds
            !== undefined && (
              <span>
                {formatDuration(
                  activity
                    .movingTimeSeconds,
                )}
              </span>
            )}

          {activity.distanceM
            !== undefined && (
              <span>
                {formatDistance(
                  activity.distanceM,
                )}
              </span>
            )}

          {activity.elevationGainM
            !== undefined && (
              <span>
                {Math.round(
                  activity
                    .elevationGainM,
                )}{' '}
                m D+
              </span>
            )}

          <span
            className={[
              (
                'rounded-full border '
                + 'px-2 py-0.5 text-[10px] '
                + 'font-semibold'
              ),
              getMatchBadgeClass(
                activity.matchScore,
              ),
            ].join(' ')}
          >
            {Math.round(
              activity.matchScore,
            )}{' '}
            %
          </span>

        </div>
      </div>


      {selected && (
        <div
          className="
            mt-3
            border-t
            border-emerald-500/15 dark:border-emerald-400/15
            pt-3
          "
        >
          <p
            className="
              text-xs
              text-slate-500 dark:text-slate-400
            "
          >
            Cliquez à nouveau pour
            désassocier cette activité.
          </p>
        </div>
      )}


      {activity.feel
        !== undefined && (
          <div
            className="
              mt-2
              flex items-center
              gap-2
            "
          >
            <FeelStars
              feel={
                activity.feel
              }
            />

            <span
              className="
                text-xs
                text-slate-400 dark:text-slate-500
              "
            >
              {formatFeelLabel(
                activity.feel,
              )}
            </span>
          </div>
        )}
    </button>
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
      <section
        className="
          border-t
          border-black/[0.06] dark:border-white/[0.07]
          pt-5
        "
      >
        <div
          className="
            flex items-center
            gap-2
            text-sm
            text-slate-500 dark:text-slate-400
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

          Chargement du débriefing…
        </div>
      </section>
    )
  }

  if (!debrief) {
    return null
  }

  return (
    <section
      className="
        border-t
        border-black/[0.06] dark:border-white/[0.07]
        pt-5
      "
    >
      <div
        className="
          workout-debrief-card
          rounded-xl
          border
          border-black/[0.06] dark:border-white/[0.07]
          bg-white dark:bg-[#141a1e]
          p-4
        "
      >
        <div
          className="
            flex flex-wrap
            items-start
            justify-between
            gap-3
          "
        >
          <div className="min-w-0">
            <p
              className="
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-slate-400 dark:text-slate-500
              "
            >
              Débriefing coach
            </p>

            <h3
              className="
                mt-1
                font-semibold
                text-slate-800 dark:text-slate-100
              "
            >
              {debrief.objective}
            </h3>
          </div>

          <span
            className={[
              (
                'shrink-0 rounded-full border '
                + 'px-2.5 py-1 text-[10.5px] '
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
            mt-4
            text-sm
            leading-6
            text-slate-600 dark:text-slate-300
          "
        >
          {debrief.debriefing}
        </p>

        {debrief.strengths.length > 0 && (
          <div className="mt-5">
            <p
              className="
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-emerald-600 dark:text-emerald-400
              "
            >
              Points forts
            </p>

            <ul
              className="
                mt-2
                space-y-2
                text-sm
                text-slate-600 dark:text-slate-300
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
                      size={15}
                      className="
                        mt-0.5
                        shrink-0
                        text-emerald-600 dark:text-emerald-400
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
          <div className="mt-5">
            <p
              className="
                text-xs
                font-semibold
                uppercase
                tracking-wide
                text-amber-600 dark:text-amber-400
              "
            >
              Points d&apos;attention
            </p>

            <ul
              className="
                mt-2
                space-y-2
                text-sm
                text-slate-600 dark:text-slate-300
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
                        mt-1
                        size-1.5
                        shrink-0
                        rounded-full
                        bg-amber-500 dark:bg-amber-400
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
    </section>
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
