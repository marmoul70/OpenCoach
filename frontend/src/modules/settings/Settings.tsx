import { useAthleteProfile } from '../../core/profile'

import {
  BackupSection,
} from './BackupSection'

import {
  NotificationsSection,
} from './NotificationsSection'

import {
  TasksSection,
} from './TasksSection'

import {
  LocationSection,
} from './SettingsSections'

import {
  IntervalsSection,
} from './IntervalsSection'


export function Settings() {
  const profile = useAthleteProfile()

  return (
    <main className="min-h-screen bg-base-200">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-base-content">
            Réglages
          </h1>

          <p className="mt-1 text-sm text-base-content/60">
            Configurez les paramètres utilisés par OpenCoach
            pour personnaliser votre entraînement.
          </p>
        </header>

        <div className="space-y-4">
          <LocationSection
            location={profile.location}
          />

          <IntervalsSection />

          <NotificationsSection />

          <TasksSection />

          <BackupSection />
        </div>
      </div>
    </main>
  )
}
