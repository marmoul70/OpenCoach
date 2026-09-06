import {
  Backpack,
  Bike,
  CalendarDays,
  Check,
  Clock3,
  Dumbbell,
  Gauge,
  Mountain,
  Pencil,
  Plus,
  Route,
  Utensils,
  Watch,
} from 'lucide-react'

import {
  useState,
  type ReactNode,
} from 'react'

import {
  updateAthleteProfile,
} from '../../core/profile'

import {
  parseOptionalNumber,
} from './ProfileForm'


/* =====================================================
   TRAINING
   ===================================================== */

interface AthleteTrainingSectionProps {
  training: {
    weeklySessions?: number
    weeklyDurationMinutes?: number
    weeklyDistanceKm?: number
    availableDays: number[]
    fatigueThreshold?: number

    experience?:
      | 'beginner'
      | 'intermediate'
      | 'advanced'
      | 'expert'

    sportDisciplines: Array<
      | 'road_running'
      | 'trail_running'
    >
  }
}


const TRAINING_DAYS = [
  {
    label: 'L',
    name: 'Lundi',
    value: 0,
  },
  {
    label: 'M',
    name: 'Mardi',
    value: 1,
  },
  {
    label: 'M',
    name: 'Mercredi',
    value: 2,
  },
  {
    label: 'J',
    name: 'Jeudi',
    value: 3,
  },
  {
    label: 'V',
    name: 'Vendredi',
    value: 4,
  },
  {
    label: 'S',
    name: 'Samedi',
    value: 5,
  },
  {
    label: 'D',
    name: 'Dimanche',
    value: 6,
  },
] as const


export function AthleteTrainingSection({
  training,
}: AthleteTrainingSectionProps) {
  const [
    editing,
    setEditing,
  ] = useState(false)

  const [
    saved,
    setSaved,
  ] = useState(false)

  const [
    weeklySessions,
    setWeeklySessions,
  ] = useState(
    training.weeklySessions
      ?.toString()
    ?? '',
  )

  const [
    weeklyDurationMinutes,
    setWeeklyDurationMinutes,
  ] = useState(
    training.weeklyDurationMinutes
      ?.toString()
    ?? '',
  )

  const [
    weeklyDistanceKm,
    setWeeklyDistanceKm,
  ] = useState(
    training.weeklyDistanceKm
      ?.toString()
    ?? '',
  )

  const [
    fatigueThreshold,
    setFatigueThreshold,
  ] = useState(
    training.fatigueThreshold
      ?.toString()
    ?? '',
  )

  const [
    experience,
    setExperience,
  ] = useState(
    training.experience
    ?? 'intermediate',
  )

  const [
    availableDays,
    setAvailableDays,
  ] = useState(
    training.availableDays,
  )

  const [
    sportDisciplines,
    setSportDisciplines,
  ] = useState<
    Array<
      | 'road_running'
      | 'trail_running'
    >
  >(
    training.sportDisciplines
    ?? [],
  )


  function toggleDay(
    value: number,
  ) {
    setAvailableDays(
      current =>
        current.includes(value)
          ? current.filter(
              day =>
                day !== value,
            )
          : [
              ...current,
              value,
            ].sort(),
    )
  }


  function toggleDiscipline(
    value:
      | 'road_running'
      | 'trail_running',
  ) {
    setSportDisciplines(
      current =>
        current.includes(value)
          ? current.filter(
              item =>
                item !== value,
            )
          : [
              ...current,
              value,
            ],
    )
  }


  async function handleSave() {
    await updateAthleteProfile(
      current => ({
        ...current,

        training: {
          ...current.training,

          weeklySessions:
            parseOptionalNumber(
              weeklySessions,
            ),

          weeklyDurationMinutes:
            parseOptionalNumber(
              weeklyDurationMinutes,
            ),

          weeklyDistanceKm:
            parseOptionalNumber(
              weeklyDistanceKm,
            ),

          fatigueThreshold:
            parseOptionalNumber(
              fatigueThreshold,
            ),

          experience,
          availableDays,
          sportDisciplines,
        },
      }),
    )

    setEditing(false)
    setSaved(true)

    window.setTimeout(
      () => setSaved(false),
      2000,
    )
  }


  function handleCancel() {
    setWeeklySessions(
      training.weeklySessions
        ?.toString()
      ?? '',
    )

    setWeeklyDurationMinutes(
      training
        .weeklyDurationMinutes
        ?.toString()
      ?? '',
    )

    setWeeklyDistanceKm(
      training.weeklyDistanceKm
        ?.toString()
      ?? '',
    )

    setFatigueThreshold(
      training.fatigueThreshold
        ?.toString()
      ?? '',
    )

    setExperience(
      training.experience
      ?? 'intermediate',
    )

    setAvailableDays(
      training.availableDays,
    )

    setSportDisciplines(
      training.sportDisciplines
      ?? [],
    )

    setEditing(false)
  }


  return (
    <AthleteSection
      title="Entraînement"
      description="Organisation habituelle de ta semaine"
      icon={
        <Dumbbell
          className="h-4 w-4"
        />
      }
      editing={editing}
      saved={saved}
      onEdit={() =>
        setEditing(true)
      }
      onCancel={handleCancel}
      onSave={handleSave}
    >
      {!editing ? (
        <>
          <div
            className="
              grid
              grid-cols-3
              gap-2
            "
          >
            <MetricTile
              icon={
                <CalendarDays
                  className="
                    h-3.5
                    w-3.5
                  "
                />
              }
              label="Séances"
              value={
                weeklySessions
                  ? weeklySessions
                  : '—'
              }
              unit="/ sem."
            />

            <MetricTile
              icon={
                <Clock3
                  className="
                    h-3.5
                    w-3.5
                  "
                />
              }
              label="Volume"
              value={
                weeklyDurationMinutes
                  ? formatDuration(
                      weeklyDurationMinutes,
                    )
                  : '—'
              }
            />

            <MetricTile
              icon={
                <Route
                  className="
                    h-3.5
                    w-3.5
                  "
                />
              }
              label="Distance"
              value={
                weeklyDistanceKm
                  ? weeklyDistanceKm
                  : '—'
              }
              unit={
                weeklyDistanceKm
                  ? 'km'
                  : undefined
              }
            />
          </div>


          <div className="mt-4">
            <SmallHeading>
              Disciplines
            </SmallHeading>

            <div
              className="
                mt-2
                grid
                grid-cols-2
                gap-2
              "
            >
              <DisciplineCard
                icon={
                  <Route
                    className="
                      h-4
                      w-4
                    "
                  />
                }
                label="Route"
                active={
                  sportDisciplines
                    .includes(
                      'road_running',
                    )
                }
              />

              <DisciplineCard
                icon={
                  <Mountain
                    className="
                      h-4
                      w-4
                    "
                  />
                }
                label="Trail"
                active={
                  sportDisciplines
                    .includes(
                      'trail_running',
                    )
                }
              />
            </div>
          </div>


          <div className="mt-4">
            <SmallHeading>
              Jours disponibles
            </SmallHeading>

            <WeekDays
              selected={
                availableDays
              }
            />
          </div>


          <div
            className="
              mt-4
              grid
              grid-cols-2
              gap-2
            "
          >
            <InfoRow
              label="Niveau"
              value={
                experienceLabel(
                  experience,
                )
              }
            />

            <InfoRow
              label="Seuil fatigue"
              value={
                fatigueThreshold
                  ? `${fatigueThreshold} %`
                  : 'Non renseigné'
              }
            />
          </div>
        </>
      ) : (
        <div className="space-y-3.5">
          <div
            className="
              grid
              gap-3
              sm:grid-cols-2
              lg:grid-cols-4
            "
          >
            <ModernNumberField
              label="Séances / semaine"
              value={
                weeklySessions
              }
              onChange={
                setWeeklySessions
              }
              unit="séances"
            />

            <ModernNumberField
              label="Durée / semaine"
              value={
                weeklyDurationMinutes
              }
              onChange={
                setWeeklyDurationMinutes
              }
              unit="min"
            />

            <ModernNumberField
              label="Distance / semaine"
              value={
                weeklyDistanceKm
              }
              onChange={
                setWeeklyDistanceKm
              }
              unit="km"
            />

            <ModernNumberField
              label="Seuil fatigue"
              value={
                fatigueThreshold
              }
              onChange={
                setFatigueThreshold
              }
              unit="%"
            />
          </div>


          <div>
            <SmallHeading>
              Niveau
            </SmallHeading>

            <div
              className="
                mt-2
                grid
                grid-cols-2
                gap-1.5
                sm:grid-cols-4
              "
            >
              {[
                [
                  'beginner',
                  'Débutant',
                ],
                [
                  'intermediate',
                  'Intermédiaire',
                ],
                [
                  'advanced',
                  'Avancé',
                ],
                [
                  'expert',
                  'Expert',
                ],
              ].map(
                option => (
                  <ChoiceButton
                    key={
                      option[0]
                    }
                    active={
                      experience
                      === option[0]
                    }
                    onClick={() =>
                      setExperience(
                        option[0] as
                          typeof experience,
                      )
                    }
                  >
                    {option[1]}
                  </ChoiceButton>
                ),
              )}
            </div>
          </div>


          <div>
            <SmallHeading>
              Disciplines pratiquées
            </SmallHeading>

            <div
              className="
                mt-2
                grid
                grid-cols-2
                gap-2
              "
            >
              <SelectableDiscipline
                active={
                  sportDisciplines
                    .includes(
                      'road_running',
                    )
                }
                icon={
                  <Route
                    className="
                      h-4
                      w-4
                    "
                  />
                }
                label="Course sur route"
                onClick={() =>
                  toggleDiscipline(
                    'road_running',
                  )
                }
              />

              <SelectableDiscipline
                active={
                  sportDisciplines
                    .includes(
                      'trail_running',
                    )
                }
                icon={
                  <Mountain
                    className="
                      h-4
                      w-4
                    "
                  />
                }
                label="Trail"
                onClick={() =>
                  toggleDiscipline(
                    'trail_running',
                  )
                }
              />
            </div>
          </div>


          <div>
            <SmallHeading>
              Jours disponibles
            </SmallHeading>

            <div
              className="
                mt-2
                grid
                grid-cols-7
                gap-1.5
              "
            >
              {TRAINING_DAYS.map(
                day => {
                  const active =
                    availableDays
                      .includes(
                        day.value,
                      )

                  return (
                    <button
                      key={day.value}
                      type="button"
                      title={day.name}
                      aria-label={
                        day.name
                      }
                      aria-pressed={
                        active
                      }
                      onClick={() =>
                        toggleDay(
                          day.value,
                        )
                      }
                      className={[
                        (
                          'flex aspect-square '
                          + 'items-center '
                          + 'justify-center '
                          + 'rounded-[9px] '
                          + 'border '
                          + 'text-[10.5px] '
                          + 'font-bold transition'
                        ),
                        active
                          ? (
                              'border-emerald-500/35 '
                              + 'bg-emerald-50 '
                              + 'text-emerald-700 '
                              + 'dark:bg-emerald-500/[0.08] '
                              + 'dark:text-emerald-400'
                            )
                          : (
                              'border-black/[0.06] '
                              + 'bg-slate-50 '
                              + 'text-slate-400 '
                              + 'dark:border-white/[0.06] '
                              + 'dark:bg-white/[0.02] '
                              + 'dark:text-slate-500'
                            ),
                      ].join(' ')}
                    >
                      {day.label}
                    </button>
                  )
                },
              )}
            </div>
          </div>
        </div>
      )}
    </AthleteSection>
  )
}


