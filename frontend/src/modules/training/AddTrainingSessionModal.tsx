import type { ReactNode } from 'react'
import {
  Bike,
  Check,
  ChevronDown,
  Dumbbell,
  Footprints,
  Link2,
  LoaderCircle,
  Mountain,
  Plus,
  RefreshCw,
  Waves,
} from 'lucide-react'

import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  fetchAvailableTrainingActivities,
} from '../../core/training/api'


import {
  SidePanel,
} from '../../components/ui/SidePanel'
import {
  useTrainingSessions,
} from './trainingStore'

import type {
  TrainingAvailableActivity,
  TrainingSessionCreate,
} from './types'

import {
  TRAINING_INTENSITIES,
} from './intensity'


interface AddTrainingSessionModalProps {
  open: boolean
  date: string
  onClose: () => void
}


type CreationMode =
  | 'intervals'
  | 'coros'
  | 'manual'


interface ManualFormState {
  sportType: string
  title: string
  durationMinutes: string
  distanceKm: string
  elevationGainM: string
  intensity: string
  heartRateZone: string
  description: string
}


const EMPTY_MANUAL_FORM: ManualFormState = {
  sportType: 'Run',
  title: '',
  durationMinutes: '',
  distanceKm: '',
  elevationGainM: '',
  intensity: '',
  heartRateZone: '',
  description: '',
}


const SPORT_OPTIONS = [
  {
    value: 'Run',
    label: 'Course',
    icon: Footprints,
  },
  {
    value: 'TrailRun',
    label: 'Trail',
    icon: Mountain,
  },
  {
    value: 'Ride',
    label: 'Vélo',
    icon: Bike,
  },
  {
    value: 'Swim',
    label: 'Natation',
    icon: Waves,
  },
  {
    value: 'StrengthTraining',
    label: 'Renfo',
    icon: Dumbbell,
  },
  {
    value: 'Walk',
    label: 'Marche',
    icon: Footprints,
  },
] as const


