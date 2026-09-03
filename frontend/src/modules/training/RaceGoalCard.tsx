import {
  Trophy,
} from 'lucide-react'


interface RaceGoalCardProps {
  name?: string
  details?: string
}


export function RaceGoalCard({
  name,
  details,
}: RaceGoalCardProps) {
  return (
    <section
      aria-label="Objectif principal"
      className="
        rounded-2xl
        border
        border-slate-200 dark:border-white/[0.08]
        bg-white dark:bg-[#141a1e]
        px-4 py-4
        sm:px-5
      "
    >
      <div
        className="
          flex
          items-center
          gap-3
        "
      >
        <div
          className="
            flex
            size-10
            shrink-0
            items-center
            justify-center
            rounded-xl
            bg-emerald-500/10 dark:bg-emerald-400/10
            text-emerald-600 dark:text-emerald-400
          "
        >
          <Trophy
            size={19}
            strokeWidth={2}
          />
        </div>

        <div className="min-w-0 flex-1">
          <p
            className="
              text-xs
              font-semibold
              uppercase
              tracking-wide
              text-slate-400 dark:text-slate-500
            "
          >
            Objectif
          </p>

          <p
            className="
              mt-0.5
              truncate
              font-semibold
              text-slate-800 dark:text-slate-100
            "
          >
            {
              name
              ?? 'Aucun objectif prioritaire'
            }
          </p>

          {details && (
            <p
              className="
                mt-0.5
                text-sm
                text-slate-500 dark:text-slate-400
              "
            >
              {details}
            </p>
          )}
        </div>
      </div>
    </section>
  )
}
