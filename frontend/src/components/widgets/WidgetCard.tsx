import type { WidgetDefinition } from '../../core/widgets'

interface WidgetCardProps {
  widget: WidgetDefinition
  onClick?: () => void
}

export function WidgetCard({ widget, onClick }: WidgetCardProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="w-full rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">
            {widget.title}
          </h2>

          {widget.description && (
            <p className="mt-1 text-sm text-slate-500">
              {widget.description}
            </p>
          )}
        </div>

        <span className="text-slate-400">→</span>
      </div>
    </button>
  )
}
