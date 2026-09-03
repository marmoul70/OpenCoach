import {
  Check,
  Clock3,
  FlaskConical,
  Plus,
  X,
} from 'lucide-react'

import {
  formatPhysiologicalTestProtocol,
} from '../physiological-tests'

import type {
  PhysiologicalTestProposal,
} from '../physiological-tests'

import type {
  TrainingSession,
} from './types'

import {
  formatTrainingIntensity,
} from './intensity'


export interface TrainingWeekDay {
  label: string
  date: string

  sessions:
    TrainingSession[]

  isToday: boolean
}


interface TrainingWeekDaysProps {
  days: TrainingWeekDay[]

  physiologicalTestProposals:
    PhysiologicalTestProposal[]

  onOpenSession: (
    sessionId: string,
  ) => void

  onAddSession: (
    date: string,
  ) => void
}


export function TrainingWeekDays({
  days,
  physiologicalTestProposals,
  onOpenSession,
  onAddSession,
}: TrainingWeekDaysProps) {
  return (
    <section
      aria-label="Planning de la semaine"
      className="training-polish__week"
    >
      <div
        className="
          mb-2.5
          flex
          items-end
          justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-[11px]
              font-bold
              uppercase
              tracking-[0.14em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Planning
          </p>

          <h2
            className="
              mt-0.5
              text-[17px]
              font-semibold
              tracking-[-0.02em]
              text-slate-950
              dark:text-white
            "
          >
            Cette semaine
          </h2>

          <p
            className="
              mt-0.5
              text-[12px]
              text-slate-400
              dark:text-slate-500
            "
          >
            Les autres séances du planning
          </p>
        </div>
      </div>


      <div
        className="
          space-y-2.5
        "
      >
        {days.map(
          ({
            label,
            date,
            sessions,
            isToday,
          }) => (
            <DayRow
              key={date}
              label={label}
              date={date}
              sessions={sessions}
              physiologicalTestProposals={
                physiologicalTestProposals
              }
              isToday={isToday}
              onOpenSession={
                onOpenSession
              }
              onAddSession={() =>
                onAddSession(
                  date,
                )
              }
            />
          ),
        )}
      </div>
    </section>
  )
}


interface DayRowProps {
  label: string
  date: string

  sessions:
    TrainingSession[]

  physiologicalTestProposals:
    PhysiologicalTestProposal[]

  isToday: boolean

  onOpenSession: (
    sessionId: string,
  ) => void

  onAddSession: () => void
}


function DayRow({
  label,
  date,
  sessions,
  physiologicalTestProposals,
  isToday,
  onOpenSession,
  onAddSession,
}: DayRowProps) {
  const restSession =
    sessions.find(
      (session) =>
        session.type
        === 'rest',
    )

  const trainingSessions =
    sessions.filter(
      (session) =>
        session.type
        !== 'rest',
    )

  return (
    <article
      className={[
        (
          'training-polish__day relative overflow-hidden rounded-[14px] '
          + 'border bg-white '
          + 'shadow-[0_1px_2px_rgba(15,23,42,0.025)] '
          + 'dark:bg-[#151b1f]'
        ),
        isToday
          ? (
              'border-emerald-500/25 '
              + 'dark:border-emerald-500/20'
            )
          : (
              'border-black/[0.07] '
              + 'dark:border-white/[0.075]'
            ),
      ].join(' ')}
    >
      <div
        className="
          grid
          gap-3
          p-3
          pr-14
          md:grid-cols-[125px_minmax(0,1fr)_48px]
          md:items-stretch
          md:pr-3
        "
      >
        <DayHeading
          label={label}
          date={date}
          isToday={isToday}
        />


        <div
          className="
            min-w-0
            space-y-2
          "
        >
          {restSession && (
            <RestSessionRow
              session={restSession}
              onOpen={() =>
                onOpenSession(
                  restSession.id,
                )
              }
            />
          )}

          {trainingSessions.length === 0
            && !restSession && (
              <EmptyDay />
            )}

          {trainingSessions.map(
            (session) => (
              <SessionRow
                key={session.id}
                session={session}
                physiologicalTestProposal={
                  physiologicalTestProposals.find(
                    (proposal) =>
                      proposal.target_session_id
                      === session.id,
                  )
                  ?? null
                }
                onOpen={() =>
                  onOpenSession(
                    session.id,
                  )
                }
              />
            ),
          )}
        </div>


        <div
          className="
            absolute
            right-3
            top-3
            z-10

            md:static
            md:flex
            md:h-full
            md:items-center
            md:justify-center
            md:border-l
            md:border-black/[0.06]
            md:pl-3
            md:dark:border-white/[0.06]
          "
        >
          <button
            type="button"
            onClick={onAddSession}
            className="
              flex
              h-8
              items-center
              gap-1.5
              rounded-[9px]
              px-2.5
              text-[12px]
              font-medium
              border
              border-emerald-500/40
              bg-transparent
              text-emerald-600
              transition
              hover:border-emerald-500/60
              hover:bg-emerald-500/[0.06]
              hover:text-emerald-700
              dark:border-emerald-400/35
              dark:text-emerald-400
              dark:hover:border-emerald-400/55
              dark:hover:bg-emerald-400/[0.08]
              dark:hover:text-emerald-300
            "
          >
            <Plus
              className="
                h-3
                w-3
              "
            />
          </button>
        </div>
      </div>
    </article>
  )
}


function DayHeading({
  label,
  date,
  isToday,
}: {
  label: string
  date: string
  isToday: boolean
}) {
  return (
    <div>
      <div
        className="
          flex
          flex-wrap
          items-center
          gap-1.5
        "
      >
        <p
          className="
            text-[13.5px]
            font-bold
            uppercase
            tracking-[0.08em]
            text-slate-800
            dark:text-slate-200
          "
        >
          {label}
        </p>

        {isToday && (
          <span
            className="
              rounded-full
              bg-emerald-50
              px-1.5
              py-0.5
              text-[10px]
              font-bold
              text-emerald-700
              dark:bg-emerald-500/10
              dark:text-emerald-400
            "
          >
            Aujourd’hui
          </span>
        )}
      </div>

      <p
        className="
          mt-1
          text-[11.5px]
          text-slate-400
          dark:text-slate-500
        "
      >
        {formatLongDate(
          date,
        )}
      </p>
    </div>
  )
}


function RestSessionRow({
  session,
  onOpen,
}: {
  session: TrainingSession
  onOpen: () => void
}) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="
        flex
        w-full
        items-center
        justify-between
        gap-3
        rounded-[10px]
        border
        border-slate-200/70
        bg-slate-50
        px-3
        py-2.5
        text-left
        transition
        hover:border-slate-300
        hover:bg-slate-100
        dark:border-white/[0.055]
        dark:bg-white/[0.025]
        dark:hover:border-white/[0.08]
        dark:hover:bg-white/[0.04]
      "
    >
      <div className="min-w-0">
        <div
          className="
            flex
            flex-wrap
            items-center
            gap-1.5
          "
        >
          <h3
            className="
              text-[13.5px]
              font-semibold
              text-slate-700
              dark:text-slate-300
            "
          >
            Repos
          </h3>

          <span
            className="
              rounded-full
              bg-slate-200/70
              px-1.5
              py-0.5
              text-[10px]
              font-semibold
              text-slate-500
              dark:bg-white/[0.05]
              dark:text-slate-500
            "
          >
            OpenCoach
          </span>
        </div>

        <p
          className="
            mt-0.5
            text-[11.5px]
            text-slate-400
            dark:text-slate-500
          "
        >
          Récupération recommandée
        </p>
      </div>

      <StatusBadge
        status={
          session.status
        }
      />
    </button>
  )
}


