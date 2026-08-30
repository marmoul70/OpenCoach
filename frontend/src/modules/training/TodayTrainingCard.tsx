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
}


export function TodayTrainingCard({
  sessions,
  onOpenSession,
}: TodayTrainingCardProps) {
  return (
    <section
      aria-label="Entraînement du jour"
      className="
        rounded-2xl
        border
        border-primary/25
        bg-primary/5
        p-4
        sm:p-5
      "
    >
      <div
        className="
          flex
          items-center
          justify-between
          gap-4
        "
      >
        <div>
          <p
            className="
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-primary
            "
          >
            Aujourd’hui
          </p>

          <p
            className="
              mt-1
              text-sm
              text-base-content/55
            "
          >
            Votre entraînement prévu
            pour aujourd’hui.
          </p>
        </div>

        <span
          className="
            badge
            badge-primary
            badge-outline
          "
        >
          {sessions.length} séance{
            sessions.length > 1
              ? 's'
              : ''
          }
        </span>
      </div>

      <div
        className="
          mt-4
          space-y-2
        "
      >
        {sessions.length === 0 && (
          <div
            className="
              rounded-xl
              bg-base-100/70
              px-4 py-3
              text-sm
              text-base-content/55
            "
          >
            Aucune séance prévue aujourd’hui.
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
      onClick={onOpen}
      className="
        flex
        w-full
        items-center
        justify-between
        gap-4
        rounded-xl
        border
        border-base-300
        bg-base-100
        px-4 py-3
        text-left
        transition
        hover:border-primary/40
        hover:bg-base-100
      "
    >
      <div className="min-w-0">
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
              truncate
              font-semibold
              text-base-content
            "
          >
            {session.title}
          </p>

          <span
            className={[
              'badge badge-sm',
              getSessionStatusClass(
                session.status,
              ),
            ].join(' ')}
          >
            {formatSessionStatus(
              session.status,
            )}
          </span>
        </div>

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
            ? (
              ` · ${
                formatTrainingIntensity(
                  session.intensity,
                )
              }`
            )
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


function getSessionStatusClass(
  status: TrainingSession['status'],
): string {
  switch (status) {
    case 'completed':
      return 'badge-success'

    case 'skipped':
      return 'badge-error'

    default:
      return 'badge-warning'
  }
}


function formatSessionStatus(
  status: TrainingSession['status'],
): string {
  switch (status) {
    case 'completed':
      return 'Analysée'

    case 'skipped':
      return 'Non réalisée'

    default:
      return 'À faire'
  }
}
