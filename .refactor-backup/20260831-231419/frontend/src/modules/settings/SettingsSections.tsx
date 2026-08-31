import { useState } from 'react'
import type { ReactNode } from 'react'

import {
  updateAthleteProfile,
} from '../../core/profile'

import { ProfileSection } from '../profile/ProfileSection'
import {
  FormField,
  SectionActions,
  parseOptionalNumber,
} from '../profile/ProfileForm'


interface TrainingSectionProps {
  training: {
    weeklySessions?: number
    weeklyDurationMinutes?: number
    weeklyDistanceKm?: number
    availableDays: number[]
    fatigueThreshold?: number
    experience?: 'beginner' | 'intermediate' | 'advanced' | 'expert'
    sportDisciplines: Array<
      'road_running'
      | 'trail_running'
    >
  }
}

export function TrainingSection({
  training,
}: TrainingSectionProps) {
    const SPORT_DISCIPLINES = [
    {
      value: 'road_running',
      label: 'Course sur route',
      description: (
        'Route, piste cyclable et terrain roulant.'
      ),
    },
    {
      value: 'trail_running',
      label: 'Trail',
      description: (
        'Sentiers, dénivelé et terrain naturel.'
      ),
    },
  ] as const

  const TRAINING_DAYS = [
    { label: 'L', value: 0, name: 'Lundi' },
    { label: 'M', value: 1, name: 'Mardi' },
    { label: 'M', value: 2, name: 'Mercredi' },
    { label: 'J', value: 3, name: 'Jeudi' },
    { label: 'V', value: 4, name: 'Vendredi' },
    { label: 'S', value: 5, name: 'Samedi' },
    { label: 'D', value: 6, name: 'Dimanche' },
  ] as const

  const [weeklySessions, setWeeklySessions] = useState(
    training.weeklySessions?.toString() ?? '',
  )
  const [weeklyDurationMinutes, setWeeklyDurationMinutes] = useState(
    training.weeklyDurationMinutes?.toString() ?? '',
  )
  const [weeklyDistanceKm, setWeeklyDistanceKm] = useState(
    training.weeklyDistanceKm?.toString() ?? '',
  )
  const [availableDays, setAvailableDays] = useState(
    training.availableDays,
  )
  const [fatigueThreshold, setFatigueThreshold] = useState(
    training.fatigueThreshold?.toString() ?? '',
  )
  const [experience, setExperience] = useState(
    training.experience ?? 'intermediate',
  )

  const [
    sportDisciplines,
    setSportDisciplines,
  ] = useState<
    Array<
      'road_running'
      | 'trail_running'
    >
  >(
    training.sportDisciplines ?? [],
  )
  const [saved, setSaved] = useState(false)

  function toggleDay(day: number) {
    setAvailableDays((current) =>
      current.includes(day)
        ? current.filter((value) => value !== day)
        : [...current, day].sort(),
    )
  }

  function toggleSportDiscipline(
    discipline:
      | 'road_running'
      | 'trail_running',
  ) {
    setSportDisciplines(
      (current) => (
        current.includes(
          discipline,
        )
          ? current.filter(
              (value) =>
                value !== discipline,
            )
          : [
              ...current,
              discipline,
            ]
      ),
    )
  }


  async function handleSave() {
    await updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      training: {
        ...currentProfile.training,
        weeklySessions: parseOptionalNumber(weeklySessions),
        weeklyDurationMinutes: parseOptionalNumber(
          weeklyDurationMinutes,
        ),
        weeklyDistanceKm: parseOptionalNumber(
          weeklyDistanceKm,
        ),
        availableDays,
        fatigueThreshold: parseOptionalNumber(
          fatigueThreshold,
        ),
        experience,
        sportDisciplines,
      },
    }))

    setSaved(true)

    window.setTimeout(() => {
      setSaved(false)
    }, 2000)
  }

  function handleReset() {
    setWeeklySessions(
      training.weeklySessions?.toString() ?? '',
    )
    setWeeklyDurationMinutes(
      training.weeklyDurationMinutes?.toString() ?? '',
    )
    setWeeklyDistanceKm(
      training.weeklyDistanceKm?.toString() ?? '',
    )
    setAvailableDays(training.availableDays)
    setFatigueThreshold(
      training.fatigueThreshold?.toString() ?? '',
    )
    setExperience(training.experience ?? 'intermediate')
    setSportDisciplines(
      training.sportDisciplines ?? [],
    )
    setSaved(false)
  }

  return (
    <ProfileSection
      title="Entraînement"
      description="Paramètres utilisés pour construire votre entraînement."
    >
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <FormField
            label="Séances / semaine"
            type="number"
            value={weeklySessions}
            onChange={setWeeklySessions}
            placeholder="4"
            min="1"
            max="14"
            step="1"
          />

          <FormField
            label="Durée / semaine"
            type="number"
            value={weeklyDurationMinutes}
            onChange={setWeeklyDurationMinutes}
            placeholder="300"
            min="0"
            max="2000"
            step="15"
          />

          <FormField
            label="Distance / semaine"
            type="number"
            value={weeklyDistanceKm}
            onChange={setWeeklyDistanceKm}
            placeholder="40"
            min="0"
            max="500"
            step="1"
          />

          <FormField
            label="Seuil de fatigue"
            type="number"
            value={fatigueThreshold}
            onChange={setFatigueThreshold}
            placeholder="70"
            min="0"
            max="100"
            step="1"
          />

          <fieldset className="fieldset">
            <label
              htmlFor="profile-experience"
              className="fieldset-legend"
            >
              Niveau d'expérience
            </label>

            <select
              id="profile-experience"
              value={experience}
              onChange={(event) =>
                setExperience(
                  event.target.value as
                    | 'beginner'
                    | 'intermediate'
                    | 'advanced'
                    | 'expert',
                )
              }
              className="select select-bordered w-full"
            >
              <option value="beginner">Débutant</option>
              <option value="intermediate">Intermédiaire</option>
              <option value="advanced">Avancé</option>
              <option value="expert">Expert</option>
            </select>
          </fieldset>

        </div>

        <div>
          <p className="text-sm font-semibold text-base-content">
            Disciplines pratiquées
          </p>

          <p className="mt-1 text-sm text-base-content/50">
            Sélectionnez toutes les disciplines que vous pratiquez.
            OpenCoach pourra adapter les séances et les tests proposés.
          </p>

          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {SPORT_DISCIPLINES.map(
              (discipline) => {
                const selected =
                  sportDisciplines.includes(
                    discipline.value,
                  )

                return (
                  <button
                    key={
                      discipline.value
                    }
                    type="button"
                    aria-pressed={
                      selected
                    }
                    onClick={() =>
                      toggleSportDiscipline(
                        discipline.value,
                      )
                    }
                    className={[
                      'flex items-start gap-3',
                      'rounded-xl border p-4',
                      'text-left transition',
                      selected
                        ? (
                            'border-primary '
                            + 'bg-primary/10'
                          )
                        : (
                            'border-base-300 '
                            + 'bg-base-100 '
                            + 'hover:bg-base-200/60'
                          ),
                    ].join(' ')}
                  >
                    <input
                      type="checkbox"
                      checked={selected}
                      readOnly
                      tabIndex={-1}
                      className="
                        checkbox
                        checkbox-primary
                        mt-0.5
                        shrink-0
                      "
                      aria-hidden="true"
                    />

                    <span>
                      <span className="block font-semibold text-base-content">
                        {
                          discipline.label
                        }
                      </span>

                      <span className="mt-1 block text-sm text-base-content/50">
                        {
                          discipline.description
                        }
                      </span>
                    </span>
                  </button>
                )
              },
            )}
          </div>
        </div>


        <div>
          <p className="text-sm font-semibold text-base-content">
            Jours disponibles
          </p>

          <div className="grid grid-cols-7 gap-2">
            {TRAINING_DAYS.map((day) => {
              const selected = availableDays.includes(day.value)

              return (
                <button
                  key={day.value}
                  type="button"
                  onClick={() => toggleDay(day.value)}
                  aria-pressed={selected}
                  aria-label={day.name}
                  title={day.name}
                  className={[
                    'btn h-11 min-h-11 flex-1',
                    selected
                      ? 'btn-primary'
                      : 'btn-ghost border border-base-300 bg-base-100',
                  ].join(' ')}
                >
                  {day.label}
                </button>
              )
            })}
          </div>

          <p className="mt-2 text-xs text-slate-400">
            Sélectionnez les jours pendant lesquels vous pouvez
            habituellement vous entraîner.
          </p>
        </div>

        <SectionActions
          saved={saved}
          onReset={handleReset}
          onSave={handleSave}
        />
      </div>
    </ProfileSection>
  )
}


