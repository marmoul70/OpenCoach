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
        border-base-300
        bg-base-100
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
            bg-primary/10
            text-primary
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
              text-base-content/40
            "
          >
            Objectif
          </p>

          <p
            className="
              mt-0.5
              truncate
              font-semibold
              text-base-content
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
                text-base-content/50
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
