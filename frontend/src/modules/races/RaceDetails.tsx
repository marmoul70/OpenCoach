import {
  CalendarDays,
  Check,
  Clock3,
  Flag,
  MapPin,
  Mountain,
  Route,
  Trophy,
  X,
} from 'lucide-react'

import {
  useState,
} from 'react'

import {
  useRaces,
} from './raceStore'

import type {
  Race,
} from './types'


interface RaceDetailsProps {
  race: Race
  onClose: () => void
}


type ResultStatus =
  | 'completed'
  | 'abandoned'
  | 'not_participated'


export function RaceDetails({
  race,
  onClose,
}: RaceDetailsProps) {
  const {
    updateRace,
  } = useRaces()

  const [
    status,
    setStatus,
  ] = useState<ResultStatus>(
    race.status === 'abandoned'
      ? 'abandoned'
      : race.status === 'not_participated'
        ? 'not_participated'
        : 'completed',
  )

  const [
    actualDistanceKm,
    setActualDistanceKm,
  ] = useState(
    race.actualDistanceKm
      ?.toString()
    ?? '',
  )

  const [
    actualElevationGainM,
    setActualElevationGainM,
  ] = useState(
    race.actualElevationGainM
      ?.toString()
    ?? '',
  )

  const [
    actualTimeMinutes,
    setActualTimeMinutes,
  ] = useState(
    race.actualTimeMinutes
      ?.toString()
    ?? '',
  )

  const [
    ranking,
    setRanking,
  ] = useState(
    race.ranking
      ?.toString()
    ?? '',
  )

  const [
    notes,
    setNotes,
  ] = useState(
    race.notes
    ?? '',
  )


  const isPlanned =
    race.status === 'planned'


  function handleSubmit(
    event:
      React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const noResult =
      status === 'abandoned'
      || status === 'not_participated'

    const updatedRace:
    Race = {
      ...race,

      status,

      actualDistanceKm:
        status === 'not_participated'
          ? undefined
          : actualDistanceKm
            ? Number(
                actualDistanceKm,
              )
            : undefined,

      actualElevationGainM:
        status === 'not_participated'
          ? undefined
          : actualElevationGainM
            ? Number(
                actualElevationGainM,
              )
            : undefined,

      actualTimeMinutes:
        noResult
          ? undefined
          : actualTimeMinutes
            ? Number(
                actualTimeMinutes,
              )
            : undefined,

      ranking:
        noResult
          ? undefined
          : ranking
            ? Number(
                ranking,
              )
            : undefined,

      notes:
        notes.trim()
        || undefined,
    }

    updateRace(
      updatedRace,
    )

    onClose()
  }


  return (
    <div className="space-y-5">
      <RaceHeader
        race={race}
      />

      <RaceSummary
        race={race}
      />

      {isPlanned ? (
        <form
          onSubmit={
            handleSubmit
          }
          className="
            space-y-5
            border-t
            border-base-300
            pt-5
          "
        >
          <section>
            <h3
              className="
                font-semibold
                text-base-content
              "
            >
              Résultat de la course
            </h3>

            <p
              className="
                mt-1
                text-sm
                text-base-content/50
              "
            >
              À compléter une fois
              la course passée.
            </p>
          </section>


          <section className="space-y-3">
            <p
              className="
                text-sm
                font-medium
                text-base-content/70
              "
            >
              Statut
            </p>

            <div
              className="
                grid gap-2
                sm:grid-cols-3
              "
            >
              <StatusButton
                active={
                  status === 'completed'
                }
                variant="success"
                icon={Check}
                label="Terminée"
                onClick={() =>
                  setStatus(
                    'completed',
                  )
                }
              />

              <StatusButton
                active={
                  status === 'abandoned'
                }
                variant="error"
                icon={X}
                label="Abandon"
                onClick={() =>
                  setStatus(
                    'abandoned',
                  )
                }
              />

              <StatusButton
                active={
                  status
                  === 'not_participated'
                }
                variant="neutral"
                icon={Flag}
                label="Non participant"
                onClick={() =>
                  setStatus(
                    'not_participated',
                  )
                }
              />
            </div>
          </section>


          {status
            !== 'not_participated' && (
              <section
                className="
                  grid gap-4
                  sm:grid-cols-2
                "
              >
                <NumberField
                  label="Distance réalisée"
                  icon={Route}
                  value={
                    actualDistanceKm
                  }
                  onChange={
                    setActualDistanceKm
                  }
                  placeholder="42.8"
                  unit="km"
                  step="0.1"
                />

                <NumberField
                  label="Dénivelé réalisé"
                  icon={Mountain}
                  value={
                    actualElevationGainM
                  }
                  onChange={
                    setActualElevationGainM
                  }
                  placeholder="2150"
                  unit="m"
                  step="1"
                />

                {status
                  === 'completed' && (
                    <>
                      <NumberField
                        label="Chrono"
                        icon={Clock3}
                        value={
                          actualTimeMinutes
                        }
                        onChange={
                          setActualTimeMinutes
                        }
                        placeholder="510"
                        unit="min"
                        step="1"
                      />

                      <NumberField
                        label="Classement"
                        icon={Trophy}
                        value={
                          ranking
                        }
                        onChange={
                          setRanking
                        }
                        placeholder="125"
                        step="1"
                      />
                    </>
                  )}
              </section>
            )}


          <section>
            <label className="form-control">
              <span
                className="
                  mb-1.5
                  text-sm
                  font-medium
                  text-base-content/70
                "
              >
                Notes
              </span>

              <textarea
                value={notes}
                onChange={
                  (event) =>
                    setNotes(
                      event.target.value,
                    )
                }
                className="
                  textarea
                  textarea-bordered
                  min-h-24
                  w-full
                "
                placeholder={
                  'Sensations, difficultés, '
                  + 'points positifs…'
                }
              />
            </label>
          </section>


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
              className="btn btn-ghost"
              onClick={
                onClose
              }
            >
              Annuler
            </button>

            <button
              type="submit"
              className="btn btn-primary"
            >
              <Check
                size={15}
              />

              Enregistrer
            </button>
          </div>
        </form>
      ) : (
        <CompletedRace
          race={race}
        />
      )}
    </div>
  )
}


