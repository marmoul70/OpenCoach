import { useState } from 'react'

import { WidgetCard } from '../../components/widgets/WidgetCard'
import { Modal } from '../../components/ui/Modal'
import { getWidgetViewComponent } from '../../components/widgets/WidgetViewRegistry'
import { getWidgets } from '../../core/widgets'
import { getWidgetComponent } from '../../components/widgets/WidgetComponentRegistry'

export function Dashboard() {
  const widgets = getWidgets().filter((widget) => widget.enabled)

  const widgetComponents = widgets.map((widget) => ({
    widget,
    Component: getWidgetComponent(widget.id),
  }))

  const [selectedWidgetId, setSelectedWidgetId] = useState<string | null>(
    null,
  )

  const selectedWidget = selectedWidgetId
    ? widgets.find((widget) => widget.id === selectedWidgetId)
    : undefined

  const DetailsComponent = selectedWidget?.detailsViewId
    ? getWidgetViewComponent(selectedWidget.detailsViewId)
    : undefined

  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-7xl px-6 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            OpenCoach
          </h1>

          <p className="mt-2 text-slate-500">
            Votre tableau de bord sportif
          </p>
        </header>

        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {widgetComponents.map(({ widget, Component }) => {
            if (Component) {
              return (
                <Component
                  key={widget.id}
                  onClick={() => setSelectedWidgetId(widget.id)}
                />
              )
            }

            return (
              <WidgetCard
                key={widget.id}
                widget={widget}
                onClick={() => setSelectedWidgetId(widget.id)}
              />
            )
          })}
        </section>
      </div>

      {selectedWidget && DetailsComponent && (
        <Modal
          title={selectedWidget.title}
          open
          onClose={() => setSelectedWidgetId(null)}
        >
          <DetailsComponent />
        </Modal>
      )}
    </main>
  )
}