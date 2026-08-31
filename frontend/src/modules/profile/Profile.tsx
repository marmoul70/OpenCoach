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

  const [z1Max, setZ1Max] = useState(
    profile.physiology.heartRateZones.z1?.maxBpm?.toString() ?? '',
  )

  const [z2Max, setZ2Max] = useState(
    profile.physiology.heartRateZones.z2?.maxBpm?.toString() ?? '',
  )

  const [z3Max, setZ3Max] = useState(
    profile.physiology.heartRateZones.z3?.maxBpm?.toString() ?? '',
  )

  const [z4Max, setZ4Max] = useState(
    profile.physiology.heartRateZones.z4?.maxBpm?.toString() ?? '',
  )

  const [z5Max, setZ5Max] = useState(
    profile.physiology.heartRateZones.z5?.maxBpm?.toString() ?? '',
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

        heartRateZones: {
          z1: buildHeartRateZone(
            z1Max,
          ),
          z2: buildHeartRateZone(
            z2Max,
          ),
          z3: buildHeartRateZone(
            z3Max,
          ),
          z4: buildHeartRateZone(
            z4Max,
          ),
          z5: buildHeartRateZone(
            z5Max,
          ),
        },
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
        setZ1Max(
      profile.physiology.heartRateZones.z1?.maxBpm?.toString() ?? '',
    )

        setZ2Max(
      profile.physiology.heartRateZones.z2?.maxBpm?.toString() ?? '',
    )

        setZ3Max(
      profile.physiology.heartRateZones.z3?.maxBpm?.toString() ?? '',
    )

        setZ4Max(
      profile.physiology.heartRateZones.z4?.maxBpm?.toString() ?? '',
    )

        setZ5Max(
      profile.physiology.heartRateZones.z5?.maxBpm?.toString() ?? '',
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

              <div
                className="
                  rounded-xl
                  border border-base-300
                  bg-base-100
                  p-4
                "
              >
                <div className="mb-4">
                  <h3 className="font-semibold text-base-content">
                    Zones de fréquence cardiaque
                  </h3>

                  <p className="mt-1 text-sm text-base-content/55">
                    Plages BPM personnalisées utilisées par OpenCoach
                    pour les consignes d'entraînement.
                  </p>
                </div>

                <div className="space-y-3">
                  <HeartRateZoneRow
                    zone="Z1"
                    label="Récupération"
                    maxValue={z1Max}
                    onMaxChange={setZ1Max}
                  />

                  <HeartRateZoneRow
                    zone="Z2"
                    label="Endurance"
                    maxValue={z2Max}
                    onMaxChange={setZ2Max}
                  />

                  <HeartRateZoneRow
                    zone="Z3"
                    label="Tempo"
                    maxValue={z3Max}
                    onMaxChange={setZ3Max}
                  />

                  <HeartRateZoneRow
                    zone="Z4"
                    label="Seuil"
                    maxValue={z4Max}
                    onMaxChange={setZ4Max}
                  />

                  <HeartRateZoneRow
                    zone="Z5"
                    label="Haute intensité"
                    maxValue={z5Max}
                    onMaxChange={setZ5Max}
                  />
                </div>
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

function buildHeartRateZone(
  maximum: string,
): {
  maxBpm: number
} | undefined {
  const maxBpm =
    parseOptionalNumber(
      maximum,
    )

  if (maxBpm === undefined) {
    return undefined
  }

  return {
    maxBpm,
  }
}


function HeartRateZoneRow({
  zone,
  label,
  maxValue,
  onMaxChange,
}: {
  zone: string
  label: string
  maxValue: string
  onMaxChange: (value: string) => void
}) {
  return (
    <div
      className="
        grid
        grid-cols-[3rem_1fr_6rem_3rem]
        items-center
        gap-3
      "
    >
      <span className="font-semibold text-base-content">
        {zone}
      </span>

      <span className="text-sm text-base-content/65">
        {label}
      </span>

      <input
        type="number"
        value={maxValue}
        min="30"
        max="230"
        step="1"
        placeholder="Max"
        onChange={(event) =>
          onMaxChange(
            event.target.value,
          )
        }
        className="
          input
          input-bordered
          input-sm
          w-full
        "
      />

      <span className="text-xs text-base-content/40">
        bpm
      </span>
    </div>
  )
}
