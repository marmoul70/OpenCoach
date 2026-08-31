import {
  Check,
  Clock3,
  Route,
  X,
} from 'lucide-react'


interface WeeklyLoadCardProps {
  actualPercent?: number

  actualLoad: number
  isCurrentWeek: boolean
  isFutureWeek: boolean

  status: string
  statusLabel: string

  completedCount: number
  remainingCount: number
  skippedCount: number

  remainingSessionsCount: number

  statsLoading: boolean
  totalDistanceLabel: string
  sessionsCount: number

  targetRaceName?: string
  targetRaceDate?: string
}


export function WeeklyLoadCard({
  actualPercent,
  actualLoad,
  isCurrentWeek,
  isFutureWeek,
  statusLabel,
  completedCount,
  remainingCount,
  skippedCount,
  statsLoading,
  totalDistanceLabel,
  sessionsCount,
  targetRaceName,
  targetRaceDate,
}: WeeklyLoadCardProps) {
  const mainValue =
    isCurrentWeek
      && actualPercent !== undefined
      ? `${Math.round(
          actualPercent,
        )} %`
      : `${Math.round(
          actualLoad,
        )}`

  const mainLabel =
    isCurrentWeek
      ? 'objectif réalisé'
      : (
        isFutureWeek
          ? 'charge réalisée'
          : 'charge enregistrée'
      )

  return (
    <section
      aria-label="Synthèse de la semaine"
      className="
        overflow-hidden
        rounded-2xl
        border
        border-base-300
        bg-base-100
        shadow-sm
      "
    >
      <div className="p-4 sm:p-5">
        <div
          className="
            flex
            items-start
            justify-between
            gap-4
          "
        >
          <div>
            <p
              className="
                text-xs
                font-medium
                uppercase
                tracking-wide
                text-base-content/40
              "
            >
              Charge semaine
            </p>

            <div
              className="
                mt-1
                flex
                items-baseline
                gap-1.5
              "
            >
              <span
                className="
                  text-2xl
                  font-bold
                  tabular-nums
                  text-base-content
                "
              >
                {mainValue}
              </span>

              <span
                className="
                  text-xs
                  text-base-content/45
                "
              >
                {mainLabel}
              </span>
            </div>
          </div>

          {isCurrentWeek && (
            <p
              className="
                max-w-32
                text-right
                text-xs
                font-medium
                text-base-content/45
              "
            >
              {statusLabel}
            </p>
          )}
        </div>


        {isCurrentWeek && (
          <progress
            className="
              progress
              progress-primary
              mt-3
              h-2
              w-full
            "
            value={
              actualPercent !== undefined
                ? Math.min(
                    100,
                    Math.max(
                      0,
                      actualPercent,
                    ),
                  )
                : 0
            }
            max={100}
          />
        )}


        <div
          className="
            mt-4
            grid
            grid-cols-3
            divide-x
            divide-base-300
          "
        >
          <WeekMetric
            icon={Check}
            value={completedCount}
            label="Réalisées"
          />

          <WeekMetric
            icon={Clock3}
            value={remainingCount}
            label="À faire"
          />

          <WeekMetric
            icon={X}
            value={skippedCount}
            label="Non faites"
          />
        </div>



      </div>


      <details
        className="
          border-t
          border-base-300
        "
      >
        <summary
          className="
            cursor-pointer
            list-none
            px-4 py-3
            text-sm
            font-medium
            text-base-content/55
            sm:px-5
          "
        >
          Statistiques générales
        </summary>

        <div
          className="
            grid
            grid-cols-2
            border-t
            border-base-300
            divide-x
            divide-base-300
          "
        >
          <OverviewItem
            icon={Route}
            value={
              statsLoading
                ? '…'
                : totalDistanceLabel
            }
            label="Cette année"
          />

          <OverviewItem
            icon={Check}
            value={
              statsLoading
                ? '…'
                : `${sessionsCount}`
            }
            label="Séances"
          />


          {targetRaceName
            && targetRaceDate && (
              <div
                className="
                  col-span-2
                  border-t
                  border-base-300
                  px-4 py-3
                "
              >
                <p
                  className="
                    text-xs
                    font-medium
                    uppercase
                    tracking-wide
                    text-base-content/40
                  "
                >
                  Prochaine course
                </p>

                <div
                  className="
                    mt-1
                    flex
                    items-baseline
                    justify-between
                    gap-3
                  "
                >
                  <p
                    className="
                      min-w-0
                      truncate
                      font-semibold
                      text-base-content
                    "
                  >
                    {targetRaceName}
                  </p>

                  <span
                    className="
                      shrink-0
                      text-xs
                      font-medium
                      text-base-content/50
                    "
                  >
                    {formatRaceDate(
                      targetRaceDate,
                    )}
                  </span>
                </div>
              </div>
            )}
        </div>
      </details>
    </section>
  )
}


function WeekMetric({
  icon: Icon,
  value,
  label,
}: {
  icon: typeof Check
  value: number
  label: string
}) {
  return (
    <div
      className="
        px-2
        text-center
      "
    >
      <div
        className="
          mx-auto
          flex
          items-center
          justify-center
          gap-1
        "
      >
        <Icon
          size={14}
          className="
            text-base-content/40
          "
        />

        <span
          className="
            text-lg
            font-bold
            tabular-nums
            text-base-content
          "
        >
          {value}
        </span>
      </div>

      <p
        className="
          mt-0.5
          text-xs
          text-base-content/45
        "
      >
        {label}
      </p>
    </div>
  )
}


function OverviewItem({
  icon: Icon,
  value,
  label,
}: {
  icon: typeof Route
  value: string
  label: string
}) {
  return (
    <div
      className="
        flex
        items-center
        gap-3
        px-4 py-3
      "
    >
      <Icon
        size={16}
        className="
          shrink-0
          text-primary
        "
      />

      <div className="min-w-0">
        <p
          className="
            font-bold
            text-base-content
          "
        >
          {value}
        </p>

        <p
          className="
            truncate
            text-xs
            text-base-content/40
          "
        >
          {label}
        </p>
      </div>
    </div>
  )
}


function formatRaceDate(
  value: string,
): string {
  const date =
    new Date(
      `${value}T12:00:00`,
    )

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    },
  ).format(
    date,
  )
}
