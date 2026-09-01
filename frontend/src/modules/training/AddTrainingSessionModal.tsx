import type { ReactNode } from 'react'
import {
  Bike,
  Dumbbell,
  Footprints,
  Link2,
  LoaderCircle,
  Mountain,
  Plus,
  RefreshCw,
  Waves,
  X,
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
                  + 'activités Intervals.icu.'
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
    setError(null)
    setForm(EMPTY_MANUAL_FORM)

    void loadActivities()
  }, [
    open,
    loadActivities,
  ])


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
      document.body.style.overflow =
        previousOverflow

      window.removeEventListener(
        'keydown',
        handleEscape,
      )
    }
  }, [
    open,
    onClose,
  ])


  async function addIntervalsActivity(
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
          'Activité importée depuis Intervals.icu.',
        durationMinutes,
        distanceKm:
          activity.distanceM !== undefined
            ? activity.distanceM / 1000
            : undefined,
        elevationGainM:
          activity.elevationGainM,
        intensity: '',
        status: 'completed',
        activityId:
          activity.id,
      })

      setActivities(
        current =>
          current.filter(
            item =>
              item.id
              !== activity.id,
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

    setSubmittingManual(true)
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
      setSubmittingManual(false)
    }
  }


  if (!open) {
    return null
  }


  return (
    <div
      className="
        fixed
        inset-0
        z-[100]
        flex
        items-end
        justify-center
        sm:items-center
        sm:px-6
        sm:py-6
      "
      role="dialog"
      aria-modal="true"
    >
      <button
        type="button"
        aria-label="Fermer"
        onClick={onClose}
        className="
          absolute
          inset-0
          cursor-default
          bg-black/45
          backdrop-blur-[4px]
          dark:bg-black/55
        "
      />


      <div
        className="
          relative
          z-10
          flex
          max-h-[82dvh]
          w-full
          flex-col
          overflow-hidden
          rounded-t-[20px]
          border
          border-black/[0.07]
          border-b-0
          bg-white
          shadow-[0_-18px_55px_rgba(15,23,42,0.18)]
          dark:border-white/[0.08]
          dark:bg-[#151b1f]

          sm:max-h-[82vh]
          sm:max-w-[700px]
          sm:rounded-[18px]
          sm:border-b
          sm:shadow-[0_24px_70px_rgba(15,23,42,0.22)]
        "
      >

        <div
          className="
            flex
            justify-center
            pt-2
            sm:hidden
          "
        >
          <div
            className="
              h-1
              w-9
              rounded-full
              bg-slate-300
              dark:bg-white/[0.14]
            "
          />
        </div>


        <header
          className="
            flex
            shrink-0
            items-start
            justify-between
            gap-4
            border-b
            border-black/[0.06]
            px-4
            py-3.5
            dark:border-white/[0.07]
            sm:px-5
          "
        >
          <div>
            <p
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.13em]
                text-emerald-600
                dark:text-emerald-400
              "
            >
              Séance supplémentaire
            </p>

            <h2
              className="
                mt-0.5
                text-[17px]
                font-semibold
                tracking-[-0.025em]
                text-slate-950
                dark:text-white
              "
            >
              Ajouter une séance
            </h2>

            <p
              className="
                mt-1
                text-[10.5px]
                text-slate-400
                dark:text-slate-500
              "
            >
              {formatDisplayDate(
                date,
              )}
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Fermer"
            className="
              flex
              h-8
              w-8
              items-center
              justify-center
              rounded-[9px]
              text-slate-400
              transition
              hover:bg-slate-100
              hover:text-slate-900
              dark:hover:bg-white/[0.055]
              dark:hover:text-white
            "
          >
            <X className="h-4 w-4" />
          </button>
        </header>


        <div
          className="
            min-h-0
            flex-1
            overflow-y-auto
            overscroll-contain
            px-4
            py-4
            sm:px-5
          "
        >

          <div
            className="
              grid
              grid-cols-2
              gap-1
              rounded-[10px]
              border
              border-black/[0.055]
              bg-slate-100
              p-1
              dark:border-white/[0.06]
              dark:bg-white/[0.035]
            "
          >
            <ModeButton
              active={
                mode === 'intervals'
              }
              icon={Link2}
              label="Intervals.icu"
              onClick={() =>
                setMode(
                  'intervals',
                )
              }
            />

            <ModeButton
              active={
                mode === 'manual'
              }
              icon={Plus}
              label="Saisie manuelle"
              onClick={() =>
                setMode(
                  'manual',
                )
              }
            />
          </div>


          {error && (
            <div
              className="
                mt-3
                rounded-[10px]
                border
                border-red-500/15
                bg-red-50
                px-3
                py-2.5
                text-[11px]
                font-medium
                text-red-600
                dark:bg-red-500/[0.06]
                dark:text-red-400
              "
            >
              {error}
            </div>
          )}


          {mode === 'intervals' ? (
            <IntervalsPanel
              activities={
                activities
              }
              loading={
                loadingActivities
              }
              submittingActivityId={
                submittingActivityId
              }
              onAdd={
                addIntervalsActivity
              }
              onRefresh={
                loadActivities
              }
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
      </div>
    </div>
  )
}


function ModeButton({
  active,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean
  icon: typeof Link2
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        (
          'flex h-9 items-center '
          + 'justify-center gap-2 '
          + 'rounded-[8px] '
          + 'text-[11px] '
          + 'font-semibold transition'
        ),
        active
          ? (
              'bg-white text-slate-900 '
              + 'shadow-[0_1px_2px_rgba(15,23,42,0.06)] '
              + 'dark:bg-white/[0.07] '
              + 'dark:text-white'
            )
          : (
              'text-slate-400 '
              + 'hover:text-slate-700 '
              + 'dark:text-slate-500 '
              + 'dark:hover:text-slate-300'
            ),
      ].join(' ')}
    >
      <Icon className="h-3.5 w-3.5" />
      {label}
    </button>
  )
}


