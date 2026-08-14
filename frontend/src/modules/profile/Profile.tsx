import { useState } from 'react'
import type { ReactNode } from 'react'

import {
  getAthleteProfile,
  updateAthleteProfile,
} from '../../core/profile'

import { ProfileSection } from './ProfileSection'

export function Profile() {
  const profile = getAthleteProfile()

  const [firstName, setFirstName] = useState(profile.identity.firstName)
  const [lastName, setLastName] = useState(profile.identity.lastName)
  const [birthDate, setBirthDate] = useState(profile.identity.birthDate)
  const [gender, setGender] = useState(
    profile.identity.gender ?? 'unspecified',
  )
  const [avatar, setAvatar] = useState(profile.identity.avatar ?? '')

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

  function handleSaveIdentity() {
    updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      identity: {
        ...currentProfile.identity,
        firstName: firstName.trim(),
        lastName: lastName.trim(),
        birthDate,
        gender,
        avatar: avatar || undefined,
      },
    }))

    showSaved('identity')
  }

  function handleSaveBody() {
    updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      body: {
        ...currentProfile.body,
        heightCm: parseOptionalNumber(heightCm),
        weightKg: parseOptionalNumber(weightKg),
      },
    }))

    showSaved('body')
  }

  function handleSavePhysiology() {
    updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      physiology: {
        ...currentProfile.physiology,
        vma: parseOptionalNumber(vma),
        maxHeartRate: parseOptionalNumber(maxHeartRate),
        restingHeartRate: parseOptionalNumber(restingHeartRate),
        thresholdHeartRate1: parseOptionalNumber(thresholdHeartRate1),
        thresholdHeartRate2: parseOptionalNumber(thresholdHeartRate2),
      },
    }))

    showSaved('physiology')
  }

  function handleResetIdentity() {
    setFirstName(profile.identity.firstName)
    setLastName(profile.identity.lastName)
    setBirthDate(profile.identity.birthDate)
    setGender(profile.identity.gender ?? 'unspecified')
    setAvatar(profile.identity.avatar ?? '')
    setSavedSection(null)
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
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto max-w-5xl px-6 py-8">
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">
            Profil athlète
          </h1>

          <p className="mt-2 text-slate-500">
            Vos informations et paramètres utilisés par OpenCoach.
          </p>
        </header>

        <div className="space-y-4">
          <ProfileSection
            title="Identité"
            description="Informations personnelles de votre profil."
            defaultOpen
          >
            <div className="space-y-6">
              <div className="flex items-center gap-5">
                <AvatarPreview
                  firstName={firstName}
                  lastName={lastName}
                  avatar={avatar}
                />

                <div>
                  <p className="font-medium text-slate-900">
                    Photo de profil
                  </p>

                  <p className="mt-1 text-sm text-slate-500">
                    Indiquez l'URL d'une image pour le moment.
                  </p>
                </div>
              </div>

              <div className="grid gap-4 sm:grid-cols-2">
                <FormField
                  label="Prénom"
                  value={firstName}
                  onChange={setFirstName}
                  placeholder="Votre prénom"
                />

                <FormField
                  label="Nom"
                  value={lastName}
                  onChange={setLastName}
                  placeholder="Votre nom"
                />

                <FormField
                  label="Date de naissance"
                  type="date"
                  value={birthDate}
                  onChange={setBirthDate}
                />

                <div>
                  <label
                    htmlFor="profile-gender"
                    className="mb-2 block text-sm font-medium text-slate-700"
                  >
                    Genre
                  </label>

                  <select
                    id="profile-gender"
                    value={gender}
                    onChange={(event) =>
                      setGender(
                        event.target.value as
                          | 'male'
                          | 'female'
                          | 'other'
                          | 'unspecified',
                      )
                    }
                    className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
                  >
                    <option value="unspecified">
                      Non renseigné
                    </option>
                    <option value="male">Homme</option>
                    <option value="female">Femme</option>
                    <option value="other">Autre</option>
                  </select>
                </div>

                <div className="sm:col-span-2">
                  <FormField
                    label="URL de l'avatar"
                    value={avatar}
                    onChange={setAvatar}
                    placeholder="https://..."
                  />
                </div>
              </div>

              <SectionActions
                saved={savedSection === 'identity'}
                onReset={handleResetIdentity}
                onSave={handleSaveIdentity}
              />
            </div>
          </ProfileSection>

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
                  label="VMA"
                  type="number"
                  value={vma}
                  onChange={setVma}
                  placeholder="15"
                  min="5"
                  max="30"
                  step="0.1"
                />

                <FormField
                  label="FC maximale"
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
                  label="SV1"
                  type="number"
                  value={thresholdHeartRate1}
                  onChange={setThresholdHeartRate1}
                  placeholder="160"
                  min="100"
                  max="220"
                  step="1"
                />

                <FormField
                  label="SV2"
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

          <TrainingSection
            training={profile.training}
          />

          <LocationSection location={profile.location} />

          <EquipmentSection equipment={profile.equipment} />

          <NutritionSection nutrition={profile.nutrition} />
        </div>
      </div>
    </main>
  )
}