export function AddTrainingSessionModal({
  open,
  date,
  onClose,
}: AddTrainingSessionModalProps) {
  const {
    createSession,
  } = useTrainingSessions()

  const [
    mode,
    setMode,
  ] = useState<CreationMode>(
    'intervals',
  )

  const [modeMenuOpen, setModeMenuOpen] = useState(false)

  const [
    activities,
    setActivities,
  ] = useState<
    TrainingAvailableActivity[]
  >([])

  const [
    loadingActivities,
    setLoadingActivities,
  ] = useState(false)

  const [
    submittingActivityId,
    setSubmittingActivityId,
  ] = useState<string | null>(
    null,
  )

  const [
    submittingManual,
    setSubmittingManual,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )

  const [
    form,
    setForm,
  ] = useState<ManualFormState>(
    EMPTY_MANUAL_FORM,
  )


  const loadActivities =
    useCallback(
      async (): Promise<void> => {
        setLoadingActivities(true)
        setError(null)

        try {
          const result =
            await fetchAvailableTrainingActivities(
              date,
            )

          setActivities(result)
        } catch (caughtError) {
          setError(
            caughtError instanceof Error
              ? caughtError.message
              : (
                  'Impossible de charger les '
                  + 'activités disponibles.'
                ),
          )
        } finally {
          setLoadingActivities(false)
        }
      },
      [
        date,
      ],
    )


  useEffect(() => {
    if (!open) {
      return
    }

    setMode('intervals')
    setModeMenuOpen(false)
    setError(null)
    setForm(EMPTY_MANUAL_FORM)

    void loadActivities()
  }, [
    open,
    loadActivities,
  ])


  async function addImportedActivity(
    activity: TrainingAvailableActivity,
  ): Promise<void> {
    setSubmittingActivityId(
      activity.id,
    )

    setError(null)

    try {
      const durationMinutes =
        Math.max(
          1,
          Math.round(
            (
              activity.movingTimeSeconds
              ?? 60
            ) / 60,
          ),
        )

      await createSession({
        date,
        type: 'supplementary',
        sportType:
          activity.sportType,
        title:
          activity.name
          || 'Séance supplémentaire',
        description:
          activity.provider === 'coros'
            ? 'Activité importée depuis COROS.'
            : 'Activité importée depuis Intervals.icu.',
        durationMinutes,
        distanceKm:
          activity.distanceM !== undefined
            ? activity.distanceM / 1000
            : undefined,
        elevationGainM:
          activity.elevationGainM,
        intensity: '',
        status: 'completed',
        activityId: activity.id,
      })

      setActivities(
        (current) =>
          current.filter(
            (item) =>
              item.id !== activity.id,
          ),
      )

      onClose()
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : (
              'Impossible d’ajouter '
              + 'cette activité.'
            ),
      )
    } finally {
      setSubmittingActivityId(
        null,
      )
    }
  }


  async function addManualSession():
  Promise<void> {
    const durationMinutes =
      Number(
        form.durationMinutes,
      )

    if (!form.title.trim()) {
      setError(
        'Le titre de la séance est obligatoire.',
      )

      return
    }

    if (
      !Number.isFinite(
        durationMinutes,
      )
      || durationMinutes <= 0
    ) {
      setError(
        'La durée doit être supérieure à 0 minute.',
      )

      return
    }

    setSubmittingManual(
      true,
    )

    setError(null)

    try {
      const payload:
      TrainingSessionCreate = {
        date,
        type: 'supplementary',
        sportType:
          form.sportType,
        title:
          form.title.trim(),
        description:
          form.description.trim(),
        durationMinutes,
        intensity:
          form.intensity.trim(),
        status: 'completed',
      }

      const distanceKm =
        optionalNumber(
          form.distanceKm,
        )

      const elevationGainM =
        optionalNumber(
          form.elevationGainM,
        )

      if (
        distanceKm !== undefined
      ) {
        payload.distanceKm =
          distanceKm
      }

      if (
        elevationGainM !== undefined
      ) {
        payload.elevationGainM =
          elevationGainM
      }

      if (
        form.heartRateZone.trim()
      ) {
        payload.heartRateZone =
          form.heartRateZone.trim()
      }

      await createSession(
        payload,
      )

      onClose()
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : (
              'Impossible de créer '
              + 'la séance.'
            ),
      )
    } finally {
      setSubmittingManual(
        false,
      )
    }
  }


  useEffect(() => {
    if (!open) {
      return
    }

    const previousOverflow =
      document.body.style.overflow

    document.body.style.overflow =
      'hidden'

    function handleEscape(
      event: KeyboardEvent,
    ) {
      if (event.key === 'Escape') {
        onClose()
      }
    }

    window.addEventListener(
      'keydown',
      handleEscape,
    )

    return () => {
      window.removeEventListener(
        'keydown',
        handleEscape,
      )

      document.body.style.overflow =
        previousOverflow
    }
  }, [
    open,
    onClose,
  ])


  if (!open) {
    return null
  }


  return (
    <SidePanel
      open={open}
      eyebrow="Planning"
      title="Ajouter une séance"
      onClose={onClose}
    >
      <div
        className="
          space-y-4
        "
      >
        <section
          className="
            border-b
            border-[var(--oc-border)]
            pb-3
            border-[var(--oc-border)]
          "
        >
          <p
            className="
              text-[8.5px]
              font-bold
              uppercase
              tracking-[0.12em]
              text-[var(--oc-muted)]
              text-[var(--oc-muted)]
            "
          >
            Date de la séance
          </p>

          <p
            className="
              mt-0.5
              text-[13px]
              font-semibold
              text-[var(--oc-text)]
              text-[var(--oc-text)]
            "
          >
            {formatDisplayDate(
              date,
            )}
          </p>
        </section>


        <div
          className="relative z-20"
          onBlur={(event) => {
            if (
              !event.currentTarget.contains(
                event.relatedTarget as Node | null,
              )
            ) {
              setModeMenuOpen(false)
            }
          }}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              setModeMenuOpen(false)
            }
          }}
        >
          <button
            type="button"
            aria-haspopup="menu"
            aria-expanded={modeMenuOpen}
            aria-label="Choisir le mode d'ajout"
            onClick={() => setModeMenuOpen((current) => !current)}
            className="
              flex
              min-h-[52px]
              w-full
              items-center
              gap-3
              rounded-[12px]
              border
              border-[var(--oc-border)]
              bg-[var(--oc-surface)]
              px-3
              text-left
              shadow-sm
              transition
              hover:border-emerald-500/35
              hover:bg-[var(--oc-surface-hover)]
              focus:outline-none
              focus:ring-2
              focus:ring-emerald-500/15
            "
          >
            <span
              className="
                flex
                h-8
                w-8
                shrink-0
                items-center
                justify-center
                rounded-[9px]
                bg-emerald-500/[0.09]
                text-emerald-600
                dark:text-emerald-400
              "
            >
              {mode === 'intervals' ? (
                <Link2 className="h-4 w-4" />
              ) : mode === 'coros' ? (
                <Footprints className="h-4 w-4" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
            </span>

            <span className="min-w-0 flex-1">
              <span className="block text-[9px] font-semibold uppercase tracking-[0.1em] text-[var(--oc-muted)]">
                Mode d'ajout
              </span>
              <span className="mt-0.5 block truncate text-[12px] font-semibold text-[var(--oc-text)]">
                {mode === 'intervals'
                  ? 'Intervals.icu'
                  : mode === 'coros'
                    ? 'COROS'
                    : 'Saisie manuelle'}
              </span>
            </span>

            <span className="flex items-center gap-2 text-[10px] font-medium text-[var(--oc-muted)]">
              Modifier
              <ChevronDown
                className={`h-4 w-4 transition-transform ${modeMenuOpen ? 'rotate-180' : ''}`}
              />
            </span>
          </button>

          {modeMenuOpen && (
            <div
              role="menu"
              aria-label="Modes d'ajout disponibles"
              className="
                absolute
                left-0
                right-0
                top-[calc(100%+6px)]
                overflow-hidden
                rounded-[12px]
                border
                border-[var(--oc-border)]
                bg-[var(--oc-page)]
                p-1.5
                shadow-[0_12px_32px_rgba(15,23,42,0.14)]
                dark:shadow-[0_12px_32px_rgba(0,0,0,0.32)]
              "
            >
              <button
                type="button"
                role="menuitemradio"
                aria-checked={mode === 'intervals'}
                onClick={() => {
                  setMode('intervals')
                  setModeMenuOpen(false)
                }}
                className={`
                  flex w-full items-center gap-3 rounded-[9px] px-2.5 py-2.5 text-left transition
                  ${mode === 'intervals'
                    ? 'bg-emerald-500/[0.08]'
                    : 'hover:bg-[var(--oc-surface-hover)]'}
                `}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[9px] bg-[var(--oc-surface-muted)] text-[var(--oc-text-secondary)]">
                  <Link2 className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[11.5px] font-semibold text-[var(--oc-text)]">
                    Intervals.icu
                  </span>
                  <span className="mt-0.5 block text-[10px] text-[var(--oc-muted)]">
                    Importer une activité synchronisée
                  </span>
                </span>
                {mode === 'intervals' && (
                  <Check className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                )}
              </button>

              <button
                type="button"
                role="menuitemradio"
                aria-checked={mode === 'coros'}
                onClick={() => {
                  setMode('coros')
                  setModeMenuOpen(false)
                }}
                className={`
                  flex w-full items-center gap-3 rounded-[9px] px-2.5 py-2.5 text-left transition
                  ${mode === 'coros'
                    ? 'bg-emerald-500/[0.08]'
                    : 'hover:bg-[var(--oc-surface-hover)]'}
                `}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[9px] bg-[var(--oc-surface-muted)] text-[var(--oc-text-secondary)]">
                  <Footprints className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[11.5px] font-semibold text-[var(--oc-text)]">
                    COROS
                  </span>
                  <span className="mt-0.5 block text-[10px] text-[var(--oc-muted)]">
                    Importer une activité depuis votre montre
                  </span>
                </span>
                {mode === 'coros' && (
                  <Check className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                )}
              </button>

              <button
                type="button"
                role="menuitemradio"
                aria-checked={mode === 'manual'}
                onClick={() => {
                  setMode('manual')
                  setModeMenuOpen(false)
                }}
                className={`
                  flex w-full items-center gap-3 rounded-[9px] px-2.5 py-2.5 text-left transition
                  ${mode === 'manual'
                    ? 'bg-emerald-500/[0.08]'
                    : 'hover:bg-[var(--oc-surface-hover)]'}
                `}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-[9px] bg-[var(--oc-surface-muted)] text-[var(--oc-text-secondary)]">
                  <Plus className="h-4 w-4" />
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block text-[11.5px] font-semibold text-[var(--oc-text)]">
                    Saisie manuelle
                  </span>
                  <span className="mt-0.5 block text-[10px] text-[var(--oc-muted)]">
                    Renseigner une séance soi-même
                  </span>
                </span>
                {mode === 'manual' && (
                  <Check className="h-4 w-4 shrink-0 text-emerald-600 dark:text-emerald-400" />
                )}
              </button>
            </div>
          )}
        </div>


        {error && (
          <div
            className="
              rounded-[10px]
              border
              border-rose-500/20
              bg-rose-500/[0.05]
              px-3
              py-2.5
              text-[11px]
              leading-5
              text-rose-600
              dark:border-rose-400/20
              dark:bg-rose-400/[0.05]
              dark:text-rose-400
            "
          >
            {error}
          </div>
        )}


        {mode === 'intervals' || mode === 'coros' ? (
          <IntervalsPanel
            activities={activities.filter(activity =>
              activity.provider === (mode === 'coros' ? 'coros' : 'intervals')
            )}
            providerLabel={mode === 'coros' ? 'COROS' : 'Intervals.icu'}
            loading={loadingActivities}
            submittingActivityId={submittingActivityId}
            onAdd={addImportedActivity}
            onRefresh={loadActivities}
          />
        ) : (
          <ManualPanel
            form={form}
            submitting={
              submittingManual
            }
            onChange={
              setForm
            }
            onSubmit={
              addManualSession
            }
          />
        )}
      </div>
    </SidePanel>
  )
}