/* =====================================================
   EQUIPMENT
   ===================================================== */

interface AthleteEquipmentSectionProps {
  equipment: {
    shoes: Array<{
      id: string
      brand?: string
      model: string
      active: boolean
      category?: 'road' | 'trail' | 'mixed'
      preferred: boolean
      distanceKm: number
      warningDistanceKm?: number
      maxDistanceKm?: number
    }>

    bikes: Array<{
      id: string
      brand?: string
      model: string
      active: boolean
      category?: 'road' | 'gravel' | 'mtb' | 'indoor'
      preferred: boolean
      distanceKm: number
      maintenanceDistanceKm?: number
    }>

    watches: Array<{
      id: string
      brand?: string
      model: string
      active: boolean
    }>
  }
}


function createEquipmentId(): string {
  const cryptoApi =
    globalThis.crypto

  if (
    cryptoApi
    && typeof cryptoApi.randomUUID
      === 'function'
  ) {
    return cryptoApi.randomUUID()
  }

  return [
    'equipment',
    Date.now().toString(36),
    Math.random()
      .toString(36)
      .slice(2, 10),
  ].join('-')
}


function shoeCategoryLabel(
  category?: string,
): string {
  switch (category) {
    case 'road':
      return 'Route'
    case 'trail':
      return 'Trail'
    case 'mixed':
      return 'Mixte'
    default:
      return 'Non définie'
  }
}


function bikeCategoryLabel(
  category?: string,
): string {
  switch (category) {
    case 'road':
      return 'Route'
    case 'gravel':
      return 'Gravel'
    case 'mtb':
      return 'VTT'
    case 'indoor':
      return 'Home trainer'
    default:
      return 'Non défini'
  }
}


function shoeUsageStatus(
  distanceKm: number,
  warningDistanceKm?: number,
  maxDistanceKm?: number,
): 'ok' | 'warning' | 'critical' {
  if (
    maxDistanceKm !== undefined
    && maxDistanceKm > 0
    && distanceKm >= maxDistanceKm
  ) {
    return 'critical'
  }

  if (
    warningDistanceKm !== undefined
    && warningDistanceKm > 0
    && distanceKm >= warningDistanceKm
  ) {
    return 'warning'
  }

  return 'ok'
}


