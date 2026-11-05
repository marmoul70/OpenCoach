import {
  ArrowRight,
  Check,
  Dumbbell,
  Footprints,
  Moon,
} from 'lucide-react'

import {
  useTrainingSessions,
} from '../training/trainingStore'

import type {
  TrainingSession,
} from '../training/types'


interface DashboardWeekStripProps {
  onOpenTraining: () => void
}


export function DashboardWeekStrip({
  onOpenTraining,
}: DashboardWeekStripProps) {
  const {
    sessions,
    loading,
    error,
  } = useTrainingSessions()

  const week =
    getWeekDays(
      new Date(),
    )


  if (loading) {
    return (
      <div
        className="
          flex min-h-40 items-center justify-center oc-surface
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
        <p className="text-sm font-semibold text-red-500">
          Semaine indisponible
        </p>
      </div>
    )
  }


  return (
    <button
      type="button"
      onClick={onOpenTraining}
      className="
        oc-surface oc-interactive-surface group w-full p-5 text-left
      "
    >
      <div
        className="
          grid grid-cols-7
          gap-1.5
          sm:gap-2
        "
      >
        {week.map(
          (day) => {
            const daySessions =
              sessions.filter(
                (session) =>
                  session.date
                  === day.date
                  && session.type
                  !== 'supplementary',
              )

            return (
              <WeekDay
                key={day.date}
                label={day.label}
                dayNumber={day.dayNumber}
                isToday={day.isToday}
                sessions={daySessions}
              />
            )
          },
        )}
      </div>


      <div
        className="
          mt-5 flex
          items-center justify-between
          border-t
          border-[var(--oc-border)]
          pt-4
        "
      >
        <div>
          <p
            className="
              oc-type-body font-semibold text-[var(--oc-text)]
            "
          >
            {getWeekSummary(
              sessions,
              week,
            )}
          </p>

          <p
            className="
              mt-0.5 oc-type-secondary
            "
          >
            Programme de la semaine en cours
          </p>
        </div>

        <ArrowRight
          className="
            h-4 w-4
            text-emerald-600
            transition-transform
            group-hover:translate-x-1
            dark:text-emerald-400
          "
        />
      </div>
    </button>
  )
}


function WeekDay({
  label,
  dayNumber,
  isToday,
  sessions,
}: {
  label: string
  dayNumber: number
  isToday: boolean
  sessions: TrainingSession[]
}) {
  const primary =
    sessions.find(
      (session) =>
        session.type !== 'rest',
    )

  const completed =
    sessions.length > 0
    && sessions
      .filter(
        (session) =>
          session.type !== 'rest',
      )
      .every(
        (session) =>
          session.status === 'completed',
      )


  return (
    <div className="min-w-0 text-center">
      <p
        className={[
          (
            'text-[10px] font-semibold '
            + 'uppercase tracking-wide'
          ),
          isToday
            ? 'text-emerald-600 dark:text-emerald-400'
            : 'text-[var(--oc-muted)]',
        ].join(' ')}
      >
        {label}
      </p>

      <div
        className={[
          (
            'mx-auto mt-1.5 '
            + 'flex h-10 w-10 '
            + 'items-center justify-center '
            + 'rounded-xl '
            + 'text-sm font-bold '
            + 'transition'
          ),
          isToday
            ? (
                'bg-emerald-600 text-white '
                + 'shadow-sm '
                + 'dark:bg-emerald-500'
              )
            : (
                'bg-[var(--oc-surface-muted)] text-[var(--oc-text-secondary)] '
                + ''
                + ''
              ),
        ].join(' ')}
      >
        {dayNumber}
      </div>

      <div
        className="
          mt-2 flex h-5
          items-center justify-center
        "
      >
        {completed ? (
          <Check
            className="
              h-3.5 w-3.5
              text-emerald-500
            "
          />
        ) : primary ? (
          getIcon(
            primary,
          )
        ) : (
          <Moon
            className="
              h-3.5 w-3.5
              text-[var(--oc-muted-soft)]
            "
          />
        )}
      </div>
    </div>
  )
}


function getIcon(
  session: TrainingSession,
): React.ReactNode {
  if (
    session.type.includes(
      'strength',
    )
  ) {
    return (
      <Dumbbell
        className="
          h-3.5 w-3.5
          text-violet-500
        "
      />
    )
  }

  return (
    <Footprints
      className="
        h-3.5 w-3.5
        text-emerald-500
      "
    />
  )
}


function getWeekSummary(
  sessions: TrainingSession[],
  week: Array<{
    date: string
  }>,
): string {
  const dates =
    new Set(
      week.map(
        (day) => day.date,
      ),
    )

  const weekSessions =
    sessions.filter(
      (session) =>
        dates.has(
          session.date,
        )
        && session.type
        !== 'rest'
        && session.type
        !== 'supplementary',
    )

  const completed =
    weekSessions.filter(
      (session) =>
        session.status === 'completed',
    ).length

  return (
    `${completed}/${weekSessions.length} `
    + 'séances réalisées'
  )
}


function getWeekDays(
  today: Date,
): Array<{
  date: string
  label: string
  dayNumber: number
  isToday: boolean
}> {
  const day =
    today.getDay()

  const offset =
    day === 0
      ? -6
      : 1 - day

  const monday =
    new Date(today)

  monday.setHours(
    12, 0, 0, 0,
  )

  monday.setDate(
    today.getDate()
    + offset,
  )

  const labels = [
    'Lun',
    'Mar',
    'Mer',
    'Jeu',
    'Ven',
    'Sam',
    'Dim',
  ]

  const todayKey =
    formatLocalDate(
      today,
    )

  return labels.map(
    (
      label,
      index,
    ) => {
      const date =
        new Date(monday)

      date.setDate(
        monday.getDate()
        + index,
      )

      const dateKey =
        formatLocalDate(
          date,
        )

      return {
        date: dateKey,
        label,
        dayNumber:
          date.getDate(),
        isToday:
          dateKey === todayKey,
      }
    },
  )
}


function formatLocalDate(
  date: Date,
): string {
  const year =
    date.getFullYear()

  const month =
    String(
      date.getMonth() + 1,
    ).padStart(
      2,
      '0',
    )

  const day =
    String(
      date.getDate(),
    ).padStart(
      2,
      '0',
    )

  return `${year}-${month}-${day}`
}