interface IntervalsPanelProps {
  activities:
    TrainingAvailableActivity[]
  providerLabel: string
  loading: boolean
  submittingActivityId:
    string | null

  onAdd: (
    activity:
      TrainingAvailableActivity,
  ) => Promise<void>

  onRefresh: () => Promise<void>
}


function IntervalsPanel({
  activities,
  providerLabel,
  loading,
  submittingActivityId,
  onAdd,
  onRefresh,
}: IntervalsPanelProps) {
  if (loading) {
    return (
      <div
        className="
          flex
          min-h-44
          flex-col
          items-center
          justify-center
          gap-2.5
        "
      >
        <div
          className="
            flex
            h-10
            w-10
            items-center
            justify-center
            rounded-full
            bg-emerald-500/[0.07]
            dark:bg-emerald-400/[0.07]
          "
        >
          <LoaderCircle
            className="
              h-5
              w-5
              animate-spin
              text-emerald-600
              dark:text-emerald-400
            "
          />
        </div>

        <div className="text-center">
          <p
            className="
              text-[11.5px]
              font-semibold
              text-[var(--oc-text-secondary)]
              text-[var(--oc-text-secondary)]
            "
          >
            Recherche des activités
          </p>

          <p
            className="
              mt-0.5
              text-[10px]
              text-[var(--oc-muted)]
              text-[var(--oc-muted)]
            "
          >
            Chargement des activités {providerLabel}
          </p>
        </div>
      </div>
    )
  }


  return (
    <div className="pt-1">
      <div
        className="
          flex
          items-start
          justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.11em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Activités disponibles
          </p>

          <p
            className="
              mt-0.5
              text-[11px]
              text-[var(--oc-muted)]
              text-[var(--oc-muted)]
            "
          >
            Importer une activité déjà réalisée depuis {providerLabel}
          </p>
        </div>

        <button
          type="button"
          onClick={() =>
            void onRefresh()
          }
          className="
            inline-flex
            h-8
            shrink-0
            items-center
            gap-1.5
            rounded-[8px]
            border
            border-[var(--oc-border)]
            bg-[var(--oc-surface)]
            px-2.5
            text-[10px]
            font-semibold
            text-[var(--oc-muted)]
            transition
            hover:border-[var(--oc-border-strong)]
            hover:bg-[var(--oc-surface-hover)]
            hover:text-[var(--oc-text)]
            border-[var(--oc-border)]
            bg-[var(--oc-surface)]/[0.03]
            text-[var(--oc-muted)]
            dark:hover:bg-[var(--oc-surface)]/[0.06]
            dark:hover:text-[var(--oc-text-secondary)]
          "
        >
          <RefreshCw className="h-3 w-3" />

          Actualiser
        </button>
      </div>


      {activities.length === 0 ? (
        <div
          className="
            mt-3
            rounded-[11px]
            border
            border-dashed
            border-[var(--oc-border)]
            bg-[var(--oc-surface-muted)]
            px-4
            py-7
            text-center
            border-[var(--oc-border)]
            bg-[var(--oc-surface)]/[0.018]
          "
        >
          <div
            className="
              mx-auto
              flex
              h-9
              w-9
              items-center
              justify-center
              rounded-full
              bg-[var(--oc-surface-muted)]
              text-[var(--oc-muted)]
              bg-[var(--oc-surface)]/[0.04]
              text-[var(--oc-muted)]
            "
          >
            <Link2 className="h-4 w-4" />
          </div>

          <p
            className="
              mt-2
              text-[11.5px]
              font-semibold
              text-[var(--oc-text-secondary)]
              text-[var(--oc-muted)]
            "
          >
            Aucune activité disponible
          </p>

          <p
            className="
              mx-auto
              mt-1
              max-w-[300px]
              text-[10px]
              leading-4
              text-[var(--oc-muted)]
              text-[var(--oc-muted)]
            "
          >
            Les activités déjà associées
            à une séance ne sont pas proposées.
          </p>
        </div>
      ) : (
        <div
          className="
            mt-3
            space-y-2
          "
        >
          {activities.map(
            activity => (
              <ActivityRow
                key={activity.id}
                activity={activity}
                submitting={
                  submittingActivityId
                  === activity.id
                }
                onAdd={onAdd}
              />
            ),
          )}
        </div>
      )}
    </div>
  )
}