interface IntervalsPanelProps {
  activities:
    TrainingAvailableActivity[]
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
          min-h-40
          items-center
          justify-center
        "
      >
        <LoaderCircle
          className="
            h-5
            w-5
            animate-spin
            text-emerald-500
          "
        />
      </div>
    )
  }


  return (
    <div className="mt-4">
      <SectionHeading
        title="Activités disponibles"
        subtitle="Intervals.icu"
      />

      {activities.length === 0 ? (
        <div
          className="
            mt-2.5
            rounded-[11px]
            border
            border-dashed
            border-black/[0.08]
            bg-slate-50
            px-4
            py-5
            text-center
            dark:border-white/[0.07]
            dark:bg-white/[0.02]
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
            Aucune activité disponible
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
            Les activités déjà associées
            ne sont pas proposées ici.
          </p>

          <button
            type="button"
            onClick={() =>
              void onRefresh()
            }
            className="
              mt-3
              inline-flex
              h-8
              items-center
              gap-1.5
              rounded-[8px]
              px-2.5
              text-[10.5px]
              font-semibold
              text-slate-500
              transition
              hover:bg-white
              hover:text-slate-900
              dark:hover:bg-white/[0.05]
              dark:hover:text-white
            "
          >
            <RefreshCw className="h-3 w-3" />
            Actualiser
          </button>
        </div>
      ) : (
        <div className="mt-2.5 space-y-2">
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
        flex
        items-center
        justify-between
        gap-3
        rounded-[10px]
        border
        border-black/[0.065]
        bg-slate-50
        px-3
        py-2.5
        transition
        hover:border-emerald-500/20
        dark:border-white/[0.065]
        dark:bg-white/[0.025]
      "
    >
      <div className="min-w-0">
        <div
          className="
            flex
            items-center
            gap-2
          "
        >
          <div
            className="
              flex
              h-7
              w-7
              shrink-0
              items-center
              justify-center
              rounded-[8px]
              bg-emerald-50
              text-emerald-600
              dark:bg-emerald-500/[0.08]
              dark:text-emerald-400
            "
          >
            <Dumbbell
              className="h-3.5 w-3.5"
            />
          </div>

          <div className="min-w-0">
            <p
              className="
                truncate
                text-[12px]
                font-semibold
                text-slate-900
                dark:text-slate-100
              "
            >
              {activity.name}
            </p>

            <p
              className="
                mt-0.5
                text-[10px]
                text-slate-400
                dark:text-slate-500
              "
            >
              {activity.startAtLocal
                ? (
                    `${
                      formatActivityTime(
                        activity.startAtLocal,
                      )
                    } · `
                  )
                : ''}
              {formatActivitySummary(
                activity,
              )}
            </p>
          </div>
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
          flex
          h-8
          shrink-0
          items-center
          gap-1.5
          rounded-[8px]
          bg-emerald-600
          px-2.5
          text-[10.5px]
          font-semibold
          text-white
          transition
          hover:bg-emerald-700
          disabled:opacity-50
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
    <div className="mt-4">
      <SectionHeading
        title="Saisie manuelle"
        subtitle="Séance déjà réalisée"
      />


      <div className="mt-3">
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
                      'flex min-h-14 '
                      + 'flex-col items-center '
                      + 'justify-center gap-1 '
                      + 'rounded-[9px] border '
                      + 'text-[9.5px] '
                      + 'font-semibold transition'
                    ),
                    active
                      ? (
                          'border-emerald-500/30 '
                          + 'bg-emerald-50 '
                          + 'text-emerald-700 '
                          + 'dark:bg-emerald-500/[0.08] '
                          + 'dark:text-emerald-400'
                        )
                      : (
                          'border-black/[0.06] '
                          + 'bg-slate-50 '
                          + 'text-slate-500 '
                          + 'hover:border-black/[0.10] '
                          + 'dark:border-white/[0.06] '
                          + 'dark:bg-white/[0.02] '
                          + 'dark:text-slate-400'
                        ),
                  ].join(' ')}
                >
                  <Icon className="h-4 w-4" />
                  {option.label}
                </button>
              )
            },
          )}
        </div>
      </div>


      <div
        className="
          mt-4
          grid
          gap-3
          sm:grid-cols-2
        "
      >
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
              border-black/[0.07]
              bg-white
              dark:border-white/[0.07]
              dark:bg-white/[0.025]
            "
          >
            <button
              type="button"
              onClick={() =>
                changeDuration(-5)
              }
              className="
                h-full
                w-10
                text-[16px]
                text-slate-400
                hover:bg-slate-50
                dark:hover:bg-white/[0.04]
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
                text-slate-900
                outline-none
                dark:text-white
              "
            />

            <span
              className="
                pr-2
                text-[10px]
                text-slate-400
              "
            >
              min
            </span>

            <button
              type="button"
              onClick={() =>
                changeDuration(5)
              }
              className="
                h-full
                w-10
                text-[16px]
                text-slate-400
                hover:bg-slate-50
                dark:hover:bg-white/[0.04]
              "
            >
              +
            </button>
          </div>
        </div>


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


      <div className="mt-3">
        <FieldLabel>
          Notes
        </FieldLabel>

        <textarea
          value={form.description}
          placeholder="Optionnel"
          onChange={(event) =>
            update(
              'description',
              event.target.value,
            )
          }
          className="
            min-h-20
            w-full
            resize-y
            rounded-[9px]
            border
            border-black/[0.07]
            bg-white
            px-3
            py-2.5
            text-[11.5px]
            text-slate-800
            outline-none
            transition
            placeholder:text-slate-300
            focus:border-emerald-500/45
            focus:ring-2
            focus:ring-emerald-500/[0.08]
            dark:border-white/[0.07]
            dark:bg-white/[0.025]
            dark:text-slate-200
            dark:placeholder:text-slate-600
          "
        />
      </div>


      <div
        className="
          mt-4
          flex
          justify-end
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
            h-9
            w-full
            items-center
            justify-center
            gap-1.5
            rounded-[9px]
            bg-emerald-600
            px-4
            text-[11px]
            font-semibold
            text-white
            transition
            hover:bg-emerald-700
            disabled:opacity-50
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