function EmptyDay() {
  return (
    <div
      className="
        rounded-[10px]
        border
        border-dashed
        border-slate-200
        bg-slate-50/60
        px-3
        py-2.5
        dark:border-white/[0.055]
        dark:bg-white/[0.018]
      "
    >
      <p
        className="
          text-[13px]
          font-medium
          text-slate-500
          dark:text-slate-400
        "
      >
        Repos
      </p>

      <p
        className="
          mt-0.5
          text-[11.5px]
          text-slate-400
          dark:text-slate-600
        "
      >
        Aucune séance prévue
      </p>
    </div>
  )
}


function SessionRow({
  session,
  physiologicalTestProposal,
  onOpen,
}: {
  session: TrainingSession

  physiologicalTestProposal:
    PhysiologicalTestProposal
    | null

  onOpen: () => void
}) {
  const supplementary =
    session.type
    === 'supplementary'

  return (
    <button
      type="button"
      onClick={onOpen}
      className={[
        sessionVisualClass(
          session,
        ),
        (
          'flex w-full flex-col gap-2.5 '
          + 'rounded-[10px] border '
          + 'px-3 py-2.5 text-left '
          + 'transition '
          + 'sm:flex-row sm:items-center '
          + 'sm:justify-between'
        ),

        session.status === 'completed'
          ? (
              'border-emerald-500/15 '
              + 'bg-emerald-50/60 '
              + 'hover:bg-emerald-50 '
              + 'dark:bg-emerald-500/[0.045] '
              + 'dark:hover:bg-emerald-500/[0.065]'
            )
          : '',

        session.status === 'skipped'
          ? (
              'border-red-500/12 '
              + 'bg-red-50/50 '
              + 'hover:bg-red-50 '
              + 'dark:bg-red-500/[0.035] '
              + 'dark:hover:bg-red-500/[0.055]'
            )
          : '',

        (
          session.status !== 'completed'
          && session.status !== 'skipped'
        )
          ? (
              'border-black/[0.065] '
              + 'bg-white '
              + 'hover:border-black/[0.10] '
              + 'hover:bg-slate-50 '
              + 'dark:border-white/[0.065] '
              + 'dark:bg-white/[0.02] '
              + 'dark:hover:border-white/[0.09] '
              + 'dark:hover:bg-white/[0.035]'
            )
          : '',
      ].join(' ')}
    >
      <div
        className="
          min-w-0
          flex-1
        "
      >
        <div
          className="
            flex
            flex-wrap
            items-center
            gap-1.5
          "
        >
          <h3
            className="
              truncate
              text-[13.5px]
              font-semibold
              text-slate-900
              dark:text-slate-100
            "
          >
            {session.title}
          </h3>

          <SessionStatusLabel
            status={
              session.status
            }
          />

          {supplementary && (
            <span
              className="
                rounded-full
                border
                border-slate-200
                px-1.5
                py-0.5
                text-[10px]
                font-semibold
                text-slate-500
                dark:border-white/[0.07]
                dark:text-slate-500
              "
            >
              Supplémentaire
            </span>
          )}
        </div>

        <p
          className="
            mt-0.5
            text-[11.5px]
            text-slate-400
            dark:text-slate-500
          "
        >
          {formatSportType(
            session.sportType,
          )}
        </p>


        {physiologicalTestProposal && (
          <div
            className="
              mt-2
              inline-flex
              items-center
              gap-1.5
              rounded-[8px]
              border
              border-emerald-500/15
              bg-emerald-50
              px-2
              py-1
              text-[10.5px]
              font-semibold
              text-emerald-700
              dark:bg-emerald-500/[0.07]
              dark:text-emerald-400
            "
            title={
              physiologicalTestProposal
                .recommendation
            }
          >
            <FlaskConical
              className="
                h-3
                w-3
              "
            />

            Test proposé ·{' '}
            {
              formatPhysiologicalTestProtocol(
                physiologicalTestProposal
                  .protocol,
              )
            }
          </div>
        )}
      </div>


      <div
        className="
          flex
          flex-wrap
          items-center
          gap-x-2
          gap-y-1
          text-[11px]
          text-slate-500
          dark:text-slate-400
          sm:justify-end
        "
      >
        <MetricPill
          value={
            `${session.durationMinutes} min`
          }
        />

        {session.distanceKm
          !== undefined && (
            <MetricPill
              value={
                `${
                  formatNumber(
                    session.distanceKm,
                  )
                } km`
              }
            />
          )}

        {session.intensity && (
          <MetricPill
            value={
              formatTrainingIntensity(
                session.intensity,
              )
            }
          />
        )}

        {session.heartRateZone && (
          <MetricPill
            value={
              session.heartRateZone
            }
          />
        )}
      </div>
    </button>
  )
}