interface ActivityRowProps {
  activity:
    TrainingAvailableActivity
  submitting: boolean

  onAdd: (
    activity:
      TrainingAvailableActivity,
  ) => Promise<void>
}


function ActivityRow({
  activity,
  submitting,
  onAdd,
}: ActivityRowProps) {
  return (
    <div
      className="
        rounded-[11px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]
        px-3
        py-3
        transition
        hover:border-emerald-500/20
        hover:shadow-[0_3px_12px_rgba(15,23,42,0.035)]
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]/[0.025]
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
        <div
          className="
            flex
            min-w-0
            items-start
            gap-2.5
          "
        >
          <div
            className="
              flex
              h-8
              w-8
              shrink-0
              items-center
              justify-center
              rounded-[9px]
              bg-emerald-500/[0.07]
              text-emerald-600
              dark:bg-emerald-400/[0.07]
              dark:text-emerald-400
            "
          >
            <Dumbbell className="h-3.5 w-3.5" />
          </div>

          <div className="min-w-0">
            <p
              className="
                truncate
                text-[12.5px]
                font-semibold
                text-[var(--oc-text)]
                text-[var(--oc-text)]
              "
            >
              {activity.name}
            </p>

            {activity.startAtLocal && (
              <p
                className="
                  mt-0.5
                  text-[9.5px]
                  font-medium
                  text-[var(--oc-muted)]
                  text-[var(--oc-muted)]
                "
              >
                {formatActivityTime(
                  activity.startAtLocal,
                )}
              </p>
            )}
          </div>
        </div>


        <button
          type="button"
          disabled={submitting}
          onClick={() =>
            void onAdd(
              activity,
            )
          }
          className="
            inline-flex
            h-8
            shrink-0
            items-center
            justify-center
            gap-1.5
            rounded-[8px]
            border
            border-emerald-500/25
            bg-emerald-500/[0.06]
            px-2.5
            text-[10px]
            font-semibold
            text-emerald-700
            transition
            hover:border-emerald-500/40
            hover:bg-emerald-500/[0.10]
            disabled:pointer-events-none
            disabled:opacity-45
            dark:border-emerald-400/20
            dark:bg-emerald-400/[0.06]
            dark:text-emerald-400
          "
        >
          {submitting ? (
            <LoaderCircle
              className="
                h-3.5
                w-3.5
                animate-spin
              "
            />
          ) : (
            <Plus className="h-3.5 w-3.5" />
          )}

          Ajouter
        </button>
      </div>


      <div
        className="
          mt-2
          border-t
          border-[var(--oc-border)]
          pt-2
          border-[var(--oc-border)]
        "
      >
        <p
          className="
            text-[10.5px]
            leading-4
            text-[var(--oc-muted)]
            text-[var(--oc-muted)]
          "
        >
          {formatActivitySummary(
            activity,
          )}
        </p>
      </div>
    </div>
  )
}


