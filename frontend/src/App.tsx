import { useState } from 'react'

import { getAthleteProfile } from './core/profile'
import { Dashboard } from './modules/dashboard/Dashboard'
import { Profile } from './modules/profile/Profile'

type Page = 'dashboard' | 'profile'

function App() {
  const [page, setPage] = useState<Page>('dashboard')
  const profile = getAthleteProfile()

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <button
            type="button"
            onClick={() => setPage('dashboard')}
            className="text-lg font-bold tracking-tight text-slate-900"
          >
            OpenCoach
          </button>

          <button
            type="button"
            onClick={() => setPage('profile')}
            className="flex h-10 w-10 items-center justify-center overflow-hidden rounded-full border border-slate-200 bg-slate-100 text-sm font-semibold text-slate-600 transition hover:ring-2 hover:ring-slate-200"
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
      </header>

      {page === 'dashboard' && <Dashboard />}
      {page === 'profile' && <Profile />}
    </div>
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
