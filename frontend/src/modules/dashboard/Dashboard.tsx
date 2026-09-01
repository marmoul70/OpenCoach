import {
  useEffect,
  useState,
} from 'react'

import {
  CalendarDays,
  Sparkles,
} from 'lucide-react'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  useToast,
} from '../../components/ui/ToastProvider'

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
  PhysiologicalTestProposalCard,
} from '../physiological-tests'

import {
  WeatherWidget,
} from '../weather/WeatherWidget'

import {
  fetchBackupStatus,
} from '../settings/backupApi'

import {
  DashboardRaceGoal,
} from './DashboardRaceGoal'

import {
  DashboardWeekStrip,
} from './DashboardWeekStrip'

import './DashboardV2.css'


interface DashboardProps {
  onOpenTraining: () => void
  onOpenCoach: () => void
  onOpenFeeling: () => void
  onOpenRaces: () => void
}


export function Dashboard({
  onOpenTraining,
  onOpenCoach,
  onOpenFeeling,
  onOpenRaces,
}: DashboardProps) {
  const profile =
    useAthleteProfile()

  const {
    toast,
  } = useToast()

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
        Component:
          getWidgetComponent(
            widget.id,
          ),
      }),
    )

  const weatherWidget =
    widgetComponents.find(
      ({ widget }) =>
        widget.id === 'weather',
    )

  const trainingWidget =
    widgetComponents.find(
      ({ widget }) =>
        widget.id === 'training',
    )

  const fitnessWidget =
    widgetComponents.find(
      ({ widget }) =>
        widget.id === 'fitness',
    )

  const feelingWidget =
    widgetComponents.find(
      ({ widget }) =>
        widget.id === 'feeling',
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
    let cancelled = false

    async function checkBackupStatus() {
      try {
        const status =
          await fetchBackupStatus()

        if (
          cancelled
          || status.status !== 'failed'
          || !status.executedAt
        ) {
          return
        }

        const storageKey =
          'opencoach.backup.failure.seen'

        const alreadySeen =
          window.localStorage.getItem(
            storageKey,
          )

        if (
          alreadySeen
          === status.executedAt
        ) {
          return
        }

        window.localStorage.setItem(
          storageKey,
          status.executedAt,
        )

        toast({
          type: 'error',
          title:
            'Échec de la sauvegarde automatique',
          message:
            status.error
            ?? (
              'La sauvegarde nocturne '
              + 'de la base OpenCoach a échoué.'
            ),
          duration: null,
        })
      } catch {
        // Le contrôle du backup ne doit jamais
        // empêcher le Dashboard de fonctionner.
      }
    }

    void checkBackupStatus()

    return () => {
      cancelled = true
    }
  }, [
    toast,
  ])


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
          (widget) =>
            widget.id
            === selectedWidgetId,
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
              widget.id === 'training'
            ) {
              onOpenTraining()
              return
            }

            if (
              widget.id === 'feeling'
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
    <main className="dashboard-v2">
      <div
        className="
          mx-auto
          max-w-7xl
          px-4
          py-5
          sm:px-6
          sm:py-7
          lg:px-8
          lg:py-8
        "
      >

        {/* ==================================================
            En-tête
           ================================================== */}

        <header
          className="
            mb-6
            flex
            items-start
            justify-between
            gap-4
          "
        >
          <div className="min-w-0">
            <div
              className="
                mb-2
                flex
                items-center
                gap-2
                text-xs
                font-semibold
                uppercase
                tracking-[0.16em]
                text-emerald-600
                dark:text-emerald-400
              "
            >
              <Sparkles
                className="h-3.5 w-3.5"
              />

              Aujourd’hui
            </div>

            <h1
              className="
                text-2xl
                font-bold
                tracking-[-0.035em]
                text-slate-950
                sm:text-3xl
                dark:text-white
              "
            >
              Bonjour
              {firstName
                ? ` ${firstName}`
                : ''}
              {' '}👋
            </h1>

            <p
              className="
                mt-1.5
                max-w-xl
                text-sm
                leading-6
                text-slate-500
                dark:text-slate-400
              "
            >
              Voici ce que ton coach
              recommande aujourd’hui.
            </p>
          </div>


          <div
            className="
              flex
              shrink-0
              flex-col
              items-end
              gap-2
            "
          >
            <div
              className="
                hidden
                items-center
                gap-2
                rounded-xl
                border
                border-black/[0.07]
                bg-white
                px-3
                py-2
                text-xs
                font-medium
                text-slate-600
                shadow-sm
                sm:flex
                dark:border-white/[0.08]
                dark:bg-[#14181d]
                dark:text-slate-300
              "
            >
              <CalendarDays
                className="h-4 w-4"
              />

              {formatTodayShort()}
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


        <PhysiologicalTestProposalCard />


        {/* ==================================================
            Vue principale
           ================================================== */}

        <div
          className="
            mt-5
            grid
            gap-5
            lg:grid-cols-12
          "
        >

          {/* Coach */}

          <section
            aria-label="Coach"
            className="
              lg:col-span-7
            "
          >
            <SectionHeader
              title="Analyse du coach"
              description={
                'La recommandation prioritaire '
                + 'pour ta journée.'
              }
            />

            <CoachTodayWidget
              onOpenCoach={
                onOpenCoach
              }
            />
          </section>


          {/* Objectif principal */}

                  <section
                    aria-label="Objectif principal"
                    className="lg:col-span-4"
                  >
                    <SectionHeader
                      title="Prochain objectif"
                      description={
                        'La course qui guide '
                        + 'ta préparation.'
                      }
                    />

                    <DashboardRaceGoal
                      onOpenRaces={onOpenRaces}
                    />
                  </section>


                  {/* Séance du jour */}

          {trainingWidget && (
            <section
              aria-label="Entraînement du jour"
              className="
                dashboard-v2-training-focus
                lg:col-span-8
              "
            >
              <SectionHeader
                title="Séance du jour"
                description={
                  'Ta priorité '
                  + 'd’entraînement.'
                }
                action="Programme"
              />

              {renderWidget(
                trainingWidget.widget,
                trainingWidget.Component,
              )}
            </section>
          )}


          {/* État de l’athlète */}

                  {fitnessWidget && (
                    <section
                      aria-label="État de forme"
                      className="lg:col-span-4"
                    >
                      <SectionHeader
                        title="État de l’athlète"
                        description={
                          'Récupération, forme '
                          + 'et charge récente.'
                        }
                      />

                      {renderWidget(
                        fitnessWidget.widget,
                        fitnessWidget.Component,
                      )}
                    </section>
                  )}


                  {/* Semaine */}

                  <section
                    aria-label="Semaine d'entraînement"
                    className="lg:col-span-8"
                  >
                    <SectionHeader
                      title="Cette semaine"
                      description={
                        'Une vue rapide '
                        + 'de ton programme.'
                      }
                    />

                    <DashboardWeekStrip
                      onOpenTraining={
                        onOpenTraining
                      }
                    />
                  </section>


                  {/* Ressenti */}

          {feelingWidget && (
            <section
              aria-label="Ressenti"
              className="
                lg:col-span-4
              "
            >
              <SectionHeader
                title="Ressenti"
                description={
                  'Ton retour complète '
                  + 'les données objectives.'
                }
              />

              {renderWidget(
                feelingWidget.widget,
                feelingWidget.Component,
              )}
            </section>
          )}

        </div>


        {/* ==================================================
            Indicateurs complémentaires
           ================================================== */}

        {mainWidgets.length > 0 && (
          <section
            aria-label="Autres indicateurs"
            className="mt-8"
          >
            <div
              className="
                mb-4
                flex
                items-end
                justify-between
                gap-4
              "
            >
              <div>
                <h2
                  className="
                    text-lg
                    font-bold
                    tracking-[-0.025em]
                    text-slate-950
                    dark:text-white
                  "
                >
                  Tes indicateurs
                </h2>

                <p
                  className="
                    mt-1
                    text-sm
                    text-slate-500
                    dark:text-slate-400
                  "
                >
                  Les autres données utiles
                  à ton suivi.
                </p>
              </div>
            </div>

            <div
              className="
                grid
                gap-4
                sm:grid-cols-2
                xl:grid-cols-3
              "
            >
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


      {selectedWidget
        && DetailsComponent && (
          <Modal
            title={
              selectedWidget.title
            }
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


function SectionHeader({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: string
}) {
  return (
    <div
      className="
        mb-3
        flex
        min-h-10
        items-end
        justify-between
        gap-3
      "
    >
      <div>
        <h2
          className="
            dashboard-v2-section-title
          "
        >
          {title}
        </h2>

        <p
          className="
            dashboard-v2-section-description
          "
        >
          {description}
        </p>
      </div>

      {action && (
        <span
          className="
            hidden
            text-xs
            font-semibold
            text-emerald-600
            sm:inline
            dark:text-emerald-400
          "
        >
          {action}
        </span>
      )}
    </div>
  )
}


function formatTodayShort(): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'short',
      day: 'numeric',
      month: 'long',
    },
  ).format(
    new Date(),
  )
}