function RaceHeader({
  race,
}: {
  race: Race
}) {
  return (
    <section
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
            gap-x-4
            gap-y-2
            text-sm
            text-base-content/55
          "
        >
          <span
            className="
              flex items-center
              gap-1.5
            "
          >
            <CalendarDays
              size={14}
            />

            {formatDate(
              race.date,
            )}
          </span>

          <span
            className="
              flex items-center
              gap-1.5
            "
          >
            <MapPin
              size={14}
            />

            {race.location}
          </span>
        </div>

        <p
          className="
            mt-2
            text-sm
            font-medium
            text-base-content/70
          "
        >
          {formatRaceType(
            race.type,
          )}
        </p>
      </div>

      <RaceStatusBadge
        status={
          race.status
        }
      />
    </section>
  )
}


function RaceSummary({
  race,
}: {
  race: Race
}) {
  return (
    <section
      className="
        overflow-hidden
        rounded-xl
        border
        border-base-300
      "
    >
      <div
        className="
          grid
          grid-cols-2
          divide-x
          divide-y
          divide-base-300
          sm:grid-cols-4
          sm:divide-y-0
        "
      >
        <SummaryItem
          icon={Route}
          label="Distance"
          value={
            `${formatNumber(
              race.distanceKm,
            )} km`
          }
        />

        <SummaryItem
          icon={Mountain}
          label="Dénivelé"
          value={
            race.elevationGainM
            !== undefined
              ? (
                `${Math.round(
                  race.elevationGainM,
                )} m`
              )
              : '—'
          }
        />

        <SummaryItem
          icon={Clock3}
          label="Objectif"
          value={
            race.targetTimeMinutes
            !== undefined
              ? formatDuration(
                  race.targetTimeMinutes,
                )
              : '—'
          }
        />

        <SummaryItem
          icon={Flag}
          label="Type"
          value={
            formatRaceType(
              race.type,
            )
          }
        />
      </div>
    </section>
  )
}


function SummaryItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Route
  label: string
  value: string
}) {
  return (
    <div
      className="
        flex items-center
        gap-3
        px-3 py-3
      "
    >
      <Icon
        size={16}
        className="
          shrink-0
          text-base-content/35
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


function StatusButton({
  active,
  variant,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean
  variant:
    | 'success'
    | 'error'
    | 'neutral'
  icon: typeof Check
  label: string
  onClick: () => void
}) {
  const activeClass =
    variant === 'success'
      ? 'btn-success'
      : variant === 'error'
        ? 'btn-error'
        : 'btn-neutral'

  return (
    <button
      type="button"
      onClick={
        onClick
      }
      className={[
        'btn btn-sm',
        active
          ? activeClass
          : (
            'btn-ghost '
            + 'border '
            + 'border-base-300'
          ),
      ].join(' ')}
    >
      <Icon
        size={14}
      />

      {label}
    </button>
  )
}


function NumberField({
  label,
  icon: Icon,
  value,
  onChange,
  placeholder,
  unit,
  step,
}: {
  label: string
  icon: typeof Route
  value: string
  onChange:
    (value: string) => void
  placeholder: string
  unit?: string
  step: string
}) {
  return (
    <label className="form-control">
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
      </span>

      <div className="join w-full">
        <input
          type="number"
          min="0"
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
        />

        {unit && (
          <span
            className="
              join-item
              flex items-center
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
        )}
      </div>
    </label>
  )
}


function CompletedRace({
  race,
}: {
  race: Race
}) {
  return (
    <section
      className="
        space-y-4
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
          Résultat
        </h3>

        <p
          className="
            mt-1
            text-sm
            text-base-content/50
          "
        >
          Données enregistrées
          pour cette course.
        </p>
      </div>


      {race.status
        !== 'not_participated' && (
          <div
            className="
              overflow-hidden
              rounded-xl
              border
              border-base-300
            "
          >
            <div
              className="
                grid
                grid-cols-2
                divide-x
                divide-y
                divide-base-300
                sm:grid-cols-4
                sm:divide-y-0
              "
            >
              <ResultItem
                label="Distance"
                value={
                  race.actualDistanceKm
                  !== undefined
                    ? (
                      `${formatNumber(
                        race.actualDistanceKm,
                      )} km`
                    )
                    : '—'
                }
              />

              <ResultItem
                label="Dénivelé"
                value={
                  race.actualElevationGainM
                  !== undefined
                    ? (
                      `${Math.round(
                        race
                          .actualElevationGainM,
                      )} m`
                    )
                    : '—'
                }
              />

              <ResultItem
                label="Chrono"
                value={
                  race.actualTimeMinutes
                  !== undefined
                    ? formatDuration(
                        race
                          .actualTimeMinutes,
                      )
                    : '—'
                }
              />

              <ResultItem
                label="Classement"
                value={
                  race.ranking
                  !== undefined
                    ? `${race.ranking}e`
                    : '—'
                }
              />
            </div>
          </div>
        )}


      {race.status
        === 'not_participated' && (
          <div
            className="
              rounded-xl
              border
              border-base-300
              bg-base-200/30
              px-4 py-4
              text-sm
              text-base-content/60
            "
          >
            Aucune participation
            enregistrée pour cette course.
          </div>
        )}


      {race.notes && (
        <div
          className="
            rounded-xl
            bg-base-200/50
            px-4 py-3
          "
        >
          <p
            className="
              text-[11px]
              font-medium
              uppercase
              tracking-wide
              text-base-content/40
            "
          >
            Notes
          </p>

          <p
            className="
              mt-1.5
              whitespace-pre-wrap
              text-sm
              leading-relaxed
              text-base-content/70
            "
          >
            {race.notes}
          </p>
        </div>
      )}
    </section>
  )
}


function ResultItem({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        px-4 py-3
      "
    >
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
          mt-0.5
          text-sm
          font-semibold
          text-base-content
        "
      >
        {value}
      </p>
    </div>
  )
}


function RaceStatusBadge({
  status,
}: {
  status: Race['status']
}) {
  if (
    status === 'planned'
  ) {
    return (
      <span
        className="
          badge
          badge-primary
          badge-sm
        "
      >
        À venir
      </span>
    )
  }

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
          size={11}
        />

        Terminée
      </span>
    )
  }

  if (
    status === 'abandoned'
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
          size={11}
        />

        Abandon
      </span>
    )
  }

  return (
    <span
      className="
        badge
        badge-ghost
        badge-sm
      "
    >
      Non participant
    </span>
  )
}


function formatDate(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    },
  ).format(
    new Date(
      `${dateString}T12:00:00`,
    ),
  )
}


function formatDuration(
  totalMinutes: number,
): string {
  const hours =
    Math.floor(
      totalMinutes / 60,
    )

  const minutes =
    totalMinutes % 60

  return (
    `${hours}h${
      minutes
        .toString()
        .padStart(
          2,
          '0',
        )
    }`
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


function formatRaceType(
  type: Race['type'],
): string {
  switch (type) {
    case 'trail':
      return 'Trail'

    case 'road':
      return 'Route'

    case 'ultra':
      return 'Ultra'

    default:
      return 'Autre'
  }
}