function SectionHeading({
  title,
  subtitle,
}: {
  title: string
  subtitle?: string
}) {
  return (
    <div
      className="
        flex
        items-end
        justify-between
        gap-3
      "
    >
      <p
        className="
          text-[11.5px]
          font-semibold
          text-slate-900
          dark:text-slate-100
        "
      >
        {title}
      </p>

      {subtitle && (
        <p
          className="
            text-[9.5px]
            text-slate-400
            dark:text-slate-500
          "
        >
          {subtitle}
        </p>
      )}
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
        text-slate-400
        dark:text-slate-500
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
          border-black/[0.07]
          bg-white
          px-3
          text-[11.5px]
          text-slate-800
          outline-none
          transition
          placeholder:text-slate-300
          focus:border-emerald-500/45
          focus:ring-2
          focus:ring-emerald-500/[0.08]
          dark:border-white/[0.07]
          dark:bg-white/[0.025]
          dark:text-slate-200
          dark:placeholder:text-slate-600
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
          border-black/[0.07]
          bg-white
          dark:border-white/[0.07]
          dark:bg-white/[0.025]
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
            text-slate-800
            outline-none
            dark:text-slate-200
          "
        />

        <span
          className="
            pr-3
            text-[10px]
            text-slate-400
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
          border-black/[0.07]
          bg-white
          px-3
          text-[11.5px]
          text-slate-800
          outline-none
          focus:border-emerald-500/45
          focus:ring-2
          focus:ring-emerald-500/[0.08]
          dark:border-white/[0.07]
          dark:bg-[#151b1f]
          dark:text-slate-200
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
