import { useState } from 'react'

import { getAthleteProfile } from './core/profile'
import { Dashboard } from './modules/dashboard/Dashboard'
import { Profile } from './modules/profile/Profile'
import { TrainingWeek } from './modules/training/TrainingWeek'
import { TrainingProvider } from './modules/training/trainingStore'

type Page = 'dashboard' | 'training' | 'profile'

function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const profile = getAthleteProfile()

  return (
    <TrainingProvider>
      <div className="min-h-screen bg-base-200">
        <header className="sticky top-0 z-40 border-b border-base-300 bg-base-100/95 shadow-sm backdrop-blur">
          <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
            <button
              type="button"
              onClick={() => setPage('dashboard')}
              className="text-lg font-bold tracking-tight text-base-content transition hover:text-primary"
            >
              OpenCoach
            </button>

            <div className="flex items-center gap-3">
              <button
                type="button"
                onClick={() => setPage('training')}
                className={[
                  'btn btn-sm',
                  page === 'training'
                    ? 'btn-primary'
                    : 'btn-ghost',
                ].join(' ')}
              >
                Entraînement
              </button>
              <button
                type="button"
                onClick={() => setPage('profile')}
                className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full border border-base-300 bg-base-200 text-sm font-semibold text-base-content transition hover:ring-2 hover:ring-primary/30"
                aria-label="Ouvrir le profil"
                title="Profil"
              >
                {profile.identity.avatar ? (
                  <img
                    src={profile.identity.avatar}
                    alt="Avatar du profil"
                    className="h-full w-full object-cover"
                  />
                ) : (
                  <span>
                    {getInitials(
                      profile.identity.firstName,
                      profile.identity.lastName,
                    )}
                  </span>
                )}
              </button>
            </div>
          </div>
        </header>

        {page === 'dashboard' && (
          <Dashboard onOpenTraining={() => setPage('training')} />
        )}
        {page === 'training' && <TrainingWeek />}
        {page === 'profile' && <Profile />}
      </div>
    </TrainingProvider>
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