interface ManualPanelProps {
  form: ManualFormState
  submitting: boolean

  onChange: (
    value: ManualFormState,
  ) => void

  onSubmit: () => Promise<void>
}


function ManualPanel({
  form,
  submitting,
  onChange,
  onSubmit,
}: ManualPanelProps) {
  function update(
    field: keyof ManualFormState,
    value: string,
  ): void {
    onChange({
      ...form,
      [field]: value,
    })
  }


  function changeDuration(
    delta: number,
  ) {
    const current =
      Number(
        form.durationMinutes,
      ) || 0

    const next =
      Math.max(
        0,
        current + delta,
      )

    update(
      'durationMinutes',
      next === 0
        ? ''
        : String(next),
    )
  }


  return (
    <div className="pt-1">
      <div>
        <p
          className="
            text-[9px]
            font-bold
            uppercase
            tracking-[0.11em]
            text-emerald-600
            dark:text-emerald-400
          "
        >
          Saisie manuelle
        </p>

        <p
          className="
            mt-0.5
            text-[11px]
            text-[var(--oc-muted)]
            text-[var(--oc-muted)]
          "
        >
          Ajouter une séance déjà réalisée
        </p>
      </div>


      <section className="mt-4">
        <FieldLabel>
          Sport
        </FieldLabel>

        <div
          className="
            grid
            grid-cols-3
            gap-1.5
            sm:grid-cols-6
          "
        >
          {SPORT_OPTIONS.map(
            option => {
              const Icon =
                option.icon

              const active =
                form.sportType
                === option.value

              return (
                <button
                  key={option.value}
                  type="button"
                  onClick={() =>
                    update(
                      'sportType',
                      option.value,
                    )
                  }
                  className={[
                    (
                      'relative flex min-h-[58px] '
                      + 'flex-col items-center '
                      + 'justify-center gap-1 '
                      + 'rounded-[9px] border '
                      + 'text-[9.5px] '
                      + 'font-semibold transition'
                    ),
                    active
                      ? (
                          'border-emerald-500/30 '
                          + 'bg-emerald-500/[0.065] '
                          + 'text-emerald-700 '
                          + 'shadow-[inset_0_0_0_1px_rgba(16,185,129,0.04)] '
                          + 'dark:border-emerald-400/25 '
                          + 'dark:bg-emerald-400/[0.07] '
                          + 'dark:text-emerald-400'
                        )
                      : (
                          'border-[var(--oc-border)] '
                          + 'bg-[var(--oc-surface)] '
                          + 'text-[var(--oc-muted)] '
                          + 'hover:border-[var(--oc-border-strong)] '
                          + 'hover:bg-[var(--oc-surface-hover)] '
                          + 'border-[var(--oc-border)] '
                          + 'bg-[var(--oc-surface)]/[0.025] '
                          + 'text-[var(--oc-muted)] '
                          + 'dark:hover:bg-[var(--oc-surface)]/[0.045]'
                        ),
                  ].join(' ')}
                >
                  <Icon className="h-4 w-4" />

                  {option.label}

                  {active && (
                    <span
                      className="
                        absolute
                        right-1.5
                        top-1.5
                        h-1.5
                        w-1.5
                        rounded-full
                        bg-emerald-500
                      "
                    />
                  )}
                </button>
              )
            },
          )}
        </div>
      </section>


      <section
        className="
          mt-4
          border-t
          border-[var(--oc-border)]
          pt-4
          border-[var(--oc-border)]
        "
      >
        <p
          className="
            mb-3
            text-[9px]
            font-bold
            uppercase
            tracking-[0.10em]
            text-[var(--oc-muted)]
            text-[var(--oc-muted)]
          "
        >
          Informations
        </p>

        <div
          className="
            grid
            gap-3
            sm:grid-cols-2
          "
        >
          <div className="sm:col-span-2">
            <TextField
              label="Titre"
              value={form.title}
              placeholder="Ex. Footing récupération"
              onChange={value =>
                update(
                  'title',
                  value,
                )
              }
            />
          </div>


          <div>
            <FieldLabel>
              Durée
            </FieldLabel>

            <div
              className="
                flex
                h-10
                items-center
                overflow-hidden
                rounded-[9px]
                border
                border-[var(--oc-border)]
                bg-[var(--oc-surface)]
                transition
                focus-within:border-emerald-500/40
                focus-within:ring-2
                focus-within:ring-emerald-500/[0.07]
                border-[var(--oc-border)]
                bg-[var(--oc-surface)]/[0.025]
              "
            >
              <button
                type="button"
                onClick={() =>
                  changeDuration(-5)
                }
                aria-label="Retirer 5 minutes"
                className="
                  flex
                  h-full
                  w-10
                  items-center
                  justify-center
                  border-r
                  border-[var(--oc-border)]
                  text-[17px]
                  text-[var(--oc-muted)]
                  transition
                  hover:bg-[var(--oc-surface-hover)]
                  hover:text-[var(--oc-text-secondary)]
                  border-[var(--oc-border)]
                  dark:hover:bg-[var(--oc-surface)]/[0.04]
                  dark:hover:text-[var(--oc-text-secondary)]
                "
              >
                −
              </button>

              <input
                type="number"
                min="1"
                value={
                  form.durationMinutes
                }
                onChange={(event) =>
                  update(
                    'durationMinutes',
                    event.target.value,
                  )
                }
                className="
                  min-w-0
                  flex-1
                  bg-transparent
                  text-center
                  text-[13px]
                  font-semibold
                  text-[var(--oc-text)]
                  outline-none
                  text-[var(--oc-text)]
                "
              />

              <span
                className="
                  pr-2
                  text-[9.5px]
                  font-medium
                  text-[var(--oc-muted)]
                "
              >
                min
              </span>

              <button
                type="button"
                onClick={() =>
                  changeDuration(5)
                }
                aria-label="Ajouter 5 minutes"
                className="
                  flex
                  h-full
                  w-10
                  items-center
                  justify-center
                  border-l
                  border-[var(--oc-border)]
                  text-[17px]
                  text-[var(--oc-muted)]
                  transition
                  hover:bg-[var(--oc-surface-hover)]
                  hover:text-[var(--oc-text-secondary)]
                  border-[var(--oc-border)]
                  dark:hover:bg-[var(--oc-surface)]/[0.04]
                  dark:hover:text-[var(--oc-text-secondary)]
                "
              >
                +
              </button>
            </div>
          </div>


          <UnitField
            label="Distance"
            unit="km"
            value={form.distanceKm}
            onChange={value =>
              update(
                'distanceKm',
                value,
              )
            }
          />

          <UnitField
            label="Dénivelé +"
            unit="m"
            value={
              form.elevationGainM
            }
            onChange={value =>
              update(
                'elevationGainM',
                value,
              )
            }
          />

          <SelectField
            label="Intensité"
            value={form.intensity}
            onChange={value =>
              update(
                'intensity',
                value,
              )
            }
          >
            <option value="">
              Non renseignée
            </option>

            {TRAINING_INTENSITIES.map(
              intensity => (
                <option
                  key={
                    intensity.value
                  }
                  value={
                    intensity.value
                  }
                >
                  {intensity.label}
                </option>
              ),
            )}
          </SelectField>


          <div className="sm:col-span-2">
            <SelectField
              label="Zone cardiaque"
              value={
                form.heartRateZone
              }
              onChange={value =>
                update(
                  'heartRateZone',
                  value,
                )
              }
            >
              <option value="">
                Aucune
              </option>

              {[
                'Z1',
                'Z2',
                'Z3',
                'Z4',
                'Z5',
                'Z1-Z2',
                'Z2-Z3',
                'Z3-Z4',
                'Z4-Z5',
              ].map(
                zone => (
                  <option
                    key={zone}
                    value={zone}
                  >
                    {zone}
                  </option>
                ),
              )}
            </SelectField>
          </div>
        </div>
      </section>


      <section
        className="
          mt-4
          border-t
          border-[var(--oc-border)]
          pt-4
          border-[var(--oc-border)]
        "
      >
        <FieldLabel>
          Notes
        </FieldLabel>

        <textarea
          value={form.description}
          placeholder="Ajouter une note ou une consigne…"
          onChange={(event) =>
            update(
              'description',
              event.target.value,
            )
          }
          className="
            min-h-24
            w-full
            resize-y
            rounded-[9px]
            border
            border-[var(--oc-border)]
            bg-[var(--oc-surface)]
            px-3
            py-2.5
            text-[11.5px]
            leading-5
            text-[var(--oc-text)]
            outline-none
            transition
            placeholder:text-[var(--oc-muted)]
            focus:border-emerald-500/45
            focus:ring-2
            focus:ring-emerald-500/[0.08]
            border-[var(--oc-border)]
            bg-[var(--oc-surface)]/[0.025]
            text-[var(--oc-text-secondary)]
            dark:placeholder:text-[var(--oc-text-secondary)]
          "
        />
      </section>


      <div
        className="
          sticky
          bottom-0
          -mx-1
          mt-4
          border-t
          border-[var(--oc-border)]
          bg-[var(--oc-page)]/95
          px-1
          pb-1
          pt-3
          backdrop-blur-lg
          border-[var(--oc-border)]
          dark:bg-[var(--oc-page)]/95
        "
      >
        <button
          type="button"
          disabled={submitting}
          onClick={() =>
            void onSubmit()
          }
          className="
            flex
            h-10
            w-full
            items-center
            justify-center
            gap-1.5
            rounded-[9px]
            bg-emerald-600
            px-4
            text-[11.5px]
            font-semibold
            text-[var(--oc-text)]
            shadow-[0_4px_12px_rgba(5,150,105,0.14)]
            transition
            hover:bg-emerald-700
            disabled:pointer-events-none
            disabled:opacity-45
            dark:bg-emerald-500
            dark:hover:bg-emerald-400
            sm:ml-auto
            sm:w-auto
          "
        >
          {submitting ? (
            <LoaderCircle
              className="
                h-3.5
                w-3.5
                animate-spin
              "
            />
          ) : (
            <Plus className="h-3.5 w-3.5" />
          )}

          Ajouter la séance
        </button>
      </div>
    </div>
  )
}