export function AthleteEquipmentSection({
  equipment,
}: AthleteEquipmentSectionProps) {
  const [
    editing,
    setEditing,
  ] = useState(false)

  const [
    saved,
    setSaved,
  ] = useState(false)

  const [
    shoes,
    setShoes,
  ] = useState(
    equipment.shoes,
  )

  const [
    bikes,
    setBikes,
  ] = useState(
    equipment.bikes,
  )

  const [
    watches,
    setWatches,
  ] = useState(
    equipment.watches,
  )

  const [
    shoeBrand,
    setShoeBrand,
  ] = useState('')

  const [
    shoeModel,
    setShoeModel,
  ] = useState('')

  const [
    shoeDistance,
    setShoeDistance,
  ] = useState('0')

  const [
    shoeMaxDistance,
    setShoeMaxDistance,
  ] = useState('')

  const [
    shoeCategory,
    setShoeCategory,
  ] = useState<
    'road' | 'trail' | 'mixed'
  >('trail')

  const [
    shoeWarningDistance,
    setShoeWarningDistance,
  ] = useState('500')

  const [
    bikeBrand,
    setBikeBrand,
  ] = useState('')

  const [
    bikeModel,
    setBikeModel,
  ] = useState('')

  const [
    bikeCategory,
    setBikeCategory,
  ] = useState<
    'road' | 'gravel' | 'mtb' | 'indoor'
  >('road')

  const [
    bikeDistance,
    setBikeDistance,
  ] = useState('0')

  const [
    bikeMaintenanceDistance,
    setBikeMaintenanceDistance,
  ] = useState('')

  const [
    watchBrand,
    setWatchBrand,
  ] = useState('')

  const [
    watchModel,
    setWatchModel,
  ] = useState('')


  function addShoe() {
    const model =
      shoeModel.trim()

    if (!model) {
      return
    }

    setShoes(
      current => [
        ...current,
        {
          id:
            createEquipmentId(),

          brand:
            shoeBrand.trim()
            || undefined,

          model,
          active: true,
          category: shoeCategory,
          preferred: false,

          distanceKm:
            Number(
              shoeDistance,
            ) || 0,

          warningDistanceKm:
            parseOptionalNumber(
              shoeWarningDistance,
            ),

          maxDistanceKm:
            parseOptionalNumber(
              shoeMaxDistance,
            ),
        },
      ],
    )

    setShoeBrand('')
    setShoeModel('')
    setShoeDistance('0')
    setShoeWarningDistance('500')
    setShoeMaxDistance('')
  }


  function addBike() {
    const model =
      bikeModel.trim()

    if (!model) {
      return
    }

    setBikes(
      current => [
        ...current,
        {
          id:
            createEquipmentId(),

          brand:
            bikeBrand.trim()
            || undefined,

          model,
          active: true,
          category: bikeCategory,
          preferred: false,

          distanceKm:
            Number(
              bikeDistance,
            ) || 0,

          maintenanceDistanceKm:
            parseOptionalNumber(
              bikeMaintenanceDistance,
            ),
        },
      ],
    )

    setBikeBrand('')
    setBikeModel('')
    setBikeDistance('0')
    setBikeMaintenanceDistance('')
  }


  function addWatch() {
    const model =
      watchModel.trim()

    if (!model) {
      return
    }

    setWatches(
      current => [
        ...current,
        {
          id:
            createEquipmentId(),

          brand:
            watchBrand.trim()
            || undefined,

          model,
          active: true,
        },
      ],
    )

    setWatchBrand('')
    setWatchModel('')
  }


  function togglePreferredShoe(
    shoeId: string,
  ) {
    setShoes(
      current => {
        const selected =
          current.find(
            shoe =>
              shoe.id === shoeId,
          )

        if (!selected) {
          return current
        }

        const category =
          selected.category
          ?? '__uncategorized__'

        const nextPreferred =
          !selected.preferred

        return current.map(
          shoe => {
            const shoeCategory =
              shoe.category
              ?? '__uncategorized__'

            if (
              shoeCategory
              !== category
            ) {
              return shoe
            }

            if (
              shoe.id === shoeId
            ) {
              return {
                ...shoe,
                preferred:
                  nextPreferred,
              }
            }

            if (!nextPreferred) {
              return shoe
            }

            return {
              ...shoe,
              preferred: false,
            }
          },
        )
      },
    )
  }


  function togglePreferredBike(
    bikeId: string,
  ) {
    setBikes(
      current => {
        const selected =
          current.find(
            bike =>
              bike.id === bikeId,
          )

        if (!selected) {
          return current
        }

        const category =
          selected.category
          ?? '__uncategorized__'

        const nextPreferred =
          !selected.preferred

        return current.map(
          bike => {
            const currentCategory =
              bike.category
              ?? '__uncategorized__'

            if (
              currentCategory
              !== category
            ) {
              return bike
            }

            if (
              bike.id === bikeId
            ) {
              return {
                ...bike,
                preferred:
                  nextPreferred,
              }
            }

            if (!nextPreferred) {
              return bike
            }

            return {
              ...bike,
              preferred: false,
            }
          },
        )
      },
    )
  }


  async function handleSave() {
    await updateAthleteProfile(
      current => ({
        ...current,

        equipment: {
          shoes,
          bikes,
          watches,
        },
      }),
    )

    setEditing(false)
    setSaved(true)

    window.setTimeout(
      () => setSaved(false),
      2000,
    )
  }


  function handleCancel() {
    setShoes(
      equipment.shoes,
    )

    setBikes(
      equipment.bikes,
    )

    setWatches(
      equipment.watches,
    )

    setEditing(false)
  }


  return (
    <AthleteSection
      title="Matériel"
      description="Équipement utilisé à l'entraînement"
      icon={
        <Backpack
          className="h-4 w-4"
        />
      }
      editing={editing}
      saved={saved}
      onEdit={() =>
        setEditing(true)
      }
      onCancel={handleCancel}
      onSave={handleSave}
    >
      <div
        className="
          grid
          gap-3
          lg:grid-cols-3
        "
      >
        {/* ==================================================
            CHAUSSURES
            ================================================== */}

        <div
          className="
            overflow-hidden
            rounded-[14px]
            border
            border-emerald-200/70
            bg-emerald-50/40
            dark:border-emerald-400/10
            dark:bg-emerald-400/[0.025]
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              border-b
              border-emerald-100
              bg-emerald-100/55
              px-3
              py-2
              dark:border-emerald-400/10
              dark:bg-emerald-400/[0.055]
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
                  h-6
                  w-6
                  items-center
                  justify-center
                  rounded-[7px]
                  bg-white
                  text-emerald-600
                  shadow-sm
                  dark:bg-white/[0.06]
                  dark:text-emerald-300
                "
              >
                <Route
                  className="h-3.5 w-3.5"
                />
              </div>

              <div>
                <div
                  className="
                    text-[9.5px]
                    font-bold
                    uppercase
                    tracking-[0.08em]
                    text-emerald-800
                    dark:text-emerald-300
                  "
                >
                  Chaussures
                </div>

                <div
                  className="
                    text-[8.5px]
                    text-emerald-600/70
                    dark:text-emerald-300/50
                  "
                >
                  Running & trail
                </div>
              </div>
            </div>

            <span
              className="
                flex
                h-5
                min-w-5
                items-center
                justify-center
                rounded-full
                bg-white
                px-1.5
                text-[9px]
                font-bold
                text-emerald-700
                shadow-sm
                dark:bg-white/[0.07]
                dark:text-emerald-300
              "
            >
              {shoes.length}
            </span>
          </div>

          <div className="space-y-2 p-2">
            {shoes.length === 0 ? (
              <EmptyEquipment />
            ) : (
              shoes.map(
                shoe => {
                  const status =
                    shoeUsageStatus(
                      shoe.distanceKm,
                      shoe.warningDistanceKm,
                      shoe.maxDistanceKm,
                    )

                  const progress =
                    shoe.maxDistanceKm
                    && shoe.maxDistanceKm > 0
                      ? Math.min(
                          100,
                          (
                            shoe.distanceKm
                            / shoe.maxDistanceKm
                          ) * 100,
                        )
                      : undefined

                  return (
                    <div
                      key={shoe.id}
                      className="
                        relative
                        overflow-hidden
                        rounded-[11px]
                        border
                        border-black/[0.055]
                        bg-white
                        shadow-[0_1px_2px_rgba(15,23,42,0.025)]
                        dark:border-white/[0.06]
                        dark:bg-white/[0.025]
                      "
                    >
                      <div className="p-2.5">
                        <div
                          className="
                            flex
                            items-start
                            gap-2.5
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
                              dark:bg-emerald-400/10
                              dark:text-emerald-300
                            "
                          >
                            <Route
                              className="h-4 w-4"
                            />
                          </div>

                          <div
                            className="
                              min-w-0
                              flex-1
                            "
                          >
                            <div
                              className="
                                flex
                                min-w-0
                                items-center
                                gap-1.5
                                pr-5
                              "
                            >
                              <span
                                className="
                                  truncate
                                  text-[10.5px]
                                  font-semibold
                                  text-slate-800
                                  dark:text-slate-100
                                "
                              >
                                {gearName(
                                  shoe.brand,
                                  shoe.model,
                                )}
                              </span>

                              {shoe.active && (
                                <span
                                  className="
                                    h-1.5
                                    w-1.5
                                    shrink-0
                                    rounded-full
                                    bg-emerald-500
                                  "
                                />
                              )}
                            </div>

                            <div
                              className="
                                mt-0.5
                                text-[9px]
                                text-slate-400
                                dark:text-slate-500
                              "
                            >
                              {shoe.distanceKm}
                              {shoe.maxDistanceKm
                                ? ` / ${shoe.maxDistanceKm}`
                                : ''}
                              {' km'}
                            </div>
                          </div>

                          {shoe.preferred && (
                            <div
                              title="Chaussure préférée"
                              className="
                                absolute
                                right-2.5
                                top-2.5
                                flex
                                h-6
                                w-6
                                items-center
                                justify-center
                                rounded-full
                                bg-amber-50
                                text-[14px]
                                text-amber-500
                                dark:bg-amber-400/10
                              "
                            >
                              ★
                            </div>
                          )}
                        </div>

                        <div
                          className="
                            mt-2
                            flex
                            flex-wrap
                            items-center
                            gap-1.5
                          "
                        >
                          <span
                            className="
                              inline-flex
                              rounded-full
                              border
                              border-emerald-200
                              bg-emerald-50
                              px-2
                              py-0.5
                              text-[8.5px]
                              font-semibold
                              text-emerald-700
                              dark:border-emerald-400/15
                              dark:bg-emerald-400/10
                              dark:text-emerald-300
                            "
                          >
                            {shoeCategoryLabel(
                              shoe.category,
                            )}
                          </span>

                          <span
                            className={`
                              inline-flex
                              items-center
                              gap-1
                              rounded-full
                              px-2
                              py-0.5
                              text-[8.5px]
                              font-semibold
                              ${
                                status === 'critical'
                                  ? `
                                    bg-red-50
                                    text-red-600
                                    dark:bg-red-400/10
                                    dark:text-red-300
                                  `
                                  : status === 'warning'
                                    ? `
                                      bg-amber-50
                                      text-amber-600
                                      dark:bg-amber-400/10
                                      dark:text-amber-300
                                    `
                                    : `
                                      bg-emerald-50
                                      text-emerald-600
                                      dark:bg-emerald-400/10
                                      dark:text-emerald-300
                                    `
                              }
                            `}
                          >
                            <span
                              className={`
                                h-1.5
                                w-1.5
                                rounded-full
                                ${
                                  status
                                  === 'critical'
                                    ? 'bg-red-500'
                                    : status
                                      === 'warning'
                                      ? 'bg-amber-500'
                                      : 'bg-emerald-500'
                                }
                              `}
                            />

                            {status === 'critical'
                              ? 'À remplacer'
                              : status === 'warning'
                                ? 'À surveiller'
                                : 'OK'}
                          </span>
                        </div>

                        {progress !== undefined && (
                          <div
                            className="
                              mt-2
                              h-1
                              overflow-hidden
                              rounded-full
                              bg-slate-100
                              dark:bg-white/[0.06]
                            "
                          >
                            <div
                              className={`
                                h-full
                                rounded-full
                                transition-all
                                ${
                                  status
                                  === 'critical'
                                    ? 'bg-red-500'
                                    : status
                                      === 'warning'
                                      ? 'bg-amber-500'
                                      : 'bg-emerald-500'
                                }
                              `}
                              style={{
                                width:
                                  `${progress}%`,
                              }}
                            />
                          </div>
                        )}

                        {editing && (
                          <div
                            className="
                              mt-2
                              grid
                              grid-cols-2
                              gap-1.5
                            "
                          >
                            <button
                              type="button"
                              onClick={() =>
                                togglePreferredShoe(
                                  shoe.id,
                                )
                              }
                              className="
                                rounded-[7px]
                                border
                                border-black/[0.06]
                                bg-slate-50
                                px-2
                                py-1.5
                                text-[8.5px]
                                font-medium
                                text-slate-600
                                transition
                                hover:bg-slate-100
                                dark:border-white/[0.06]
                                dark:bg-white/[0.035]
                                dark:text-slate-300
                              "
                            >
                              {shoe.preferred
                                ? '★ Retirer'
                                : '☆ Préférée'}
                            </button>

                            <button
                              type="button"
                              onClick={() =>
                                setShoes(
                                  current =>
                                    current.map(
                                      item =>
                                        item.id
                                        === shoe.id
                                          ? {
                                              ...item,
                                              active:
                                                !item.active,
                                            }
                                          : item,
                                    ),
                                )
                              }
                              className="
                                rounded-[7px]
                                border
                                border-black/[0.06]
                                bg-slate-50
                                px-2
                                py-1.5
                                text-[8.5px]
                                font-medium
                                text-slate-600
                                transition
                                hover:bg-slate-100
                                dark:border-white/[0.06]
                                dark:bg-white/[0.035]
                                dark:text-slate-300
                              "
                            >
                              {shoe.active
                                ? 'Désactiver'
                                : 'Activer'}
                            </button>

                            <button
                              type="button"
                              onClick={() =>
                                setShoes(
                                  current =>
                                    current.filter(
                                      item =>
                                        item.id
                                        !== shoe.id,
                                    ),
                                )
                              }
                              className="
                                col-span-2
                                rounded-[7px]
                                border
                                border-red-100
                                bg-red-50/60
                                px-2
                                py-1.5
                                text-[8.5px]
                                font-medium
                                text-red-500
                                transition
                                hover:bg-red-50
                                dark:border-red-400/10
                                dark:bg-red-400/[0.04]
                                dark:text-red-300
                              "
                            >
                              Supprimer
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  )
                },
              )
            )}

            {editing && (
              <AddGearCard
                fields={
                  <>
                    <MiniInput
                      placeholder="Marque"
                      value={shoeBrand}
                      onChange={setShoeBrand}
                    />

                    <MiniInput
                      placeholder="Modèle"
                      value={shoeModel}
                      onChange={setShoeModel}
                    />

                    <label>
                      <span
                        className="
                          mb-1
                          block
                          text-[8.5px]
                          font-semibold
                          uppercase
                          tracking-[0.06em]
                          text-slate-400
                        "
                      >
                        Catégorie
                      </span>

                      <select
                        value={shoeCategory}
                        onChange={
                          event =>
                            setShoeCategory(
                              event.target.value as
                                | 'road'
                                | 'trail'
                                | 'mixed',
                            )
                        }
                        className="
                          h-8
                          w-full
                          rounded-[8px]
                          border
                          border-black/[0.07]
                          bg-white
                          px-2
                          text-[10px]
                          text-slate-700
                          outline-none
                          dark:border-white/[0.07]
                          dark:bg-white/[0.035]
                          dark:text-slate-300
                        "
                      >
                        <option value="road">
                          Route
                        </option>

                        <option value="trail">
                          Trail
                        </option>

                        <option value="mixed">
                          Mixte
                        </option>
                      </select>
                    </label>

                    <MiniInput
                      placeholder="Km actuels"
                      value={shoeDistance}
                      onChange={setShoeDistance}
                      type="number"
                    />

                    <MiniInput
                      placeholder="Alerte à partir de (km)"
                      value={
                        shoeWarningDistance
                      }
                      onChange={
                        setShoeWarningDistance
                      }
                      type="number"
                    />

                    <MiniInput
                      placeholder="Km maximum"
                      value={shoeMaxDistance}
                      onChange={
                        setShoeMaxDistance
                      }
                      type="number"
                    />
                  </>
                }
                onAdd={addShoe}
              />
            )}
          </div>
        </div>

        {/* ==================================================
            VÉLOS
            ================================================== */}

        <div
          className="
            overflow-hidden
            rounded-[14px]
            border
            border-sky-200/70
            bg-sky-50/40
            dark:border-sky-400/10
            dark:bg-sky-400/[0.025]
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              border-b
              border-sky-100
              bg-sky-100/55
              px-3
              py-2
              dark:border-sky-400/10
              dark:bg-sky-400/[0.055]
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
                  h-6
                  w-6
                  items-center
                  justify-center
                  rounded-[7px]
                  bg-white
                  text-sky-600
                  shadow-sm
                  dark:bg-white/[0.06]
                  dark:text-sky-300
                "
              >
                <Bike
                  className="h-3.5 w-3.5"
                />
              </div>

              <div>
                <div
                  className="
                    text-[9.5px]
                    font-bold
                    uppercase
                    tracking-[0.08em]
                    text-sky-800
                    dark:text-sky-300
                  "
                >
                  Vélos
                </div>

                <div
                  className="
                    text-[8.5px]
                    text-sky-600/70
                    dark:text-sky-300/50
                  "
                >
                  Route, gravel & VTT
                </div>
              </div>
            </div>

            <span
              className="
                flex
                h-5
                min-w-5
                items-center
                justify-center
                rounded-full
                bg-white
                px-1.5
                text-[9px]
                font-bold
                text-sky-700
                shadow-sm
                dark:bg-white/[0.07]
                dark:text-sky-300
              "
            >
              {bikes.length}
            </span>
          </div>

          <div className="space-y-2 p-2">
            {bikes.length === 0 ? (
              <EmptyEquipment />
            ) : (
              bikes.map(
                bike => {
                  const maintenanceDue =
                    bike.maintenanceDistanceKm
                    !== undefined
                    && bike.maintenanceDistanceKm > 0
                    && bike.distanceKm
                      >= bike.maintenanceDistanceKm

                  const progress =
                    bike.maintenanceDistanceKm
                    !== undefined
                    && bike.maintenanceDistanceKm > 0
                      ? Math.min(
                          100,
                          (
                            bike.distanceKm
                            / bike.maintenanceDistanceKm
                          ) * 100,
                        )
                      : undefined

                  return (
                    <div
                      key={bike.id}
                      className="
                        relative
                        rounded-[11px]
                        border
                        border-black/[0.055]
                        bg-white
                        p-2.5
                        shadow-[0_1px_2px_rgba(15,23,42,0.025)]
                        dark:border-white/[0.06]
                        dark:bg-white/[0.025]
                      "
                    >
                      <div
                        className="
                          flex
                          items-start
                          gap-2.5
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
                            bg-sky-50
                            text-sky-600
                            dark:bg-sky-400/10
                            dark:text-sky-300
                          "
                        >
                          <Bike
                            className="h-4 w-4"
                          />
                        </div>

                        <div
                          className="
                            min-w-0
                            flex-1
                          "
                        >
                          <div
                            className="
                              flex
                              items-center
                              gap-1.5
                              pr-5
                            "
                          >
                            <span
                              className="
                                truncate
                                text-[10.5px]
                                font-semibold
                                text-slate-800
                                dark:text-slate-100
                              "
                            >
                              {gearName(
                                bike.brand,
                                bike.model,
                              )}
                            </span>

                            {bike.active && (
                              <span
                                className="
                                  h-1.5
                                  w-1.5
                                  shrink-0
                                  rounded-full
                                  bg-emerald-500
                                "
                              />
                            )}
                          </div>

                          <div
                            className="
                              mt-0.5
                              text-[9px]
                              text-slate-400
                              dark:text-slate-500
                            "
                          >
                            {bike.distanceKm}
                            {bike.maintenanceDistanceKm
                              ? ` / ${bike.maintenanceDistanceKm}`
                              : ''}
                            {' km'}
                          </div>
                        </div>

                        {bike.preferred && (
                          <div
                            title="Vélo principal"
                            className="
                              absolute
                              right-2.5
                              top-2.5
                              flex
                              h-6
                              w-6
                              items-center
                              justify-center
                              rounded-full
                              bg-amber-50
                              text-[14px]
                              text-amber-500
                              dark:bg-amber-400/10
                            "
                          >
                            ★
                          </div>
                        )}
                      </div>

                      <div
                        className="
                          mt-2
                          flex
                          flex-wrap
                          items-center
                          gap-1.5
                        "
                      >
                        <span
                          className="
                            rounded-full
                            border
                            border-sky-200
                            bg-sky-50
                            px-2
                            py-0.5
                            text-[8.5px]
                            font-semibold
                            text-sky-700
                            dark:border-sky-400/15
                            dark:bg-sky-400/10
                            dark:text-sky-300
                          "
                        >
                          {bikeCategoryLabel(
                            bike.category,
                          )}
                        </span>

                        <span
                          className={`
                            inline-flex
                            items-center
                            gap-1
                            rounded-full
                            px-2
                            py-0.5
                            text-[8.5px]
                            font-semibold
                            ${
                              maintenanceDue
                                ? `
                                  bg-amber-50
                                  text-amber-600
                                  dark:bg-amber-400/10
                                  dark:text-amber-300
                                `
                                : `
                                  bg-emerald-50
                                  text-emerald-600
                                  dark:bg-emerald-400/10
                                  dark:text-emerald-300
                                `
                            }
                          `}
                        >
                          <span
                            className={`
                              h-1.5
                              w-1.5
                              rounded-full
                              ${
                                maintenanceDue
                                  ? 'bg-amber-500'
                                  : 'bg-emerald-500'
                              }
                            `}
                          />

                          {maintenanceDue
                            ? 'Entretien à prévoir'
                            : 'OK'}
                        </span>
                      </div>

                      {progress !== undefined && (
                        <div
                          className="
                            mt-2
                            h-1
                            overflow-hidden
                            rounded-full
                            bg-slate-100
                            dark:bg-white/[0.06]
                          "
                        >
                          <div
                            className={`
                              h-full
                              rounded-full
                              ${
                                maintenanceDue
                                  ? 'bg-amber-500'
                                  : 'bg-sky-500'
                              }
                            `}
                            style={{
                              width:
                                `${progress}%`,
                            }}
                          />
                        </div>
                      )}

                      {editing && (
                        <div
                          className="
                            mt-2
                            grid
                            grid-cols-2
                            gap-1.5
                          "
                        >
                          <button
                            type="button"
                            onClick={() =>
                              togglePreferredBike(
                                bike.id,
                              )
                            }
                            className="
                              rounded-[7px]
                              border
                              border-black/[0.06]
                              bg-slate-50
                              px-2
                              py-1.5
                              text-[8.5px]
                              font-medium
                              text-slate-600
                              dark:border-white/[0.06]
                              dark:bg-white/[0.035]
                              dark:text-slate-300
                            "
                          >
                            {bike.preferred
                              ? '★ Retirer'
                              : '☆ Principal'}
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              setBikes(
                                current =>
                                  current.map(
                                    item =>
                                      item.id
                                      === bike.id
                                        ? {
                                            ...item,
                                            active:
                                              !item.active,
                                          }
                                        : item,
                                  ),
                              )
                            }
                            className="
                              rounded-[7px]
                              border
                              border-black/[0.06]
                              bg-slate-50
                              px-2
                              py-1.5
                              text-[8.5px]
                              font-medium
                              text-slate-600
                              dark:border-white/[0.06]
                              dark:bg-white/[0.035]
                              dark:text-slate-300
                            "
                          >
                            {bike.active
                              ? 'Désactiver'
                              : 'Activer'}
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              setBikes(
                                current =>
                                  current.filter(
                                    item =>
                                      item.id
                                      !== bike.id,
                                  ),
                              )
                            }
                            className="
                              col-span-2
                              rounded-[7px]
                              border
                              border-red-100
                              bg-red-50/60
                              px-2
                              py-1.5
                              text-[8.5px]
                              font-medium
                              text-red-500
                              dark:border-red-400/10
                              dark:bg-red-400/[0.04]
                              dark:text-red-300
                            "
                          >
                            Supprimer
                          </button>
                        </div>
                      )}
                    </div>
                  )
                },
              )
            )}

            {editing && (
              <AddGearCard
                fields={
                  <>
                    <MiniInput
                      placeholder="Marque"
                      value={bikeBrand}
                      onChange={setBikeBrand}
                    />

                    <MiniInput
                      placeholder="Modèle"
                      value={bikeModel}
                      onChange={setBikeModel}
                    />

                    <label>
                      <span
                        className="
                          mb-1
                          block
                          text-[8.5px]
                          font-semibold
                          uppercase
                          tracking-[0.06em]
                          text-slate-400
                        "
                      >
                        Catégorie
                      </span>

                      <select
                        value={bikeCategory}
                        onChange={
                          event =>
                            setBikeCategory(
                              event.target.value as
                                | 'road'
                                | 'gravel'
                                | 'mtb'
                                | 'indoor',
                            )
                        }
                        className="
                          h-8
                          w-full
                          rounded-[8px]
                          border
                          border-black/[0.07]
                          bg-white
                          px-2
                          text-[10px]
                          text-slate-700
                          outline-none
                          dark:border-white/[0.07]
                          dark:bg-white/[0.035]
                          dark:text-slate-300
                        "
                      >
                        <option value="road">
                          Route
                        </option>

                        <option value="gravel">
                          Gravel
                        </option>

                        <option value="mtb">
                          VTT
                        </option>

                        <option value="indoor">
                          Home trainer
                        </option>
                      </select>
                    </label>

                    <MiniInput
                      placeholder="Km actuels"
                      value={bikeDistance}
                      onChange={setBikeDistance}
                      type="number"
                    />

                    <MiniInput
                      placeholder="Entretien à (km)"
                      value={
                        bikeMaintenanceDistance
                      }
                      onChange={
                        setBikeMaintenanceDistance
                      }
                      type="number"
                    />
                  </>
                }
                onAdd={addBike}
              />
            )}
          </div>
        </div>

        {/* ==================================================
            MONTRES
            ================================================== */}

        <div
          className="
            overflow-hidden
            rounded-[14px]
            border
            border-violet-200/70
            bg-violet-50/40
            dark:border-violet-400/10
            dark:bg-violet-400/[0.025]
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              border-b
              border-violet-100
              bg-violet-100/55
              px-3
              py-2
              dark:border-violet-400/10
              dark:bg-violet-400/[0.055]
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
                  h-6
                  w-6
                  items-center
                  justify-center
                  rounded-[7px]
                  bg-white
                  text-violet-600
                  shadow-sm
                  dark:bg-white/[0.06]
                  dark:text-violet-300
                "
              >
                <Watch
                  className="h-3.5 w-3.5"
                />
              </div>

              <div>
                <div
                  className="
                    text-[9.5px]
                    font-bold
                    uppercase
                    tracking-[0.08em]
                    text-violet-800
                    dark:text-violet-300
                  "
                >
                  Montres
                </div>

                <div
                  className="
                    text-[8.5px]
                    text-violet-600/70
                    dark:text-violet-300/50
                  "
                >
                  Historique appareils
                </div>
              </div>
            </div>

            <span
              className="
                flex
                h-5
                min-w-5
                items-center
                justify-center
                rounded-full
                bg-white
                px-1.5
                text-[9px]
                font-bold
                text-violet-700
                shadow-sm
                dark:bg-white/[0.07]
                dark:text-violet-300
              "
            >
              {watches.length}
            </span>
          </div>

          <div className="space-y-2 p-2">
            {watches.length === 0 ? (
              <EmptyEquipment />
            ) : (
              watches.map(
                watch => (
                  <div
                    key={watch.id}
                    className="
                      rounded-[11px]
                      border
                      border-black/[0.055]
                      bg-white
                      p-2.5
                      shadow-[0_1px_2px_rgba(15,23,42,0.025)]
                      dark:border-white/[0.06]
                      dark:bg-white/[0.025]
                    "
                  >
                    <div
                      className="
                        flex
                        items-center
                        gap-2.5
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
                          bg-violet-50
                          text-violet-600
                          dark:bg-violet-400/10
                          dark:text-violet-300
                        "
                      >
                        <Watch
                          className="h-4 w-4"
                        />
                      </div>

                      <div
                        className="
                          min-w-0
                          flex-1
                        "
                      >
                        <div
                          className="
                            flex
                            items-center
                            gap-1.5
                          "
                        >
                          <span
                            className="
                              truncate
                              text-[10.5px]
                              font-semibold
                              text-slate-800
                              dark:text-slate-100
                            "
                          >
                            {gearName(
                              watch.brand,
                              watch.model,
                            )}
                          </span>

                          {watch.active && (
                            <span
                              className="
                                h-1.5
                                w-1.5
                                rounded-full
                                bg-emerald-500
                              "
                            />
                          )}
                        </div>

                        <div
                          className="
                            mt-0.5
                            text-[9px]
                            text-slate-400
                            dark:text-slate-500
                          "
                        >
                          {watch.active
                            ? 'Montre actuelle'
                            : 'Ancienne montre'}
                        </div>
                      </div>
                    </div>

                    {editing && (
                      <div
                        className="
                          mt-2
                          grid
                          grid-cols-2
                          gap-1.5
                        "
                      >
                        <button
                          type="button"
                          onClick={() =>
                            setWatches(
                              current =>
                                current.map(
                                  item =>
                                    item.id
                                    === watch.id
                                      ? {
                                          ...item,
                                          active:
                                            !item.active,
                                        }
                                      : item,
                                ),
                            )
                          }
                          className="
                            rounded-[7px]
                            border
                            border-black/[0.06]
                            bg-slate-50
                            px-2
                            py-1.5
                            text-[8.5px]
                            font-medium
                            text-slate-600
                            dark:border-white/[0.06]
                            dark:bg-white/[0.035]
                            dark:text-slate-300
                          "
                        >
                          {watch.active
                            ? 'Archiver'
                            : 'Réactiver'}
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            setWatches(
                              current =>
                                current.filter(
                                  item =>
                                    item.id
                                    !== watch.id,
                                ),
                            )
                          }
                          className="
                            rounded-[7px]
                            border
                            border-red-100
                            bg-red-50/60
                            px-2
                            py-1.5
                            text-[8.5px]
                            font-medium
                            text-red-500
                            dark:border-red-400/10
                            dark:bg-red-400/[0.04]
                            dark:text-red-300
                          "
                        >
                          Supprimer
                        </button>
                      </div>
                    )}
                  </div>
                ),
              )
            )}

            {editing && (
              <AddGearCard
                fields={
                  <>
                    <MiniInput
                      placeholder="Marque"
                      value={watchBrand}
                      onChange={setWatchBrand}
                    />

                    <MiniInput
                      placeholder="Modèle"
                      value={watchModel}
                      onChange={setWatchModel}
                    />
                  </>
                }
                onAdd={addWatch}
              />
            )}
          </div>
        </div>
      </div>
    </AthleteSection>
  )
}


