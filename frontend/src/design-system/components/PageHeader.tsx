import type { ReactNode } from 'react'

export interface PageHeaderProps {
  eyebrow?: ReactNode
  title: string
  description?: ReactNode
  actions?: ReactNode
  className?: string
}

/** Shared page heading. Content and actions remain owned by each module. */
export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className = '',
}: PageHeaderProps) {
  return (
    <header className={['oc-page-header', className].filter(Boolean).join(' ')}>
      <div className="min-w-0">
        {eyebrow ? <div className="oc-page-eyebrow">{eyebrow}</div> : null}
        <h1 className="oc-page-title">{title}</h1>
        {description ? <p className="oc-page-description">{description}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div> : null}
    </header>
  )
}
