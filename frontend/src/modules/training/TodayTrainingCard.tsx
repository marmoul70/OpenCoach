import {
  ArrowRight,
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
        rounded-[14px]
        border
        border-emerald-500/15
        bg-[#111814]
        p-3.5
        text-white
        shadow-[0_8px_28px_rgba(15,23,42,0.08)]
      "
    >
      <div
        className="
          flex
          items-center
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
              text-emerald-400
            "
          >
            Aujourd’hui
          </p>

          <p
            className="
              mt-0.5
              text-[12px]
              text-slate-500
            "
          >
            Séance prioritaire
          </p>
        </div>

        <button
          type="button"
          onClick={onAddSession}
          className="
            flex
            h-8
            items-center
            gap-1.5
            rounded-[9px]
            border
            border-white/[0.07]
            bg-white/[0.035]
            px-2.5
            text-[12px]
            font-medium
            text-slate-300
            transition
            hover:bg-white/[0.06]
          "
        >
          <Plus className="h-3 w-3" />
        </button>
      </div>


      <div className="mt-3 space-y-2">
        {sessions.length === 0 && (
          <div
            className="
              rounded-[10px]
              border
              border-white/[0.06]
              bg-white/[0.035]
              px-3
              py-2.5
            "
          >
            <p
              className="
                text-[14px]
                font-semibold
                text-slate-200
              "
            >
              Repos
            </p>

            <p
              className="
                mt-0.5
                text-[12px]
                text-slate-500
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
        group
        flex
        w-full
        items-center
        justify-between
        gap-4
        rounded-[10px]
        border
        border-white/[0.07]
        bg-white/[0.04]
        px-3
        py-2.5
        text-left
        transition
        hover:border-emerald-500/20
        hover:bg-white/[0.055]
      "
    >
      <div className="min-w-0">
        <p
          className="
            truncate
            text-[15px]
            font-semibold
            text-white
          "
        >
          {session.title}
        </p>

        <p
          className="
            mt-0.5
            text-[12.5px]
            text-slate-400
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

      <ArrowRight
        className="
          h-4
          w-4
          shrink-0
          text-emerald-400
          transition-transform
          group-hover:translate-x-0.5
        "
      />
    </button>
  )
}
