import {
  ArrowRight,
  Flag,
  MapPin,
  Mountain,
  Route,
} from 'lucide-react'

import {
  useRaces,
} from '../races/raceStore'

import {
  getNextPrimaryRace,
} from '../races/selectors'


interface DashboardRaceGoalProps {
  onOpenRaces: () => void
}


export function DashboardRaceGoal({
  onOpenRaces,
}: DashboardRaceGoalProps) {
  const {
    races,
    loading,
    error,
  } = useRaces()

  const race =
    getNextPrimaryRace(
      races,
    )


  if (loading) {
    return (
      <div
        className="
          flex min-h-52 items-center justify-center oc-surface
        "
      >
        <span
          className="
            h-5
            w-5
            animate-spin
            rounded-full
            border-2
            border-[var(--oc-border)] border-t-[var(--oc-accent)]
          "
          aria-hidden="true"
        />
      </div>
    )
  }


  if (error) {
    return (
      <div
        className="
          oc-surface rounded-2xl p-5
        "
      >
        <p className="font-semibold text-red-500">
          Objectif indisponible
        </p>
      </div>
    )
  }


  if (!race) {
    return (
      <button
        type="button"
        onClick={onOpenRaces}
        className="
          oc-surface oc-interactive-surface group flex min-h-52 w-full flex-col justify-between border-dashed p-5 text-left hover:border-emerald-500/40
        "
      >
        <div>
          <div
            className="
              flex h-10 w-10
              items-center justify-center
              rounded-xl
              bg-emerald-50
              text-emerald-600
              dark:bg-emerald-500/10
              dark:text-emerald-400
            "
          >
            <Flag className="h-5 w-5" />
          </div>

          <h3
            className="
              mt-4 oc-type-card-title font-bold tracking-[-0.02em]
            "
          >
            Aucun objectif principal
          </h3>

          <p
            className="
              mt-1 oc-type-body leading-6
            "
          >
            Ajoute une course prioritaire
            pour orienter la planification.
          </p>
        </div>

        <span
          className="
            mt-4 flex items-center
            gap-2 text-xs font-semibold
            text-emerald-600
            dark:text-emerald-400
          "
        >
          Ajouter une course
          <ArrowRight className="h-4 w-4" />
        </span>
      </button>
    )
  }


  const days =
    getDaysUntil(
      race.date,
    )

  const progress =
    getPreparationProgress(
      race.date,
    )


  return (
    <button
      type="button"
      onClick={onOpenRaces}
      className="
        oc-surface oc-interactive-surface group w-full p-5 text-left
      "
    >
      <div
        className="
          flex items-start
          justify-between gap-4
        "
      >
        <div className="min-w-0">
          <p
            className="
              text-[11px]
              font-semibold uppercase
              tracking-[0.16em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Objectif principal
          </p>

          <h3
            className="
              mt-2 truncate
              text-xl font-bold tracking-[-0.03em] text-[var(--oc-text)]
            "
          >
            {race.name}
          </h3>

          <div
            className="
              mt-1 flex items-center gap-1.5 oc-type-secondary
            "
          >
            <MapPin className="h-3.5 w-3.5" />
            <span className="truncate">
              {race.location}
            </span>
          </div>
        </div>

        <div
          className="
            rounded-xl
            bg-emerald-50
            px-3 py-2
            text-center
            dark:bg-emerald-500/10
          "
        >
          <p
            className="
              oc-type-caption
              font-semibold uppercase
              tracking-wide
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Dans
          </p>

          <p
            className="
              mt-0.5
              text-xl font-bold tabular-nums text-[var(--oc-text)]
            "
          >
            J-{days}
          </p>
        </div>
      </div>


      <div
        className="
          mt-5 grid
          grid-cols-3
          divide-x
          divide-[var(--oc-border)]
        "
      >
        <Metric
          icon={<Route className="h-4 w-4" />}
          value={`${formatNumber(race.distanceKm)} km`}
          label="Distance"
        />

        <Metric
          icon={<Mountain className="h-4 w-4" />}
          value={
            race.elevationGainM
              ? `${Math.round(race.elevationGainM)} m`
              : '—'
          }
          label="D+"
        />

        <Metric
          icon={<Flag className="h-4 w-4" />}
          value={formatDateShort(race.date)}
          label="Date"
        />
      </div>


      <div className="mt-5">
        <div
          className="
            mb-2 flex items-center
            justify-between oc-type-secondary
          "
        >
          <span
            className="
              font-medium text-[var(--oc-muted)]
            "
          >
            Préparation
          </span>

          <span
            className="
              font-semibold tabular-nums text-[var(--oc-text-secondary)]
            "
          >
            {progress} %
          </span>
        </div>

        <div
          className="
            h-1.5 overflow-hidden
            rounded-full
            bg-[var(--oc-surface-muted)]
          "
        >
          <div
            className="
              h-full rounded-full
              bg-emerald-500
            "
            style={{
              width: `${progress}%`,
            }}
          />
        </div>
      </div>


      <div
        className="
          mt-5 flex items-center
          justify-end
        "
      >
        <span
          className="
            flex items-center gap-2
            oc-type-body font-semibold
            text-emerald-600
            dark:text-emerald-400
          "
        >
          Voir l’objectif

          <ArrowRight
            className="
              h-4 w-4
              transition-transform
              group-hover:translate-x-1
            "
          />
        </span>
      </div>
    </button>
  )
}


function Metric({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode
  value: string
  label: string
}) {
  return (
    <div className="px-3 first:pl-0 last:pr-0">
      <div
        className="
          flex items-center gap-1.5
          text-emerald-600
          dark:text-emerald-400
        "
      >
        {icon}

        <span
          className="
            truncate text-sm font-bold text-[var(--oc-text)]
          "
        >
          {value}
        </span>
      </div>

      <p
        className="
          mt-1 oc-type-caption font-medium uppercase tracking-wide
        "
      >
        {label}
      </p>
    </div>
  )
}


function getDaysUntil(
  dateValue: string,
): number {
  const now = new Date()

  now.setHours(
    12, 0, 0, 0,
  )

  const raceDate =
    new Date(
      `${dateValue}T12:00:00`,
    )

  return Math.max(
    0,
    Math.ceil(
      (
        raceDate.getTime()
        - now.getTime()
      )
      / 86400000,
    ),
  )
}


function getPreparationProgress(
  raceDate: string,
): number {
  /*
   * Indicateur visuel provisoire :
   * fenêtre de préparation maximale de 16 semaines.
   *
   * Ce n'est PAS une donnée physiologique ni une
   * décision du moteur de coaching.
   */
  const days =
    getDaysUntil(
      raceDate,
    )

  const preparationWindowDays =
    16 * 7

  const elapsed =
    preparationWindowDays
    - Math.min(
        days,
        preparationWindowDays,
      )

  return Math.max(
    0,
    Math.min(
      100,
      Math.round(
        elapsed
        / preparationWindowDays
        * 100,
      ),
    ),
  )
}


function formatDateShort(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'short',
    },
  ).format(
    new Date(
      `${value}T12:00:00`,
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
  ).format(value)
}
