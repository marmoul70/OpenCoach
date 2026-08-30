import {
  Check,
  Clock3,
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
    <section>
      <div
        className="
          mb-3
          flex
          items-center
          justify-between
        "
      >
        <div>
          <h2
            className="
              font-semibold
              text-base-content
            "
          >
            Cette semaine
          </h2>

          <p
            className="
              mt-0.5
              text-sm
              text-base-content/45
            "
          >
            Les autres séances du planning.
          </p>
        </div>
      </div>

      <div className="space-y-3">
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
          'rounded-2xl border '
          + 'bg-base-100 shadow-sm'
        ),
        isToday
          ? (
            'border-primary '
            + 'ring-1 '
            + 'ring-primary/20'
          )
          : 'border-base-300',
      ].join(' ')}
    >
      <div
        className="
          grid gap-4
          p-4
          md:grid-cols-[150px_minmax(0,1fr)_auto]
          md:items-start
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
              session={
                restSession
              }
              onOpen={() =>
                onOpenSession(
                  restSession.id,
                )
              }
            />
          )}

          {trainingSessions.length
            === 0
            && !restSession && (
              <EmptyDay />
            )}

          {trainingSessions.map(
            (session) => (
              <SessionRow
                key={
                  session.id
                }
                session={
                  session
                }
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
            flex
            md:justify-end
          "
        >
          <button
            type="button"
            className="
              btn
              btn-ghost
              btn-sm
              gap-1
              text-base-content/60
            "
            onClick={
              onAddSession
            }
          >
            <Plus
              size={15}
            />

            Ajouter
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
          flex flex-wrap
          items-center
          gap-2
        "
      >
        <p
          className="
            text-sm
            font-bold
            uppercase
            tracking-wide
            text-base-content
          "
        >
          {label}
        </p>

        {isToday && (
          <span
            className="
              badge
              badge-primary
              badge-sm
            "
          >
            Aujourd&apos;hui
          </span>
        )}
      </div>

      <p
        className="
          mt-1
          text-xs
          text-base-content/50
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
      onClick={
        onOpen
      }
      className="
        flex
        w-full
        items-center
        justify-between
        gap-4
        rounded-xl
        bg-base-200/70
        px-4 py-3
        text-left
        transition
        hover:bg-base-200
      "
    >
      <div className="min-w-0">
        <div
          className="
            flex flex-wrap
            items-center
            gap-2
          "
        >
          <h3
            className="
              font-semibold
              text-base-content
            "
          >
            Repos
          </h3>

          <span
            className="
              badge
              badge-ghost
              badge-sm
            "
          >
            OpenCoach
          </span>
        </div>

        <p
          className="
            mt-1
            text-sm
            text-base-content/50
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
        rounded-xl
        bg-base-200/50
        px-4 py-3
      "
    >
      <p
        className="
          font-medium
          text-base-content/70
        "
      >
        Repos
      </p>

      <p
        className="
          mt-1
          text-sm
          text-base-content/45
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
      onClick={
        onOpen
      }
      className={[
        (
          'flex w-full flex-col gap-3 '
          + 'rounded-xl border px-4 py-3'
        ),
        'text-left transition',
        (
          'sm:flex-row sm:items-center '
          + 'sm:justify-between'
        ),
        session.status
        === 'completed'
          ? (
            'border-success/25 '
            + 'bg-success/5 '
            + 'hover:bg-success/10'
          )
          : '',
        session.status
        === 'skipped'
          ? (
            'border-error/25 '
            + 'bg-error/5 '
            + 'hover:bg-error/10'
          )
          : '',
        (
          session.status
          !== 'completed'
          && session.status
          !== 'skipped'
        )
          ? (
            'border-base-300 '
            + 'hover:bg-base-200/60'
          )
          : '',
      ].join(' ')}
    >
      <div className="min-w-0">
        <div
          className="
            flex flex-wrap
            items-center
            gap-2
          "
        >
          <h3
            className="
              truncate
              font-semibold
              text-base-content
            "
          >
            {session.title}
          </h3>

          <SessionStatusLabel
            status={
              session.status
            }
          />

          {physiologicalTestProposal && (
            <span
              className="
                badge
                badge-primary
                badge-outline
                badge-sm
                gap-1
              "
              title={
                physiologicalTestProposal
                  .recommendation
              }
            >
              Test proposé · {
                formatPhysiologicalTestProtocol(
                  physiologicalTestProposal
                    .protocol,
                )
              }
            </span>
          )}

          {supplementary && (
            <span
              className="
                badge
                badge-outline
                badge-sm
              "
            >
              Supplémentaire
            </span>
          )}
        </div>

        <p
          className="
            mt-1
            text-sm
            text-base-content/50
          "
        >
          {formatSportType(
            session.sportType,
          )}
        </p>
      </div>

      <div
        className="
          flex flex-wrap
          items-center
          gap-x-4
          gap-y-2
          text-sm
        "
      >
        <InlineValue
          value={
            `${session.durationMinutes} min`
          }
        />

        {session.distanceKm
          !== undefined && (
            <InlineValue
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
          <InlineValue
            value={
              formatTrainingIntensity(
                session.intensity,
              )
            }
          />
        )}

        {session.heartRateZone && (
          <InlineValue
            value={
              session.heartRateZone
            }
          />
        )}
      </div>
    </button>
  )
}


function SessionStatusLabel({
  status,
}: {
  status:
    TrainingSession['status']
}) {
  if (status === 'completed') {
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
          strokeWidth={3}
        />

        Réalisée
      </span>
    )
  }

  if (status === 'skipped') {
    return (
      <span
        className="
          badge
          badge-error
          badge-outline
          badge-sm
          gap-1
        "
      >
        <X
          size={11}
          strokeWidth={2.5}
        />

        Non réalisée
      </span>
    )
  }

  return (
    <span
      className="
        badge
        badge-primary
        badge-outline
        badge-sm
      "
    >
      À faire
    </span>
  )
}


function InlineValue({
  value,
}: {
  value: string
}) {
  return (
    <span
      className="
        text-base-content/60
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
  if (status === 'completed') {
    return (
      <span
        className="
          badge
          badge-success
          badge-sm
          gap-1
        "
        title="Séance réalisée"
      >
        <Check size={12} />

        Réalisée
      </span>
    )
  }

  if (status === 'skipped') {
    return (
      <span
        className="
          badge
          badge-error
          badge-sm
          gap-1
        "
        title="Séance non réalisée"
      >
        <X size={12} />

        Non réalisée
      </span>
    )
  }

  return (
    <span
      className="
        badge
        badge-warning
        badge-sm
        gap-1
      "
      title="Séance à faire"
    >
      <Clock3 size={12} />

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
