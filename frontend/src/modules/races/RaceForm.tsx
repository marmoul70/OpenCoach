import {
  CalendarDays,
  Clock3,
  Flag,
  MapPin,
  Mountain,
  Route,
} from 'lucide-react'

import {
  useState,
} from 'react'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  useRaces,
} from './raceStore'

import type {
  Race,
  RacePriority,
  RaceType,
} from './types'


interface RaceFormProps {
  open: boolean
  onClose: () => void
}


export function RaceForm({
  open,
  onClose,
}: RaceFormProps) {
  const {
    addRace,
  } = useRaces()

  const [
    name,
    setName,
  ] = useState('')

  const [
    date,
    setDate,
  ] = useState('')

  const [
    location,
    setLocation,
  ] = useState('')

  const [
    type,
    setType,
  ] = useState<RaceType>(
    'trail',
  )

  const [
    priority,
    setPriority,
  ] = useState<RacePriority>(
    'training',
  )

  const [
    distanceKm,
    setDistanceKm,
  ] = useState('')

  const [
    elevationGainM,
    setElevationGainM,
  ] = useState('')

  const [
    targetTime,
    setTargetTime,
  ] = useState('')


  function resetForm() {
    setName('')
    setDate('')
    setLocation('')
    setType('trail')
    setPriority('training')
    setDistanceKm('')
    setElevationGainM('')
    setTargetTime('')
  }


  function handleClose() {
    resetForm()
    onClose()
  }


  function handleSubmit(
    event:
      React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const distance =
      Number(
        distanceKm,
      )

    if (
      !name.trim()
      || !date
      || !location.trim()
      || !distanceKm
      || !Number.isFinite(
        distance,
      )
      || distance <= 0
    ) {
      return
    }

    const race:
    Race = {
      id:
        `race-${Date.now()}`,

      name:
        name.trim(),

      location:
        location.trim(),

      date,

      type,

      priority,

      distanceKm:
        distance,

      elevationGainM:
        elevationGainM
          ? Number(
              elevationGainM,
            )
          : undefined,

      targetTimeMinutes:
        targetTime
          ? Number(
              targetTime,
            )
          : undefined,

      status:
        'planned',
    }

    addRace(
      race,
    )

    resetForm()
    onClose()
  }


  return (
    <Modal
      title="Ajouter une course"
      open={open}
      onClose={
        handleClose
      }
    >
      <form
        onSubmit={
          handleSubmit
        }
        className="space-y-5"
      >
        <div
          className="
            flex items-start
            gap-3
          "
        >
          <div
            className="
              flex size-10
              shrink-0
              items-center
              justify-center
              rounded-xl
              bg-primary/10
              text-primary
            "
          >
            <Flag
              size={19}
            />
          </div>

          <div>
            <h2
              className="
                font-semibold
                text-base-content
              "
            >
              Nouvelle course
            </h2>

            <p
              className="
                mt-1
                text-sm
                text-base-content/50
              "
            >
              Ajoutez les informations
              principales de votre course
              et définissez son rôle dans
              votre préparation.
            </p>
          </div>
        </div>


        <div
          className="
            grid gap-4
            sm:grid-cols-2
          "
        >
          <Field
            label="Nom de la course"
            icon={Flag}
            required
            wide
          >
            <input
              type="text"
              value={name}
              onChange={
                (event) =>
                  setName(
                    event.target.value,
                  )
              }
              placeholder="Ex. Trail des Vosges"
              className="
                input
                input-bordered
                w-full
              "
              required
            />
          </Field>


          <Field
            label="Date"
            icon={CalendarDays}
            required
          >
            <input
              type="date"
              value={date}
              onChange={
                (event) =>
                  setDate(
                    event.target.value,
                  )
              }
              className="
                input
                input-bordered
                w-full
              "
              required
            />
          </Field>


          <Field
            label="Lieu"
            icon={MapPin}
            required
          >
            <input
              type="text"
              value={location}
              onChange={
                (event) =>
                  setLocation(
                    event.target.value,
                  )
              }
              placeholder="Ex. Belfort"
              className="
                input
                input-bordered
                w-full
              "
              required
            />
          </Field>


          <Field
            label="Type"
            icon={Flag}
          >
            <select
              value={type}
              onChange={
                (event) =>
                  setType(
                    event.target.value as RaceType,
                  )
              }
              className="
                select
                select-bordered
                w-full
              "
            >
              <option value="trail">
                Trail
              </option>

              <option value="road">
                Route
              </option>

              <option value="ultra">
                Ultra
              </option>

              <option value="other">
                Autre
              </option>
            </select>
          </Field>


          <Field
            label="Rôle dans l'entraînement"
            icon={Flag}
            wide
          >
            <div
              className="
                grid gap-3
                sm:grid-cols-2
              "
            >
              <button
                type="button"
                onClick={() =>
                  setPriority(
                    'primary',
                  )
                }
                className={[
                  (
                    'rounded-xl border '
                    + 'p-4 text-left '
                    + 'transition'
                  ),
                  priority === 'primary'
                    ? (
                        'border-primary '
                        + 'bg-primary/5 '
                        + 'ring-1 '
                        + 'ring-primary/20'
                      )
                    : (
                        'border-base-300 '
                        + 'hover:bg-base-200/50'
                      ),
                ].join(' ')}
              >
                <div
                  className="
                    flex items-center
                    gap-2
                    font-semibold
                    text-base-content
                  "
                >
                  <span
                    className="
                      text-primary
                    "
                  >
                    ★
                  </span>

                  Course prioritaire
                </div>

                <p
                  className="
                    mt-2
                    text-sm
                    leading-relaxed
                    text-base-content/55
                  "
                >
                  Objectif principal.
                  Le plan d&apos;entraînement
                  est construit pour arriver
                  en forme sur cette course.
                </p>
              </button>


              <button
                type="button"
                onClick={() =>
                  setPriority(
                    'training',
                  )
                }
                className={[
                  (
                    'rounded-xl border '
                    + 'p-4 text-left '
                    + 'transition'
                  ),
                  priority === 'training'
                    ? (
                        'border-primary '
                        + 'bg-primary/5 '
                        + 'ring-1 '
                        + 'ring-primary/20'
                      )
                    : (
                        'border-base-300 '
                        + 'hover:bg-base-200/50'
                      ),
                ].join(' ')}
              >
                <div
                  className="
                    flex items-center
                    gap-2
                    font-semibold
                    text-base-content
                  "
                >
                  <Flag
                    size={16}
                    className="
                      text-base-content/50
                    "
                  />

                  Course d&apos;entraînement
                </div>

                <p
                  className="
                    mt-2
                    text-sm
                    leading-relaxed
                    text-base-content/55
                  "
                >
                  Course intégrée au programme
                  comme séance spécifique,
                  sans modifier l&apos;objectif
                  principal.
                </p>
              </button>
            </div>
          </Field>


          <Field
            label="Distance"
            icon={Route}
            required
          >
            <UnitInput
              value={distanceKm}
              onChange={
                setDistanceKm
              }
              min="0.1"
              step="0.1"
              placeholder="42"
              unit="km"
              required
            />
          </Field>


          <Field
            label="Dénivelé positif"
            icon={Mountain}
          >
            <UnitInput
              value={
                elevationGainM
              }
              onChange={
                setElevationGainM
              }
              min="0"
              step="1"
              placeholder="1800"
              unit="m"
            />
          </Field>


          <Field
            label="Objectif chrono"
            icon={Clock3}
            wide
          >
            <UnitInput
              value={targetTime}
              onChange={
                setTargetTime
              }
              min="1"
              step="1"
              placeholder="300"
              unit="min"
            />

            <p
              className="
                mt-1
                text-xs
                text-base-content/40
              "
            >
              Exemple :
              300 min = 5h00.
            </p>
          </Field>
        </div>


        <div
          className="
            flex justify-end
            gap-2
            border-t
            border-base-300
            pt-4
          "
        >
          <button
            type="button"
            className="
              btn btn-ghost
            "
            onClick={
              handleClose
            }
          >
            Annuler
          </button>

          <button
            type="submit"
            className="
              btn btn-primary
            "
          >
            <Flag
              size={15}
            />

            Ajouter
          </button>
        </div>
      </form>
    </Modal>
  )
}


