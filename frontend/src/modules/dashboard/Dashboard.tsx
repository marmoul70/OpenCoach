import { useState } from 'react'

import { Modal } from '../../components/ui/Modal'
import { WidgetCard } from '../../components/widgets/WidgetCard'
import { getWidgetComponent } from '../../components/widgets/WidgetComponentRegistry'
import { getWidgetViewComponent } from '../../components/widgets/WidgetViewRegistry'
import { getWidgets } from '../../core/widgets'
import { useAthleteProfile } from '../../core/profile'

interface DashboardProps {
  onOpenTraining: () => void
}

export function Dashboard({
  onOpenTraining,
}: DashboardProps) {
  const profile = useAthleteProfile()
  const firstName = profile.identity.firstName.trim()

  const widgets = getWidgets().filter(
    (widget) =>
      widget.enabled && widget.id !== 'dashboard-welcome',
  )

  const widgetComponents = widgets.map((widget) => ({
    widget,
    Component: getWidgetComponent(widget.id),
  }))

  const trainingWidget = widgetComponents.find(
    ({ widget }) => widget.id === 'training',
  )

  const secondaryWidgets = widgetComponents.filter(
    ({ widget }) => widget.id !== 'training',
  )

  const [selectedWidgetId, setSelectedWidgetId] = useState<
    string | null
  >(null)

  const selectedWidget = selectedWidgetId
    ? widgets.find(
        (widget) => widget.id === selectedWidgetId,
      )
    : undefined

  const DetailsComponent = selectedWidget?.detailsViewId
    ? getWidgetViewComponent(
        selectedWidget.detailsViewId,
      )
    : undefined

  function openWidget(widgetId: string) {
    setSelectedWidgetId(widgetId)
  }

  function renderWidget(
    widget: (typeof widgetComponents)[number]['widget'],
    Component: (typeof widgetComponents)[number]['Component'],
  ) {
    if (Component) {
      return (
        <Component
          key={widget.id}
          onClick={() => {
            if (widget.id === 'training') {
              onOpenTraining()
              return
            }

            openWidget(widget.id)
          }}
        />
      )
    }

    return (
      <WidgetCard
        key={widget.id}
        widget={widget}
        onClick={() => openWidget(widget.id)}
      />
    )
  }

  return (
    <main className="min-h-screen bg-base-200">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <header className="mb-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <div className="badge badge-primary badge-outline mb-3">
                Dashboard
              </div>

              <h1 className="text-3xl font-bold tracking-tight text-base-content sm:text-4xl">
                Bonjour{firstName ? ` ${firstName}` : ''} 👋
              </h1>

              <p className="mt-2 max-w-2xl text-base text-base-content/60">
                Voici l’état actuel de votre suivi sportif.
              </p>
            </div>

            <div className="text-sm font-medium text-base-content/50">
              OpenCoach
            </div>
          </div>
        </header>

        {widgets.length > 0 ? (
          <div className="space-y-6">
            {trainingWidget && (
              <section aria-label="Entraînement du jour">
                {renderWidget(
                  trainingWidget.widget,
                  trainingWidget.Component,
                )}
              </section>
            )}

            {secondaryWidgets.length > 0 && (
              <section aria-label="Indicateurs">
                <div className="mb-3">
                  <h2 className="text-lg font-semibold text-base-content">
                    Vos indicateurs
                  </h2>

                  <p className="mt-1 text-sm text-base-content/50">
                    Les principales données de votre suivi.
                  </p>
                </div>

                <div className="grid gap-4 md:grid-cols-2">
                  {secondaryWidgets.map(
                    ({ widget, Component }) =>
                      renderWidget(widget, Component),
                  )}
                </div>
              </section>
            )}
          </div>
        ) : (
          <div className="card border border-base-300 bg-base-100 shadow-sm">
            <div className="card-body items-center py-12 text-center">
              <h2 className="card-title">
                Votre dashboard est prêt
              </h2>

              <p className="max-w-md text-base-content/60">
                Les modules OpenCoach apparaîtront ici
                progressivement.
              </p>
            </div>
          </div>
        )}
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