function FieldLabel({
  children,
}: {
  children: string
}) {
  return (
    <p
      className="
        mb-1.5
        text-[9.5px]
        font-semibold
        uppercase
        tracking-[0.08em]
        text-[var(--oc-muted)]
        text-[var(--oc-muted)]
      "
    >
      {children}
    </p>
  )
}


function TextField({
  label,
  value,
  placeholder,
  onChange,
}: {
  label: string
  value: string
  placeholder?: string
  onChange: (
    value: string,
  ) => void
}) {
  return (
    <label>
      <FieldLabel>
        {label}
      </FieldLabel>

      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(event) =>
          onChange(
            event.target.value,
          )
        }
        className="
          h-10
          w-full
          rounded-[9px]
          border
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]
          px-3
          text-[11.5px]
          text-[var(--oc-text)]
          outline-none
          transition
          placeholder:text-[var(--oc-muted)]
          focus:border-emerald-500/45
          focus:ring-2
          focus:ring-emerald-500/[0.08]
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]/[0.025]
          text-[var(--oc-text-secondary)]
          dark:placeholder:text-[var(--oc-text-secondary)]
        "
      />
    </label>
  )
}


function UnitField({
  label,
  unit,
  value,
  onChange,
}: {
  label: string
  unit: string
  value: string
  onChange: (
    value: string,
  ) => void
}) {
  return (
    <label>
      <FieldLabel>
        {label}
      </FieldLabel>

      <div
        className="
          flex
          h-10
          items-center
          rounded-[9px]
          border
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]/[0.025]
        "
      >
        <input
          type="number"
          min="0"
          step="0.1"
          value={value}
          onChange={(event) =>
            onChange(
              event.target.value,
            )
          }
          className="
            min-w-0
            flex-1
            bg-transparent
            px-3
            text-[11.5px]
            text-[var(--oc-text)]
            outline-none
            text-[var(--oc-text-secondary)]
          "
        />

        <span
          className="
            pr-3
            text-[10px]
            text-[var(--oc-muted)]
          "
        >
          {unit}
        </span>
      </div>
    </label>
  )
}