interface FormFieldProps {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder?: string
  type?: string
  min?: string
  max?: string
  step?: string
}

function FormField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  min,
  max,
  step,
}: FormFieldProps) {
  return (
    <div>
      <label className="mb-2 block text-sm font-medium text-slate-700">
        {label}
      </label>

      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        min={min}
        max={max}
        step={step}
        className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
      />
    </div>
  )
}

interface SectionActionsProps {
  saved: boolean
  onReset: () => void
  onSave: () => void
}

function SectionActions({
  saved,
  onReset,
  onSave,
}: SectionActionsProps) {
  return (
    <div className="flex flex-wrap items-center justify-end gap-3 border-t border-slate-100 pt-5">
      {saved && (
        <p className="mr-auto text-sm font-medium text-emerald-600">
          Paramètres enregistrés.
        </p>
      )}

      <button
        type="button"
        onClick={onReset}
        className="rounded-xl px-4 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
      >
        Annuler
      </button>

      <button
        type="button"
        onClick={onSave}
        className="rounded-xl bg-slate-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-slate-800"
      >
        Enregistrer
      </button>
    </div>
  )
}

interface AvatarPreviewProps {
  firstName: string
  lastName: string
  avatar: string
}

function AvatarPreview({
  firstName,
  lastName,
  avatar,
}: AvatarPreviewProps) {
  if (avatar) {
    return (
      <img
        src={avatar}
        alt="Aperçu de l'avatar"
        className="h-20 w-20 rounded-full border border-slate-200 object-cover"
      />
    )
  }

  return (
    <div className="flex h-20 w-20 items-center justify-center rounded-full bg-slate-100 text-lg font-semibold text-slate-500">
      {getInitials(firstName, lastName)}
    </div>
  )
}

function getInitials(
  firstName: string,
  lastName: string,
): string {
  const initials =
    `${firstName.trim().charAt(0)}${lastName.trim().charAt(0)}`.toUpperCase()

  return initials || 'OC'
}

interface TrainingSectionProps {
  training: {
    weeklySessions?: number
    weeklyDurationMinutes?: number
    weeklyDistanceKm?: number
    availableDays: number[]
    fatigueThreshold?: number
    experience?: 'beginner' | 'intermediate' | 'advanced' | 'expert'
  }
}