/* =====================================================
   NUTRITION
   ===================================================== */

interface AthleteNutritionSectionProps {
  nutrition: {
    carbohydratesPerHour?: number
    fluidsPerHour?: number
    sodiumPerHour?: number
  }
}


export function AthleteNutritionSection({
  nutrition,
}: AthleteNutritionSectionProps) {
  const [
    editing,
    setEditing,
  ] = useState(false)

  const [
    saved,
    setSaved,
  ] = useState(false)

  const [
    carbohydrates,
    setCarbohydrates,
  ] = useState(
    nutrition
      .carbohydratesPerHour
      ?.toString()
    ?? '',
  )

  const [
    fluids,
    setFluids,
  ] = useState(
    nutrition
      .fluidsPerHour
      ?.toString()
    ?? '',
  )

  const [
    sodium,
    setSodium,
  ] = useState(
    nutrition
      .sodiumPerHour
      ?.toString()
    ?? '',
  )


  async function handleSave() {
    await updateAthleteProfile(
      current => ({
        ...current,

        nutrition: {
          carbohydratesPerHour:
            parseOptionalNumber(
              carbohydrates,
            ),

          fluidsPerHour:
            parseOptionalNumber(
              fluids,
            ),

          sodiumPerHour:
            parseOptionalNumber(
              sodium,
            ),
        },
      }),
    )

    setEditing(false)
    setSaved(true)

    window.setTimeout(
      () => setSaved(false),
      2000,
    )
  }


  function handleCancel() {
    setCarbohydrates(
      nutrition
        .carbohydratesPerHour
        ?.toString()
      ?? '',
    )

    setFluids(
      nutrition
        .fluidsPerHour
        ?.toString()
      ?? '',
    )

    setSodium(
      nutrition
        .sodiumPerHour
        ?.toString()
      ?? '',
    )

    setEditing(false)
  }


  return (
    <AthleteSection
      title="Nutrition"
      description="Stratégie d'apport pendant l'effort"
      icon={
        <Utensils
          className="h-4 w-4"
        />
      }
      editing={editing}
      saved={saved}
      onEdit={() =>
        setEditing(true)
      }
      onCancel={handleCancel}
      onSave={handleSave}
    >
      {editing ? (
        <div
          className="
            grid
            gap-3
            sm:grid-cols-3
          "
        >
          <ModernNumberField
            label="Glucides"
            value={
              carbohydrates
            }
            onChange={
              setCarbohydrates
            }
            unit="g/h"
          />

          <ModernNumberField
            label="Hydratation"
            value={fluids}
            onChange={
              setFluids
            }
            unit="ml/h"
          />

          <ModernNumberField
            label="Sodium"
            value={sodium}
            onChange={
              setSodium
            }
            unit="mg/h"
          />
        </div>
      ) : (
        <div
          className="
            grid
            grid-cols-3
            gap-2
          "
        >
          <NutritionMetric
            label="Glucides"
            value={
              carbohydrates
              || '—'
            }
            unit="g/h"
            description="Énergie"
          />

          <NutritionMetric
            label="Hydratation"
            value={
              fluids
              || '—'
            }
            unit="ml/h"
            description="Liquides"
          />

          <NutritionMetric
            label="Sodium"
            value={
              sodium
              || '—'
            }
            unit="mg/h"
            description="Électrolytes"
          />
        </div>
      )}


      {!editing && (
        <div
          className="
            mt-3
            flex
            items-start
            gap-2
            rounded-[9px]
            bg-emerald-50/60
            px-3
            py-2.5
            dark:bg-emerald-500/[0.05]
          "
        >
          <Gauge
            className="
              mt-0.5
              h-3.5
              w-3.5
              shrink-0
              text-emerald-600
              dark:text-emerald-400
            "
          />

          <p
            className="
              text-[10px]
              leading-4
              text-slate-500
              dark:text-slate-400
            "
          >
            Ces repères peuvent être
            utilisés par OpenCoach pour
            préparer les recommandations
            des sorties longues et des
            compétitions.
          </p>
        </div>
      )}
    </AthleteSection>
  )
}