function sessionVisualClass(
  session: TrainingSession,
): string {
  const signature = [
    session.type,
    session.sportType,
    session.title,
    session.intensity ?? '',
  ]
    .join(' ')
    .toLowerCase()

  if (
    signature.includes('strength')
    || signature.includes('renfo')
    || signature.includes('muscu')
  ) {
    return (
      'border-l-[3px] '
      + 'border-l-sky-400/70 '
      + 'dark:border-l-sky-400/60'
    )
  }

  if (
    signature.includes('long')
    || signature.includes('trail')
  ) {
    return (
      'border-l-[3px] '
      + 'border-l-orange-500/65 '
      + 'dark:border-l-orange-400/60'
    )
  }

  if (
    signature.includes('interval')
    || signature.includes('fraction')
    || signature.includes('threshold')
    || signature.includes('seuil')
    || signature.includes('tempo')
    || signature.includes('vo2')
    || signature.includes('vma')
  ) {
    return (
      'border-l-[3px] '
      + 'border-l-amber-400/75 '
      + 'dark:border-l-amber-400/65'
    )
  }

  if (
    signature.includes('easy')
    || signature.includes('endurance')
    || signature.includes('recovery')
    || signature.includes('récup')
  ) {
    return (
      'border-l-[3px] '
      + 'border-l-emerald-500/60 '
      + 'dark:border-l-emerald-400/55'
    )
  }

  return (
    'border-l-[3px] '
    + 'border-l-slate-300/80 '
    + 'dark:border-l-slate-600'
  )
}

