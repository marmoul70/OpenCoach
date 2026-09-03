import type {
  ReactNode,
} from 'react'


type DashboardSectionSpan =
  | 3
  | 4
  | 5
  | 6
  | 7
  | 8
  | 9
  | 12


interface DashboardSectionProps {
  title?: string
  description?: string
  action?: ReactNode
  children: ReactNode
  ariaLabel?: string
  desktopSpan?: DashboardSectionSpan
  className?: string
}


const desktopSpanClasses:
  Record<
    DashboardSectionSpan,
    string
  > = {
    3: 'dashboard__span-3',
    4: 'dashboard__span-4',
    5: 'dashboard__span-5',
    6: 'dashboard__span-6',
    7: 'dashboard__span-7',
    8: 'dashboard__span-8',
    9: 'dashboard__span-9',
    12: 'dashboard__span-12',
  }


export function DashboardSection({
  title,
  description,
  action,
  children,
  ariaLabel,
  desktopSpan = 12,
  className = '',
}: DashboardSectionProps) {
  const hasHeader =
    Boolean(
      title
      || description
      || action,
    )

  return (
    <section
      aria-label={
        ariaLabel
        ?? title
      }
      className={[
        'dashboard__section',
        desktopSpanClasses[
          desktopSpan
        ],
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {hasHeader && (
        <div
          className="
            dashboard__section-header
          "
        >
          <div
            className="
              min-w-0
              flex-1
            "
          >
            {title && (
              <h2
                className="
                  dashboard__section-title
                "
              >
                {title}
              </h2>
            )}

            {description && (
              <p
                className="
                  dashboard__section-description
                "
              >
                {description}
              </p>
            )}
          </div>

          {action && (
            <div
              className="
                dashboard__section-action
                shrink-0
              "
            >
              {action}
            </div>
          )}
        </div>
      )}

      {children}
    </section>
  )
}
