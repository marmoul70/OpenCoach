import {
  Activity,
  Gauge,
  HeartPulse,
  Pencil,
  Ruler,
  Scale,
  Undo2,
} from 'lucide-react'

import {
  useState,
  type ReactNode,
} from 'react'

import {
  MetricTooltip,
} from '../../components/metrics/MetricTooltip'

import {
  updateAthleteProfile,
  useAthleteProfile,
} from '../../core/profile'

import {
  AthleteEquipmentSection,
  AthleteNutritionSection,
  AthleteTrainingSection,
} from './AthleteProfileSections'

import {
  parseOptionalNumber,
} from './ProfileForm'


export function Profile() {
  const profile =
    useAthleteProfile()

  const [
    heightCm,
    setHeightCm,
  ] = useState(
    profile.body.heightCm
      ?.toString()
    ?? '',
  )

  const [
    weightKg,
    setWeightKg,
  ] = useState(
    profile.body.weightKg
      ?.toString()
    ?? '',
  )

  const [
    maxHeartRate,
    setMaxHeartRate,
  ] = useState(
    profile.physiology
      .maxHeartRate
      ?.toString()
    ?? '',
  )

  const [
    restingHeartRate,
    setRestingHeartRate,
  ] = useState(
    profile.physiology
      .restingHeartRate
      ?.toString()
    ?? '',
  )

  const [
    vma,
    setVma,
  ] = useState(
    profile.physiology.vma
      ?.toString()
    ?? '',
  )

  const [
    thresholdHeartRate1,
    setThresholdHeartRate1,
  ] = useState(
    profile.physiology
      .thresholdHeartRate1
      ?.toString()
    ?? '',
  )

  const [
    thresholdHeartRate2,
    setThresholdHeartRate2,
  ] = useState(
    profile.physiology
      .thresholdHeartRate2
      ?.toString()
    ?? '',
  )

  const [
    z1Max,
    setZ1Max,
  ] = useState(
    profile.physiology
      .heartRateZones
      .z1
      ?.maxBpm
      ?.toString()
    ?? '',
  )

  const [
    z2Max,
    setZ2Max,
  ] = useState(
    profile.physiology
      .heartRateZones
      .z2
      ?.maxBpm
      ?.toString()
    ?? '',
  )

  const [
    z3Max,
    setZ3Max,
  ] = useState(
    profile.physiology
      .heartRateZones
      .z3
      ?.maxBpm
      ?.toString()
    ?? '',
  )

  const [
    z4Max,
    setZ4Max,
  ] = useState(
    profile.physiology
      .heartRateZones
      .z4
      ?.maxBpm
      ?.toString()
    ?? '',
  )

  const [
    z5Max,
    setZ5Max,
  ] = useState(
    profile.physiology
      .heartRateZones
      .z5
      ?.maxBpm
      ?.toString()
    ?? '',
  )

  const [
    editingBody,
    setEditingBody,
  ] = useState(false)

  const [
    editingPhysiology,
    setEditingPhysiology,
  ] = useState(false)

  const [
    savedSection,
    setSavedSection,
  ] = useState<string | null>(
    null,
  )


  async function handleSaveBody() {
    await updateAthleteProfile(
      currentProfile => ({
        ...currentProfile,

        body: {
          ...currentProfile.body,

          heightCm:
            parseOptionalNumber(
              heightCm,
            ),

          weightKg:
            parseOptionalNumber(
              weightKg,
            ),
        },
      }),
    )

    setEditingBody(false)

    showSaved('body')
  }


  async function handleSavePhysiology() {
    await updateAthleteProfile(
      currentProfile => ({
        ...currentProfile,

        physiology: {
          ...currentProfile
            .physiology,

          vma:
            parseOptionalNumber(
              vma,
            ),

          maxHeartRate:
            parseOptionalNumber(
              maxHeartRate,
            ),

          restingHeartRate:
            parseOptionalNumber(
              restingHeartRate,
            ),

          thresholdHeartRate1:
            parseOptionalNumber(
              thresholdHeartRate1,
            ),

          thresholdHeartRate2:
            parseOptionalNumber(
              thresholdHeartRate2,
            ),

          heartRateZones: {
            z1:
              buildHeartRateZone(
                z1Max,
              ),

            z2:
              buildHeartRateZone(
                z2Max,
              ),

            z3:
              buildHeartRateZone(
                z3Max,
              ),

            z4:
              buildHeartRateZone(
                z4Max,
              ),

            z5:
              buildHeartRateZone(
                z5Max,
              ),
          },
        },
      }),
    )

    setEditingPhysiology(false)

    showSaved(
      'physiology',
    )
  }


  function handleResetBody() {
    setHeightCm(
      profile.body.heightCm
        ?.toString()
      ?? '',
    )

    setWeightKg(
      profile.body.weightKg
        ?.toString()
      ?? '',
    )

    setEditingBody(false)
    setSavedSection(null)
  }


  function handleResetPhysiology() {
    setMaxHeartRate(
      profile.physiology
        .maxHeartRate
        ?.toString()
      ?? '',
    )

    setRestingHeartRate(
      profile.physiology
        .restingHeartRate
        ?.toString()
      ?? '',
    )

    setVma(
      profile.physiology.vma
        ?.toString()
      ?? '',
    )

    setThresholdHeartRate1(
      profile.physiology
        .thresholdHeartRate1
        ?.toString()
      ?? '',
    )

    setThresholdHeartRate2(
      profile.physiology
        .thresholdHeartRate2
        ?.toString()
      ?? '',
    )

    setZ1Max(
      profile.physiology
        .heartRateZones
        .z1
        ?.maxBpm
        ?.toString()
      ?? '',
    )

    setZ2Max(
      profile.physiology
        .heartRateZones
        .z2
        ?.maxBpm
        ?.toString()
      ?? '',
    )

    setZ3Max(
      profile.physiology
        .heartRateZones
        .z3
        ?.maxBpm
        ?.toString()
      ?? '',
    )

    setZ4Max(
      profile.physiology
        .heartRateZones
        .z4
        ?.maxBpm
        ?.toString()
      ?? '',
    )

    setZ5Max(
      profile.physiology
        .heartRateZones
        .z5
        ?.maxBpm
        ?.toString()
      ?? '',
    )

    setEditingPhysiology(false)
    setSavedSection(null)
  }


  function showSaved(
    section: string,
  ) {
    setSavedSection(section)

    window.setTimeout(
      () => {
        setSavedSection(
          current =>
            current === section
              ? null
              : current,
        )
      },
      2000,
    )
  }


  return (
    <main
      className="
        min-h-screen
        bg-[#f5f7f6]
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          mx-auto
          max-w-[1380px]
          px-3
          py-4
          sm:px-5
          lg:px-5
          lg:py-[18px]
        "
      >

        {/* PAGE HEADER */}

        <header
          className="
            mb-4
            flex
            items-end
            justify-between
            gap-4
          "
        >
          <div>
            <p
              className="
                text-[10px]
                font-bold
                uppercase
                tracking-[0.13em]
                text-emerald-600
                dark:text-emerald-400
              "
            >
              Athlète
            </p>

            <h1
              className="
                mt-1
                text-[24px]
                font-bold
                tracking-[-0.035em]
                text-slate-950
                dark:text-white
              "
            >
              Profil sportif
            </h1>

            <p
              className="
                mt-1
                max-w-2xl
                text-[11.5px]
                text-slate-400
                dark:text-slate-500
              "
            >
              Les données utilisées par
              OpenCoach pour individualiser
              ton entraînement.
            </p>
          </div>
        </header>


        {/* ATHLETE SNAPSHOT */}

        <section
          className="
            overflow-hidden
            rounded-[14px]
            border
            border-black/[0.07]
            bg-white
            shadow-[0_1px_2px_rgba(15,23,42,0.025)]
            dark:border-white/[0.075]
            dark:bg-[#151b1f]
          "
        >
          <div
            className="
              border-b
              border-black/[0.06]
              px-3.5
              py-3
              dark:border-white/[0.07]
              sm:px-4
            "
          >
            <div
              className="
                flex
                items-center
                gap-2
              "
            >
              <div
                className="
                  flex
                  h-8
                  w-8
                  items-center
                  justify-center
                  rounded-[9px]
                  bg-emerald-50
                  text-emerald-600
                  dark:bg-emerald-500/[0.08]
                  dark:text-emerald-400
                "
              >
                <Activity
                  className="
                    h-4
                    w-4
                  "
                />
              </div>

              <div>
                <h2
                  className="
                    text-[12.5px]
                    font-semibold
                    text-slate-900
                    dark:text-slate-100
                  "
                >
                  Profil athlète
                </h2>

                <p
                  className="
                    mt-0.5
                    text-[9.5px]
                    text-slate-400
                    dark:text-slate-500
                  "
                >
                  Paramètres principaux
                </p>
              </div>
            </div>
          </div>


          <div
            className="
              grid
              grid-cols-2
              divide-x
              divide-y
              divide-black/[0.055]
              dark:divide-white/[0.06]
              sm:grid-cols-4
              sm:divide-y-0
            "
          >
            <SnapshotMetric
              label="VMA"
              value={
                displayValue(
                  vma,
                  '—',
                )
              }
              unit="km/h"
            />

            <SnapshotMetric
              label="FC max"
              value={
                displayValue(
                  maxHeartRate,
                  '—',
                )
              }
              unit="bpm"
            />

            <SnapshotMetric
              label="FC repos"
              value={
                displayValue(
                  restingHeartRate,
                  '—',
                )
              }
              unit="bpm"
            />

            <SnapshotMetric
              label="Poids"
              value={
                displayValue(
                  weightKg,
                  '—',
                )
              }
              unit="kg"
            />
          </div>
        </section>


        {/* MAIN GRID */}

        <div
          className="
            mt-3
            grid
            gap-3
            lg:grid-cols-[0.72fr_1.28fr]
          "
        >

          {/* BODY */}

          <ProfileCard
            title="Physique"
            description="Mensurations corporelles"
            icon={
              <Scale
                className="h-4 w-4"
              />
            }
            editing={editingBody}
            saved={
              savedSection === 'body'
            }
            onEdit={() =>
              setEditingBody(true)
            }
            onCancel={
              handleResetBody
            }
            onSave={
              handleSaveBody
            }
          >
            {editingBody ? (
              <div
                className="
                  grid
                  gap-3
                  sm:grid-cols-2
                  lg:grid-cols-1
                  xl:grid-cols-2
                "
              >
                <ModernField
                  label="Taille"
                  value={heightCm}
                  onChange={
                    setHeightCm
                  }
                  unit="cm"
                  min="100"
                  max="250"
                  step="1"
                />

                <ModernField
                  label="Poids"
                  value={weightKg}
                  onChange={
                    setWeightKg
                  }
                  unit="kg"
                  min="30"
                  max="250"
                  step="0.1"
                />
              </div>
            ) : (
              <div
                className="
                  grid
                  grid-cols-2
                  gap-2
                "
              >
                <ReadMetric
                  icon={
                    <Ruler
                      className="
                        h-3.5
                        w-3.5
                      "
                    />
                  }
                  label="Taille"
                  value={
                    heightCm
                      ? `${heightCm} cm`
                      : 'Non renseignée'
                  }
                />

                <ReadMetric
                  icon={
                    <Scale
                      className="
                        h-3.5
                        w-3.5
                      "
                    />
                  }
                  label="Poids"
                  value={
                    weightKg
                      ? `${weightKg} kg`
                      : 'Non renseigné'
                  }
                />
              </div>
            )}
          </ProfileCard>


          {/* PHYSIOLOGY */}

          <ProfileCard
            title="Physiologie"
            description="Repères de performance"
            icon={
              <HeartPulse
                className="h-4 w-4"
              />
            }
            editing={
              editingPhysiology
            }
            saved={
              savedSection
              === 'physiology'
            }
            onEdit={() =>
              setEditingPhysiology(
                true,
              )
            }
            onCancel={
              handleResetPhysiology
            }
            onSave={
              handleSavePhysiology
            }
          >
            {editingPhysiology ? (
              <div
                className="
                  grid
                  gap-3
                  sm:grid-cols-2
                  xl:grid-cols-5
                "
              >
                <ModernField
                  label={
                    <MetricTooltip
                      metric="vma"
                      label="VMA"
                    />
                  }
                  value={vma}
                  onChange={setVma}
                  unit="km/h"
                  min="5"
                  max="30"
                  step="0.1"
                />

                <ModernField
                  label={
                    <MetricTooltip
                      metric="max_hr"
                      label="FC max"
                    />
                  }
                  value={
                    maxHeartRate
                  }
                  onChange={
                    setMaxHeartRate
                  }
                  unit="bpm"
                  min="100"
                  max="230"
                  step="1"
                />

                <ModernField
                  label="FC repos"
                  value={
                    restingHeartRate
                  }
                  onChange={
                    setRestingHeartRate
                  }
                  unit="bpm"
                  min="30"
                  max="120"
                  step="1"
                />

                <ModernField
                  label={
                    <MetricTooltip
                      metric="sv1"
                      label="SV1"
                    />
                  }
                  value={
                    thresholdHeartRate1
                  }
                  onChange={
                    setThresholdHeartRate1
                  }
                  unit="bpm"
                  min="100"
                  max="220"
                  step="1"
                />

                <ModernField
                  label={
                    <MetricTooltip
                      metric="sv2"
                      label="SV2"
                    />
                  }
                  value={
                    thresholdHeartRate2
                  }
                  onChange={
                    setThresholdHeartRate2
                  }
                  unit="bpm"
                  min="100"
                  max="220"
                  step="1"
                />
              </div>
            ) : (
              <div
                className="
                  grid
                  grid-cols-2
                  gap-2
                  sm:grid-cols-5
                "
              >
                <CompactMetric
                  label="VMA"
                  value={
                    valueWithUnit(
                      vma,
                      'km/h',
                    )
                  }
                />

                <CompactMetric
                  label="FC max"
                  value={
                    valueWithUnit(
                      maxHeartRate,
                      'bpm',
                    )
                  }
                />

                <CompactMetric
                  label="FC repos"
                  value={
                    valueWithUnit(
                      restingHeartRate,
                      'bpm',
                    )
                  }
                />

                <CompactMetric
                  label="SV1"
                  value={
                    valueWithUnit(
                      thresholdHeartRate1,
                      'bpm',
                    )
                  }
                />

                <CompactMetric
                  label="SV2"
                  value={
                    valueWithUnit(
                      thresholdHeartRate2,
                      'bpm',
                    )
                  }
                />
              </div>
            )}
          </ProfileCard>
        </div>


        {/* HR ZONES */}

        <section
          className="
            mt-3
            rounded-[14px]
            border
            border-black/[0.07]
            bg-white
            p-3.5
            shadow-[0_1px_2px_rgba(15,23,42,0.025)]
            dark:border-white/[0.075]
            dark:bg-[#151b1f]
            sm:p-4
          "
        >
          <div
            className="
              flex
              items-start
              justify-between
              gap-4
            "
          >
            <div>
              <div
                className="
                  flex
                  items-center
                  gap-2
                "
              >
                <div
                  className="
                    flex
                    h-8
                    w-8
                    items-center
                    justify-center
                    rounded-[9px]
                    bg-emerald-50
                    text-emerald-600
                    dark:bg-emerald-500/[0.08]
                    dark:text-emerald-400
                  "
                >
                  <Gauge
                    className="
                      h-4
                      w-4
                    "
                  />
                </div>

                <div>
                  <h2
                    className="
                      text-[12.5px]
                      font-semibold
                      text-slate-900
                      dark:text-slate-100
                    "
                  >
                    Zones cardiaques
                  </h2>

                  <p
                    className="
                      mt-0.5
                      text-[9.5px]
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    Limites supérieures
                    utilisées par OpenCoach
                  </p>
                </div>
              </div>
            </div>
          </div>


          <div
            className="
              mt-4
              space-y-2
            "
          >
            <HeartRateZone
              zone="Z1"
              label="Récupération"
              value={z1Max}
              editing={
                editingPhysiology
              }
              onChange={
                setZ1Max
              }
            />

            <HeartRateZone
              zone="Z2"
              label="Endurance"
              value={z2Max}
              editing={
                editingPhysiology
              }
              onChange={
                setZ2Max
              }
            />

            <HeartRateZone
              zone="Z3"
              label="Tempo"
              value={z3Max}
              editing={
                editingPhysiology
              }
              onChange={
                setZ3Max
              }
            />

            <HeartRateZone
              zone="Z4"
              label="Seuil"
              value={z4Max}
              editing={
                editingPhysiology
              }
              onChange={
                setZ4Max
              }
            />

            <HeartRateZone
              zone="Z5"
              label="Haute intensité"
              value={z5Max}
              editing={
                editingPhysiology
              }
              onChange={
                setZ5Max
              }
            />
          </div>
        </section>


        {/* EXISTING ADVANCED SECTIONS */}

        <div
          className="
            mt-3
            space-y-3
          "
        >
          <AthleteTrainingSection
            training={
              profile.training
            }
          />

          <AthleteEquipmentSection
            equipment={
              profile.equipment
            }
          />

          <AthleteNutritionSection
            nutrition={
              profile.nutrition
            }
          />
        </div>
      </div>
    </main>
  )
}


function ProfileCard({
  title,
  description,
  icon,
  editing,
  saved,
  onEdit,
  onCancel,
  onSave,
  children,
}: {
  title: string
  description: string
  icon: ReactNode
  editing: boolean
  saved: boolean
  onEdit: () => void
  onCancel: () => void
  onSave: () => void | Promise<void>
  children: ReactNode
}) {
  return (
    <section
      className="
        rounded-[14px]
        border
        border-black/[0.07]
        bg-white
        p-3.5
        shadow-[0_1px_2px_rgba(15,23,42,0.025)]
        dark:border-white/[0.075]
        dark:bg-[#151b1f]
        sm:p-4
      "
    >
      <div
        className="
          flex
          items-start
          justify-between
          gap-3
        "
      >
        <div
          className="
            flex
            items-center
            gap-2
          "
        >
          <div
            className="
              flex
              h-8
              w-8
              shrink-0
              items-center
              justify-center
              rounded-[9px]
              bg-emerald-50
              text-emerald-600
              dark:bg-emerald-500/[0.08]
              dark:text-emerald-400
            "
          >
            {icon}
          </div>

          <div>
            <h2
              className="
                text-[12.5px]
                font-semibold
                text-slate-900
                dark:text-slate-100
              "
            >
              {title}
            </h2>

            <p
              className="
                mt-0.5
                text-[9.5px]
                text-slate-400
                dark:text-slate-500
              "
            >
              {description}
            </p>
          </div>
        </div>


        {!editing && (
          <button
            type="button"
            onClick={onEdit}
            className="
              flex
              h-8
              items-center
              gap-1.5
              rounded-[8px]
              border
              border-black/[0.06]
              px-2.5
              text-[10px]
              font-semibold
              text-slate-500
              transition
              hover:bg-slate-50
              hover:text-slate-900
              dark:border-white/[0.065]
              dark:text-slate-400
              dark:hover:bg-white/[0.04]
              dark:hover:text-white
            "
          >
            <Pencil
              className="
                h-3
                w-3
              "
            />
            Modifier
          </button>
        )}
      </div>


      <div className="mt-4">
        {children}
      </div>


      {saved && (
        <div
          className="
            mt-3
            rounded-[8px]
            bg-emerald-50
            px-2.5
            py-2
            text-[10px]
            font-semibold
            text-emerald-700
            dark:bg-emerald-500/[0.07]
            dark:text-emerald-400
          "
        >
          Modifications enregistrées
        </div>
      )}


      {editing && (
        <div
          className="
            mt-4
            flex
            items-center
            justify-end
            gap-2
            border-t
            border-black/[0.055]
            pt-3
            dark:border-white/[0.06]
          "
        >
          <button
            type="button"
            onClick={onCancel}
            className="
              flex
              h-8
              items-center
              gap-1.5
              rounded-[8px]
              px-2.5
              text-[10.5px]
              font-semibold
              text-slate-400
              transition
              hover:bg-slate-50
              hover:text-slate-700
              dark:hover:bg-white/[0.04]
              dark:hover:text-slate-200
            "
          >
            <Undo2
              className="
                h-3
                w-3
              "
            />
            Annuler
          </button>

          <button
            type="button"
            onClick={() =>
              void onSave()
            }
            className="
              h-8
              rounded-[8px]
              bg-emerald-600
              px-3
              text-[10.5px]
              font-semibold
              text-white
              transition
              hover:bg-emerald-700
            "
          >
            Enregistrer
          </button>
        </div>
      )}
    </section>
  )
}


function SnapshotMetric({
  label,
  value,
  unit,
}: {
  label: string
  value: string
  unit?: string
}) {
  return (
    <div
      className="
        px-3
        py-3
        text-center
        sm:px-4
      "
    >
      <div
        className="
          flex
          items-baseline
          justify-center
          gap-1
        "
      >
        <span
          className="
            text-[19px]
            font-bold
            tabular-nums
            tracking-[-0.035em]
            text-slate-950
            dark:text-white
          "
        >
          {value}
        </span>

        {unit && value !== '—' && (
          <span
            className="
              text-[9px]
              font-medium
              text-slate-400
              dark:text-slate-500
            "
          >
            {unit}
          </span>
        )}
      </div>

      <p
        className="
          mt-1
          text-[9px]
          font-semibold
          uppercase
          tracking-[0.08em]
          text-slate-400
          dark:text-slate-500
        "
      >
        {label}
      </p>
    </div>
  )
}


function ReadMetric({
  icon,
  label,
  value,
}: {
  icon: ReactNode
  label: string
  value: string
}) {
  return (
    <div
      className="
        rounded-[10px]
        border
        border-black/[0.055]
        bg-slate-50
        p-3
        dark:border-white/[0.055]
        dark:bg-white/[0.022]
      "
    >
      <div
        className="
          flex
          items-center
          gap-1.5
          text-slate-400
        "
      >
        {icon}

        <span
          className="
            text-[9px]
            font-semibold
            uppercase
            tracking-[0.07em]
          "
        >
          {label}
        </span>
      </div>

      <p
        className="
          mt-2
          text-[14px]
          font-semibold
          text-slate-900
          dark:text-slate-100
        "
      >
        {value}
      </p>
    </div>
  )
}


function CompactMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        rounded-[9px]
        bg-slate-50
        px-2.5
        py-2.5
        text-center
        dark:bg-white/[0.025]
      "
    >
      <p
        className="
          text-[12px]
          font-semibold
          tabular-nums
          text-slate-900
          dark:text-slate-100
        "
      >
        {value}
      </p>

      <p
        className="
          mt-1
          text-[8.5px]
          font-semibold
          uppercase
          tracking-[0.07em]
          text-slate-400
          dark:text-slate-500
        "
      >
        {label}
      </p>
    </div>
  )
}


function ModernField({
  label,
  value,
  onChange,
  unit,
  min,
  max,
  step,
}: {
  label: ReactNode
  value: string
  onChange: (
    value: string,
  ) => void
  unit?: string
  min?: string
  max?: string
  step?: string
}) {
  return (
    <label>
      <span
        className="
          mb-1.5
          block
          text-[9.5px]
          font-semibold
          uppercase
          tracking-[0.07em]
          text-slate-400
          dark:text-slate-500
        "
      >
        {label}
      </span>

      <div
        className="
          flex
          h-10
          items-center
          overflow-hidden
          rounded-[9px]
          border
          border-black/[0.07]
          bg-slate-50/60
          transition
          focus-within:border-emerald-500/40
          focus-within:ring-2
          focus-within:ring-emerald-500/[0.08]
          dark:border-white/[0.07]
          dark:bg-white/[0.025]
        "
      >
        <input
          type="number"
          value={value}
          min={min}
          max={max}
          step={step}
          onChange={
            event =>
              onChange(
                event.target.value,
              )
          }
          className="
            min-w-0
            flex-1
            bg-transparent
            px-3
            text-[11.5px]
            font-medium
            text-slate-900
            outline-none
            dark:text-slate-100
          "
        />

        {unit && (
          <span
            className="
              pr-3
              text-[9.5px]
              text-slate-400
              dark:text-slate-500
            "
          >
            {unit}
          </span>
        )}
      </div>
    </label>
  )
}


function HeartRateZone({
  zone,
  label,
  value,
  editing,
  onChange,
}: {
  zone: string
  label: string
  value: string
  editing: boolean
  onChange: (
    value: string,
  ) => void
}) {
  const numericValue =
    Number(value)

  const progress =
    Number.isFinite(
      numericValue,
    )
      ? Math.min(
          100,
          Math.max(
            15,
            (
              numericValue
              / 220
            ) * 100,
          ),
        )
      : 15

  return (
    <div
      className="
        grid
        grid-cols-[34px_92px_1fr_74px]
        items-center
        gap-2
        sm:grid-cols-[38px_130px_1fr_90px]
      "
    >
      <span
        className="
          text-[10px]
          font-bold
          text-emerald-600
          dark:text-emerald-400
        "
      >
        {zone}
      </span>

      <span
        className="
          truncate
          text-[10px]
          font-medium
          text-slate-500
          dark:text-slate-400
        "
      >
        {label}
      </span>

      <div
        className="
          h-[4px]
          overflow-hidden
          rounded-full
          bg-slate-100
          dark:bg-white/[0.055]
        "
      >
        <div
          className="
            h-full
            rounded-full
            bg-emerald-500
          "
          style={{
            width:
              `${progress}%`,
          }}
        />
      </div>

      {editing ? (
        <div
          className="
            flex
            h-8
            items-center
            rounded-[8px]
            border
            border-black/[0.07]
            bg-slate-50
            dark:border-white/[0.07]
            dark:bg-white/[0.025]
          "
        >
          <input
            type="number"
            min="30"
            max="230"
            step="1"
            value={value}
            onChange={
              event =>
                onChange(
                  event.target.value,
                )
            }
            className="
              min-w-0
              flex-1
              bg-transparent
              pl-2
              text-right
              text-[10.5px]
              font-semibold
              text-slate-800
              outline-none
              dark:text-slate-200
            "
          />

          <span
            className="
              px-1.5
              text-[8.5px]
              text-slate-400
            "
          >
            bpm
          </span>
        </div>
      ) : (
        <p
          className="
            text-right
            text-[10.5px]
            font-semibold
            tabular-nums
            text-slate-700
            dark:text-slate-300
          "
        >
          {
            value
              ? `${value} bpm`
              : '—'
          }
        </p>
      )}
    </div>
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

  if (
    maxBpm === undefined
  ) {
    return undefined
  }

  return {
    maxBpm,
  }
}


function displayValue(
  value: string,
  fallback: string,
): string {
  return value.trim()
    || fallback
}


function valueWithUnit(
  value: string,
  unit: string,
): string {
  if (!value.trim()) {
    return '—'
  }

  return `${value} ${unit}`
}
