import { useAthleteProfile } from '../../core/profile'

import {
  BackupSection,
} from './BackupSection'

import {
  EquipmentSection,
  LocationSection,
  NutritionSection,
  TrainingSection,
} from './SettingsSections'


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
          <TrainingSection
            training={profile.training}
          />

          <LocationSection
            location={profile.location}
          />

          <EquipmentSection
            equipment={profile.equipment}
          />

          <NutritionSection
            nutrition={profile.nutrition}
          />

          <BackupSection />
        </div>
      </div>
    </main>
  )
}