function TrainingSection({
  training,
}: TrainingSectionProps) {
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
  const [saved, setSaved] = useState(false)

  function toggleDay(day: number) {
    setAvailableDays((current) =>
      current.includes(day)
        ? current.filter((value) => value !== day)
        : [...current, day].sort(),
    )
  }

  function handleSave() {
    updateAthleteProfile((currentProfile) => ({
      ...currentProfile,
      training: {
        ...currentProfile.training,
        weeklySessions: parseOptionalNumber(weeklySessions),
        weeklyDurationMinutes: parseOptionalNumber(
          weeklyDurationMinutes,
        ),
        weeklyDistanceKm: parseOptionalNumber(weeklyDistanceKm),
        availableDays,
        fatigueThreshold: parseOptionalNumber(fatigueThreshold),
        experience,
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

          <div>
            <label
              htmlFor="profile-experience"
              className="mb-2 block text-sm font-medium text-slate-700"
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
              className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-slate-400 focus:ring-2 focus:ring-slate-200"
            >
              <option value="beginner">Débutant</option>
              <option value="intermediate">Intermédiaire</option>
              <option value="advanced">Avancé</option>
              <option value="expert">Expert</option>
            </select>
          </div>
        </div>

        <div>
          <p className="mb-3 text-sm font-medium text-slate-700">
            Jours disponibles
          </p>

          <div className="grid grid-cols-7 gap-2">
            {[
              ['L', 1],
              ['M', 2],
              ['M', 3],
              ['J', 4],
              ['V', 5],
              ['S', 6],
              ['D', 0],
            ].map(([label, day]) => {
              const numericDay = Number(day)
              const selected = availableDays.includes(numericDay)

              return (
                <button
                  key={numericDay}
                  type="button"
                  onClick={() => toggleDay(numericDay)}
                  aria-pressed={selected}
                  className={[
                    'flex h-11 items-center justify-center rounded-xl border text-sm font-medium transition',
                    selected
                      ? 'border-slate-900 bg-slate-900 text-white'
                      : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50',
                  ].join(' ')}
                >
                  {label}
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

interface ProfileValueProps {
  label: string
  value: unknown
}

interface LocationSectionProps {
  location: {
    name?: string
    latitude?: number
    longitude?: number
  }
}

function LocationSection({
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

        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-sm font-medium text-slate-700">
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

function EquipmentSection({
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
              className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 sm:col-span-2"
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
              className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 sm:col-span-2"
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
              className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 sm:col-span-2"
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
    <div className="flex items-center justify-between gap-4 rounded-xl border border-slate-200 bg-white p-4">
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
      <p className="truncate font-medium text-slate-900">
        {title}
      </p>

      <p className="mt-1 text-sm text-slate-500">
        {details}
      </p>

      <p
        className={
          active
            ? 'mt-1 text-xs font-medium text-emerald-600'
            : 'mt-1 text-xs font-medium text-slate-400'
        }
      >
        {active ? 'Actif' : 'Inactif'}
      </p>
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
        className="rounded-lg px-3 py-2 text-xs font-medium text-slate-500 transition hover:bg-slate-100 hover:text-slate-900"
      >
        {active ? 'Désactiver' : 'Activer'}
      </button>

      <button
        type="button"
        onClick={onRemove}
        className="rounded-lg px-3 py-2 text-xs font-medium text-red-500 transition hover:bg-red-50 hover:text-red-700"
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

function NutritionSection({
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

        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-sm font-medium text-slate-700">
            Utilisation par OpenCoach
          </p>

          <p className="mt-1 text-sm leading-6 text-slate-500">
            Ces valeurs pourront être utilisées pour générer
            automatiquement les recommandations nutritionnelles
            pendant les sorties longues et les compétitions.
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
    <div className="rounded-xl border border-slate-100 bg-slate-50 p-4">
      <p className="text-sm font-medium text-slate-700">
        {label}
      </p>

      <p className="mt-1 text-lg font-semibold text-slate-900">
        {unit}
      </p>

      <p className="mt-1 text-xs text-slate-400">
        {description}
      </p>
    </div>
  )
}

function ProfileValue({
  label,
  value,
}: ProfileValueProps) {
  const displayValue =
    value === undefined ||
    value === null ||
    value === ''
      ? 'Non renseigné'
      : String(value)

  return (
    <div className="rounded-xl bg-slate-50 p-4">
      <p className="text-sm text-slate-500">
        {label}
      </p>

      <p className="mt-1 font-medium text-slate-900">
        {displayValue}
      </p>
    </div>
  )
}

function formatValue(
  value: number | undefined,
  unit: string,
): string {
  if (value === undefined) {
    return 'Non renseigné'
  }

  return `${value} ${unit}`
}

function parseOptionalNumber(
  value: string,
): number | undefined {
  const trimmedValue = value.trim()

  if (!trimmedValue) {
    return undefined
  }

  const parsedValue = Number(trimmedValue)

  return Number.isFinite(parsedValue)
    ? parsedValue
    : undefined
}