interface LocationSectionProps {
  location: {
    name?: string
    latitude?: number
    longitude?: number
  }
}

export function LocationSection({
  location,
}: LocationSectionProps) {
  const [name, setName] = useState(location.name ?? '')
  const [latitude, setLatitude] = useState(
    location.latitude?.toString() ?? '',
  )
  const [longitude, setLongitude] = useState(
    location.longitude?.toString() ?? '',
  )
  const [saved, setSaved] = useState(false)

  function handleSave() {
    updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      location: {
        name: name.trim() || undefined,
        latitude: parseOptionalNumber(latitude),
        longitude: parseOptionalNumber(longitude),
      },
    }))

    setSaved(true)

    window.setTimeout(() => {
      setSaved(false)
    }, 2000)
  }

  function handleReset() {
    setName(location.name ?? '')
    setLatitude(location.latitude?.toString() ?? '')
    setLongitude(location.longitude?.toString() ?? '')
    setSaved(false)
  }

  return (
    <ProfileSection
      title="Localisation"
      description="Localisation principale utilisée par les services comme la météo."
    >
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-3">
          <div className="sm:col-span-3">
            <FormField
              label="Lieu"
              value={name}
              onChange={setName}
              placeholder="Lure"
            />
          </div>

          <FormField
            label="Latitude"
            type="number"
            value={latitude}
            onChange={setLatitude}
            placeholder="47.685"
            min="-90"
            max="90"
            step="0.000001"
          />

          <FormField
            label="Longitude"
            type="number"
            value={longitude}
            onChange={setLongitude}
            placeholder="6.496"
            min="-180"
            max="180"
            step="0.000001"
          />
        </div>

        <div className="alert bg-base-200">
          <p className="text-sm font-semibold text-base-content">
            Utilisation
          </p>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            Ces coordonnées seront utilisées par OpenCoach pour
            récupérer les données météo correspondant à votre lieu
            d'entraînement.
          </p>
        </div>

        <SectionActions
          saved={saved}
          onReset={handleReset}
          onSave={handleSave}
        />
      </div>
    </ProfileSection>
  )
}

