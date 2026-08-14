import { useState } from 'react'
import {
  CalendarDays,
  Check,
  Clock3,
  Mountain,
  Route,
  X,
} from 'lucide-react'

import { Modal } from '../../components/ui/Modal'
import { TrainingDetails } from './TrainingDetails'
import { useTrainingSessions } from './trainingStore'
import type { TrainingSession } from './types'

const dayLabels = [
  'Lundi',
  'Mardi',
  'Mercredi',
  'Jeudi',
  'Vendredi',
  'Samedi',
  'Dimanche',
]

export function TrainingWeek() {
  const {
    sessions,
    updateSessionStatus,
  } = useTrainingSessions()
  const [selectedSessionId, setSelectedSessionId] = useState<
    string | null
  >(null)

  const sessionsByDay = getWeekSessions(sessions)

  const selectedSession = selectedSessionId
    ? sessions.find(
        (session) => session.id === selectedSessionId,
      )
    : undefined

  function openSession(sessionId: string) {
    setSelectedSessionId(sessionId)
  }

  function closeSession() {
    setSelectedSessionId(null)
  }


  return (
    <main>
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:py-8">
        <header className="mb-8">
          <div className="flex items-start gap-4">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <CalendarDays size={24} strokeWidth={2} />
            </div>

            <div>
              <h1 className="text-3xl font-bold tracking-tight text-base-content">
                Entraînement
              </h1>

              <p className="mt-1 text-sm text-base-content/60">
                Votre semaine d'entraînement et vos séances prévues.
              </p>
            </div>
          </div>
        </header>

        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold text-base-content">
                Cette semaine
              </h2>

              <p className="mt-1 text-sm text-base-content/60">
                Vue hebdomadaire
              </p>
            </div>

            <span className="badge badge-outline">
              {sessions.filter(
                (session) => session.status === 'planned',
              ).length}{' '}
              séances prévues
            </span>
          </div>

          <div className="grid gap-3 md:grid-cols-7">
            {sessionsByDay.map(
              ({ label, session, isToday }) => (
                <DayCard
                  key={label}
                  label={label}
                  session={session}
                  isToday={isToday}
                  onOpen={
                    session
                      ? () => openSession(session.id)
                      : undefined
                  }
                />
              ),
            )}
          </div>
        </section>
      </div>

      {selectedSession && (
        <Modal
          title={selectedSession.title}
          open
          onClose={closeSession}
        >
          <TrainingDetails
            session={selectedSession}
            onStatusChange={(status) => {
              updateSessionStatus(selectedSession.id, status)
              closeSession()
            }}
          />
        </Modal>
      )}
    </main>
  )
}

interface DayCardProps {
  label: string
  session?: TrainingSession
  isToday: boolean
  onOpen?: () => void
}

function DayCard({
  label,
  session,
  isToday,
  onOpen,
}: DayCardProps) {
  return (
    <article
      className={[
        'card border bg-base-100 shadow-sm',
        isToday
          ? 'border-primary ring-1 ring-primary/20'
          : 'border-base-300',
      ].join(' ')}
    >
      <div className="card-body gap-3 p-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-base-content/50">
              {label}
            </p>

            {isToday && (
              <span className="badge badge-primary badge-sm mt-1">
                Aujourd'hui
              </span>
            )}
          </div>

          {session && (
            <StatusBadge status={session.status} />
          )}
        </div>

        {!session || session.type === 'rest' ? (
          <div className="flex min-h-32 flex-col items-center justify-center rounded-xl bg-base-200 px-3 text-center">
            <span className="text-sm font-semibold text-base-content/70">
              Repos
            </span>

            <span className="mt-1 text-xs text-base-content/50">
              Récupération
            </span>

            {session && onOpen && (
              <button
                type="button"
                onClick={onOpen}
                className="btn btn-ghost btn-xs mt-3"
              >
                Voir le détail
              </button>
            )}
          </div>
        ) : (
          <button
            type="button"
            onClick={onOpen}
            className="flex min-h-32 flex-col rounded-xl bg-base-200 p-3 text-left transition hover:bg-base-300"
          >
            <div>
              <h3 className="font-semibold leading-tight text-base-content">
                {session.title}
              </h3>

              <p className="mt-1 text-xs text-base-content/50">
                {session.intensity}
                {session.heartRateZone
                  ? ` · ${session.heartRateZone}`
                  : ''}
              </p>
            </div>

            <div className="mt-auto space-y-2 pt-4">
              <MiniMetric
                icon={Clock3}
                value={`${session.durationMinutes} min`}
              />

              {session.distanceKm !== undefined && (
                <MiniMetric
                  icon={Route}
                  value={`${session.distanceKm} km`}
                />
              )}

              {session.elevationGainM !== undefined && (
                <MiniMetric
                  icon={Mountain}
                  value={`${session.elevationGainM} m D+`}
                />
              )}
            </div>
          </button>
        )}
      </div>
    </article>
  )
}

function MiniMetric({
  icon: Icon,
  value,
}: {
  icon: typeof Clock3
  value: string
}) {
  return (
    <div className="flex items-center gap-2 text-xs text-base-content/60">
      <Icon className="h-3.5 w-3.5 shrink-0" />
      <span>{value}</span>
    </div>
  )
}

function StatusBadge({
  status,
}: {
  status: TrainingSession['status']
}) {
  if (status === 'completed') {
    return (
      <span className="badge badge-success badge-sm gap-1">
        <Check className="h-3 w-3" />
        Réalisée
      </span>
    )
  }

  if (status === 'skipped') {
    return (
      <span className="badge badge-error badge-sm gap-1">
        <X className="h-3 w-3" />
        Non réalisée
      </span>
    )
  }

  return (
    <span className="badge badge-warning badge-sm">
      À faire
    </span>
  )
}

function getWeekSessions(
  sessions: TrainingSession[],
) {
  const today = new Date()
  const currentDay = today.getDay()
  const mondayOffset =
    currentDay === 0 ? -6 : 1 - currentDay

  const monday = new Date(today)
  monday.setDate(today.getDate() + mondayOffset)

  return dayLabels.map((label, index) => {
    const date = new Date(monday)
    date.setDate(monday.getDate() + index)

    const dateString = date.toISOString().slice(0, 10)

    return {
      label,
      session: sessions.find(
        (item) => item.date === dateString,
      ),
      isToday:
        dateString ===
        today.toISOString().slice(0, 10),
    }
  })
}
