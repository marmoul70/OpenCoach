import {
  useEffect,
  useState,
} from 'react'

import {
  Modal,
} from '../../components/ui/Modal'
import {
  WidgetCard,
} from '../../components/widgets/WidgetCard'
import {
  getWidgetComponent,
} from '../../components/widgets/WidgetComponentRegistry'
import {
  getWidgetViewComponent,
} from '../../components/widgets/WidgetViewRegistry'
import {
  useAthleteProfile,
} from '../../core/profile'
import {
  getWidgets,
} from '../../core/widgets'
import {
  CoachTodayWidget,
} from '../coach/CoachTodayWidget'
import {
  WeatherWidget,
} from '../weather/WeatherWidget'


interface DashboardProps {
  onOpenTraining: () => void
  onOpenCoach: () => void
  onOpenFeeling: () => void
}


export function Dashboard({
  onOpenTraining,
  onOpenCoach,
  onOpenFeeling,
}: DashboardProps) {
  const profile =
    useAthleteProfile()

  const firstName =
    profile.identity.firstName.trim()

  const widgets =
    getWidgets().filter(
      (widget) => (
        widget.enabled
        && widget.id !== 'dashboard-welcome'
      ),
    )

  const widgetComponents =
    widgets.map(
      (widget) => ({
        widget,
        Component: getWidgetComponent(
          widget.id,
        ),
      }),
    )

  const weatherWidget =
    widgetComponents.find(
      ({ widget }) => (
        widget.id === 'weather'
      ),
    )

  const trainingWidget =
    widgetComponents.find(
      ({ widget }) => (
        widget.id === 'training'
      ),
    )

  const fitnessWidget =
    widgetComponents.find(
      ({ widget }) => (
        widget.id === 'fitness'
      ),
    )


  const feelingWidget =
    widgetComponents.find(
      ({ widget }) => (
        widget.id === 'feeling'
      ),
    )

  const mainWidgets =
    widgetComponents.filter(
      ({ widget }) => (
        widget.id !== 'weather'
        && widget.id !== 'training'
        && widget.id !== 'fitness'
        && widget.id !== 'feeling'
      ),
    )

  const [
    selectedWidgetId,
    setSelectedWidgetId,
  ] = useState<string | null>(
    null,
  )

  useEffect(() => {
    function closeWidgetModal() {
      setSelectedWidgetId(
        null,
      )
    }

    window.addEventListener(
      'opencoach:close-widget-modal',
      closeWidgetModal,
    )

    return () => {
      window.removeEventListener(
        'opencoach:close-widget-modal',
        closeWidgetModal,
      )
    }
  }, [])


  const selectedWidget =
    selectedWidgetId
      ? widgets.find(
          (widget) => (
            widget.id
            === selectedWidgetId
          ),
        )
      : undefined

  const DetailsComponent =
    selectedWidget?.detailsViewId
      ? getWidgetViewComponent(
          selectedWidget.detailsViewId,
        )
      : undefined

  function openWidget(
    widgetId: string,
  ) {
    setSelectedWidgetId(
      widgetId,
    )
  }

  function renderWidget(
    widget: (
      typeof widgetComponents
    )[number]['widget'],
    Component: (
      typeof widgetComponents
    )[number]['Component'],
  ) {
    if (Component) {
      return (
        <Component
          key={widget.id}
          onClick={() => {
            if (
              widget.id
              === 'training'
            ) {
              onOpenTraining()
              return
            }

            if (
              widget.id
              === 'feeling'
            ) {
              onOpenFeeling()
              return
            }

            openWidget(
              widget.id,
            )
          }}
        />
      )
    }

    return (
      <WidgetCard
        key={widget.id}
        widget={widget}
        onClick={() => {
          openWidget(
            widget.id,
          )
        }}
      />
    )
  }

  return (
    <main className="min-h-screen bg-base-200">
      <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8 lg:py-6">

        <header className="mb-5">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-base-content sm:text-3xl">
                Bonjour
                {firstName
                  ? ` ${firstName}`
                  : ''}
                {' '}👋
              </h1>

              <p className="mt-1 text-sm text-base-content/50">
                {formatTodayMessage()}
              </p>
            </div>

            {weatherWidget && (
              <WeatherWidget
                compact
                onClick={() => {
                  openWidget(
                    'weather',
                  )
                }}
              />
            )}
          </div>
        </header>

        <div className="space-y-4">

          <section aria-label="Coach">
            <CoachTodayWidget
              onOpenCoach={onOpenCoach}
            />
          </section>

          {fitnessWidget && (
            <section aria-label="État de forme">
              {renderWidget(
                fitnessWidget.widget,
                fitnessWidget.Component,
              )}
            </section>
          )}


          {feelingWidget && (
            <section aria-label="Ressenti">
              {renderWidget(
                feelingWidget.widget,
                feelingWidget.Component,
              )}
            </section>
          )}

          {trainingWidget && (
            <section aria-label="Entraînement du jour">
              {renderWidget(
                trainingWidget.widget,
                trainingWidget.Component,
              )}
            </section>
          )}

          {mainWidgets.length > 0 && (
            <section
              aria-label="Autres indicateurs"
              className="pt-1"
            >
              <div className="mb-3">
                <h2 className="text-lg font-semibold text-base-content">
                  Vos indicateurs
                </h2>

                <p className="mt-0.5 text-sm text-base-content/50">
                  Les autres données utiles à votre suivi.
                </p>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                {mainWidgets.map(
                  ({
                    widget,
                    Component,
                  }) => (
                    renderWidget(
                      widget,
                      Component,
                    )
                  ),
                )}
              </div>
            </section>
          )}

        </div>
      </div>

      {selectedWidget && DetailsComponent && (
        <Modal
          title={selectedWidget.title}
          open
          onClose={() => {
            setSelectedWidgetId(
              null,
            )
          }}
        >
          <DetailsComponent />
        </Modal>
      )}
    </main>
  )
}


function formatTodayMessage(): string {
  const formattedDate =
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
      },
    ).format(
      new Date(),
    )

  return (
    `Voici votre journée du ${formattedDate}.`
  )
}
