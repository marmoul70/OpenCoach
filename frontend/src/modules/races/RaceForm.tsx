import {
  CalendarDays,
  Clock3,
  Flag,
  MapPin,
  Mountain,
  Route,
  Sparkles,
  Trophy,
} from 'lucide-react'

import {
  useState,
} from 'react'

import {
  SidePanel,
} from '../../components/ui/SidePanel'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import {
  useRaces,
} from './raceStore'

import type {
  RacePriority,
  RaceType,
} from './types'

import type {
  RaceWritePayload,
} from '../../core/races/api'


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

  const {
    toast,
  } = useToast()

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

  const [
    saving,
    setSaving,
  ] = useState(false)


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


  async function handleSubmit(
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

    const payload: RaceWritePayload = {
      name:
        name.trim(),

      location:
        location.trim(),

      date,

      raceType:
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

      notes:
        '',
    }

    setSaving(true)

    try {
      const createdRace = await addRace(
        payload,
      )

      if (createdRace.planningWarning) {
        toast({
          type: 'warning',
          title: 'Course enregistrée — préparation trop courte',
          message: createdRace.planningWarning,
          duration: 9000,
        })
      }

      resetForm()
      onClose()
    } finally {
      setSaving(false)
    }
  }


  return (
    <SidePanel
      open={open}
      onClose={
        handleClose
      }
      eyebrow="Course"
      title="Ajouter une course"
    >
      <form
        onSubmit={
          handleSubmit
        }
        className="
          space-y-4
        "
      >

        {/* ================================================
            IDENTITÉ
            ================================================ */}

        <FormSection
          eyebrow="Course"
          title="Informations principales"
        >
          <div
            className="
              grid
              gap-3
              sm:grid-cols-2
            "
          >
            <Field
              label="Nom de la course"
              icon={Flag}
              required
              wide
            >
              <TextInput
                value={name}
                onChange={
                  setName
                }
                placeholder="Trail des Vosges"
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
                  event =>
                    setDate(
                      event.target.value,
                    )
                }
                className="
                  h-10
                  w-full
                  rounded-[9px]
                  border
                  border-[var(--oc-border)]
                  bg-[var(--oc-surface-muted)]
                  px-3
                  text-[12px]
                  font-medium
                  text-[var(--oc-text-secondary)]
                  outline-none
                  transition
                  focus:border-emerald-500/35
                  focus:bg-[var(--oc-surface)]
                  dark:border-white/[0.08]
                  dark:bg-[var(--oc-surface-muted)]
                  dark:text-[var(--oc-text-secondary)]
                "
                required
              />
            </Field>


            <Field
              label="Lieu"
              icon={MapPin}
              required
            >
              <TextInput
                value={location}
                onChange={
                  setLocation
                }
                placeholder="Gérardmer"
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
                  event =>
                    setType(
                      event.target
                        .value as RaceType,
                    )
                }
                className="
                  h-10
                  w-full
                  rounded-[9px]
                  border
                  border-[var(--oc-border)]
                  bg-[var(--oc-surface-muted)]
                  px-3
                  text-[12px]
                  font-medium
                  text-[var(--oc-text-secondary)]
                  outline-none
                  transition
                  focus:border-emerald-500/35
                  focus:bg-[var(--oc-surface)]
                  dark:border-white/[0.08]
                  dark:bg-[var(--oc-surface-muted)]
                  dark:text-[var(--oc-text-secondary)]
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
          </div>
        </FormSection>


        {/* ================================================
            PRIORITÉ
            ================================================ */}

        <FormSection
          eyebrow="Stratégie"
          title="Rôle dans la préparation"
        >
          <div
            className="
              grid
              gap-2.5
              sm:grid-cols-2
            "
          >
            <PriorityCard
              active={
                priority === 'primary'
              }
              icon={
                <Trophy
                  className="
                    h-4
                    w-4
                  "
                />
              }
              eyebrow="A-Race"
              title="Objectif principal"
              description="
                Course cible de la préparation.
                Le plan est construit pour arriver
                au meilleur niveau de forme.
              "
              onClick={() =>
                setPriority(
                  'primary',
                )
              }
            />

            <PriorityCard
              active={
                priority === 'training'
              }
              icon={
                <Flag
                  className="
                    h-4
                    w-4
                  "
                />
              }
              eyebrow="B-Race"
              title="Course de préparation"
              description="
                Course intégrée comme séance
                spécifique sans remplacer
                l’objectif principal.
              "
              onClick={() =>
                setPriority(
                  'training',
                )
              }
            />
          </div>
        </FormSection>


        {/* ================================================
            PERFORMANCE
            ================================================ */}

        <FormSection
          eyebrow="Données"
          title="Profil de la course"
        >
          <div
            className="
              grid
              gap-3
              sm:grid-cols-2
            "
          >
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

              <div
                className="
                  mt-2
                  flex
                  items-center
                  gap-1.5
                  text-[9.5px]
                  text-[var(--oc-muted-soft)]
                  dark:text-[var(--oc-muted-soft)]
                "
              >
                <Sparkles
                  className="
                    h-3
                    w-3
                    text-emerald-500
                  "
                />

                Exemple :
                300 min = 5 h 00.
              </div>
            </Field>
          </div>
        </FormSection>


        {/* ================================================
            ACTIONS
            ================================================ */}

        <div
          className="
            flex
            items-center
            justify-end
            gap-2
            border-t
            border-[var(--oc-border)]
            pt-3
            dark:border-white/[0.055]
          "
        >
          <button
            type="button"
            onClick={
              handleClose
            }
            disabled={saving}
            className="
              h-9
              rounded-[8px]
              px-3
              text-[10.5px]
              font-semibold
              text-[var(--oc-muted-soft)]
              transition
              hover:bg-[var(--oc-surface-muted)]
              hover:text-[var(--oc-text-secondary)]
              disabled:opacity-40
              dark:hover:bg-[var(--oc-surface-hover)]
              dark:hover:text-[var(--oc-text-secondary)]
            "
          >
            Annuler
          </button>

          <button
            type="submit"
            disabled={saving}
            className="
              inline-flex
              h-9
              items-center
              justify-center
              gap-1.5
              rounded-[8px]
              border
              border-emerald-500/25
              bg-emerald-500/[0.08]
              px-3.5
              text-[10.5px]
              font-semibold
              text-emerald-700
              transition
              hover:bg-emerald-500/[0.13]
              disabled:opacity-40
              dark:text-emerald-400
            "
          >
            {saving ? (
              <span
                className="
                  h-3.5
                  w-3.5
                  animate-spin
                  rounded-full
                  border-2
                  border-emerald-500/20
                  border-t-emerald-500
                "
              />
            ) : (
              <Flag
                className="
                  h-3.5
                  w-3.5
                "
              />
            )}

            Ajouter la course
          </button>
        </div>
      </form>
    </SidePanel>
  )
}


