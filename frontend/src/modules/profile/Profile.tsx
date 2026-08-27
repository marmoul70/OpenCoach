import { useState } from 'react'
import { MetricTooltip } from '../../components/metrics/MetricTooltip'

import {
  updateAthleteProfile,
  useAthleteProfile,
} from '../../core/profile'

import { ProfileSection } from './ProfileSection'

import {
  FormField,
  SectionActions,
  parseOptionalNumber,
} from './ProfileForm'

export function Profile() {
  const profile = useAthleteProfile()

  const [heightCm, setHeightCm] = useState(
    profile.body.heightCm?.toString() ?? '',
  )
  const [weightKg, setWeightKg] = useState(
    profile.body.weightKg?.toString() ?? '',
  )

  const [maxHeartRate, setMaxHeartRate] = useState(
    profile.physiology.maxHeartRate?.toString() ?? '',
  )
  const [restingHeartRate, setRestingHeartRate] = useState(
    profile.physiology.restingHeartRate?.toString() ?? '',
  )
  const [vma, setVma] = useState(
    profile.physiology.vma?.toString() ?? '',
  )
  const [thresholdHeartRate1, setThresholdHeartRate1] = useState(
    profile.physiology.thresholdHeartRate1?.toString() ?? '',
  )
  const [thresholdHeartRate2, setThresholdHeartRate2] = useState(
    profile.physiology.thresholdHeartRate2?.toString() ?? '',
  )

  const [savedSection, setSavedSection] = useState<string | null>(null)

  async function handleSaveBody() {
    await updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      body: {
        ...currentProfile.body,
        heightCm: parseOptionalNumber(heightCm),
        weightKg: parseOptionalNumber(weightKg),
      },
    }))

    showSaved('body')
  }

  async function handleSavePhysiology() {
    await updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      physiology: {
        ...currentProfile.physiology,
        vma: parseOptionalNumber(vma),
        maxHeartRate: parseOptionalNumber(maxHeartRate),
        restingHeartRate: parseOptionalNumber(restingHeartRate),
        thresholdHeartRate1:
          parseOptionalNumber(thresholdHeartRate1),
        thresholdHeartRate2:
          parseOptionalNumber(thresholdHeartRate2),
      },
    }))

    showSaved('physiology')
  }

  function handleResetBody() {
    setHeightCm(profile.body.heightCm?.toString() ?? '')
    setWeightKg(profile.body.weightKg?.toString() ?? '')
    setSavedSection(null)
  }

  function handleResetPhysiology() {
    setMaxHeartRate(
      profile.physiology.maxHeartRate?.toString() ?? '',
    )
    setRestingHeartRate(
      profile.physiology.restingHeartRate?.toString() ?? '',
    )
    setVma(profile.physiology.vma?.toString() ?? '')
    setThresholdHeartRate1(
      profile.physiology.thresholdHeartRate1?.toString() ?? '',
    )
    setThresholdHeartRate2(
      profile.physiology.thresholdHeartRate2?.toString() ?? '',
    )
    setSavedSection(null)
  }

  function showSaved(section: string) {
    setSavedSection(section)

    window.setTimeout(() => {
      setSavedSection((current) =>
        current === section ? null : current,
      )
    }, 2000)
  }

  return (
    <main className="min-h-screen bg-base-200">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:py-8">
        <header className="mb-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="flex items-center gap-3">
                <div>
                  <h1 className="text-3xl font-bold tracking-tight text-base-content">
                    Profil sportif
                  </h1>

                  <p className="mt-1 text-sm text-base-content/60">
                    Vos données physiques et physiologiques utilisées par OpenCoach.
                  </p>
                </div>
              </div>
            </div>

          </div>
        </header>

        <div className="space-y-4">
          <ProfileSection
            title="Physique"
            description="Données corporelles utilisées pour les calculs."
          >
            <div className="space-y-6">
              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  label="Taille"
                  type="number"
                  value={heightCm}
                  onChange={setHeightCm}
                  placeholder="185"
                  min="100"
                  max="250"
                  step="1"
                />

                <FormField
                  label="Poids"
                  type="number"
                  value={weightKg}
                  onChange={setWeightKg}
                  placeholder="85"
                  min="30"
                  max="250"
                  step="0.1"
                />
              </div>

              <SectionActions
                saved={savedSection === 'body'}
                onReset={handleResetBody}
                onSave={handleSaveBody}
              />
            </div>
          </ProfileSection>

          <ProfileSection
            title="Physiologie"
            description="Vos principaux paramètres physiologiques."
          >
            <div className="space-y-6">


              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                <FormField
                  label={
                    <MetricTooltip
                      metric="vma"
                      label="VMA"
                    />
                  }
                  type="number"
                  value={vma}
                  onChange={setVma}
                  placeholder="15"
                  min="5"
                  max="30"
                  step="0.1"
                />

                <FormField
                  label={
                    <MetricTooltip
                      metric="max_hr"
                      label="FC maximale"
                    />
                  }
                  type="number"
                  value={maxHeartRate}
                  onChange={setMaxHeartRate}
                  placeholder="194"
                  min="100"
                  max="230"
                  step="1"
                />

                <FormField
                  label="FC de repos"
                  type="number"
                  value={restingHeartRate}
                  onChange={setRestingHeartRate}
                  placeholder="50"
                  min="30"
                  max="120"
                  step="1"
                />

                <FormField
                  label={
                    <MetricTooltip
                      metric="sv1"
                      label="SV1"
                    />
                  }
                  type="number"
                  value={thresholdHeartRate1}
                  onChange={setThresholdHeartRate1}
                  placeholder="160"
                  min="100"
                  max="220"
                  step="1"
                />

                <FormField
                  label={
                    <MetricTooltip
                      metric="sv2"
                      label="SV2"
                    />
                  }
                  type="number"
                  value={thresholdHeartRate2}
                  onChange={setThresholdHeartRate2}
                  placeholder="175"
                  min="100"
                  max="220"
                  step="1"
                />
              </div>

              <SectionActions
                saved={savedSection === 'physiology'}
                onReset={handleResetPhysiology}
                onSave={handleSavePhysiology}
              />
            </div>
          </ProfileSection>

        </div>
      </div>
    </main>
  )
}
