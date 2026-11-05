import { lazy, Suspense, useEffect, useState } from 'react'

import {
  useToast,
} from './components/ui/ToastProvider'

import {
  AppNavigation,
} from './components/navigation/AppNavigation'

import {
  OpenCoachLoadingScreen,
} from './components/feedback/OpenCoachLoadingScreen'

import {
  loadAthleteProfile,
  useAthleteProfile,
} from './core/profile'

import { TrainingProvider } from './modules/training/trainingStore'
import { RaceProvider } from './modules/races/raceStore'
import { logout as logoutOpenCoach } from './modules/auth'

/**
 * Les pages sont chargées à la demande : le premier écran ne télécharge
 * pas les modules non visités (activités, météo, santé, réglages, etc.).
 */
const Dashboard = lazy(() => import('./modules/dashboard/Dashboard').then(module => ({ default: module.Dashboard })))
const CoachPage = lazy(() => import('./modules/coach/CoachPage').then(module => ({ default: module.CoachPage })))
const Profile = lazy(() => import('./modules/profile/Profile').then(module => ({ default: module.Profile })))
const PersonalProfile = lazy(() => import('./modules/profile/PersonalProfile').then(module => ({ default: module.PersonalProfile })))
const TrainingWeek = lazy(() => import('./modules/training/TrainingWeek').then(module => ({ default: module.TrainingWeek })))
const RacePage = lazy(() => import('./modules/races/RacePage').then(module => ({ default: module.RacePage })))
const ActivityPage = lazy(() => import('./modules/activities/ActivityPage').then(module => ({ default: module.ActivityPage })))
const FeelingPage = lazy(() => import('./modules/feeling/FeelingPage').then(module => ({ default: module.FeelingPage })))
const Settings = lazy(() => import('./modules/settings').then(module => ({ default: module.Settings })))
const WeatherPage = lazy(() => import('./modules/weather/WeatherPage').then(module => ({ default: module.WeatherPage })))
const HealthPage = lazy(() => import('./modules/health/HealthPage').then(module => ({ default: module.HealthPage })))
const NotificationsPage = lazy(() => import('./modules/notifications/NotificationsPage').then(module => ({ default: module.NotificationsPage })))

type Page =
  | 'dashboard'
  | 'coach'
  | 'training'
  | 'feeling'
  | 'profile-personal'
  | 'profile-sport'
  | 'settings'
  | 'races'
  | 'activities'
  | 'weather'
  | 'health'
  | 'notifications'

type Theme = 'light' | 'dark' | 'system'

interface BuildInfo {
  application: string
  version: string
  commit: string
  built_at: string
}


