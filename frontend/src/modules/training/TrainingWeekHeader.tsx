import {
  CalendarDays,
} from 'lucide-react'


interface TrainingWeekHeaderProps {
  weekRange: string

  weekTypeLabel?: string
  weekTypeClass?: string

  phaseLabel?: string
  phaseClass?: string

  phaseWeekIndex?: number
}


export function TrainingWeekHeader({
  weekRange,
  weekTypeLabel,
  weekTypeClass,
  phaseLabel,
  phaseClass,
  phaseWeekIndex,
}: TrainingWeekHeaderProps) {
  return (
    <header className="mb-6">
      <div
        className="
          flex
          items-start
          justify-between
          gap-6
        "
      >
        <div className="min-w-0">
          <p
            className="
              text-sm
              text-base-content/60
            "
          >
            {weekRange}
          </p>

          {(weekTypeLabel
            || phaseLabel
            || phaseWeekIndex !== undefined) && (
            <div
              className="
                mt-3
                flex
                items-center
                justify-between
                gap-4
              "
            >
              <div
                className="
                  flex flex-wrap
                  items-center
                  gap-x-4
                  gap-y-2
                "
              >
                {weekTypeLabel
                  && weekTypeClass && (
                    <div
                      className={
                        weekTypeClass
                      }
                    >
                      <span
                        className="
                          size-2
                          rounded-full
                          bg-current
                          opacity-80
                        "
                      />

                      <span
                        className="
                          font-semibold
                        "
                      >
                        {weekTypeLabel}
                      </span>
                    </div>
                  )}

                {phaseLabel
                  && phaseClass && (
                    <div
                      className="
                        flex
                        items-center
                        gap-1.5
                        text-sm
                      "
                    >
                      <span
                        className="
                          text-base-content/40
                        "
                      >
                        Phase
                      </span>

                      <span
                        className={
                          phaseClass
                        }
                      >
                        {phaseLabel}
                      </span>
                    </div>
                  )}
              </div>

              {phaseWeekIndex !== undefined && (
                <div
                  className="
                    shrink-0
                    text-right
                  "
                >
                  <span
                    className="
                      text-xs
                      text-base-content/40
                    "
                  >
                    Semaine
                  </span>

                  <span
                    className="
                      ml-1.5
                      font-semibold
                      tabular-nums
                      text-base-content/80
                    "
                  >
                    {phaseWeekIndex}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        <div
          className="
            flex
            shrink-0
            items-center
            gap-3
          "
        >
          <div className="text-right">
            <h1
              className="
                text-3xl
                font-bold
                tracking-tight
                text-base-content
              "
            >
              Entraînement
            </h1>
          </div>

          <div
            className="
              flex
              size-11
              shrink-0
              items-center
              justify-center
              rounded-2xl
              bg-primary/10
              text-primary
            "
          >
            <CalendarDays
              size={24}
              strokeWidth={2}
            />
          </div>
        </div>
      </div>
    </header>
  )
}