/* =====================================================
   SHARED UI
   ===================================================== */

function AthleteSection({
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
            flex
            items-center
            gap-1.5
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
          <Check
            className="
              h-3
              w-3
            "
          />
          Modifications enregistrées
        </div>
      )}


      {editing && (
        <div
          className="
            mt-4
            flex
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
              h-8
              rounded-[8px]
              px-3
              text-[10.5px]
              font-semibold
              text-slate-400
              hover:bg-slate-50
              hover:text-slate-700
              dark:hover:bg-white/[0.04]
              dark:hover:text-slate-200
            "
          >
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


function MetricTile({
  icon,
  label,
  value,
  unit,
}: {
  icon: ReactNode
  label: string
  value: string
  unit?: string
}) {
  return (
    <div
      className="
        rounded-[10px]
        bg-slate-50
        p-3
        dark:bg-white/[0.025]
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
            text-[8.5px]
            font-semibold
            uppercase
            tracking-[0.07em]
          "
        >
          {label}
        </span>
      </div>

      <div
        className="
          mt-2
          flex
          items-baseline
          gap-1
        "
      >
        <span
          className="
            text-[15px]
            font-bold
            tabular-nums
            text-slate-900
            dark:text-slate-100
          "
        >
          {value}
        </span>

        {unit && (
          <span
            className="
              text-[8.5px]
              text-slate-400
            "
          >
            {unit}
          </span>
        )}
      </div>
    </div>
  )
}


function SmallHeading({
  children,
}: {
  children: ReactNode
}) {
  return (
    <p
      className="
        text-[9px]
        font-bold
        uppercase
        tracking-[0.09em]
        text-slate-400
        dark:text-slate-500
      "
    >
      {children}
    </p>
  )
}


function DisciplineCard({
  icon,
  label,
  active,
}: {
  icon: ReactNode
  label: string
  active: boolean
}) {
  return (
    <div
      className={[
        (
          'flex items-center gap-2 '
          + 'rounded-[9px] border '
          + 'px-2.5 py-2'
        ),
        active
          ? (
              'border-emerald-500/20 '
              + 'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/[0.06] '
              + 'dark:text-emerald-400'
            )
          : (
              'border-black/[0.055] '
              + 'text-slate-400 '
              + 'dark:border-white/[0.055]'
            ),
      ].join(' ')}
    >
      {icon}

      <span
        className="
          text-[10.5px]
          font-semibold
        "
      >
        {label}
      </span>
    </div>
  )
}


function SelectableDiscipline({
  icon,
  label,
  active,
  onClick,
}: {
  icon: ReactNode
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={[
        (
          'flex items-center gap-2 '
          + 'rounded-[9px] border '
          + 'px-3 py-2.5 '
          + 'text-left transition'
        ),
        active
          ? (
              'border-emerald-500/30 '
              + 'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/[0.08] '
              + 'dark:text-emerald-400'
            )
          : (
              'border-black/[0.06] '
              + 'bg-slate-50 '
              + 'text-slate-500 '
              + 'dark:border-white/[0.06] '
              + 'dark:bg-white/[0.02] '
              + 'dark:text-slate-400'
            ),
      ].join(' ')}
    >
      {icon}

      <span
        className="
          text-[10.5px]
          font-semibold
        "
      >
        {label}
      </span>
    </button>
  )
}


function WeekDays({
  selected,
}: {
  selected: number[]
}) {
  return (
    <div
      className="
        mt-2
        grid
        grid-cols-7
        gap-1.5
      "
    >
      {TRAINING_DAYS.map(
        day => {
          const active =
            selected.includes(
              day.value,
            )

          return (
            <div
              key={day.value}
              title={day.name}
              className={[
                (
                  'flex aspect-square '
                  + 'items-center '
                  + 'justify-center '
                  + 'rounded-[9px] '
                  + 'text-[10px] '
                  + 'font-bold'
                ),
                active
                  ? (
                      'bg-emerald-600 '
                      + 'text-white'
                    )
                  : (
                      'bg-slate-50 '
                      + 'text-slate-300 '
                      + 'dark:bg-white/[0.025] '
                      + 'dark:text-slate-600'
                    ),
              ].join(' ')}
            >
              {day.label}
            </div>
          )
        },
      )}
    </div>
  )
}


function InfoRow({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        flex
        items-center
        justify-between
        rounded-[9px]
        border
        border-black/[0.055]
        px-2.5
        py-2
        dark:border-white/[0.055]
      "
    >
      <span
        className="
          text-[9.5px]
          text-slate-400
        "
      >
        {label}
      </span>

      <span
        className="
          text-[10px]
          font-semibold
          text-slate-700
          dark:text-slate-300
        "
      >
        {value}
      </span>
    </div>
  )
}


function ChoiceButton({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        (
          'h-9 rounded-[8px] border '
          + 'text-[10px] '
          + 'font-semibold transition'
        ),
        active
          ? (
              'border-emerald-500/30 '
              + 'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/[0.08] '
              + 'dark:text-emerald-400'
            )
          : (
              'border-black/[0.06] '
              + 'bg-slate-50 '
              + 'text-slate-400 '
              + 'dark:border-white/[0.06] '
              + 'dark:bg-white/[0.02]'
            ),
      ].join(' ')}
    >
      {children}
    </button>
  )
}


