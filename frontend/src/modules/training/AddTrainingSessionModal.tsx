import {
  Dumbbell,
  Link2,
  LoaderCircle,
  Plus,
  X,
} from 'lucide-react'
import {
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


  useEffect(() => {
    if (!open) {
      return
    }

    setMode('intervals')
    setError(null)
    setForm(EMPTY_MANUAL_FORM)

    void loadActivities()
  }, [open, date])


  async function loadActivities():
  Promise<void> {
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
  }


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
              activity
                .movingTimeSeconds
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
        activityId: activity.id,
      })

      setActivities((current) =>
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
      Number(form.durationMinutes)

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
    <div className="modal modal-open">
      <div className="modal-box max-w-2xl">
        <div
          className="
            flex items-start
            justify-between gap-4
          "
        >
          <div>
            <h3 className="text-lg font-semibold">
              Ajouter une séance
            </h3>

            <p
              className="
                mt-1 text-sm
                text-base-content/60
              "
            >
              {formatDisplayDate(
                date,
              )}
            </p>
          </div>

          <button
            type="button"
            className="
              btn btn-ghost
              btn-sm btn-circle
            "
            onClick={onClose}
            aria-label="Fermer"
          >
            <X size={18} />
          </button>
        </div>


        <div
          role="tablist"
          className="
            tabs tabs-box
            mt-5
          "
        >
          <button
            type="button"
            role="tab"
            className={
              `tab ${
                mode === 'intervals'
                  ? 'tab-active'
                  : ''
              }`
            }
            onClick={() =>
              setMode(
                'intervals',
              )
            }
          >
            <Link2 size={16} />

            Intervals.icu
          </button>

          <button
            type="button"
            role="tab"
            className={
              `tab ${
                mode === 'manual'
                  ? 'tab-active'
                  : ''
              }`
            }
            onClick={() =>
              setMode(
                'manual',
              )
            }
          >
            <Plus size={16} />

            Saisie manuelle
          </button>
        </div>


        {error && (
          <div
            className="
              alert alert-error
              mt-4 text-sm
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

      <button
        type="button"
        className="modal-backdrop"
        onClick={onClose}
        aria-label="Fermer"
      />
    </div>
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
          flex min-h-40
          items-center
          justify-center
        "
      >
        <LoaderCircle
          className="animate-spin"
          size={24}
        />
      </div>
    )
  }


  return (
    <div className="mt-5">
      {activities.length === 0 ? (
        <div
          className="
            rounded-box
            border border-base-300
            bg-base-200/40
            p-5 text-center
          "
        >
          <p className="font-medium">
            Aucune activité disponible
          </p>

          <p
            className="
              mt-1 text-sm
              text-base-content/60
            "
          >
            Les activités Intervals.icu
            déjà associées ne sont pas
            proposées ici.
          </p>

          <button
            type="button"
            className="
              btn btn-ghost
              btn-sm mt-3
            "
            onClick={() =>
              void onRefresh()
            }
          >
            Actualiser
          </button>
        </div>
      ) : (
        <div className="space-y-2">
          {activities.map(
            (activity) => (
              <ActivityRow
                key={activity.id}
                activity={
                  activity
                }
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
        flex items-center
        justify-between gap-4
        rounded-box
        border border-base-300
        bg-base-100
        px-4 py-3
      "
    >
      <div className="min-w-0">
        <div
          className="
            flex items-center
            gap-2
          "
        >
          <Dumbbell
            size={16}
            className="
              shrink-0
              text-primary
            "
          />

          <p
            className="
              truncate
              font-medium
            "
          >
            {activity.name}
          </p>

          {activity.startAtLocal && (
            <span
              className="
                text-xs
                text-base-content/50
              "
            >
              {formatActivityTime(
                activity.startAtLocal,
              )}
            </span>
          )}
        </div>

        <p
          className="
            mt-1 text-sm
            text-base-content/60
          "
        >
          {formatActivitySummary(
            activity,
          )}
        </p>
      </div>

      <button
        type="button"
        className="
          btn btn-primary
          btn-sm shrink-0
        "
        disabled={submitting}
        onClick={() =>
          void onAdd(
            activity,
          )
        }
      >
        {submitting ? (
          <LoaderCircle
            className="animate-spin"
            size={16}
          />
        ) : (
          <Plus size={16} />
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


  return (
    <div
      className="
        mt-5 grid
        gap-4
        sm:grid-cols-2
      "
    >
      <label className="form-control">
        <span
          className="
            label-text mb-1
            text-sm
          "
        >
          Sport
        </span>

        <select
          className="
            select
            select-bordered
            w-full
          "
          value={form.sportType}
          onChange={(event) =>
            update(
              'sportType',
              event.target.value,
            )
          }
        >
          <option value="Run">
            Course à pied
          </option>

          <option value="TrailRun">
            Trail
          </option>

          <option value="Ride">
            Vélo
          </option>

          <option value="Swim">
            Natation
          </option>

          <option value="StrengthTraining">
            Renforcement
          </option>

          <option value="Walk">
            Marche
          </option>

          <option value="Other">
            Autre
          </option>
        </select>
      </label>


      <label className="form-control">
        <span
          className="
            label-text mb-1
            text-sm
          "
        >
          Durée
        </span>

        <div
          className="
            join w-full
          "
        >
          <input
            type="number"
            min="1"
            className="
              input
              input-bordered
              join-item
              w-full
            "
            value={
              form.durationMinutes
            }
            onChange={(event) =>
              update(
                'durationMinutes',
                event.target.value,
              )
            }
          />

          <span
            className="
              join-item
              flex items-center
              border border-base-300
              px-3 text-sm
            "
          >
            min
          </span>
        </div>
      </label>


      <label
        className="
          form-control
          sm:col-span-2
        "
      >
        <span
          className="
            label-text mb-1
            text-sm
          "
        >
          Titre
        </span>

        <input
          type="text"
          className="
            input
            input-bordered
            w-full
          "
          placeholder="Ex. Renforcement caserne"
          value={form.title}
          onChange={(event) =>
            update(
              'title',
              event.target.value,
            )
          }
        />
      </label>

      <label className="form-control">
        <span className="label-text mb-1 text-sm">
          Distance parcourue
        </span>

        <div className="join">
          <input
            type="number"
            min="0"
            step="0.1"
            className="
              input
              input-bordered
              join-item
              w-full
            "
            value={form.distanceKm}
            onChange={(event) =>
              update(
                'distanceKm',
                event.target.value,
              )
            }
          />

          <span
            className="
              join-item
              flex items-center
              border border-base-300
              px-3 text-sm
            "
          >
            km
          </span>
        </div>
      </label>

      <label className="form-control">
        <span
          className="
            label-text mb-1
            text-sm
          "
        >
          Dénivelé positif
        </span>

        <div className="join">
          <input
            type="number"
            min="0"
            step="1"
            className="
              input
              input-bordered
              join-item
              w-full
            "
            value={
              form.elevationGainM
            }
            onChange={(event) =>
              update(
                'elevationGainM',
                event.target.value,
              )
            }
          />

          <span
            className="
              join-item
              flex items-center
              border border-base-300
              px-3 text-sm
            "
          >
            m
          </span>
        </div>
      </label>

      <label className="form-control">
        <span className="label-text mb-1 text-sm">
          Intensité
        </span>

        <select
          value={form.intensity}
          onChange={(event) =>
            update(
              'intensity',
              event.target.value,
            )
          }
          className="
            select
            select-bordered
            w-full
          "
        >
          <option value="">
            Non renseignée
          </option>

          {TRAINING_INTENSITIES.map(
            (intensity) => (
              <option
                key={intensity.value}
                value={intensity.value}
              >
                {intensity.label}
              </option>
            ),
          )}
        </select>
      </label>

      <label className="form-control">
        <span className="label-text mb-1 text-sm">
          Zone cardiaque
        </span>

        <select
          className="
            select
            select-bordered
            w-full
          "
          value={form.heartRateZone}
          onChange={(event) =>
            update(
              'heartRateZone',
              event.target.value,
            )
          }
        >
          <option value="">
            Aucune
          </option>

          <option value="Z1">
            Z1
          </option>

          <option value="Z2">
            Z2
          </option>

          <option value="Z3">
            Z3
          </option>

          <option value="Z4">
            Z4
          </option>

          <option value="Z5">
            Z5
          </option>

          <option value="Z1-Z2">
            Z1-Z2
          </option>

          <option value="Z2-Z3">
            Z2-Z3
          </option>

          <option value="Z3-Z4">
            Z3-Z4
          </option>

          <option value="Z4-Z5">
            Z4-Z5
          </option>
        </select>
      </label>

      <label
        className="
          form-control
          sm:col-span-2
        "
      >
        <span
          className="
            label-text mb-1
            text-sm
          "
        >
          Notes
        </span>

        <textarea
          className="
            textarea
            textarea-bordered
            min-h-20 w-full
          "
          placeholder="Optionnel"
          value={form.description}
          onChange={(event) =>
            update(
              'description',
              event.target.value,
            )
          }
        />
      </label>


      <div
        className="
          flex justify-end
          sm:col-span-2
        "
      >
        <button
          type="button"
          className="
            btn btn-primary
          "
          disabled={submitting}
          onClick={() =>
            void onSubmit()
          }
        >
          {submitting ? (
            <LoaderCircle
              className="animate-spin"
              size={17}
            />
          ) : (
            <Plus size={17} />
          )}

          Ajouter la séance
        </button>
      </div>
    </div>
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
    new Date(`${value}T12:00:00`)

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
