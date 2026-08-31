import {
  Plus,
} from 'lucide-react'

import type {
  TrainingSession,
} from './types'

import {
  formatTrainingIntensity,
} from './intensity'


interface TodayTrainingCardProps {
  sessions: TrainingSession[]

  onOpenSession: (
    sessionId: string,
  ) => void

  onAddSession: () => void
}


export function TodayTrainingCard({
  sessions,
  onOpenSession,
  onAddSession,
}: TodayTrainingCardProps) {
  return (
    <section
      aria-label="Entraînement du jour"
      className="
        rounded-2xl
        border
        border-primary/25
        bg-primary/5
        shadow-sm
        ring-1
        ring-primary/10
      "
    >
      <div
        className="
          grid
          gap-4
          p-4
          md:grid-cols-[150px_minmax(0,1fr)_auto]
          md:items-start
        "
      >
        <div>
          <div
            className="
              flex
              flex-wrap
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
              Aujourd’hui
            </p>

            <span
              className="
                badge
                badge-primary
                badge-sm
              "
            >
              Aujourd&apos;hui
            </span>
          </div>

          <p
            className="
              mt-1
              text-xs
              text-base-content/50
            "
          >
            Séance du jour
          </p>
        </div>

        <div
          className="
            min-w-0
            space-y-2
          "
        >
          {sessions.length === 0 && (
            <div
              className="
                rounded-xl
                border
                border-base-300
                bg-base-100
                px-4
                py-3
                shadow-sm
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
          )}

          {sessions.map(
            (session) => (
              <TodayTrainingSession
                key={session.id}
                session={session}
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
    </section>
  )
}


function TodayTrainingSession({
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
        flex-col
        gap-3
        rounded-xl
        border
        border-base-300
        bg-base-100
        px-4
        py-3
        shadow-sm
        text-left
        transition
        hover:bg-base-200/60
        sm:flex-row
        sm:items-center
        sm:justify-between
      "
    >
      <div className="min-w-0">
        <p
          className="
            truncate
            font-semibold
            text-base-content
          "
        >
          {session.title}
        </p>

        <p
          className="
            mt-1
            text-sm
            text-base-content/50
          "
        >
          {session.type === 'rest'
            ? 'Repos'
            : `${session.durationMinutes} min`}

          {session.intensity
            ? ` · ${
                formatTrainingIntensity(
                  session.intensity,
                )
              }`
            : ''}

          {session.heartRateZone
            ? ` · ${session.heartRateZone}`
            : ''}
        </p>
      </div>

      <span
        className="
          shrink-0
          text-sm
          font-semibold
          text-primary
        "
      >
        Ouvrir
      </span>
    </button>
  )
}