function ModernNumberField({
  label,
  value,
  onChange,
  unit,
}: {
  label: string
  value: string
  onChange: (
    value: string,
  ) => void
  unit?: string
}) {
  return (
    <label>
      <span
        className="
          mb-1.5
          block
          text-[9px]
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
          rounded-[9px]
          border
          border-black/[0.07]
          bg-slate-50/60
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
              text-[9px]
              text-slate-400
            "
          >
            {unit}
          </span>
        )}
      </div>
    </label>
  )
}












function AddGearCard({
  fields,
  onAdd,
}: {
  fields: ReactNode
  onAdd: () => void
}) {
  return (
    <div
      className="
        rounded-[10px]
        border
        border-dashed
        border-black/[0.08]
        p-2.5
        dark:border-white/[0.07]
      "
    >
      <div
        className="
          grid
          gap-1.5
        "
      >
        {fields}
      </div>

      <button
        type="button"
        onClick={onAdd}
        className="
          mt-2
          flex
          h-8
          w-full
          items-center
          justify-center
          gap-1
          rounded-[8px]
          bg-emerald-50
          text-[9.5px]
          font-semibold
          text-emerald-700
          hover:bg-emerald-100
          dark:bg-emerald-500/[0.07]
          dark:text-emerald-400
        "
      >
        <Plus
          className="
            h-3
            w-3
          "
        />
        Ajouter
      </button>
    </div>
  )
}


