import {
  ArrowRight,
  CalendarDays,
  Check,
  Clock3,
  Dumbbell,
  Footprints,
  Mountain,
} from 'lucide-react'

import {
  useTrainingSessions,
} from './trainingStore'

import type {
  TrainingSession,
} from './types'


interface TrainingWidgetProps {
  onClick: () => void
}


export function TrainingWidget({
  onClick,
}: TrainingWidgetProps) {
  const {
    sessions,
    loading,
    error,
  } = useTrainingSessions()

  const today =
    formatLocalDate(
      new Date(),
    )

  const todaySessions =
    sessions.filter(
      (item) =>
        item.date === today
        && item.type !== 'supplementary',
    )


  if (loading) {
    return (
      <div
        className="
          flex min-h-48
          w-full items-center
          justify-center
          rounded-2xl
          bg-[#141917]
        "
      >
        <span
          className="
            h-5
            w-5
            animate-spin
            rounded-full
            border-2
            border-white/[0.10]
            border-t-emerald-400
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
          rounded-2xl
          border border-red-500/20
          bg-[#171313]
          p-5
          text-white
        "
      >
        <p
          className="
            text-xs
            font-semibold
            uppercase
            tracking-[0.14em]
            text-red-400
          "
        >
          Séance du jour
        </p>

        <p className="mt-2 font-semibold">
          Données indisponibles
        </p>

        <p
          className="
            mt-2
            text-sm
            leading-6
            text-white/55
          "
        >
          {error}
        </p>
      </div>
    )
  }


  return (
    <button
      type="button"
      onClick={onClick}
      className="
        group
        relative
        w-full
        overflow-hidden
        rounded-2xl
        border
        border-white/[0.07]
        bg-[#141917]
        p-0
        text-left
        text-white
        shadow-[0_14px_45px_rgba(4,12,8,0.13)]
        transition
        duration-200
        hover:-translate-y-0.5
        hover:bg-[#181e1b]
        focus-visible:outline-none
        focus-visible:ring-2
        focus-visible:ring-emerald-500/40
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          -right-16
          -top-20
          h-48
          w-48
          rounded-full
          bg-emerald-500/[0.08]
          blur-3xl
        "
      />

      <div
        className="
          relative
          p-5
          sm:p-6
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
            <div
              className="
                flex
                items-center
                gap-2
                text-[11px]
                font-semibold
                uppercase
                tracking-[0.16em]
                text-emerald-400
              "
            >
              <CalendarDays
                className="h-3.5 w-3.5"
              />

              Aujourd’hui
            </div>

            <h3
              className="
                mt-2
                text-xl
                font-bold
                tracking-[-0.025em]
                sm:text-2xl
              "
            >
              {todaySessions.length > 0
                ? getPrimaryTitle(
                    todaySessions[0],
                  )
                : 'Journée de récupération'}
            </h3>

            <p
              className="
                mt-1
                text-sm
                text-white/45
              "
            >
              {todaySessions.length > 0
                ? (
                    todaySessions.length > 1
                      ? `${todaySessions.length} séances prévues`
                      : todaySessions[0].title
                  )
                : 'Aucune séance programmée aujourd’hui.'}
            </p>
          </div>

          <div
            className="
              flex h-10 w-10
              shrink-0
              items-center
              justify-center
              rounded-xl
              bg-white/[0.06]
              text-white/60
            "
          >
            {todaySessions.length > 0
              ? getSessionIcon(
                  todaySessions[0],
                )
              : (
                  <Check
                    className="h-5 w-5"
                  />
                )}
          </div>
        </div>


        {todaySessions.length > 0 && (
          <>
            <div
              className="
                mt-6
                grid
                grid-cols-2
                gap-3
                sm:grid-cols-3
              "
            >
              <TrainingMetric
                icon={
                  <Clock3
                    className="h-4 w-4"
                  />
                }
                label="Durée"
                value={
                  `${todaySessions.reduce(
                    (total, session) =>
                      total
                      + session.durationMinutes,
                    0,
                  )} min`
                }
              />

              <TrainingMetric
                label="Séances"
                value={
                  `${todaySessions.length}`
                }
              />

              <div className="hidden sm:block">
                <TrainingMetric
                  label="Statut"
                  value={
                    resolveOverallStatus(
                      todaySessions,
                    )
                  }
                />
              </div>
            </div>


            {todaySessions.length > 1 && (
              <div
                className="
                  mt-5
                  divide-y
                  divide-white/[0.07]
                  border-t
                  border-white/[0.07]
                "
              >
                {todaySessions.map(
                  (
                    session,
                    index,
                  ) => (
                    <div
                      key={
                        session.id
                        ?? `${session.date}-${index}`
                      }
                      className="
                        flex
                        items-center
                        gap-3
                        py-3
                      "
                    >
                      <div
                        className="
                          min-w-0
                          flex-1
                        "
                      >
                        <p
                          className="
                            truncate
                            text-sm
                            font-semibold
                          "
                        >
                          {getPrimaryTitle(
                            session,
                          )}
                        </p>

                        <p
                          className="
                            mt-0.5
                            truncate
                            text-xs
                            text-white/40
                          "
                        >
                          {session.title}
                        </p>
                      </div>

                      <span
                        className="
                          text-xs
                          font-medium
                          text-white/55
                        "
                      >
                        {session.durationMinutes}
                        {' '}min
                      </span>
                    </div>
                  ),
                )}
              </div>
            )}


            <div
              className="
                mt-6
                flex
                items-center
                justify-between
                gap-4
              "
            >
              <StatusPill
                status={
                  resolveOverallStatusRaw(
                    todaySessions,
                  )
                }
              />

              <span
                className="
                  flex
                  items-center
                  gap-2
                  text-sm
                  font-semibold
                  text-emerald-400
                "
              >
                Voir la séance

                <ArrowRight
                  className="
                    h-4 w-4
                    transition-transform
                    group-hover:translate-x-1
                  "
                />
              </span>
            </div>
          </>
        )}


        {todaySessions.length === 0 && (
          <div
            className="
              mt-6
              flex
              items-center
              justify-between
            "
          >
            <span
              className="
                rounded-full
                bg-emerald-500/10
                px-3 py-1.5
                text-xs
                font-semibold
                text-emerald-400
              "
            >
              Récupération
            </span>

            <ArrowRight
              className="
                h-4 w-4
                text-white/30
                transition-transform
                group-hover:translate-x-1
              "
            />
          </div>
        )}
      </div>
    </button>
  )
}


function TrainingMetric({
  icon,
  label,
  value,
}: {
  icon?: React.ReactNode
  label: string
  value: string
}) {
  return (
    <div
      className="
        rounded-xl
        bg-white/[0.045]
        px-3.5
        py-3
      "
    >
      <div
        className="
          flex
          items-center
          gap-1.5
          text-[11px]
          text-white/35
        "
      >
        {icon}

        {label}
      </div>

      <p
        className="
          mt-1
          text-base
          font-bold
          tabular-nums
          text-white
        "
      >
        {value}
      </p>
    </div>
  )
}


function StatusPill({
  status,
}: {
  status:
    | 'completed'
    | 'skipped'
    | 'planned'
}) {
  if (status === 'completed') {
    return (
      <span
        className="
          rounded-full
          bg-emerald-500/10
          px-3 py-1.5
          text-xs
          font-semibold
          text-emerald-400
        "
      >
        Réalisée
      </span>
    )
  }

  if (status === 'skipped') {
    return (
      <span
        className="
          rounded-full
          bg-red-500/10
          px-3 py-1.5
          text-xs
          font-semibold
          text-red-400
        "
      >
        Non réalisée
      </span>
    )
  }

  return (
    <span
      className="
        rounded-full
        bg-amber-400/10
        px-3 py-1.5
        text-xs
        font-semibold
        text-amber-300
      "
    >
      À faire
    </span>
  )
}


function getPrimaryTitle(
  session: TrainingSession,
): string {
  return formatActivityType(
    session.sportType,
    session.type,
  )
}


function getSessionIcon(
  session: TrainingSession,
): React.ReactNode {
  const sport =
    session.sportType.toLowerCase()

  if (
    sport.includes('trail')
  ) {
    return (
      <Mountain className="h-5 w-5" />
    )
  }

  if (
    sport.includes('strength')
    || session.type.includes('strength')
  ) {
    return (
      <Dumbbell className="h-5 w-5" />
    )
  }

  return (
    <Footprints className="h-5 w-5" />
  )
}


function resolveOverallStatusRaw(
  sessions: TrainingSession[],
): 'completed' | 'skipped' | 'planned' {
  if (
    sessions.every(
      (session) =>
        session.status === 'completed',
    )
  ) {
    return 'completed'
  }

  if (
    sessions.some(
      (session) =>
        session.status === 'planned',
    )
  ) {
    return 'planned'
  }

  return 'skipped'
}


function resolveOverallStatus(
  sessions: TrainingSession[],
): string {
  const status =
    resolveOverallStatusRaw(
      sessions,
    )

  if (status === 'completed') {
    return 'Terminée'
  }

  if (status === 'skipped') {
    return 'Non réalisée'
  }

  return 'À faire'
}


function formatActivityType(
  sportType: string,
  type: string,
): string {
  const value =
    sportType.toLowerCase()

  const labels:
    Record<string, string> = {
      run: 'Course',
      running: 'Course',
      trailrunning: 'Trail',
      trail_running: 'Trail',
      strength: 'Renforcement',
      strength_training: 'Renforcement',
      bike: 'Vélo',
      cycling: 'Vélo',
      walking: 'Marche',
      hiking: 'Randonnée',
      swimming: 'Natation',
    }

  return labels[value]
    ?? sportType
    ?? type
}


function formatLocalDate(
  date: Date,
): string {
  const year =
    date.getFullYear()

  const month =
    String(
      date.getMonth()
      + 1,
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

  return (
    `${year}-${month}-${day}`
  )
}
