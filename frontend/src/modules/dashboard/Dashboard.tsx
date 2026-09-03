import {
  useEffect,
  useState,
} from 'react'

import {
  CalendarDays,
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

import {
  DashboardHeader,
  DashboardSection,
} from './dashboard'

import './Dashboard.css'


interface DashboardProps {
  onOpenTraining: () => void
  onOpenCoach: () => void
  onOpenFeeling: () => void
  onOpenRaces: () => void
  onOpenWeather: () => void
}


export function Dashboard({
  onOpenTraining,
  onOpenCoach,
  onOpenFeeling,
  onOpenRaces,
  onOpenWeather,
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
    <main className="dashboard">
      <div
        className="
          dashboard__container
          "
      >

        {/* ==================================================
            En-tête
           ================================================== */}

        <DashboardHeader
          title={
            firstName
              ? `Bonjour ${firstName}`
              : 'Bonjour'
          }
          subtitle={
            'Voici l’essentiel '
            + 'pour ta journée.'
          }
          actions={
            <div
              className="
                dashboard__date
              "
            >
              <CalendarDays
                size={16}
              />

              <span>
                {formatTodayShort()}
              </span>
            </div>
          }
        />


        <PhysiologicalTestProposalCard />


        {/* ==================================================
            Dashboard V3 — vue principale
           ================================================== */}

        <div
          className="
            dashboard__grid
            dashboard__main-grid
          "
        >

          {/* =================================================
              Coach
             ================================================= */}

          <DashboardSection
            title="Analyse du coach"
            description={
              'La recommandation prioritaire '
              + 'pour ta journée.'
            }
            ariaLabel="Coach"
            desktopSpan={7}
            className="
              dashboard__coach
            "
          >
            <CoachTodayWidget
              onOpenCoach={
                onOpenCoach
              }
            />
          </DashboardSection>


          {/* =================================================
              Colonne droite :
              prochain objectif + météo
             ================================================= */}

          <div
            className="
              dashboard__hero-side
            "
          >
            <DashboardSection
              title="Prochain objectif"
              description={
                'La course qui guide '
                + 'ta préparation.'
              }
              ariaLabel="Objectif principal"
              className="
                dashboard__race
              "
            >
              <DashboardRaceGoal
                onOpenRaces={
                  onOpenRaces
                }
              />
            </DashboardSection>


            {weatherWidget && (
              <DashboardSection
                ariaLabel="Météo"
                className="
                  dashboard__weather
                "
              >
                <WeatherWidget
                  onClick={
                    onOpenWeather
                  }
                />
              </DashboardSection>
            )}
          </div>


          {/* =================================================
              Séance du jour
             ================================================= */}

          {trainingWidget && (
            <DashboardSection
              title="Séance du jour"
              description={
                'Ta priorité '
                + 'd’entraînement.'
              }
              ariaLabel="Entraînement du jour"
              desktopSpan={8}
              className="
                dashboard__training
              "
              action={
                <button
                  type="button"
                  onClick={
                    onOpenTraining
                  }
                  className="
                    dashboard__section-link
                  "
                >
                  Programme
                </button>
              }
            >
              {renderWidget(
                trainingWidget.widget,
                trainingWidget.Component,
              )}
            </DashboardSection>
          )}


          {/* =================================================
              État de l'athlète
             ================================================= */}

          {fitnessWidget && (
            <DashboardSection
              title="État de l’athlète"
              description={
                'Récupération, forme '
                + 'et charge récente.'
              }
              ariaLabel="État de forme"
              desktopSpan={4}
              className="
                dashboard__fitness
              "
            >
              {renderWidget(
                fitnessWidget.widget,
                fitnessWidget.Component,
              )}
            </DashboardSection>
          )}


          {/* =================================================
              Cette semaine
             ================================================= */}

          <DashboardSection
            title="Cette semaine"
            description={
              'Une vue rapide '
              + 'de ton programme.'
            }
            ariaLabel="Semaine d'entraînement"
            desktopSpan={8}
            className="
              dashboard__week
            "
          >
            <DashboardWeekStrip
              onOpenTraining={
                onOpenTraining
              }
            />
          </DashboardSection>


          {/* =================================================
              Ressenti
             ================================================= */}

          {feelingWidget && (
            <DashboardSection
              title="Ressenti"
              description={
                'Ton retour complète '
                + 'les données objectives.'
              }
              ariaLabel="Ressenti"
              desktopSpan={4}
              className="
                dashboard__feeling
              "
            >
              {renderWidget(
                feelingWidget.widget,
                feelingWidget.Component,
              )}
            </DashboardSection>
          )}

        </div>


        {/* ==================================================
            Indicateurs complémentaires
           ================================================== */}

        {mainWidgets.length > 0 && (
          <section
            aria-label="Autres indicateurs"
            className="
              dashboard__secondary
            "
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
