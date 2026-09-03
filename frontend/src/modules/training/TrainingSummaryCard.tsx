import type { ComponentType } from 'react'

interface TrainingSummaryCardProps {
  icon: ComponentType<{ className?: string }>
  label: string
  value: string
  description?: string
}

export function TrainingSummaryCard({
  icon: Icon,
  label,
  value,
  description,
}: TrainingSummaryCardProps) {
  return (
    <article
      className="
        rounded-[14px]
        border
        border-slate-200
        bg-white
        p-4
        shadow-sm
        dark:border-white/[0.08]
        dark:bg-[#141a1e]
      "
    >
        <div className="flex items-center gap-2 text-slate-500 dark:text-slate-400">
          <Icon className="h-4 w-4" />

          <span className="text-xs font-medium uppercase tracking-wide">
            {label}
          </span>
        </div>

        <p className="mt-2 text-2xl font-bold text-slate-800 dark:text-slate-100">
          {value}
        </p>

        {description && (
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {description}
          </p>
        )}
    </article>
  )
}