interface EquipmentSectionProps {
  equipment: {
    shoes: Array<{
      id: string
      brand?: string
      model: string
      active: boolean
      distanceKm: number
      maxDistanceKm?: number
    }>
    bikes: Array<{
      id: string
      brand?: string
      model: string
      active: boolean
      distanceKm: number
    }>
    watches: Array<{
      id: string
      brand?: string
      model: string
      active: boolean
    }>
  }
}

export function EquipmentSection({
  equipment,
}: EquipmentSectionProps) {
  const [shoes, setShoes] = useState(equipment.shoes)
  const [bikes, setBikes] = useState(equipment.bikes)
  const [watches, setWatches] = useState(equipment.watches)

  const [newShoeBrand, setNewShoeBrand] = useState('')
  const [newShoeModel, setNewShoeModel] = useState('')
  const [newShoeDistance, setNewShoeDistance] = useState('0')
  const [newShoeMaxDistance, setNewShoeMaxDistance] = useState('')

  const [newBikeBrand, setNewBikeBrand] = useState('')
  const [newBikeModel, setNewBikeModel] = useState('')

  const [newWatchBrand, setNewWatchBrand] = useState('')
  const [newWatchModel, setNewWatchModel] = useState('')

  const [saved, setSaved] = useState(false)

  function addShoe() {
    const model = newShoeModel.trim()

    if (!model) {
      return
    }

    setShoes((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        brand: newShoeBrand.trim() || undefined,
        model,
        active: true,
        distanceKm: Number(newShoeDistance) || 0,
        maxDistanceKm: parseOptionalNumber(
          newShoeMaxDistance,
        ),
      },
    ])

    setNewShoeBrand('')
    setNewShoeModel('')
    setNewShoeDistance('0')
    setNewShoeMaxDistance('')
  }

  function addBike() {
    const model = newBikeModel.trim()

    if (!model) {
      return
    }

    setBikes((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        brand: newBikeBrand.trim() || undefined,
        model,
        active: true,
        distanceKm: 0,
      },
    ])

    setNewBikeBrand('')
    setNewBikeModel('')
  }

  function addWatch() {
    const model = newWatchModel.trim()

    if (!model) {
      return
    }

    setWatches((current) => [
      ...current,
      {
        id: crypto.randomUUID(),
        brand: newWatchBrand.trim() || undefined,
        model,
        active: true,
      },
    ])

    setNewWatchBrand('')
    setNewWatchModel('')
  }

  function handleSave() {
    updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      equipment: {
        shoes,
        bikes,
        watches,
      },
    }))

    setSaved(true)

    window.setTimeout(() => {
      setSaved(false)
    }, 2000)
  }

  function handleReset() {
    setShoes(equipment.shoes)
    setBikes(equipment.bikes)
    setWatches(equipment.watches)
    setSaved(false)
  }

  function removeShoe(id: string) {
    setShoes((current) =>
      current.filter((shoe) => shoe.id !== id),
    )
  }

  function removeBike(id: string) {
    setBikes((current) =>
      current.filter((bike) => bike.id !== id),
    )
  }

  function removeWatch(id: string) {
    setWatches((current) =>
      current.filter((watch) => watch.id !== id),
    )
  }

  function toggleShoe(id: string) {
    setShoes((current) =>
      current.map((shoe) =>
        shoe.id === id
          ? { ...shoe, active: !shoe.active }
          : shoe,
      ),
    )
  }

  function toggleBike(id: string) {
    setBikes((current) =>
      current.map((bike) =>
        bike.id === id
          ? { ...bike, active: !bike.active }
          : bike,
      ),
    )
  }

  function toggleWatch(id: string) {
    setWatches((current) =>
      current.map((watch) =>
        watch.id === id
          ? { ...watch, active: !watch.active }
          : watch,
      ),
    )
  }

  return (
    <ProfileSection
      title="Matériel"
      description="Gérez votre équipement sportif et son utilisation."
    >
      <div className="space-y-8">
        <EquipmentGroup title="Chaussures">
          {shoes.map((shoe) => (
            <EquipmentItemCard key={shoe.id}>
              <EquipmentInfo
                title={`${shoe.brand ? `${shoe.brand} ` : ''}${shoe.model}`}
                details={`${shoe.distanceKm} km${
                  shoe.maxDistanceKm
                    ? ` / ${shoe.maxDistanceKm} km`
                    : ''
                }`}
                active={shoe.active}
              />

              <EquipmentActions
                active={shoe.active}
                onToggle={() => toggleShoe(shoe.id)}
                onRemove={() => removeShoe(shoe.id)}
              />
            </EquipmentItemCard>
          ))}

          <div className="grid gap-3 rounded-xl border border-dashed border-slate-200 p-4 sm:grid-cols-2">
            <FormField
              label="Marque"
              value={newShoeBrand}
              onChange={setNewShoeBrand}
              placeholder="Asics"
            />

            <FormField
              label="Modèle"
              value={newShoeModel}
              onChange={setNewShoeModel}
              placeholder="Trabuco"
            />

            <FormField
              label="Kilométrage"
              type="number"
              value={newShoeDistance}
              onChange={setNewShoeDistance}
              min="0"
              step="1"
            />

            <FormField
              label="Durée maximale"
              type="number"
              value={newShoeMaxDistance}
              onChange={setNewShoeMaxDistance}
              placeholder="800"
              min="0"
              step="10"
            />

            <button
              type="button"
              onClick={addShoe}
              className="btn btn-outline sm:col-span-2"
            >
              + Ajouter une chaussure
            </button>
          </div>
        </EquipmentGroup>

        <EquipmentGroup title="Vélos">
          {bikes.map((bike) => (
            <EquipmentItemCard key={bike.id}>
              <EquipmentInfo
                title={`${bike.brand ? `${bike.brand} ` : ''}${bike.model}`}
                details={`${bike.distanceKm} km`}
                active={bike.active}
              />

              <EquipmentActions
                active={bike.active}
                onToggle={() => toggleBike(bike.id)}
                onRemove={() => removeBike(bike.id)}
              />
            </EquipmentItemCard>
          ))}

          <div className="grid gap-3 rounded-xl border border-dashed border-slate-200 p-4 sm:grid-cols-2">
            <FormField
              label="Marque"
              value={newBikeBrand}
              onChange={setNewBikeBrand}
              placeholder="Cube"
            />

            <FormField
              label="Modèle"
              value={newBikeModel}
              onChange={setNewBikeModel}
              placeholder="Nuroad"
            />

            <button
              type="button"
              onClick={addBike}
              className="btn btn-outline sm:col-span-2"
            >
              + Ajouter un vélo
            </button>
          </div>
        </EquipmentGroup>

        <EquipmentGroup title="Montres">
          {watches.map((watch) => (
            <EquipmentItemCard key={watch.id}>
              <EquipmentInfo
                title={`${watch.brand ? `${watch.brand} ` : ''}${watch.model}`}
                details="Montre connectée"
                active={watch.active}
              />

              <EquipmentActions
                active={watch.active}
                onToggle={() => toggleWatch(watch.id)}
                onRemove={() => removeWatch(watch.id)}
              />
            </EquipmentItemCard>
          ))}

          <div className="grid gap-3 rounded-xl border border-dashed border-slate-200 p-4 sm:grid-cols-2">
            <FormField
              label="Marque"
              value={newWatchBrand}
              onChange={setNewWatchBrand}
              placeholder="Suunto"
            />

            <FormField
              label="Modèle"
              value={newWatchModel}
              onChange={setNewWatchModel}
              placeholder="Race"
            />

            <button
              type="button"
              onClick={addWatch}
              className="btn btn-outline sm:col-span-2"
            >
              + Ajouter une montre
            </button>
          </div>
        </EquipmentGroup>

        <SectionActions
          saved={saved}
          onReset={handleReset}
          onSave={handleSave}
        />
      </div>
    </ProfileSection>
  )
}