/* ============================================================
   SECTIONS
   ============================================================ */

function FormSection({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string
  title: string
  children: React.ReactNode
}) {
  return (
    <section
      className="
        rounded-[12px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]
        p-4
        dark:border-white/[0.065]
        dark:bg-[#151b1f]
      "
    >
      <div className="mb-3">
        <p
          className="
            text-[8.5px]
            font-bold
            uppercase
            tracking-[0.10em]
            text-[var(--oc-muted-soft)]
            dark:text-[var(--oc-muted-soft)]
          "
        >
          {eyebrow}
        </p>

        <h3
          className="
            mt-0.5
            text-[13px]
            font-semibold
            text-[var(--oc-text-secondary)]
            dark:text-[var(--oc-text-secondary)]
          "
        >
          {title}
        </h3>
      </div>

      {children}
    </section>
  )
}


/* ============================================================
   FIELD
   ============================================================ */

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
      className={
        wide
          ? 'block sm:col-span-2'
          : 'block'
      }
    >
      <span
        className="
          mb-1.5
          flex
          items-center
          gap-1.5
          text-[10px]
          font-semibold
          uppercase
          tracking-[0.055em]
          text-[var(--oc-muted-soft)]
          dark:text-[var(--oc-muted-soft)]
        "
      >
        <Icon
          className="
            h-3.5
            w-3.5
            text-emerald-500
          "
        />

        {label}

        {required && (
          <span
            className="
              text-red-400
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


/* ============================================================
   TEXT INPUT
   ============================================================ */

function TextInput({
  value,
  onChange,
  placeholder,
  required = false,
}: {
  value: string
  onChange:
    (value: string) => void
  placeholder: string
  required?: boolean
}) {
  return (
    <input
      type="text"
      value={value}
      onChange={
        event =>
          onChange(
            event.target.value,
          )
      }
      placeholder={placeholder}
      required={required}
      className="
        h-10
        w-full
        rounded-[9px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface-muted)]
        px-3
        text-[12px]
        font-medium
        text-[var(--oc-text-secondary)]
        outline-none
        transition
        placeholder:text-[var(--oc-muted-soft)]
        focus:border-emerald-500/35
        focus:bg-[var(--oc-surface)]
        dark:border-white/[0.08]
        dark:bg-[var(--oc-surface-muted)]
        dark:text-[var(--oc-text-secondary)]
      "
    />
  )
}


/* ============================================================
   UNIT INPUT
   ============================================================ */

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
    <div
      className="
        flex
        h-10
        overflow-hidden
        rounded-[9px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface-muted)]
        transition
        focus-within:border-emerald-500/35
        focus-within:bg-[var(--oc-surface)]
        dark:border-white/[0.08]
        dark:bg-[var(--oc-surface-muted)]
      "
    >
      <input
        type="number"
        min={min}
        step={step}
        value={value}
        onChange={
          event =>
            onChange(
              event.target.value,
            )
        }
        placeholder={placeholder}
        required={required}
        className="
          min-w-0
          flex-1
          bg-transparent
          px-3
          text-[12px]
          font-medium
          text-[var(--oc-text-secondary)]
          outline-none
          placeholder:text-[var(--oc-muted-soft)]
          dark:text-[var(--oc-text-secondary)]
        "
      />

      <span
        className="
          flex
          items-center
          border-l
          border-[var(--oc-border)]
          px-3
          text-[10px]
          font-semibold
          text-[var(--oc-muted-soft)]
          dark:border-white/[0.06]
          dark:text-[var(--oc-muted-soft)]
        "
      >
        {unit}
      </span>
    </div>
  )
}