function SelectField({
  label,
  value,
  onChange,
  children,
}: {
  label: string
  value: string
  onChange: (
    value: string,
  ) => void
  children: ReactNode
}) {
  return (
    <label>
      <FieldLabel>
        {label}
      </FieldLabel>

      <select
        value={value}
        onChange={(event) =>
          onChange(
            event.target.value,
          )
        }
        className="
          h-10
          w-full
          rounded-[9px]
          border
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]
          px-3
          text-[11.5px]
          text-[var(--oc-text)]
          outline-none
          focus:border-emerald-500/45
          focus:ring-2
          focus:ring-emerald-500/[0.08]
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]
          text-[var(--oc-text-secondary)]
        "
      >
        {children}
      </select>
    </label>
  )
}


function optionalNumber(
  value: string,
): number | undefined {
  const normalized =
    value.trim()

  if (!normalized) {
    return undefined
  }

  const number =
    Number(normalized)

  if (!Number.isFinite(number)) {
    return undefined
  }

  return number
}


function formatDisplayDate(
  value: string,
): string {
  const date =
    new Date(
      `${value}T12:00:00`,
    )

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  ).format(date)
}


function formatActivityTime(
  value: string,
): string {
  const date =
    new Date(value)

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(date)
}


function formatActivitySummary(
  activity:
    TrainingAvailableActivity,
): string {
  const values: string[] = []

  if (
    activity.movingTimeSeconds
    !== undefined
  ) {
    values.push(
      `${Math.round(
        activity.movingTimeSeconds / 60,
      )} min`,
    )
  }

  if (
    activity.distanceM
    !== undefined
  ) {
    values.push(
      `${
        (
          activity.distanceM / 1000
        ).toFixed(1)
      } km`,
    )
  }

  if (
    activity.elevationGainM
    !== undefined
  ) {
    values.push(
      `${Math.round(
        activity.elevationGainM,
      )} m D+`,
    )
  }

  if (
    activity.trainingLoad
    !== undefined
  ) {
    values.push(
      `Charge ${Math.round(
        activity.trainingLoad,
      )}`,
    )
  }

  if (values.length === 0) {
    return activity.sportType
  }

  return values.join(' · ')
}