interface FieldProps {
  label: string
  icon:
    typeof Flag
  children:
    React.ReactNode
  required?: boolean
  wide?: boolean
}


function Field({
  label,
  icon: Icon,
  children,
  required = false,
  wide = false,
}: FieldProps) {
  return (
    <label
      className={[
        'form-control',
        wide
          ? 'sm:col-span-2'
          : '',
      ].join(' ')}
    >
      <span
        className="
          mb-1.5
          flex items-center
          gap-1.5
          text-sm
          font-medium
          text-base-content/70
        "
      >
        <Icon
          size={14}
          className="
            text-base-content/40
          "
        />

        {label}

        {required && (
          <span
            className="
              text-error
            "
          >
            *
          </span>
        )}
      </span>

      {children}
    </label>
  )
}


interface UnitInputProps {
  value: string
  onChange:
    (value: string) => void

  min: string
  step: string
  placeholder: string
  unit: string
  required?: boolean
}


function UnitInput({
  value,
  onChange,
  min,
  step,
  placeholder,
  unit,
  required = false,
}: UnitInputProps) {
  return (
    <div className="join w-full">
      <input
        type="number"
        min={min}
        step={step}
        value={value}
        onChange={
          (event) =>
            onChange(
              event.target.value,
            )
        }
        placeholder={
          placeholder
        }
        className="
          input
          input-bordered
          join-item
          w-full
        "
        required={
          required
        }
      />

      <span
        className="
          join-item
          flex
          items-center
          border
          border-base-300
          bg-base-200/40
          px-3
          text-sm
          text-base-content/50
        "
      >
        {unit}
      </span>
    </div>
  )
}