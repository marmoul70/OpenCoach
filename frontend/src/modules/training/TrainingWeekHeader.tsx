import {
  Check,
  ChevronLeft,
  ChevronRight,
  Dumbbell,
  Moon,
  Route,
} from 'lucide-react'


interface TrainingWeekHeaderProps {
  weekRange: string

  weekTypeLabel?: string
  phaseLabel?: string
  phaseClass?: string
  phaseWeekIndex?: number

  trajectoryMode?:
    | 'maintenance'
    | 'race_preparation'

  targetRaceName?: string
  targetRaceDate?: string
  preparationStartDate?: string

  workCount: number
  restCount: number
  strengthCount: number

  isCurrentWeek: boolean
  isFutureWeek: boolean

  actualPercent?: number
  actualLoad: number
  statusLabel: string

  completedCount: number
  remainingCount: number
  skippedCount: number

  statsLoading: boolean
  totalDistanceLabel: string
  sessionsCount: number

  onPreviousWeek: () => void
  onNextWeek: () => void
  onCurrentWeek: () => void
}


export function TrainingWeekHeader({
  weekRange,

  weekTypeLabel,
  phaseLabel,
  phaseWeekIndex,

  trajectoryMode,


  workCount,
  restCount,
  strengthCount,

  isCurrentWeek,
  isFutureWeek,

  actualPercent,
  actualLoad,
  statusLabel,


  statsLoading,
  totalDistanceLabel,
  sessionsCount,

  onPreviousWeek,
  onNextWeek,
  onCurrentWeek,
}: TrainingWeekHeaderProps) {
  const progress =
    Math.min(
      100,
      Math.max(
        0,
        actualPercent ?? 0,
      ),
    )

  const mainValue =
    isCurrentWeek
      && actualPercent !== undefined
        ? `${Math.round(actualPercent)} %`
        : `${Math.round(actualLoad)}`

  const mainLabel =
    isCurrentWeek
      ? 'objectif réalisé'
      : isFutureWeek
        ? 'charge prévue'
        : 'charge enregistrée'

  const phaseName =
    trajectoryMode === 'maintenance'
      ? 'Développement général'
      : phaseLabel ?? 'Préparation'

  return (
    <header className="training-polish__header mb-4">
        <div
          className="
            grid
            grid-cols-1
            gap-3
            lg:grid-cols-12
          "
        >

          <section
            aria-label="Navigation de la semaine"
            className="
              overflow-hidden
              rounded-[14px]
              border
              border-[var(--oc-border)]
              bg-[var(--oc-surface)]
              shadow-[0_1px_2px_rgba(15,23,42,0.025)]
              dark:border-[var(--oc-border)]
              
              lg:col-span-7
            "
          >
        <div className="p-3.5 sm:p-4">

          <div
            className="
              flex
              items-center
              justify-between
              gap-3
            "
          >
            <button
              type="button"
              onClick={onCurrentWeek}
              className={[
                (
                  'inline-flex items-center gap-1.5 '
                  + 'text-[11px] font-bold uppercase '
                  + 'tracking-[0.11em] transition'
                ),
                isCurrentWeek
                  ? (
                      'text-emerald-600 '
                      + 'dark:text-emerald-400'
                    )
                  : (
                      'text-[var(--oc-text-secondary)] '
                      + 'hover:text-emerald-600 '
                      + ' '
                      + 'dark:hover:text-emerald-400'
                    ),
              ].join(' ')}
            >
              <span
                className={[
                  'h-1.5 w-1.5 rounded-full',
                  isCurrentWeek
                    ? 'bg-emerald-500'
                    : (
                        'bg-[var(--oc-border-strong)] '
                        + ''
                      ),
                ].join(' ')}
              />

              {isCurrentWeek
                ? 'Semaine actuelle'
                : 'Revenir à cette semaine'}
            </button>

            {weekTypeLabel && (
              <span
                className="
                  oc-type-secondary font-medium
                "
              >
                {weekTypeLabel}
              </span>
            )}
          </div>


          <div
                    className="
                      mt-3
                      rounded-[11px]
                      border
                      border-[var(--oc-border)]
                      bg-[var(--oc-surface-muted)]
                      p-1.5
                      
                      
                    "
                  >
                    {/* Desktop */}
                    <div
                      className="
                        hidden
                        items-center
                        gap-3
                        sm:flex
                      "
                    >
                      <button
                        type="button"
                        onClick={onCurrentWeek}
                        className="
                          min-w-0
                          flex-1
                          rounded-[8px]
                          px-2.5
                          py-1.5
                          text-left
                          transition
                          hover:bg-[var(--oc-surface-hover)]
                          dark:hover:bg-[var(--oc-surface-hover)]/[0.035]
                        "
                      >
                        <p
                          className="
                            truncate
                            text-[15px]
                            font-semibold
                            tracking-[-0.025em]
                            text-[var(--oc-text)]
                            
                          "
                        >
                          {cleanWeekRange(
                            weekRange,
                          )}
                        </p>
                      </button>


                      <div
                        className="
                          flex
                          shrink-0
                          items-center
                          overflow-hidden
                          rounded-[9px]
                          border
                          border-[var(--oc-border)]
                          bg-[var(--oc-surface)]
                          shadow-[0_1px_2px_rgba(15,23,42,0.025)]
                          
                          
                        "
                      >
                        <button
                          type="button"
                          aria-label="Semaine précédente"
                          onClick={onPreviousWeek}
                          className="
                            flex
                            h-8
                            w-9
                            items-center
                            justify-center
                            text-[var(--oc-text-secondary)]
                            transition
                            hover:bg-[var(--oc-surface-muted)]
                            hover:text-[var(--oc-text)]
                            dark:hover:bg-[var(--oc-surface-hover)]/[0.05]
                            
                          "
                        >
                          <ChevronLeft
                            className="h-4 w-4"
                          />
                        </button>

                        <span
                          className="
                            h-4
                            w-px
                            bg-[var(--oc-border)]
                            
                          "
                        />

                        <button
                          type="button"
                          aria-label="Semaine suivante"
                          onClick={onNextWeek}
                          className="
                            flex
                            h-8
                            w-9
                            items-center
                            justify-center
                            text-[var(--oc-text-secondary)]
                            transition
                            hover:bg-[var(--oc-surface-muted)]
                            hover:text-[var(--oc-text)]
                            dark:hover:bg-[var(--oc-surface-hover)]/[0.05]
                            
                          "
                        >
                          <ChevronRight
                            className="h-4 w-4"
                          />
                        </button>
                      </div>
                    </div>


                    {/* Mobile */}
                    <div
                      className="
                        flex
                        items-center
                        sm:hidden
                      "
                    >
                      <button
                        type="button"
                        aria-label="Semaine précédente"
                        onClick={onPreviousWeek}
                        className="
                          flex
                          h-8
                          w-8
                          shrink-0
                          items-center
                          justify-center
                          rounded-[8px]
                          text-[var(--oc-text-secondary)]
                          transition
                          active:bg-[var(--oc-surface-hover)]
                          dark:active:bg-[var(--oc-surface-hover)]/[0.04]
                        "
                      >
                        <ChevronLeft
                          className="h-4 w-4"
                        />
                      </button>


                      <button
                        type="button"
                        onClick={onCurrentWeek}
                        className="
                          min-w-0
                          flex-1
                          px-2
                          py-1.5
                          text-center
                        "
                      >
                        <p
                          className="
                            truncate
                            text-[14px]
                            font-semibold
                            tracking-[-0.02em]
                            text-[var(--oc-text)]
                            
                          "
                        >
                          {cleanWeekRange(
                            weekRange,
                          )}
                        </p>
                      </button>


                      <button
                        type="button"
                        aria-label="Semaine suivante"
                        onClick={onNextWeek}
                        className="
                          flex
                          h-8
                          w-8
                          shrink-0
                          items-center
                          justify-center
                          rounded-[8px]
                          text-[var(--oc-text-secondary)]
                          transition
                          active:bg-[var(--oc-surface-hover)]
                          dark:active:bg-[var(--oc-surface-hover)]/[0.04]
                        "
                      >
                        <ChevronRight
                          className="h-4 w-4"
                        />
                      </button>
                    </div>
                  </div>




        </div>

            <div
              className="
                border-t
                border-[var(--oc-border)]
                
              "
            >
        <div
          className="
            border-t
            border-[var(--oc-border)]
            px-3.5
            py-3
            
            sm:px-4
          "
        >
          <div
            className="
              flex
              items-end
              justify-between
              gap-3
            "
          >
            <div>
              <p
                className="
                  text-[10px]
                  font-bold
                  uppercase
                  tracking-[0.12em]
                  text-[var(--oc-text-secondary)]
                  
                "
              >
                Phase d'entraînement
              </p>

              <p
                className="
                  mt-1
                  text-[14px]
                  font-semibold
                  text-emerald-600
                  dark:text-emerald-400
                "
              >
                {phaseLabel ?? 'Base'}
              </p>
            </div>

            {phaseWeekIndex !== undefined && (
              <p
                className="
                  text-[11px]
                  font-semibold
                  text-[var(--oc-text-secondary)]
                  
                "
              >
                Semaine {phaseWeekIndex}
              </p>
            )}
          </div>


          <div
            className="
              mt-2
              h-[3px]
              overflow-hidden
              rounded-full
              bg-[var(--oc-surface-muted)]
              
            "
          >
            <div
              className="
                h-full
                rounded-full
                bg-emerald-500
              "
              style={{
                width: phaseProgress(
                  phaseWeekIndex,
                ),
              }}
            />
          </div>

          <p
            className="
              mt-1.5
              oc-type-secondary
            "
          >
            {phaseName}
          </p>
        </div>
            </div>

          </section>


          <section
            aria-label="Résumé de la semaine"
            className="
              overflow-hidden
              rounded-[14px]
              border
              border-[var(--oc-border)]
              bg-[var(--oc-surface)]
              shadow-[0_1px_2px_rgba(15,23,42,0.025)]
              
              
              lg:col-span-5
            "
          >

            <div
              className="
                border-b
                border-[var(--oc-border)]
                px-3.5
                py-3
                
                sm:px-4
              "
            >
              <p
                className="
                  text-[10px]
                  font-bold
                  uppercase
                  tracking-[0.12em]
                  text-[var(--oc-text-secondary)]
                  
                "
              >
                Cette semaine
              </p>

              <div
                className="
                  mt-3
                  grid
                  grid-cols-3
                  divide-x
                  divide-[var(--oc-border)]
                  
                "
              >
                <PlanningMetric
                  icon={Route}
                  value={workCount}
                  label="Séances"
                />

                <PlanningMetric
                  icon={Moon}
                  value={restCount}
                  label="Repos"
                />

                <PlanningMetric
                  icon={Dumbbell}
                  value={strengthCount}
                  label="Renfo"
                />
              </div>
            </div>

        <div
          className="
            border-t
            border-[var(--oc-border)]
            px-3.5
            py-3
            
            sm:px-4
          "
        >
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
                  text-[10px]
                  font-bold
                  uppercase
                  tracking-[0.12em]
                  text-[var(--oc-text-secondary)]
                  
                "
              >
                Charge
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
                    text-[23px]
                    font-bold
                    tabular-nums
                    tracking-[-0.04em]
                    text-[var(--oc-text)]
                    
                  "
                >
                  {mainValue}
                </span>

                <span
                  className="
                    text-[11px]
                    text-[var(--oc-text-secondary)]
                    
                  "
                >
                  {mainLabel}
                </span>
              </div>
            </div>


            {isCurrentWeek && (
              <span
                className="
                  rounded-full
                  bg-emerald-50
                  px-2
                  py-1
                  text-[10px]
                  font-semibold
                  text-emerald-700
                  dark:bg-emerald-500/10
                  dark:text-emerald-400
                "
              >
                {statusLabel}
              </span>
            )}
          </div>


          {isCurrentWeek && (
            <div
              className="
                mt-2.5
                h-[4px]
                overflow-hidden
                rounded-full
                bg-[var(--oc-surface-muted)]
                
              "
            >
              <div
                className="
                  h-full
                  rounded-full
                  bg-emerald-500
                  transition-[width]
                "
                style={{
                  width: `${progress}%`,
                }}
              />
            </div>
          )}


          {/* RÉALISÉ / RESTANT / RATÉ */}

          <div
              className="
                mt-2
                grid
                grid-cols-2
                items-center
                justify-items-center
                divide-x
                divide-[var(--oc-border)]
                
              "
            >
              <div className="
                  training-general-stat
                  flex
                  min-h-[38px]
                  w-full
                  items-center
                  justify-center
                  py-0.5
                  text-center
                ">
                <OverviewItem
                icon={Route}
                value={
                  statsLoading
                    ? '…'
                    : totalDistanceLabel
                }
                label="Cette année"
              />
              </div>

              <div className="
                  training-general-stat
                  flex
                  min-h-[38px]
                  w-full
                  items-center
                  justify-center
                  py-0.5
                  text-center
                ">
                <OverviewItem
                icon={Check}
                value={
                  statsLoading
                    ? '…'
                    : `${sessionsCount}`
                }
                label="Séances"
              />
              </div>


            </div>
        </div>

          </section>

        </div>




    </header>
  )
}


