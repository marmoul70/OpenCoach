import { useState } from 'react'
import { UserRound } from 'lucide-react'

import {
  updateAthleteProfile,
  useAthleteProfile,
} from '../../core/profile'

import { ProfileSection } from './ProfileSection'

const MAX_AVATAR_SIZE = 2 * 1024 * 1024

const AVATAR_ACCEPTED_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
]

function readAvatarFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    if (!AVATAR_ACCEPTED_TYPES.includes(file.type)) {
      reject(
        new Error(
          'Format non pris en charge. Utilisez une image JPG, PNG ou WebP.',
        ),
      )
      return
    }

    if (file.size > MAX_AVATAR_SIZE) {
      reject(
        new Error("L'image ne doit pas dépasser 2 Mo."),
      )
      return
    }

    const reader = new FileReader()

    reader.onload = () => {
      if (typeof reader.result !== 'string') {
        reject(
          new Error("Impossible de lire l'image."),
        )
        return
      }

      resolve(reader.result)
    }

    reader.onerror = () => {
      reject(
        new Error("Impossible de lire l'image."),
      )
    }

    reader.readAsDataURL(file)
  })
}

export function PersonalProfile() {
  const profile = useAthleteProfile()

  const [firstName, setFirstName] = useState(
    profile.identity.firstName,
  )
  const [lastName, setLastName] = useState(
    profile.identity.lastName,
  )
  const [birthDate, setBirthDate] = useState(
    profile.identity.birthDate,
  )
  const [gender, setGender] = useState(
    profile.identity.gender ?? 'unspecified',
  )
  const [avatar, setAvatar] = useState(
    profile.identity.avatar ?? '',
  )
  const [avatarError, setAvatarError] = useState<string | null>(
    null,
  )
  const [saved, setSaved] = useState(false)

  async function handleAvatarChange(
    event: React.ChangeEvent<HTMLInputElement>,
  ) {
    const file = event.target.files?.[0]

    if (!file) {
      return
    }

    setAvatarError(null)

    try {
      const dataUrl = await readAvatarFile(file)
      setAvatar(dataUrl)
    } catch (reason: unknown) {
      setAvatarError(
        reason instanceof Error
          ? reason.message
          : "Impossible de charger l'image.",
      )
    }

    event.target.value = ''
  }

  async function handleSave() {
    await updateAthleteProfile((currentProfile) => ({
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

    setSaved(true)

    window.setTimeout(() => {
      setSaved(false)
    }, 2000)
  }

  function handleReset() {
    setFirstName(profile.identity.firstName)
    setLastName(profile.identity.lastName)
    setBirthDate(profile.identity.birthDate)
    setGender(profile.identity.gender ?? 'unspecified')
    setAvatar(profile.identity.avatar ?? '')
    setAvatarError(null)
    setSaved(false)
  }

  return (
    <main className="min-h-screen bg-base-200">
      <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 lg:py-8">
        <header className="mb-8">
          <div className="flex items-center gap-3">
            <div className="flex size-11 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <UserRound size={24} strokeWidth={2} />
            </div>

            <div>
              <h1 className="text-3xl font-bold tracking-tight text-base-content">
                Profil personnel
              </h1>

              <p className="mt-1 text-sm text-base-content/60">
                Vos informations personnelles et votre photo de profil.
              </p>
            </div>
          </div>
        </header>

        <ProfileSection
          title="Identité"
          description="Informations personnelles de votre profil."
          defaultOpen
        >
          <div className="space-y-6">
            <div className="card border border-base-300 bg-base-200/50">
              <div className="card-body">
                <div className="flex flex-col gap-5 sm:flex-row sm:items-center">
                  <AvatarPreview
                    firstName={firstName}
                    lastName={lastName}
                    avatar={avatar}
                  />

                  <div className="flex-1">
                    <p className="font-medium text-base-content">
                      Photo de profil
                    </p>

                    <p className="mt-1 text-sm text-base-content/60">
                      Ajoutez une photo qui sera utilisée dans votre
                      profil et dans la barre de navigation.
                    </p>

                    <div className="mt-4 flex flex-wrap gap-2">
                      <label className="btn btn-primary btn-sm">
                        Choisir une photo

                        <input
                          type="file"
                          accept="image/jpeg,image/png,image/webp"
                          className="hidden"
                          onChange={handleAvatarChange}
                        />
                      </label>

                      {avatar && (
                        <button
                          type="button"
                          className="btn btn-ghost btn-sm"
                          onClick={() => {
                            setAvatar('')
                            setAvatarError(null)
                          }}
                        >
                          Supprimer
                        </button>
                      )}
                    </div>

                    <p className="mt-2 text-xs text-base-content/50">
                      JPG, PNG ou WebP · 2 Mo maximum
                    </p>

                    {avatarError && (
                      <div className="alert alert-error mt-3 py-2 text-sm">
                        <span>{avatarError}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                label="Prénom"
                value={firstName}
                onChange={setFirstName}
                placeholder="Prénom"
              />

              <FormField
                label="Nom"
                value={lastName}
                onChange={setLastName}
                placeholder="Nom"
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
                  className="fieldset-legend"
                >
                  Sexe
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
                  className="select select-bordered w-full"
                >
                  <option value="unspecified">
                    Non renseigné
                  </option>
                  <option value="male">Homme</option>
                  <option value="female">Femme</option>
                  <option value="other">Autre</option>
                </select>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-3 border-t border-base-300 pt-5">
              {saved && (
                <div className="alert alert-success mr-auto w-auto py-2 text-sm">
                  <span>Paramètres enregistrés.</span>
                </div>
              )}

              <button
                type="button"
                onClick={handleReset}
                className="btn btn-ghost"
              >
                Annuler
              </button>

              <button
                type="button"
                onClick={handleSave}
                className="btn btn-primary"
              >
                Enregistrer
              </button>
            </div>
          </div>
        </ProfileSection>
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
}

function FormField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: FormFieldProps) {
  return (
    <fieldset className="fieldset">
      <label className="fieldset-legend">
        {label}
      </label>

      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        className="input input-bordered w-full"
      />
    </fieldset>
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
      <div className="avatar">
        <div className="w-20 rounded-full border border-base-300">
          <img
            src={avatar}
            alt="Aperçu de l'avatar"
          />
        </div>
      </div>
    )
  }

  return (
    <div className="avatar placeholder">
      <div className="w-20 rounded-full bg-primary text-primary-content">
        <span className="text-lg font-semibold">
          {getInitials(firstName, lastName)}
        </span>
      </div>
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