function MiniInput({
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  value: string
  onChange: (
    value: string,
  ) => void
  placeholder: string
  type?: string
}) {
  return (
    <input
      type={type}
      value={value}
      placeholder={placeholder}
      onChange={
        event =>
          onChange(
            event.target.value,
          )
      }
      className="
        h-8
        w-full
        rounded-[7px]
        border
        border-black/[0.06]
        bg-slate-50
        px-2
        text-[10px]
        text-slate-700
        outline-none
        placeholder:text-slate-300
        focus:border-emerald-500/35
        dark:border-white/[0.06]
        dark:bg-white/[0.025]
        dark:text-slate-300
        dark:placeholder:text-slate-600
      "
    />
  )
}


function EmptyEquipment() {
  return (
    <div
      className="
        rounded-[9px]
        border
        border-dashed
        border-black/[0.06]
        px-3
        py-4
        text-center
        text-[9.5px]
        text-slate-300
        dark:border-white/[0.05]
        dark:text-slate-600
      "
    >
      Aucun équipement
    </div>
  )
}


function NutritionMetric({
  label,
  value,
  unit,
  description,
}: {
  label: string
  value: string
  unit: string
  description: string
}) {
  return (
    <div
      className="
        rounded-[10px]
        bg-slate-50
        px-3
        py-3
        text-center
        dark:bg-white/[0.025]
      "
    >
      <div>
        <span
          className="
            text-[16px]
            font-bold
            tabular-nums
            text-slate-900
            dark:text-slate-100
          "
        >
          {value}
        </span>

        {value !== '—' && (
          <span
            className="
              ml-1
              text-[8.5px]
              text-slate-400
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
          text-slate-600
          dark:text-slate-400
        "
      >
        {label}
      </p>

      <p
        className="
          mt-0.5
          text-[8px]
          text-slate-300
          dark:text-slate-600
        "
      >
        {description}
      </p>
    </div>
  )
}


function gearName(
  brand: string | undefined,
  model: string,
): string {
  return [
    brand,
    model,
  ]
    .filter(Boolean)
    .join(' ')
}


function formatDuration(
  value: string,
): string {
  const minutes =
    Number(value)

  if (
    !Number.isFinite(minutes)
    || minutes <= 0
  ) {
    return '—'
  }

  const hours =
    Math.floor(
      minutes / 60,
    )

  const rest =
    minutes % 60

  if (hours === 0) {
    return `${rest} min`
  }

  if (rest === 0) {
    return `${hours} h`
  }

  return `${hours}h${String(
    rest,
  ).padStart(2, '0')}`
}


function experienceLabel(
  value:
    | 'beginner'
    | 'intermediate'
    | 'advanced'
    | 'expert',
): string {
  switch (value) {
    case 'beginner':
      return 'Débutant'

    case 'advanced':
      return 'Avancé'

    case 'expert':
      return 'Expert'

    default:
      return 'Intermédiaire'
  }
}
