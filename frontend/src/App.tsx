import { useEffect, useState } from 'react'

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
import { Connections } from './modules/connections'
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
  | 'connections'

type Theme = 'light' | 'dark' | 'system'

interface BuildInfo {
  application: string
  version: string
  commit: string
  built_at: string
}

function App() {
  const [page, setPage] = useState<Page>('dashboard')
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
        <div className="min-h-screen bg-base-200">

          <header className="sticky top-0 z-40 border-b border-base-300 bg-base-100/95 shadow-sm backdrop-blur">
            <div className="navbar mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              {/* Gauche : menu */}
              <div className="navbar-start">
                <div className="dropdown">
                  <button
                    type="button"
                    tabIndex={0}
                    className="btn btn-ghost btn-circle"
                    aria-label="Ouvrir le menu"
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className="h-5 w-5"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 6h16M4 12h16M4 18h7"
                      />
                    </svg>
                  </button>

                  <ul
                    tabIndex={-1}
                    className="menu menu-sm dropdown-content z-50 mt-3 w-52 rounded-box bg-base-100 p-2 shadow"
                  >
                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('dashboard')
                          event.currentTarget.blur()
                        }}
                      >
                        Tableau de bord
                      </button>
                    </li>

                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('coach')
                          event.currentTarget.blur()
                        }}
                        className={
                          page === 'coach'
                            ? 'text-primary font-semibold'
                            : ''
                        }
                      >
                        Coach
                      </button>
                    </li>

                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('training')
                          event.currentTarget.blur()
                        }}
                        className={page === 'training' ? 'text-primary font-semibold' : ''}
                      >
                        Entraînement
                      </button>
                    </li>
                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('feeling')
                          event.currentTarget.blur()
                        }}
                        className={
                          page === 'feeling'
                            ? 'text-primary font-semibold'
                            : ''
                        }
                      >
                        Ressenti
                      </button>
                    </li>
                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('activities')
                          event.currentTarget.blur()
                        }}
                        className={
                          page === 'activities'
                            ? 'text-primary font-semibold'
                            : ''
                        }
                      >
                        Activités
                      </button>
                    </li>
                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('races')
                          event.currentTarget.blur()
                        }}
                        className={page === 'races' ? 'text-primary font-semibold' : ''}
                      >
                        Courses
                      </button>
                    </li>
                  </ul>
                </div>
              </div>

              {/* Centre : logo */}
              <div className="navbar-center">
                <button
                  type="button"
                  onClick={() => setPage('dashboard')}
                  className="btn btn-ghost text-xl font-bold tracking-tight"
                >
                  OpenCoach
                </button>
              </div>

              {/* Droite : navigation + profil */}
              <div className="navbar-end gap-1">

                {/* Avatar + menu profil */}
                <div className="dropdown dropdown-end">
                  <button
                    type="button"
                    tabIndex={0}
                    className="btn btn-ghost btn-circle avatar"
                    aria-label="Ouvrir le menu du profil"
                  >
                    <div className="w-10 rounded-full">
                      {profile.identity.avatar ? (
                        <img
                          src={profile.identity.avatar}
                          alt="Avatar du profil"
                          className="object-cover"
                        />
                      ) : (
                        <div className="flex h-full w-full items-center justify-center bg-base-200 text-sm font-semibold text-base-content">
                          {getInitials(
                            profile.identity.firstName,
                            profile.identity.lastName,
                          )}
                        </div>
                      )}
                    </div>
                  </button>

                  <ul
                    tabIndex={-1}
                    className="menu menu-sm dropdown-content z-50 mt-3 w-56 rounded-box bg-base-100 p-2 shadow"
                  >

                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('profile-personal')
                          event.currentTarget.blur()
                        }}
                        className={
                          page === 'profile-personal'
                            ? 'text-primary font-semibold'
                            : ''
                        }
                      >
                        Profil perso
                      </button>
                    </li>

                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('profile-sport')
                          event.currentTarget.blur()
                        }}
                        className={
                          page === 'profile-sport'
                            ? 'text-primary font-semibold'
                            : ''
                        }
                      >
                        Profil sportif
                      </button>
                    </li>

                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('settings')
                          event.currentTarget.blur()
                        }}
                        className={
                          page === 'settings'
                            ? 'text-primary font-semibold'
                            : ''
                        }
                      >
                        Réglages
                      </button>
                    </li>
                    <li>
                      <button
                        type="button"
                        onClick={(event) => {
                          setPage('connections')
                          event.currentTarget.blur()
                        }}
                        className={
                          page === 'connections'
                            ? 'text-primary font-semibold'
                            : ''
                        }
                      >
                        Connexions
                      </button>
                    </li>
                    <div className="divider my-1" />
                    <li>
                      <details>
                        <summary>Apparence</summary>

                        <ul>
                          <li>
                            <button
                              type="button"
                              onClick={() => setTheme('light')}
                              className={theme === 'light' ? 'text-primary font-semibold' : ''}
                            >
                              ☀️ Clair
                            </button>
                          </li>

                          <li>
                            <button
                              type="button"
                              onClick={() => setTheme('dark')}
                              className={theme === 'dark' ? 'text-primary font-semibold' : ''}
                            >
                              🌙 Sombre
                            </button>
                          </li>

                          <li>
                            <button
                              type="button"
                              onClick={() => setTheme('system')}
                              className={theme === 'system' ? 'text-primary font-semibold' : ''}
                            >
                              🖥️ Système
                            </button>
                          </li>
                        </ul>
                      </details>
                    </li>

                    <div className="divider my-1" />

                    <li
                      className="
                        pointer-events-none
                        px-3
                        py-1
                      "
                    >
                      <div
                        className="
                          flex
                          flex-col
                          gap-0
                          p-0
                          text-[11px]
                          leading-4
                          text-base-content/40
                        "
                      >
                        <span>
                          Version : {
                            buildInfo
                              ? `v${buildInfo.version}`
                              : 'développement'
                          }
                        </span>

                        {buildInfo && (
                          <span
                            className="
                              font-mono
                              text-[10px]
                              text-base-content/30
                            "
                          >
                            {buildInfo.commit}
                          </span>
                        )}
                      </div>
                    </li>

                    <div className="divider my-1" />

                    <li>
                      <button
                        type="button"
                        className="text-error"
                        onClick={() => {
                          void logoutOpenCoach()
                            .finally(() => {
                              window.location.reload()
                            })
                        }}
                      >
                        Se déconnecter
                      </button>
                    </li>

                  </ul>
                </div>
              </div>
            </div>
          </header>

          {page === 'dashboard' && (
            <Dashboard
              onOpenTraining={() => setPage('training')}
              onOpenCoach={() => setPage('coach')}
              onOpenFeeling={() => setPage('feeling')}
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
          {page === 'connections' && <Connections />}
        </div>
      </TrainingProvider>
    </RaceProvider>
  )
}

function getInitials(
  firstName: string,
  lastName: string,
): string {
  const firstInitial = firstName.trim().charAt(0)
  const lastInitial = lastName.trim().charAt(0)

  const initials = `${firstInitial}${lastInitial}`.toUpperCase()

  return initials || 'OC'
}

export default App
