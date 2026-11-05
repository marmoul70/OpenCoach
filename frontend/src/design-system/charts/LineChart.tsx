import type { ReactNode } from 'react'

export interface LineChartPoint {
  id: string
  label: string
  value: number | null
}

interface LineChartProps {
  title: string
  points: LineChartPoint[]
  valueFormatter: (value: number) => string
  latestValue: string
  averageValue: string
  startLabel: string
  endLabel: string
  emptyMessage: string
  ariaLabel: string
  headerMeta?: ReactNode
}

/**
 * Presentational SVG line chart.
 * Data preparation, date filtering and domain-specific formatting belong to callers.
 */
export function LineChart({
  title,
  points,
  valueFormatter,
  latestValue,
  averageValue,
  startLabel,
  endLabel,
  emptyMessage,
  ariaLabel,
  headerMeta,
}: LineChartProps) {
  if (points.length === 0 || !points.some((point) => point.value !== null)) {
    return (
      <section className="oc-surface min-w-0 p-4" aria-label={title}>
        <h3 className="text-sm font-semibold text-[var(--oc-text)]">{title}</h3>
        <p className="mt-8 text-center text-sm text-[var(--oc-muted)]">{emptyMessage}</p>
        <div className="mt-7 border-t border-[var(--oc-border)]" />
      </section>
    )
  }

  const values = points
    .map((point) => point.value)
    .filter((value): value is number => value !== null)
  const minimum = values.length > 0 ? Math.min(...values) : 0
  const maximum = values.length > 0 ? Math.max(...values) : 1
  const range = maximum - minimum || 1
  const plotTop = 12
  const plotBottom = 88
  const plotLeft = 48
  const plotRight = 352
  const coordinates = points.map((point, index) => {
    const x = points.length === 1
      ? (plotLeft + plotRight) / 2
      : plotLeft + (index / (points.length - 1)) * (plotRight - plotLeft)
    const y = point.value === null
      ? null
      : plotBottom - ((point.value - minimum) / range) * (plotBottom - plotTop)
    return { x, y, point }
  })
  const segments: typeof coordinates[] = []
  let currentSegment: typeof coordinates = []
  coordinates.forEach((coordinate) => {
    if (coordinate.y === null) {
      if (currentSegment.length > 0) segments.push(currentSegment)
      currentSegment = []
      return
    }
    currentSegment.push(coordinate)
  })
  if (currentSegment.length > 0) segments.push(currentSegment)


  return (
    <section className="oc-surface min-w-0 p-4" aria-label={title}>
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-[var(--oc-text)]">{title}</h3>
        <span className="text-[10px] text-[var(--oc-muted)]">
          {headerMeta ?? `${points.length} mesures`}
        </span>
      </div>

      <p className="oc-tabular mt-2 text-xl font-bold text-[var(--oc-text)]">
        {latestValue}
      </p>

      <svg
        viewBox="0 0 360 112"
        role="img"
        aria-label={ariaLabel}
        className="mt-2 h-28 w-full overflow-visible"
      >
        {values.length > 0 && [0, 1, 2, 3].map((step) => {
          const y = plotTop + (step / 3) * (plotBottom - plotTop)
          const value = maximum - (step / 3) * (maximum - minimum)
          return (
            <g key={step}>
              <line
                x1={plotLeft}
                y1={y}
                x2={plotRight}
                y2={y}
                stroke="var(--oc-chart-grid)"
                strokeDasharray="3 4"
              />
              <text
                x="40"
                y={y + 3}
                textAnchor="end"
                fontSize="9"
                fill="var(--oc-chart-axis)"
              >
                {valueFormatter(value)}
              </text>
            </g>
          )
        })}

        {segments.map((segment, index) => (
          <polyline
            key={index}
            points={segment.map(({ x, y }) => `${x},${y}`).join(' ')}
            fill="none"
            stroke="var(--oc-chart-series-1)"
            strokeWidth="2.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        ))}

        {coordinates.map(({ x, y, point }) => point.value === null || y === null ? null : (
          <circle
            key={point.id}
            cx={x}
            cy={y}
            r="2.8"
            fill="var(--oc-chart-series-1)"
          >
            <title>{point.label} : {valueFormatter(point.value)}</title>
          </circle>
        ))}

        <text x={plotLeft} y="106" textAnchor="start" fontSize="9" fill="var(--oc-chart-axis)">
          {startLabel}
        </text>
        <text x={plotRight} y="106" textAnchor="end" fontSize="9" fill="var(--oc-chart-axis)">
          {endLabel}
        </text>
      </svg>

      <div className="mt-1 flex items-center justify-end border-t border-[var(--oc-border)] pt-2 text-[10px] text-[var(--oc-muted)]">
        <span>Moyenne {averageValue}</span>
      </div>
    </section>
  )
}
