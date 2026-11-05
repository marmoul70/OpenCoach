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
        rounded-[var(--oc-radius-card)]
        border border-[var(--oc-border)]
        bg-[var(--oc-surface-raised)]
        p-4
        shadow-[var(--oc-shadow-card)]
      "
    >
      <div className="flex items-center gap-2 text-[var(--oc-text-secondary)]">
        <Icon className="h-4 w-4" />

        <span className="oc-type-label font-medium uppercase tracking-wide">
          {label}
        </span>
      </div>

      <p className="mt-2 text-2xl font-bold tabular-nums text-[var(--oc-text)]">
        {value}
      </p>

      {description && (
        <p className="oc-type-secondary text-[var(--oc-text-secondary)]">
          {description}
        </p>
      )}
    </article>
  )
}
