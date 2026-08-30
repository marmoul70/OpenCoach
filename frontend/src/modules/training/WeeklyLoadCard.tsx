import {
  Check,
  Clock3,
  Route,
  X,
} from 'lucide-react'


interface WeeklyLoadCardProps {
  actualPercent?: number
  projectedPercent?: number

  status: string
  statusLabel: string

  completedCount: number
  remainingCount: number
  skippedCount: number
  supplementaryCount: number
  restCount: number

  remainingSessionsCount: number

  statsLoading: boolean
  totalDistanceLabel: string
  sessionsCount: number
}


export function WeeklyLoadCard({
  actualPercent,
  projectedPercent,
  status,
  statusLabel,
  completedCount,
  remainingCount,
  skippedCount,
  supplementaryCount,
  restCount,
  remainingSessionsCount,
  statsLoading,
  totalDistanceLabel,
  sessionsCount,
}: WeeklyLoadCardProps) {
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
      <div className="px-4 py-4 sm:px-5">
        <div
          className="
            flex flex-col
            gap-3
            sm:flex-row
            sm:items-center
            sm:justify-between
          "
        >
          <div>
            <p
              className="
                text-xs
                font-medium
                text-base-content/45
              "
            >
              Charge semaine
            </p>

            <p
              className="
                mt-0.5
                text-xl
                font-bold
                tabular-nums
              "
            >
              {actualPercent !== undefined
                ? `${Math.round(
                    actualPercent,
                  )} %`
                : '—'}

              <span
                className="
                  ml-1
                  text-xs
                  font-medium
                  text-base-content/40
                "
              >
                réalisé
              </span>
            </p>
          </div>

          <div
            className="
              flex
              flex-wrap
              gap-1.5
              sm:justify-end
            "
          >
            <span
              className={
                getWeeklyStatusClass(
                  status,
                )
              }
            >
              {statusLabel}
            </span>

            {completedCount > 0 && (
              <span
                className="
                  badge
                  badge-success
                  badge-outline
                  gap-1
                "
              >
                <Check
                  size={12}
                  strokeWidth={2.5}
                />

                {completedCount}{' '}
                réalisée{
                  completedCount > 1
                    ? 's'
                    : ''
                }
              </span>
            )}

            {remainingCount > 0 && (
              <span
                className="
                  badge
                  badge-primary
                  badge-outline
                  gap-1
                "
              >
                <Clock3
                  size={12}
                  strokeWidth={2}
                />

                {remainingCount}{' '}
                à faire
              </span>
            )}

            {skippedCount > 0 && (
              <span
                className="
                  badge
                  badge-error
                  badge-outline
                  gap-1
                "
              >
                <X
                  size={12}
                  strokeWidth={2}
                />

                {skippedCount}{' '}
                non réalisée{
                  skippedCount > 1
                    ? 's'
                    : ''
                }
              </span>
            )}

            {supplementaryCount > 0 && (
              <span
                className="
                  badge
                  badge-outline
                "
              >
                {supplementaryCount}{' '}
                supplémentaire{
                  supplementaryCount > 1
                    ? 's'
                    : ''
                }
              </span>
            )}

            {restCount > 0 && (
              <span
                className="
                  badge
                  badge-ghost
                "
              >
                {restCount}{' '}
                repos
              </span>
            )}
          </div>
        </div>

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

        <div
          className="
            mt-2
            flex
            flex-wrap
            items-center
            gap-x-3
            gap-y-1
            text-xs
            text-base-content/50
          "
        >
          <span>
            {projectedPercent !== undefined
              ? `${Math.round(
                  projectedPercent,
                )} % projeté`
              : 'Projection indisponible'}
          </span>

          <span aria-hidden="true">
            ·
          </span>

          <span>
            {remainingSessionsCount}{' '}
            séance{
              remainingSessionsCount > 1
                ? 's'
                : ''
            } restante{
              remainingSessionsCount > 1
                ? 's'
                : ''
            }
          </span>
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
            text-base-content/60
            sm:px-5
          "
        >
          Statistiques générales
        </summary>

        <div
          className="
            grid
            border-t
            border-base-300
            divide-y
            divide-base-300
            sm:grid-cols-2
            sm:divide-x
            sm:divide-y-0
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
            label="Séances réalisées"
          />
        </div>
      </details>
    </section>
  )
}


interface OverviewItemProps {
  icon: typeof Route
  value: string
  label: string
}


function OverviewItem({
  icon: Icon,
  value,
  label,
}: OverviewItemProps) {
  return (
    <div
      className="
        flex
        min-w-0
        items-center
        gap-3
        px-4 py-3
        sm:px-5
      "
    >
      <div
        className="
          flex
          size-8
          shrink-0
          items-center
          justify-center
          rounded-lg
          bg-primary/10
          text-primary
        "
      >
        <Icon
          size={16}
          strokeWidth={2}
        />
      </div>

      <div className="min-w-0">
        <p
          className="
            font-bold
            text-base
            text-base-content
          "
        >
          {value}
        </p>

        <p
          className="
            mt-0.5
            truncate
            text-xs
            text-base-content/45
          "
        >
          {label}
        </p>
      </div>
    </div>
  )
}


function getWeeklyStatusClass(
  status: string,
): string {
  if (status === 'aligned') {
    return (
      'badge '
      + 'badge-success '
      + 'badge-outline'
    )
  }

  if (status === 'over_target') {
    return (
      'badge '
      + 'badge-warning '
      + 'badge-outline'
    )
  }

  return 'badge badge-outline'
}
