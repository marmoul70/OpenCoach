import type { ReactNode } from 'react'

import { Card } from '../../components/ui/Card'
import { cn } from '../../lib/cn'

export interface MetricCardMeta {
  label: string
  value: string
}

export interface MetricCardProps {
  label: string
  value: ReactNode
  detail?: string
  icon?: ReactNode
  metadata?: MetricCardMeta[]
  compact?: boolean
  className?: string
}

/**
 * Shared presentation for a single metric or a compact metric summary.
 * Data formatting and business calculations stay with the calling module.
 */
export function MetricCard({
  label,
  value,
  detail,
  icon,
  metadata = [],
  compact = false,
  className,
}: MetricCardProps) {
  return (
    <Card
      className={cn(
        'min-w-0',
        compact ? 'rounded-xl p-3 shadow-none' : 'p-4',
        className,
      )}
    >
      <div className="flex items-center justify-between gap-3 text-[var(--oc-muted)]">
        <span className="min-w-0 truncate text-xs font-medium">{label}</span>
        {icon ? <span className="shrink-0">{icon}</span> : null}
      </div>

      <div className="mt-3 truncate text-xl font-bold tabular-nums text-[var(--oc-text)]">
        {value}
      </div>

      {detail ? (
        <p className="mt-1 text-xs text-[var(--oc-muted)]">{detail}</p>
      ) : null}

      {metadata.length > 0 ? (
        <dl className="mt-3 grid grid-cols-3 gap-2 border-t border-[var(--oc-border)] pt-3">
          {metadata.map((item) => (
            <div key={item.label} className="min-w-0">
              <dt className="truncate text-[10px] text-[var(--oc-muted)]">{item.label}</dt>
              <dd className="mt-1 truncate text-xs font-semibold tabular-nums text-[var(--oc-text)]">{item.value}</dd>
            </div>
          ))}
        </dl>
      ) : null}
    </Card>
  )
}
