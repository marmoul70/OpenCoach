import type { WidgetDefinition } from '../../core/widgets'

type WidgetStatus = NonNullable<
  WidgetDefinition['status']
>

type WidgetAccent = NonNullable<
  WidgetDefinition['accent']
>

interface WidgetCardProps {
  widget: WidgetDefinition
  onClick?: () => void
}

const statusClasses: Record<WidgetStatus, string> = {
  success: 'badge-success',
  warning: 'badge-warning',
  danger: 'badge-error',
  neutral: 'badge-ghost',
}

const statusLabels: Record<WidgetStatus, string> = {
  success: 'OK',
  warning: 'Attention',
  danger: 'Alerte',
  neutral: 'Info',
}

const accentClasses: Record<WidgetAccent, string> = {
  neutral: 'text-base-content',
  primary: 'text-primary',
  secondary: 'text-secondary',
  accent: 'text-accent',
  info: 'text-info',
  success: 'text-success',
  warning: 'text-warning',
  error: 'text-error',
}

const accentBackgroundClasses: Record<
  WidgetAccent,
  string
> = {
  neutral: 'bg-base-200',
  primary: 'bg-primary/10',
  secondary: 'bg-secondary/10',
  accent: 'bg-accent/10',
  info: 'bg-info/10',
  success: 'bg-success/10',
  warning: 'bg-warning/10',
  error: 'bg-error/10',
}

export function WidgetCard({
  widget,
  onClick,
}: WidgetCardProps) {
  const status = widget.status ?? 'neutral'
  const accent = widget.accent ?? 'neutral'
  const Icon = widget.icon

  return (
    <button
      type="button"
      onClick={onClick}
      className="card w-full border border-base-300 bg-base-100 text-left shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg"
    >
      <div className="card-body p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 items-center gap-3">
            {Icon && (
              <div
                className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl ${accentBackgroundClasses[accent]}`}
              >
                <Icon
                  className={`h-5 w-5 ${accentClasses[accent]}`}
                />
              </div>
            )}

            <div className="min-w-0">
              <h2 className="card-title text-base">
                {widget.title}
              </h2>

              {widget.description && (
                <p className="mt-1 text-sm text-base-content/60">
                  {widget.description}
                </p>
              )}
            </div>
          </div>

          <span
            className={`badge badge-sm shrink-0 ${statusClasses[status]}`}
          >
            {statusLabels[status]}
          </span>
        </div>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-xs text-base-content/50">
            Ouvrir
          </span>

          <span
            className={`text-sm font-medium ${accentClasses[accent]}`}
          >
            Voir →
          </span>
        </div>
      </div>
    </button>
  )
}