function EquipmentGroup({
  title,
  children,
}: {
  title: string
  children: ReactNode
}) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold text-slate-900">
        {title}
      </h3>

      {children}
    </div>
  )
}

function EquipmentItemCard({
  children,
}: {
  children: ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-box border border-base-300 bg-base-100 p-4">
      {children}
    </div>
  )
}

function EquipmentInfo({
  title,
  details,
  active,
}: {
  title: string
  details: string
  active: boolean
}) {
  return (
    <div className="min-w-0">
      <p className="truncate font-medium text-base-content">
        {title}
      </p>

      <p className="mt-1 text-sm text-base-content/60">
        {details}
      </p>

      <span
        className={[
          'badge mt-2',
          active ? 'badge-success' : 'badge-ghost',
        ].join(' ')}
      >
        {active ? 'Actif' : 'Inactif'}
      </span>
    </div>
  )
}

function EquipmentActions({
  active,
  onToggle,
  onRemove,
}: {
  active: boolean
  onToggle: () => void
  onRemove: () => void
}) {
  return (
    <div className="flex shrink-0 gap-2">
      <button
        type="button"
        onClick={onToggle}
        className="btn btn-sm btn-ghost"
      >
        {active ? 'Désactiver' : 'Activer'}
      </button>

      <button
        type="button"
        onClick={onRemove}
        className="btn btn-sm btn-error btn-outline"
      >
        Supprimer
      </button>
    </div>
  )
}