function SessionStatusLabel({
  status,
}: {
  status:
    TrainingSession['status']
}) {
  if (
    status === 'completed'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          bg-emerald-100
          px-1.5
          py-0.5
          text-[10px]
          font-bold
          text-emerald-700
          dark:bg-emerald-500/10
          dark:text-emerald-400
        "
      >
        <Check
          className="
            h-2.5
            w-2.5
          "
        />

        Réalisée
      </span>
    )
  }


  if (
    status === 'skipped'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          bg-red-100
          px-1.5
          py-0.5
          text-[10px]
          font-bold
          text-red-600
          dark:bg-red-500/10
          dark:text-red-400
        "
      >
        <X
          className="
            h-2.5
            w-2.5
          "
        />

        Non réalisée
      </span>
    )
  }


  return (
    <span
      className="
        inline-flex
        items-center
        gap-1
        rounded-full
        bg-amber-50
        px-1.5
        py-0.5
        text-[10px]
        font-bold
        text-amber-600
        dark:bg-amber-500/[0.08]
        dark:text-amber-400
      "
    >
      <Clock3
        className="
          h-2.5
          w-2.5
        "
      />

      À faire
    </span>
  )
}


function MetricPill({
  value,
}: {
  value: string
}) {
  return (
    <span
      className="
        rounded-[7px]
        bg-slate-100
        px-2
        py-1
        text-[11px]
        font-medium
        text-slate-500
        dark:bg-white/[0.045]
        dark:text-slate-400
      "
    >
      {value}
    </span>
  )
}


function StatusBadge({
  status,
}: {
  status:
    TrainingSession['status']
}) {
  if (
    status === 'completed'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          bg-emerald-100
          px-2
          py-1
          text-[10px]
          font-bold
          text-emerald-700
          dark:bg-emerald-500/10
          dark:text-emerald-400
        "
      >
        <Check
          className="
            h-2.5
            w-2.5
          "
        />

        Réalisée
      </span>
    )
  }


  if (
    status === 'skipped'
  ) {
    return (
      <span
        className="
          inline-flex
          items-center
          gap-1
          rounded-full
          bg-red-100
          px-2
          py-1
          text-[10px]
          font-bold
          text-red-600
          dark:bg-red-500/10
          dark:text-red-400
        "
      >
        <X
          className="
            h-2.5
            w-2.5
          "
        />

        Non réalisée
      </span>
    )
  }


  return (
    <span
      className="
        inline-flex
        items-center
        gap-1
        rounded-full
        bg-amber-50
        px-2
        py-1
        text-[10px]
        font-bold
        text-amber-600
        dark:bg-amber-500/[0.08]
        dark:text-amber-400
      "
    >
      <Clock3
        className="
          h-2.5
          w-2.5
        "
      />

      À faire
    </span>
  )
}


function formatLongDate(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'long',
    },
  ).format(
    new Date(
      `${dateString}T12:00:00`,
    ),
  )
}


function formatSportType(
  sportType: string,
): string {
  if (
    sportType.toLowerCase()
    === 'run'
  ) {
    return 'Course à pied'
  }

  return sportType
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
