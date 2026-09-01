import { useEffect, useState } from 'react'

import {
  useToast,
} from './components/ui/ToastProvider'

import {
  AppNavigation,
} from './components/navigation/AppNavigation'

import {
  loadAthleteProfile,
  useAthleteProfile,
} from './core/profile'

import { Dashboard } from './modules/dashboard/Dashboard'
import { CoachPage } from './modules/coach/CoachPage'
import { Profile } from './modules/profile/Profile'
import { PersonalProfile } from './modules/profile/PersonalProfile'
import { TrainingWeek } from './modules/training/TrainingWeek'
import { TrainingProvider } from './modules/training/trainingStore'
import { RacePage } from './modules/races/RacePage'
import { RaceProvider } from './modules/races/raceStore'
import { ActivityPage } from './modules/activities/ActivityPage'
import { FeelingPage } from './modules/feeling/FeelingPage'
import { Settings } from './modules/settings'
import { logout as logoutOpenCoach } from './modules/auth'

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
      url.pathname === '/training'
      || url.searchParams.has(
        'session',
      )
    ) {
      return 'training'
    }

    return 'dashboard'
  })
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
      <main className="flex min-h-screen items-center justify-center bg-base-200">
        <div className="text-center">
          <span className="loading loading-spinner loading-lg text-primary" />
          <p className="mt-4 text-sm text-base-content/60">
            Chargement du profil...
          </p>
        </div>
      </main>
    )
  }

  if (error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-base-200 px-4">
        <div className="alert alert-error max-w-xl">
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
        <div className="min-h-screen bg-base-200 pb-16 lg:pb-0 lg:pl-[14.25rem]">

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


          {page === 'dashboard' && (
            <Dashboard
              onOpenTraining={() => setPage('training')}
              onOpenCoach={() => setPage('coach')}
              onOpenFeeling={() => setPage('feeling')}
              onOpenRaces={() => setPage('races')}
            />
          )}

          {page === 'coach' && <CoachPage />}
          {page === 'training' && <TrainingWeek />}
          {page === 'feeling' && <FeelingPage />}
          {page === 'activities' && <ActivityPage />}
          {page === 'races' && <RacePage />}
          {page === 'profile-personal' && <PersonalProfile />}
          {page === 'profile-sport' && <Profile />}
          {page === 'settings' && <Settings />}
        </div>
      </TrainingProvider>
    </RaceProvider>
  )
}


export default App
