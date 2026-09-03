import type {
  ReactNode,
} from 'react'


interface DashboardHeaderProps {
  eyebrow?: string
  title: string
  subtitle?: string
  actions?: ReactNode
}


export function DashboardHeader({
  eyebrow,
  title,
  subtitle,
  actions,
}: DashboardHeaderProps) {
  return (
    <header
      className="
        dashboard__header
      "
    >
      <div
        className="
          min-w-0
          flex-1
        "
      >
        {eyebrow && (
          <p
            className="
              dashboard__eyebrow
            "
          >
            {eyebrow}
          </p>
        )}

        <h1
          className="
            dashboard__title
          "
        >
          {title}
        </h1>

        {subtitle && (
          <p
            className="
              dashboard__subtitle
            "
          >
            {subtitle}
          </p>
        )}
      </div>

      {actions && (
        <div
          className="
            dashboard__header-actions
            shrink-0
          "
        >
          {actions}
        </div>
      )}
    </header>
  )
}
