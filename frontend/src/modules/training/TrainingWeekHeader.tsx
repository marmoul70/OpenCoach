import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react'


interface TrainingWeekHeaderProps {
  weekRange: string

  weekTypeLabel?: string

  phaseLabel?: string
  phaseClass?: string

  phaseWeekIndex?: number

  trajectoryMode?: 'maintenance' | 'race_preparation'

  targetRaceName?: string
  targetRaceDate?: string
  preparationStartDate?: string

  workCount: number
  restCount: number
  strengthCount: number

  isCurrentWeek: boolean

  onPreviousWeek: () => void
  onNextWeek: () => void
  onCurrentWeek: () => void
}


export function TrainingWeekHeader({
  weekRange,
  weekTypeLabel,
  phaseLabel,
  phaseClass,
  phaseWeekIndex,
  trajectoryMode,
  targetRaceName,
  targetRaceDate,
  preparationStartDate,
  workCount,
  restCount,
  strengthCount,
  isCurrentWeek,
  onPreviousWeek,
  onNextWeek,
  onCurrentWeek,
}: TrainingWeekHeaderProps) {
  return (
    <header className="mb-5">
      <div
        className="
          flex
          items-center
          justify-between
          gap-4
        "
      >
        <div>
          <h1
            className="
              text-2xl
              font-bold
              tracking-tight
              text-base-content
              sm:text-3xl
            "
          >
            Entraînement
          </h1>

          <p
            className="
              mt-0.5
              text-xs
              text-base-content/45
            "
          >
            Planning et suivi
          </p>
        </div>

        <div
          className="
            flex
            size-10
            shrink-0
            items-center
            justify-center
            rounded-xl
            bg-primary/10
            text-primary
          "
        >
          <CalendarDays
            size={21}
            strokeWidth={2}
          />
        </div>
      </div>

      <div
        className="
          mt-4
          rounded-2xl
          border
          border-base-300
          bg-base-100
          px-2 py-2
          shadow-sm
        "
      >
        <div
          className="
            flex
            items-center
            justify-between
            gap-2
          "
        >
          <button
            type="button"
            aria-label="Semaine précédente"
            className="
              btn
              btn-ghost
              btn-sm
              btn-square
              shrink-0
            "
            onClick={onPreviousWeek}
          >
            <ChevronLeft size={19} />
          </button>

          <button
            type="button"
            className="
              min-w-0
              flex-1
              rounded-xl
              px-2 py-1.5
              text-center
              transition
              hover:bg-base-200/60
            "
            onClick={onCurrentWeek}
          >
            <p
              className="
                truncate
                text-sm
                font-semibold
                text-base-content
              "
            >
              {weekRange}
            </p>

            <p
              className={[
                (
                  'mt-0.5 text-xs '
                  + 'font-medium'
                ),
                isCurrentWeek
                  ? 'text-primary'
                  : 'text-base-content/40',
              ].join(' ')}
            >
              {isCurrentWeek
                ? 'Aujourd’hui'
                : 'Revenir à aujourd’hui'}
            </p>
          </button>

          <button
            type="button"
            aria-label="Semaine suivante"
            className="
              btn
              btn-ghost
              btn-sm
              btn-square
              shrink-0
            "
            onClick={onNextWeek}
          >
            <ChevronRight size={19} />
          </button>
        </div>

        <div
          className="
            mt-1.5
            flex
            flex-wrap
            items-center
            justify-center
            gap-x-2
            gap-y-1
            text-xs
            text-base-content/45
          "
        >
          <span>
            <strong
              className="
                font-semibold
                text-base-content/65
              "
            >
              {workCount}
            </strong>{' '}
            travail
          </span>

          <span aria-hidden="true">
            ·
          </span>

          <span>
            <strong
              className="
                font-semibold
                text-base-content/65
              "
            >
              {restCount}
            </strong>{' '}
            repos
          </span>

          {strengthCount > 0 && (
            <>
              <span aria-hidden="true">
                ·
              </span>

              <span>
                <strong
                  className="
                    font-semibold
                    text-base-content/65
                  "
                >
                  {strengthCount}
                </strong>{' '}
                renforcement
              </span>
            </>
          )}
        </div>

        {(weekTypeLabel
          || phaseLabel
          || phaseWeekIndex !== undefined) && (
          <div
            className="
              mt-2
              border-t
              border-base-300/70
              px-2 pt-2
            "
          >
            <div
              className="
                flex
                flex-wrap
                items-center
                justify-center
                gap-x-2
                gap-y-1
                text-xs
              "
            >
              {weekTypeLabel && (
                <span
                  className="
                    font-semibold
                    text-base-content/75
                  "
                >
                  {weekTypeLabel}
                </span>
              )}

              {phaseLabel && (
                <>
                  <span
                    className="
                      text-base-content/25
                    "
                  >
                    ·
                  </span>

                  <span
                    className="
                      text-base-content/50
                    "
                  >
                    {trajectoryMode
                      === 'maintenance'
                        ? 'Développement général'
                        : (
                            <>
                              Phase{' '}
                              <strong
                                className={
                                  phaseClass
                                  ?? ''
                                }
                              >
                                {phaseLabel}
                              </strong>
                            </>
                          )}
                  </span>
                </>
              )}

              {phaseWeekIndex !== undefined && (
                <>
                  <span
                    className="
                      text-base-content/25
                    "
                  >
                    ·
                  </span>

                  <span
                    className="
                      text-base-content/50
                    "
                  >
                    Semaine{' '}
                    <strong
                      className="
                        text-base-content/75
                      "
                    >
                      {phaseWeekIndex}
                    </strong>
                  </span>
                </>
              )}
            </div>

            {targetRaceName
              && targetRaceDate && (
                <div
                  className="
                    mt-2
                    text-center
                    text-xs
                    leading-5
                    text-base-content/45
                  "
                >
                  <p>
                    Objectif :{' '}
                    <strong
                      className="
                        font-semibold
                        text-base-content/65
                      "
                    >
                      {targetRaceName}
                    </strong>
                    {' · '}
                    {formatCompactDate(
                      targetRaceDate,
                    )}
                  </p>

                  {trajectoryMode
                    === 'maintenance'
                    && preparationStartDate && (
                      <p>
                        Préparation course à partir du{' '}
                        <strong
                          className="
                            font-semibold
                            text-base-content/60
                          "
                        >
                          {formatCompactDate(
                            preparationStartDate,
                          )}
                        </strong>
                      </p>
                    )}
                </div>
              )}
          </div>
        )}
      </div>
    </header>
  )
}

function formatCompactDate(
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
