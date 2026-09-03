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
        border-black/[0.065]
        bg-white
        dark:border-white/[0.065]
        dark:bg-[#151b1f]
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
                  text-slate-400
                  dark:text-slate-500
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
                  text-slate-950
                  dark:text-white
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
                    text-slate-400
                    dark:text-slate-500
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
                border-black/[0.06]
                px-2.5
                text-[10px]
                font-semibold
                text-slate-500
                transition
                hover:bg-slate-50
                hover:text-slate-900
                dark:border-white/[0.065]
                dark:text-slate-400
                dark:hover:bg-white/[0.04]
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
            border-black/[0.055]
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
              border-black/[0.055]
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
                text-slate-400
                hover:bg-slate-50
                hover:text-slate-700
                dark:hover:bg-white/[0.04]
                dark:hover:text-slate-200
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
            border-black/[0.055]
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
          border-black/[0.055]
          bg-slate-50/60
          px-4
          py-2.5
          dark:border-white/[0.06]
          dark:bg-white/[0.018]
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
                  'bg-slate-100 '
                  + 'text-slate-400 '
                  + 'dark:bg-white/[0.04]'
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
            text-slate-400
            dark:text-slate-500
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
        first:border-black/[0.055]
        dark:first:border-white/[0.06]
      "
    >
      <p
        className="
          text-[8.5px]
          font-semibold
          uppercase
          tracking-[0.08em]
          text-slate-400
          dark:text-slate-500
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
          text-slate-800
          dark:text-slate-200
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
          text-slate-400
          dark:text-slate-500
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
          border-black/[0.07]
          bg-slate-50/60
          px-3
          text-[11.5px]
          font-medium
          text-slate-900
          outline-none
          transition
          placeholder:text-slate-300
          focus:border-emerald-500/40
          focus:ring-2
          focus:ring-emerald-500/[0.08]
          dark:border-white/[0.07]
          dark:bg-white/[0.025]
          dark:text-slate-100
          dark:placeholder:text-slate-600
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