interface NutritionSectionProps {
  nutrition: {
    carbohydratesPerHour?: number
    fluidsPerHour?: number
    sodiumPerHour?: number
  }
}

export function NutritionSection({
  nutrition,
}: NutritionSectionProps) {
  const [carbohydratesPerHour, setCarbohydratesPerHour] = useState(
    nutrition.carbohydratesPerHour?.toString() ?? '',
  )
  const [fluidsPerHour, setFluidsPerHour] = useState(
    nutrition.fluidsPerHour?.toString() ?? '',
  )
  const [sodiumPerHour, setSodiumPerHour] = useState(
    nutrition.sodiumPerHour?.toString() ?? '',
  )
  const [saved, setSaved] = useState(false)

  function handleSave() {
    updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      nutrition: {
        carbohydratesPerHour: parseOptionalNumber(
          carbohydratesPerHour,
        ),
        fluidsPerHour: parseOptionalNumber(fluidsPerHour),
        sodiumPerHour: parseOptionalNumber(sodiumPerHour),
      },
    }))

    setSaved(true)

    window.setTimeout(() => {
      setSaved(false)
    }, 2000)
  }

  function handleReset() {
    setCarbohydratesPerHour(
      nutrition.carbohydratesPerHour?.toString() ?? '',
    )
    setFluidsPerHour(
      nutrition.fluidsPerHour?.toString() ?? '',
    )
    setSodiumPerHour(
      nutrition.sodiumPerHour?.toString() ?? '',
    )
    setSaved(false)
  }

  return (
    <ProfileSection
      title="Nutrition"
      description="Paramètres utilisés pour personnaliser votre stratégie nutritionnelle."
    >
      <div className="space-y-6">
        <div className="grid gap-4 sm:grid-cols-3">
          <FormField
            label="Glucides"
            type="number"
            value={carbohydratesPerHour}
            onChange={setCarbohydratesPerHour}
            placeholder="60"
            min="0"
            max="150"
            step="5"
          />

          <FormField
            label="Hydratation"
            type="number"
            value={fluidsPerHour}
            onChange={setFluidsPerHour}
            placeholder="500"
            min="0"
            max="2000"
            step="50"
          />

          <FormField
            label="Sodium"
            type="number"
            value={sodiumPerHour}
            onChange={setSodiumPerHour}
            placeholder="500"
            min="0"
            max="2000"
            step="50"
          />
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <NutritionInfo
            label="Glucides"
            unit="g/h"
            description="Apport énergétique"
          />

          <NutritionInfo
            label="Hydratation"
            unit="ml/h"
            description="Apport hydrique"
          />

          <NutritionInfo
            label="Sodium"
            unit="mg/h"
            description="Apport électrolytique"
          />
        </div>

        <div className="alert bg-base-200">
          <div>
            <p className="font-semibold">
              Utilisation par OpenCoach
            </p>

            <p className="mt-1 text-sm text-base-content/60">
              Ces valeurs pourront être utilisées pour générer
              automatiquement les recommandations nutritionnelles
              pendant les sorties longues et les compétitions.
            </p>
          </div>
        </div>

        <SectionActions
          saved={saved}
          onReset={handleReset}
          onSave={handleSave}
        />
      </div>
    </ProfileSection>
  )
}

function NutritionInfo({
  label,
  unit,
  description,
}: {
  label: string
  unit: string
  description: string
}) {
  return (
    <div className="card border border-base-300 bg-base-200">
      <div className="card-body p-4">
        <p className="text-sm font-medium text-base-content/70">
          {label}
        </p>

        <p className="text-lg font-semibold text-base-content">
          {unit}
        </p>

        <p className="text-xs text-base-content/50">
          {description}
        </p>
      </div>
    </div>
  )
}
