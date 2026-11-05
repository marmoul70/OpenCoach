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
        rounded-[var(--oc-radius-card)]
        border border-[var(--oc-border)]
        bg-[var(--oc-surface-raised)]
        px-4 py-4
        shadow-[var(--oc-shadow-card)]
        sm:px-5
      "
    >
      <div className="flex items-center gap-3">
        <div
          className="
            flex size-10 shrink-0 items-center justify-center
            rounded-xl bg-emerald-500/10
            text-emerald-600 dark:text-emerald-400
          "
        >
          <Trophy size={19} strokeWidth={2} />
        </div>

        <div className="min-w-0 flex-1">
          <p className="oc-type-label font-semibold uppercase tracking-wide text-[var(--oc-text-secondary)]">
            Objectif
          </p>

          <p className="mt-0.5 truncate font-semibold text-[var(--oc-text)]">
            {name ?? 'Aucun objectif prioritaire'}
          </p>

          {details && (
            <p className="oc-type-body mt-0.5 text-[var(--oc-text-secondary)]">
              {details}
            </p>
          )}
        </div>
      </div>
    </section>
  )
}