function PlanningMetric({
  icon: Icon,
  value,
  label,
}: {
  icon: typeof Route
  value: number
  label: string
}) {
  return (
    <div
      className="
        flex
        items-center
        justify-center
        gap-2
        px-2
      "
    >
      <Icon
        className="
          hidden
          h-3.5
          w-3.5
          text-[var(--oc-text-secondary)]
          sm:block
        "
      />

      <div className="text-center sm:text-left">
        <p
          className="
            text-[var(--oc-type-section-title)]
            font-bold
            leading-none
            tabular-nums
            text-[var(--oc-text)]
            
          "
        >
          {value}
        </p>

        <p
          className="
            mt-1
            text-[10px]
            font-medium
            uppercase
            tracking-[0.05em]
            text-[var(--oc-text-secondary)]
            
          "
        >
          {label}
        </p>
      </div>
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
        gap-2
        px-3.5
        py-2.5
        sm:px-4
      "
    >
      <Icon
        className="
          h-3.5
          w-3.5
          shrink-0
          text-emerald-500
        "
      />

      <div>
        <p
          className="
            text-[12px]
            font-bold
            text-[var(--oc-text)]
            
          "
        >
          {value}
        </p>

        <p
          className="
            text-[9px]
            text-[var(--oc-text-secondary)]
          "
        >
          {label}
        </p>
      </div>
    </div>
  )
}


function cleanWeekRange(
  value: string,
): string {
  return value
    .replace(
      /^Semaine\s+du\s+/i,
      '',
    )
    .replace(
      /^du\s+/i,
      '',
    )
}


function phaseProgress(
  phaseWeekIndex?: number,
): string {
  if (
    phaseWeekIndex === undefined
  ) {
    return '25%'
  }

  const percentage =
    Math.min(
      100,
      Math.max(
        18,
        phaseWeekIndex * 18,
      ),
    )

  return `${percentage}%`
}
