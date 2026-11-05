import {
  Check,
  CloudSun,
  MapPin,
  Navigation,
  Pencil,
} from 'lucide-react'

import {
  useState,
} from 'react'

import {
  updateAthleteProfile,
} from '../../core/profile'

import {
  parseOptionalNumber,
} from '../profile/ProfileForm'


interface LocationWidgetProps {
  location: {
    name?: string
    latitude?: number
    longitude?: number
  }
}


export function LocationWidget({
  location,
}: LocationWidgetProps) {
  const [
    editing,
    setEditing,
  ] = useState(false)

  const [
    saved,
    setSaved,
  ] = useState(false)

  const [
    name,
    setName,
  ] = useState(
    location.name ?? '',
  )

  const [
    latitude,
    setLatitude,
  ] = useState(
    location.latitude
      ?.toString()
    ?? '',
  )

  const [
    longitude,
    setLongitude,
  ] = useState(
    location.longitude
      ?.toString()
    ?? '',
  )


  async function handleSave() {
    await updateAthleteProfile(
      current => ({
        ...current,

        location: {
          name:
            name.trim()
            || undefined,

          latitude:
            parseOptionalNumber(
              latitude,
            ),

          longitude:
            parseOptionalNumber(
              longitude,
            ),
        },
      }),
    )

    setEditing(false)
    setSaved(true)

    window.setTimeout(
      () => setSaved(false),
      2000,
    )
  }


  function handleCancel() {
    setName(
      location.name ?? '',
    )

    setLatitude(
      location.latitude
        ?.toString()
      ?? '',
    )

    setLongitude(
      location.longitude
        ?.toString()
      ?? '',
    )

    setSaved(false)
    setEditing(false)
  }


  const hasCoordinates =
    Boolean(
      latitude.trim()
      && longitude.trim(),
    )


  return (
    <div
      className="
        overflow-hidden
        rounded-[12px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]
        dark:border-white/[0.065]
        dark:bg-[var(--oc-surface)]
      "
    >

      {/* HERO */}

      <div
        className="
          relative
          overflow-hidden
          px-4
          py-4
        "
      >
        <div
          className="
            pointer-events-none
            absolute
            -right-14
            -top-20
            h-40
            w-40
            rounded-full
            bg-emerald-500/[0.05]
            blur-3xl
          "
        />

        <div
          className="
            relative
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
              gap-3
            "
          >
            <div
              className="
                flex
                h-10
                w-10
                shrink-0
                items-center
                justify-center
                rounded-[11px]
                bg-emerald-50
                text-emerald-600
                dark:bg-emerald-500/[0.08]
                dark:text-emerald-400
              "
            >
              <MapPin
                className="
                  h-[18px]
                  w-[18px]
                "
              />
            </div>

            <div className="min-w-0">
              <p
                className="
                  text-[9px]
                  font-bold
                  uppercase
                  tracking-[0.1em]
                  text-[var(--oc-muted-soft)]
                  dark:text-[var(--oc-muted)]
                "
              >
                Lieu principal
              </p>

              <p
                className="
                  mt-1
                  truncate
                  text-[18px]
                  font-bold
                  tracking-[-0.025em]
                  text-[var(--oc-text)]
                  dark:text-[var(--oc-text)]
                "
              >
                {
                  name.trim()
                  || 'Non configuré'
                }
              </p>

              {!editing && (
                <p
                  className="
                    mt-1
                    text-[10px]
                    text-[var(--oc-muted-soft)]
                    dark:text-[var(--oc-muted)]
                  "
                >
                  {
                    formatCoordinates(
                      latitude,
                      longitude,
                    )
                  }
                </p>
              )}
            </div>
          </div>


          {!editing && (
            <button
              type="button"
              onClick={() =>
                setEditing(true)
              }
              className="
                flex
                h-8
                shrink-0
                items-center
                gap-1.5
                rounded-[8px]
                border
                border-[var(--oc-border)]
                px-2.5
                text-[10px]
                font-semibold
                text-[var(--oc-muted)]
                transition
                hover:bg-[var(--oc-surface-muted)]
                hover:text-[var(--oc-text)]
                dark:border-white/[0.065]
                dark:text-[var(--oc-muted-soft)]
                dark:hover:bg-[var(--oc-surface-hover)]
                dark:hover:text-white
              "
            >
              <Pencil
                className="
                  h-3
                  w-3
                "
              />

              Modifier
            </button>
          )}
        </div>
      </div>


      {editing ? (

        /* EDIT */

        <div
          className="
            border-t
            border-[var(--oc-border)]
            px-4
            py-4
            dark:border-white/[0.06]
          "
        >
          <div
            className="
              grid
              gap-3
              sm:grid-cols-2
            "
          >
            <LocationField
              label="Lieu"
              value={name}
              onChange={setName}
              placeholder="Lure"
              className="sm:col-span-2"
            />

            <LocationField
              label="Latitude"
              value={latitude}
              onChange={setLatitude}
              placeholder="47.685"
              type="number"
            />

            <LocationField
              label="Longitude"
              value={longitude}
              onChange={setLongitude}
              placeholder="6.496"
              type="number"
            />
          </div>


          <div
            className="
              mt-4
              flex
              justify-end
              gap-2
              border-t
              border-[var(--oc-border)]
              pt-3
              dark:border-white/[0.06]
            "
          >
            <button
              type="button"
              onClick={handleCancel}
              className="
                h-8
                rounded-[8px]
                px-3
                text-[10.5px]
                font-semibold
                text-[var(--oc-muted-soft)]
                hover:bg-[var(--oc-surface-muted)]
                hover:text-[var(--oc-text-secondary)]
                dark:hover:bg-[var(--oc-surface-hover)]
                dark:hover:text-[var(--oc-text-secondary)]
              "
            >
              Annuler
            </button>

            <button
              type="button"
              onClick={() =>
                void handleSave()
              }
              className="
                h-8
                rounded-[8px]
                bg-emerald-600
                px-3
                text-[10.5px]
                font-semibold
                text-white
                transition
                hover:bg-emerald-700
              "
            >
              Enregistrer
            </button>
          </div>
        </div>

      ) : (

        /* READ */

        <div
          className="
            grid
            grid-cols-2
            border-t
            border-[var(--oc-border)]
            dark:border-white/[0.06]
          "
        >
          <LocationMetric
            label="Latitude"
            value={
              latitude.trim()
              || '—'
            }
          />

          <LocationMetric
            label="Longitude"
            value={
              longitude.trim()
              || '—'
            }
          />
        </div>
      )}


      {/* STATUS */}

      <div
        className="
          flex
          items-center
          gap-2
          border-t
          border-[var(--oc-border)]
          bg-[var(--oc-surface-muted)]/60
          px-4
          py-2.5
          dark:border-white/[0.06]
          dark:bg-[var(--oc-surface-muted)]
        "
      >
        <div
          className={[
            (
              'flex h-6 w-6 '
              + 'items-center '
              + 'justify-center '
              + 'rounded-[7px]'
            ),
            hasCoordinates
              ? (
                  'bg-emerald-50 '
                  + 'text-emerald-600 '
                  + 'dark:bg-emerald-500/[0.07] '
                  + 'dark:text-emerald-400'
                )
              : (
                  'bg-[var(--oc-surface-muted)] '
                  + 'text-[var(--oc-muted-soft)] '
                  + 'dark:bg-[var(--oc-surface-muted)]'
                ),
          ].join(' ')}
        >
          {
            hasCoordinates
              ? (
                  <CloudSun
                    className="
                      h-3.5
                      w-3.5
                    "
                  />
                )
              : (
                  <Navigation
                    className="
                      h-3.5
                      w-3.5
                    "
                  />
                )
          }
        </div>

        <p
          className="
            flex-1
            text-[9.5px]
            text-[var(--oc-muted-soft)]
            dark:text-[var(--oc-muted)]
          "
        >
          {
            hasCoordinates
              ? (
                  'Utilisée pour la météo '
                  + 'et le contexte local.'
                )
              : (
                  'Ajoute les coordonnées '
                  + 'pour activer le contexte local.'
                )
          }
        </p>

        {saved && (
          <span
            className="
              flex
              items-center
              gap-1
              text-[9px]
              font-semibold
              text-emerald-600
              dark:text-emerald-400
            "
          >
            <Check
              className="
                h-3
                w-3
              "
            />

            Enregistré
          </span>
        )}
      </div>
    </div>
  )
}


function LocationMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        px-4
        py-3
        first:border-r
        first:border-[var(--oc-border)]
        dark:first:border-white/[0.06]
      "
    >
      <p
        className="
          text-[8.5px]
          font-semibold
          uppercase
          tracking-[0.08em]
          text-[var(--oc-muted-soft)]
          dark:text-[var(--oc-muted)]
        "
      >
        {label}
      </p>

      <p
        className="
          mt-1
          text-[12px]
          font-semibold
          tabular-nums
          text-[var(--oc-text-secondary)]
          dark:text-[var(--oc-text-secondary)]
        "
      >
        {value}
      </p>
    </div>
  )
}


function LocationField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  className = '',
}: {
  label: string
  value: string
  onChange:
    (value: string) => void
  placeholder?: string
  type?: string
  className?: string
}) {
  return (
    <label className={className}>
      <span
        className="
          mb-1.5
          block
          text-[9px]
          font-semibold
          uppercase
          tracking-[0.07em]
          text-[var(--oc-muted-soft)]
          dark:text-[var(--oc-muted)]
        "
      >
        {label}
      </span>

      <input
        type={type}
        value={value}
        placeholder={placeholder}
        onChange={
          event =>
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
          bg-[var(--oc-surface-muted)]/60
          px-3
          text-[11.5px]
          font-medium
          text-[var(--oc-text)]
          outline-none
          transition
          placeholder:text-[var(--oc-muted-soft)]
          focus:border-emerald-500/40
          focus:ring-2
          focus:ring-emerald-500/[0.08]
          dark:border-white/[0.07]
          dark:bg-[var(--oc-surface-muted)]
          dark:text-[var(--oc-text)]
          dark:placeholder:text-[var(--oc-text-secondary)]
        "
      />
    </label>
  )
}


function formatCoordinates(
  latitude: string,
  longitude: string,
): string {
  if (
    !latitude.trim()
    || !longitude.trim()
  ) {
    return 'Coordonnées non renseignées'
  }

  return (
    `${latitude}° · ${longitude}°`
  )
}
