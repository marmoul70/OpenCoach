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
    <article className="card border border-base-300 bg-base-100 shadow-sm">
      <div className="card-body p-4">
        <div className="flex items-center gap-2 text-base-content/50">
          <Icon className="h-4 w-4" />

          <span className="text-xs font-medium uppercase tracking-wide">
            {label}
          </span>
        </div>

        <p className="mt-2 text-2xl font-bold text-base-content">
          {value}
        </p>

        {description && (
          <p className="text-xs text-base-content/50">
            {description}
          </p>
        )}
      </div>
    </article>
  )
}
