import {
  Activity,
  Check,
  Clock3,
  Gauge,
  MapPin,
  Mountain,
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
    <div className="space-y-5">
      <SessionHeader
        session={session}
      />

      <SessionSummary
        session={session}
      />

      <div
        className="
          border-t
          border-base-300
          pt-5
        "
      >
        {loadingGuidance && (
          <div
            className="
              flex min-h-32
              items-center
              justify-center
            "
          >
            <span
              className="
                loading
                loading-spinner
                loading-sm
                text-primary
              "
            />
          </div>
        )}

        {!loadingGuidance
          && guidance && (
            <details
              className="
                group
                rounded-xl
                border
                border-base-300
                bg-base-100
              "
            >
              <summary
                className="
                  cursor-pointer
                  list-none
                  px-4 py-3
                  font-semibold
                  text-base-content
                "
              >
                <div
                  className="
                    flex items-center
                    justify-between
                    gap-3
                  "
                >
                  <div>
                    <p>
                      Déroulé de la séance
                    </p>

                    <p
                      className="
                        mt-0.5
                        text-xs
                        font-normal
                        text-base-content/45
                      "
                    >
                      Échauffement, bloc principal,
                      récupération et conseils.
                    </p>
                  </div>

                  <span
                    className="
                      text-sm
                      text-primary
                    "
                  >
                    Voir
                  </span>
                </div>
              </summary>

              <div
                className="
                  border-t
                  border-base-300
                  p-4
                "
              >
                <SessionGuidancePanel
                  guidance={
                    guidance
                  }
                />
              </div>
            </details>
          )}

        {!loadingGuidance
          && guidanceError && (
            <div
              className="
                alert
                alert-warning
                text-sm
              "
            >
              {guidanceError}
            </div>
          )}
      </div>

      {session.type
        !== 'rest' && (
          <ActivitySection
            session={session}
            activities={
              activities
            }
            loading={
              loadingActivities
            }
            error={
              activityError
            }
            selectedActivityId={
              selectedActivityId
            }
            validating={
              validating
            }
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

      {(loadingDebrief || debrief) && (
        <div
          ref={
            debriefRef
          }
          className="
            scroll-mt-4
          "
        >
          <DebriefSection
            loading={
              loadingDebrief
            }
            debrief={
              debrief
            }
          />
        </div>
      )}

    </div>
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
          <span className="text-sm font-medium text-base-content/55">
            {formatDate(
              session.date,
            )}
          </span>

          {session.type
            === 'supplementary' && (
              <span className="badge badge-outline badge-sm">
                Supplémentaire
              </span>
            )}
        </div>

        <h2
          className="
            mt-1
            text-xl
            font-bold
            text-base-content
          "
        >
          {session.title}
        </h2>

        <p
          className="
            mt-1 text-sm
            text-base-content/50
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
}: {
  session: TrainingSession
}) {
  return (
    <div
      className="
        overflow-hidden
        rounded-xl
        border border-base-300
      "
    >
      <div
        className="
          grid
          divide-y divide-base-300
          sm:grid-cols-2
          sm:divide-x
          sm:divide-y-0
          lg:grid-cols-5
        "
      >
        <SummaryValue
          icon={Clock3}
          label="Durée"
          value={
            session.type
            === 'rest'
              ? 'Repos'
              : (
                `${session.durationMinutes} min`
              )
          }
        />

        <SummaryValue
          icon={MapPin}
          label="Distance"
          value={
            session.distanceKm
            !== undefined
              ? (
                `${formatNumber(
                  session.distanceKm,
                )} km`
              )
              : '—'
          }
        />

        <SummaryValue
          icon={Mountain}
          label="Dénivelé"
          value={
            session.elevationGainM
            !== undefined
              ? (
                `${Math.round(
                  session.elevationGainM,
                )} m`
              )
              : '—'
          }
        />

        <SummaryValue
          icon={Gauge}
          label="Intensité"
          value={
            formatTrainingIntensity(
              session.intensity,
            )
            || '—'
          }
        />

        <SummaryValue
          icon={Activity}
          label="Zone"
          value={
            session.heartRateZone
            ?? '—'
          }
        />
      </div>
    </div>
  )
}


interface SummaryValueProps {
  icon:
    typeof Clock3
  label: string
  value: string
}


function SummaryValue({
  icon: Icon,
  label,
  value,
}: SummaryValueProps) {
  return (
    <div
      className="
        flex items-center
        gap-3 px-3 py-3
      "
    >
      <Icon
        size={16}
        className="
          shrink-0
          text-base-content/40
        "
      />

      <div className="min-w-0">
        <p
          className="
            text-[11px]
            uppercase
            tracking-wide
            text-base-content/40
          "
        >
          {label}
        </p>

        <p
          className="
            truncate
            text-sm
            font-semibold
            text-base-content
          "
        >
          {value}
        </p>
      </div>
    </div>
  )
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

  return (
    <section
      className="
        border-t
        border-base-300
        pt-5
      "
    >
      <div>
        <h3
          className="
            font-semibold
            text-base-content
          "
        >
          Activité réalisée
        </h3>

        <p
          className="
            mt-1 text-sm
            text-base-content/50
          "
        >
          Choisissez l&apos;activité
          Intervals.icu correspondant
          à cette séance.
        </p>
      </div>

      {loading && (
        <div
          className="
            mt-4
            flex items-center
            gap-2
            rounded-xl
            bg-base-200/60
            px-4 py-3
          "
        >
          <span
            className="
              loading
              loading-spinner
              loading-sm
            "
          />

          <span
            className="
              text-sm
              text-base-content/55
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
              mt-4
              rounded-xl
              border
              border-error/30
              bg-error/5
              px-4 py-3
              text-sm
              text-error
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
              mt-4
              rounded-xl
              bg-base-200/60
              px-4 py-3
            "
          >
            <p
              className="
                text-sm
                font-medium
                text-base-content/70
              "
            >
              Aucune activité détectée
            </p>

            <p
              className="
                mt-1 text-xs
                text-base-content/45
              "
            >
              La prochaine synchronisation
              Intervals.icu pourra faire
              apparaître votre activité.
            </p>
          </div>
        )}

      {!loading
        && !error
        && activities.length > 0 && (
          <div className="mt-4 space-y-2">
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
            mt-4
            rounded-xl
            border
            border-error/30
            bg-error/5
            px-4 py-3
            text-sm
            text-error
          "
        >
          {validationError}
        </div>
      )}

      {!completed
        && activities.length > 0 && (
          <div
            className="
              mt-5 flex
              justify-end
            "
          >
            <button
              type="button"
              className="
                btn
                btn-primary
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
                    loading
                    loading-spinner
                    loading-sm
                  "
                />
              )}

              Valider la séance
            </button>
          </div>
        )}

      {completed && (
        <div
          className="
            mt-4
            flex items-center
            gap-2
            rounded-xl
            border
            border-success/30
            bg-success/5
            px-4 py-3
            text-sm
            text-success
          "
        >
          <Check
            size={16}
          />

          Séance analysée
        </div>
      )}
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
          'w-full rounded-xl '
          + 'border px-4 py-3 '
          + 'text-left transition'
        ),
        selected
          ? (
            'border-primary '
            + 'bg-primary/5 '
            + 'ring-1 '
            + 'ring-primary/15'
          )
          : (
            'border-base-300 '
            + 'hover:bg-base-200/50'
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
                text-base-content
              "
            >
              {activity.name}
            </p>

            {activity.bestMatch && (
              <span
                className="
                  badge
                  badge-success
                  badge-sm
                "
              >
                Meilleur choix
              </span>
            )}
          </div>

          <p
            className="
              mt-1 text-xs
              text-base-content/50
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
            text-base-content/60
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
              'badge badge-sm',
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
            border-primary/15
            pt-3
          "
        >
          <p
            className="
              text-xs
              text-base-content/50
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
                text-base-content/45
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
          border-base-300
          pt-5
        "
      >
        <div
          className="
            flex items-center
            gap-2
            text-sm
            text-base-content/55
          "
        >
          <span
            className="
              loading
              loading-spinner
              loading-sm
            "
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
        border-base-300
        pt-5
      "
    >
      <div
        className="
          rounded-xl
          border
          border-base-300
          bg-base-100
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
                text-base-content/40
              "
            >
              Débriefing coach
            </p>

            <h3
              className="
                mt-1
                font-semibold
                text-base-content
              "
            >
              {debrief.objective}
            </h3>
          </div>

          <span
            className={[
              'badge',
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
            text-base-content/75
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
                text-success
              "
            >
              Points forts
            </p>

            <ul
              className="
                mt-2
                space-y-2
                text-sm
                text-base-content/70
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
                        text-success
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
                text-warning
              "
            >
              Points d&apos;attention
            </p>

            <ul
              className="
                mt-2
                space-y-2
                text-sm
                text-base-content/70
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
                        bg-warning
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
      return 'badge-success'

    case 'partial':
      return 'badge-warning'

    case 'non_compliant':
      return 'badge-error'

    default:
      return 'badge-ghost'
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
          badge
          badge-success
          badge-sm
          gap-1
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
          badge
          badge-error
          badge-sm
          gap-1
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
        badge
        badge-warning
        badge-sm
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
                  + 'text-warning'
                )
                : (
                  'text-base-content/20'
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
    return 'badge-success'
  }

  if (score >= 65) {
    return 'badge-warning'
  }

  return 'badge-error'
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