/* ============================================================
   PRIORITY CARD
   ============================================================ */

function PriorityCard({
  active,
  icon,
  eyebrow,
  title,
  description,
  onClick,
}: {
  active: boolean
  icon: React.ReactNode
  eyebrow: string
  title: string
  description: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        (
          'relative overflow-hidden '
          + 'rounded-[11px] border '
          + 'p-3.5 text-left '
          + 'transition'
        ),
        active
          ? (
              'border-emerald-500/30 '
              + 'bg-emerald-500/[0.055] '
              + 'shadow-[inset_0_0_0_1px_rgba(16,185,129,0.06)]'
            )
          : (
              'border-[var(--oc-border)] '
              + 'bg-[var(--oc-surface-muted)] '
              + 'hover:border-[var(--oc-border)] '
              + 'dark:border-white/[0.065] '
              + 'dark:bg-[var(--oc-surface-muted)] '
              + 'dark:hover:border-white/[0.11]'
            ),
      ].join(' ')}
    >
      <div
        className="
          flex
          items-center
          justify-between
          gap-3
        "
      >
        <div
          className={[
            (
              'flex h-8 w-8 '
              + 'items-center justify-center '
              + 'rounded-[8px]'
            ),
            active
              ? (
                  'bg-emerald-500/[0.10] '
                  + 'text-emerald-600 '
                  + 'dark:text-emerald-400'
                )
              : (
                  'bg-[var(--oc-surface-muted)] '
                  + 'text-[var(--oc-muted-soft)] '
                  + 'dark:bg-[var(--oc-surface-muted)]'
                ),
          ].join(' ')}
        >
          {icon}
        </div>

        <span
          className={[
            (
              'rounded-full '
              + 'px-2 py-0.5 '
              + 'text-[8px] '
              + 'font-bold '
              + 'uppercase '
              + 'tracking-[0.07em]'
            ),
            active
              ? (
                  'bg-emerald-500/[0.09] '
                  + 'text-emerald-700 '
                  + 'dark:text-emerald-400'
                )
              : (
                  'bg-[var(--oc-surface-muted)] '
                  + 'text-[var(--oc-muted-soft)] '
                  + 'dark:bg-[var(--oc-surface-muted)]'
                ),
          ].join(' ')}
        >
          {eyebrow}
        </span>
      </div>

      <p
        className="
          mt-3
          text-[12px]
          font-semibold
          text-[var(--oc-text-secondary)]
          dark:text-[var(--oc-text-secondary)]
        "
      >
        {title}
      </p>

      <p
        className="
          mt-1
          text-[10px]
          leading-[1.6]
          text-[var(--oc-muted-soft)]
          dark:text-[var(--oc-muted-soft)]
        "
      >
        {description}
      </p>
    </button>
  )
}