function App() {
  const {
    toast,
  } = useToast()

  const [page, setPage] = useState<Page>(() => {
    const url =
      new URL(
        window.location.href,
      )

    if (
      url.pathname === '/health'
    ) {
      return 'health'
    }

    if (
      url.pathname === '/notifications'
    ) {
      return 'notifications'
    }

    if (
      url.pathname === '/weather'
    ) {
      return 'weather'
    }

    if (
      url.pathname === '/training'
      || url.searchParams.has(
        'session',
      )
    ) {
      return 'training'
    }

    return 'dashboard'
  })


  useEffect(() => {
    const url =
      new URL(
        window.location.href,
      )

    if (
      page === 'notifications'
      && url.pathname !== '/notifications'
    ) {
      window.history.replaceState(
        null,
        '',
        '/notifications',
      )

      return
    }

    if (
      page === 'health'
      && url.pathname !== '/health'
    ) {
      window.history.replaceState(
        null,
        '',
        '/health',
      )

      return
    }

    if (
      page === 'weather'
      && url.pathname !== '/weather'
    ) {
      window.history.replaceState(
        null,
        '',
        '/weather',
      )

      return
    }

    if (
      page !== 'notifications'
      && url.pathname === '/notifications'
    ) {
      window.history.replaceState(
        null,
        '',
        '/',
      )

      return
    }

    if (
      page !== 'health'
      && url.pathname === '/health'
    ) {
      window.history.replaceState(
        null,
        '',
        '/',
      )

      return
    }

    if (
      page !== 'weather'
      && url.pathname === '/weather'
    ) {
      window.history.replaceState(
        null,
        '',
        '/',
      )
    }
  }, [
    page,
  ])

  const profile = useAthleteProfile()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [
    buildInfo,
    setBuildInfo,
  ] = useState<BuildInfo | null>(
    null,
  )
  const [theme, setTheme] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem('opencoach-theme')

      if (
        savedTheme === 'light' ||
        savedTheme === 'dark' ||
        savedTheme === 'system'
      ) {
        return savedTheme
      }

      return 'system'
  })

  useEffect(() => {
    let mounted = true

    loadAthleteProfile()
      .catch((reason: unknown) => {
        if (!mounted) {
          return
        }

        setError(
          reason instanceof Error
            ? reason.message
            : 'Impossible de charger le profil.',
        )
      })
      .finally(() => {
        if (mounted) {
          setLoading(false)
        }
      })

    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    void fetch(
      '/version.json',
      {
        cache: 'no-store',
      },
    )
      .then((response) => {
        if (!response.ok) {
          throw new Error(
            'Version indisponible.',
          )
        }

        return response.json()
      })
      .then((data: BuildInfo) => {
        if (!cancelled) {
          setBuildInfo(
            data,
          )
        }
      })
      .catch(() => {
        if (!cancelled) {
          setBuildInfo(
            null,
          )
        }
      })

    return () => {
      cancelled = true
    }
  }, [])



  /*
   * Onboarding Web Push.
   *
   * Aucun prompt natif n'est déclenché
   * automatiquement.
   *
   * Le toast propose simplement d'ouvrir
   * Réglages afin que l'utilisateur active
   * volontairement les notifications.
   */
  useEffect(() => {
    let cancelled = false

    const timer =
      window.setTimeout(
        () => {
          void (
            async () => {
              if (cancelled) {
                return
              }


              if (
                !(
                  'Notification'
                  in window
                )
                || !(
                  'PushManager'
                  in window
                )
                || !(
                  'serviceWorker'
                  in navigator
                )
              ) {
                return
              }


              /*
               * Permission explicitement refusée :
               * ne pas reproposer à chaque démarrage.
               */
              if (
                Notification.permission
                === 'denied'
              ) {
                return
              }


              try {
                const registration =
                  await navigator
                    .serviceWorker
                    .ready

                const subscription =
                  await registration
                    .pushManager
                    .getSubscription()


                /*
                 * Cet appareil est déjà configuré.
                 */
                if (
                  subscription
                ) {
                  return
                }
              } catch {
                /*
                 * Si le contrôle échoue, ne pas
                 * afficher un onboarding trompeur.
                 */
                return
              }


              if (cancelled) {
                return
              }


              /*
               * Marqueur de session uniquement.
               *
               * Le toast ne sera pas affiché
               * plusieurs fois pendant la même
               * utilisation d'OpenCoach.
               *
               * Au prochain démarrage, il pourra
               * revenir tant que les notifications
               * ne sont pas activées.
               */
              if (
                sessionStorage.getItem(
                  'opencoach-notification-onboarding',
                )
                === 'shown'
              ) {
                return
              }


              sessionStorage.setItem(
                'opencoach-notification-onboarding',
                'shown',
              )


              toast({
                type: 'info',

                title:
                  'Activer les notifications ?',

                message:
                  'Recevez les séances, alertes '
                  + 'et informations importantes '
                  + 'd’OpenCoach sur cet appareil.',

                duration: null,

                actionLabel:
                  'Réglages',

                onAction: () => {
                  setPage(
                    'settings',
                  )
                },
              })
            }
          )()
        },
        1500,
      )


    return () => {
      cancelled = true

      window.clearTimeout(
        timer,
      )
    }
  }, [
    toast,
  ])



  useEffect(() => {
    const root = document.documentElement

    if (theme === 'system') {
      const prefersDark = window.matchMedia(
        '(prefers-color-scheme: dark)',
      ).matches

      root.setAttribute(
        'data-theme',
        prefersDark ? 'dark' : 'light',
      )
    } else {
      root.setAttribute('data-theme', theme)
    }

    localStorage.setItem('opencoach-theme', theme)
  }, [theme])

  if (loading) {
    return (
      <OpenCoachLoadingScreen
        message="Chargement de votre profil…"
      />
    )
  }


  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-[#0b1014] px-4">
        <div
          className="
            max-w-xl
            rounded-[14px]
            border
            border-rose-500/20
            bg-rose-500/[0.05]
            p-4
            text-rose-700
            dark:border-rose-400/20
            dark:bg-rose-400/[0.05]
            dark:text-rose-300
          "
        >
          <div>
            <h1 className="font-semibold">
              Impossible de charger OpenCoach
            </h1>
            <p className="mt-1 text-sm">
              {error}
            </p>
            <p className="mt-2 text-xs opacity-70">
              Vérifiez que l'API FastAPI est démarrée sur le port 8000.
            </p>
          </div>
        </div>
      </main>
    )
  }

  return (
    <RaceProvider>
      <TrainingProvider>
        <div className="min-h-screen bg-slate-50 dark:bg-[#0b1014] pb-16 lg:pb-0 lg:pl-56">

          <AppNavigation
            activePage={page}
            firstName={
              profile.identity.firstName
            }
            lastName={
              profile.identity.lastName
            }
            avatar={
              profile.identity.avatar
            }
            theme={theme}
            version={
              buildInfo?.version
            }
            commit={
              buildInfo?.commit
            }
            onNavigate={(nextPage) => {
              setPage(nextPage)
            }}
            onThemeChange={(nextTheme) => {
              setTheme(nextTheme)
            }}
            onLogout={() => {
              void logoutOpenCoach()
                .finally(() => {
                  window.location.reload()
                })
            }}
          />


          <Suspense fallback={<OpenCoachLoadingScreen message="Chargement de la page…" />}>
            {page === 'dashboard' && (
              <Dashboard
                onOpenTraining={() => setPage('training')}
                onOpenCoach={() => setPage('coach')}
                onOpenFeeling={() => setPage('feeling')}
                onOpenRaces={() => setPage('races')}
                onOpenWeather={() => setPage('weather')}
              />
            )}
            {page === 'coach' && <CoachPage />}
            {page === 'training' && <TrainingWeek />}
            {page === 'feeling' && <FeelingPage />}
            {page === 'activities' && <ActivityPage />}
            {page === 'races' && <RacePage />}
            {page === 'weather' && <WeatherPage />}
            {page === 'health' && <HealthPage />}
            {page === 'notifications' && <NotificationsPage />}
            {page === 'profile-personal' && <PersonalProfile />}
            {page === 'profile-sport' && <Profile />}
            {page === 'settings' && <Settings />}
          </Suspense>
        </div>
      </TrainingProvider>
    </RaceProvider>
  )
}


export default App
