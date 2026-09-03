import {
  Camera,
  Check,
  Pencil,
  Trash2,
  UserRound,
} from 'lucide-react'

import {
  useState,
  type ChangeEvent,
  type ReactNode,
} from 'react'

import {
  updateAthleteProfile,
  useAthleteProfile,
} from '../../core/profile'

import {
  AccountIdentitySection,
} from '../auth/AccountIdentityCard'

import {
  AccountSecurityCard,
} from '../auth/AccountSecurityCard'

const MAX_AVATAR_SIZE =
  2 * 1024 * 1024

const AVATAR_ACCEPTED_TYPES = [
  'image/jpeg',
  'image/png',
  'image/webp',
]


function readAvatarFile(
  file: File,
): Promise<string> {
  return new Promise(
    (resolve, reject) => {
      if (
        !AVATAR_ACCEPTED_TYPES
          .includes(file.type)
      ) {
        reject(
          new Error(
            'Format non pris en charge. '
            + 'Utilisez une image JPG, PNG ou WebP.',
          ),
        )

        return
      }

      if (
        file.size
        > MAX_AVATAR_SIZE
      ) {
        reject(
          new Error(
            "L'image ne doit pas dépasser 2 Mo.",
          ),
        )

        return
      }

      const reader =
        new FileReader()

      reader.onload = () => {
        if (
          typeof reader.result
          !== 'string'
        ) {
          reject(
            new Error(
              "Impossible de lire l'image.",
            ),
          )

          return
        }

        resolve(
          reader.result,
        )
      }

      reader.onerror = () => {
        reject(
          new Error(
            "Impossible de lire l'image.",
          ),
        )
      }

      reader.readAsDataURL(
        file,
      )
    },
  )
}


export function PersonalProfile() {
  const profile =
    useAthleteProfile()

  const [
    editing,
    setEditing,
  ] = useState(false)

  const [
    firstName,
    setFirstName,
  ] = useState(
    profile.identity.firstName,
  )

  const [
    lastName,
    setLastName,
  ] = useState(
    profile.identity.lastName,
  )

  const [
    birthDate,
    setBirthDate,
  ] = useState(
    profile.identity.birthDate,
  )

  const [
    gender,
    setGender,
  ] = useState(
    profile.identity.gender
    ?? 'unspecified',
  )

  const [
    avatar,
    setAvatar,
  ] = useState(
    profile.identity.avatar
    ?? '',
  )

  const [
    avatarError,
    setAvatarError,
  ] = useState<
    string | null
  >(null)

  const [
    saved,
    setSaved,
  ] = useState(false)


  async function handleAvatarChange(
    event:
      ChangeEvent<HTMLInputElement>,
  ) {
    const file =
      event.target.files?.[0]

    if (!file) {
      return
    }

    setAvatarError(null)

    try {
      const dataUrl =
        await readAvatarFile(
          file,
        )

      setAvatar(dataUrl)
    } catch (reason: unknown) {
      setAvatarError(
        reason instanceof Error
          ? reason.message
          : (
              "Impossible de charger "
              + "l'image."
            ),
      )
    }

    event.target.value = ''
  }


  async function handleSave() {
    await updateAthleteProfile(
      currentProfile => ({
        ...currentProfile,

        identity: {
          ...currentProfile
            .identity,

          firstName:
            firstName.trim(),

          lastName:
            lastName.trim(),

          birthDate,
          gender,

          avatar:
            avatar
            || undefined,
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


  function handleReset() {
    setFirstName(
      profile.identity.firstName,
    )

    setLastName(
      profile.identity.lastName,
    )

    setBirthDate(
      profile.identity.birthDate,
    )

    setGender(
      profile.identity.gender
      ?? 'unspecified',
    )

    setAvatar(
      profile.identity.avatar
      ?? '',
    )

    setAvatarError(null)
    setSaved(false)
    setEditing(false)
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

        {/* HEADER */}

        <header
          className="
            mb-4
          "
        >
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
            Compte
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
            Profil personnel
          </h1>

          <p
            className="
              mt-1
              text-[11.5px]
              text-slate-400
              dark:text-slate-500
            "
          >
            Ton identité et ta photo
            utilisées dans OpenCoach.
          </p>
        </header>



        {/* IDENTITY CARD */}

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

          {/* HERO */}

          <div
            className="
              relative
              overflow-hidden
              border-b
              border-black/[0.06]
              px-4
              py-5
              dark:border-white/[0.065]
              sm:px-5
            "
          >
            <div
              className="
                pointer-events-none
                absolute
                -right-16
                -top-24
                h-52
                w-52
                rounded-full
                bg-emerald-500/[0.055]
                blur-3xl
                dark:bg-emerald-400/[0.035]
              "
            />

            <div
              className="
                relative
                flex
                items-center
                gap-4
              "
            >
              <AvatarPreview
                firstName={
                  firstName
                }
                lastName={
                  lastName
                }
                avatar={
                  avatar
                }
              />

              <div
                className="
                  min-w-0
                  flex-1
                "
              >
                <p
                  className="
                    truncate
                    text-[18px]
                    font-bold
                    tracking-[-0.025em]
                    text-slate-950
                    dark:text-white
                  "
                >
                  {
                    fullName(
                      firstName,
                      lastName,
                    )
                  }
                </p>

                <p
                  className="
                    mt-1
                    text-[10.5px]
                    text-slate-400
                    dark:text-slate-500
                  "
                >
                  {
                    identitySummary(
                      birthDate,
                      gender,
                    )
                  }
                </p>

                {saved && (
                  <div
                    className="
                      mt-2
                      inline-flex
                      items-center
                      gap-1
                      rounded-full
                      bg-emerald-50
                      px-2
                      py-1
                      text-[9px]
                      font-semibold
                      text-emerald-700
                      dark:bg-emerald-500/[0.08]
                      dark:text-emerald-400
                    "
                  >
                    <Check
                      className="
                        h-3
                        w-3
                      "
                    />

                    Enregistré
                  </div>
                )}
              </div>


              {!editing && (
                <button
                  type="button"
                  onClick={() =>
                    setEditing(
                      true,
                    )
                  }
                  className="
                    flex
                    h-8
                    shrink-0
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
          </div>


          {!editing ? (

            /* ==============================
               READ MODE
               ============================== */

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
              <IdentityMetric
                label="Prénom"
                value={
                  firstName
                  || '—'
                }
              />

              <IdentityMetric
                label="Nom"
                value={
                  lastName
                  || '—'
                }
              />

              <IdentityMetric
                label="Naissance"
                value={
                  formatBirthDate(
                    birthDate,
                  )
                }
              />

              <IdentityMetric
                label="Sexe"
                value={
                  genderLabel(
                    gender,
                  )
                }
              />
            </div>

          ) : (

            /* ==============================
               EDIT MODE
               ============================== */

            <div
              className="
                p-4
                sm:p-5
              "
            >

              {/* AVATAR EDIT */}

              <div
                className="
                  flex
                  flex-col
                  gap-3
                  rounded-[11px]
                  border
                  border-black/[0.055]
                  bg-slate-50
                  p-3
                  dark:border-white/[0.055]
                  dark:bg-white/[0.022]
                  sm:flex-row
                  sm:items-center
                "
              >
                <div
                  className="
                    flex
                    h-9
                    w-9
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
                  <Camera
                    className="
                      h-4
                      w-4
                    "
                  />
                </div>

                <div className="flex-1">
                  <p
                    className="
                      text-[11px]
                      font-semibold
                      text-slate-800
                      dark:text-slate-200
                    "
                  >
                    Photo de profil
                  </p>

                  <p
                    className="
                      mt-0.5
                      text-[9.5px]
                      text-slate-400
                      dark:text-slate-500
                    "
                  >
                    JPG, PNG ou WebP
                    · 2 Mo maximum
                  </p>
                </div>

                <div
                  className="
                    flex
                    gap-1.5
                  "
                >
                  <label
                    className="
                      flex
                      h-8
                      cursor-pointer
                      items-center
                      gap-1.5
                      rounded-[8px]
                      bg-emerald-600
                      px-2.5
                      text-[10px]
                      font-semibold
                      text-white
                      transition
                      hover:bg-emerald-700
                    "
                  >
                    <Camera
                      className="
                        h-3
                        w-3
                      "
                    />

                    Choisir

                    <input
                      type="file"
                      accept="
                        image/jpeg,
                        image/png,
                        image/webp
                      "
                      className="hidden"
                      onChange={
                        handleAvatarChange
                      }
                    />
                  </label>

                  {avatar && (
                    <button
                      type="button"
                      aria-label="
                        Supprimer la photo
                      "
                      onClick={() => {
                        setAvatar('')
                        setAvatarError(
                          null,
                        )
                      }}
                      className="
                        flex
                        h-8
                        w-8
                        items-center
                        justify-center
                        rounded-[8px]
                        text-slate-400
                        transition
                        hover:bg-red-50
                        hover:text-red-500
                        dark:hover:bg-red-500/[0.07]
                      "
                    >
                      <Trash2
                        className="
                          h-3.5
                          w-3.5
                        "
                      />
                    </button>
                  )}
                </div>
              </div>


              {avatarError && (
                <div
                  className="
                    mt-2
                    rounded-[8px]
                    border
                    border-red-500/15
                    bg-red-50
                    px-2.5
                    py-2
                    text-[10px]
                    text-red-600
                    dark:bg-red-500/[0.06]
                    dark:text-red-400
                  "
                >
                  {avatarError}
                </div>
              )}


              {/* FORM */}

              <div
                className="
                  mt-4
                  grid
                  gap-3
                  sm:grid-cols-2
                "
              >
                <ModernField
                  label="Prénom"
                  value={
                    firstName
                  }
                  onChange={
                    setFirstName
                  }
                  placeholder="Prénom"
                />

                <ModernField
                  label="Nom"
                  value={
                    lastName
                  }
                  onChange={
                    setLastName
                  }
                  placeholder="Nom"
                />

                <ModernField
                  label="Date de naissance"
                  type="date"
                  value={
                    birthDate
                  }
                  onChange={
                    setBirthDate
                  }
                />

                <GenderField
                  value={
                    gender
                  }
                  onChange={
                    setGender
                  }
                />
              </div>


              {/* ACTIONS */}

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
                  onClick={
                    handleReset
                  }
                  className="
                    h-8
                    rounded-[8px]
                    px-3
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
                  Annuler
                </button>

                <button
                  type="button"
                  onClick={() =>
                    void handleSave()
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
            </div>
          )}

          <AccountIdentitySection />
        </section>

        <div className="mt-4">
          <AccountSecurityCard />
        </div>
      </div>
    </main>
  )
}


function AvatarPreview({
  firstName,
  lastName,
  avatar,
}: {
  firstName: string
  lastName: string
  avatar: string
}) {
  if (avatar) {
    return (
      <div
        className="
          h-[64px]
          w-[64px]
          shrink-0
          overflow-hidden
          rounded-full
          border
          border-black/[0.08]
          bg-slate-100
          shadow-sm
          dark:border-white/[0.08]
        "
      >
        <img
          src={avatar}
          alt="
            Aperçu de l'avatar
          "
          className="
            h-full
            w-full
            object-cover
          "
        />
      </div>
    )
  }

  return (
    <div
      className="
        flex
        h-[64px]
        w-[64px]
        shrink-0
        items-center
        justify-center
        rounded-full
        bg-emerald-600
        text-white
        shadow-sm
      "
    >
      {
        firstName
        || lastName
          ? (
              <span
                className="
                  text-[17px]
                  font-bold
                  tracking-[-0.02em]
                "
              >
                {
                  getInitials(
                    firstName,
                    lastName,
                  )
                }
              </span>
            )
          : (
              <UserRound
                className="
                  h-6
                  w-6
                "
              />
            )
      }
    </div>
  )
}


function IdentityMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        min-w-0
        px-3
        py-3
        text-center
        sm:px-4
      "
    >
      <p
        className="
          truncate
          text-[12px]
          font-semibold
          text-slate-800
          dark:text-slate-200
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


function ModernField({
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
}: {
  label: ReactNode
  value: string
  onChange:
    (value: string) => void
  placeholder?: string
  type?: string
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

      <input
        type={type}
        value={value}
        placeholder={
          placeholder
        }
        onChange={
          event =>
            onChange(
              event.target.value,
            )
        }
        className="
          h-10
          w-full
          rounded-[9px]
          border
          border-black/[0.07]
          bg-slate-50/60
          px-3
          text-[11.5px]
          font-medium
          text-slate-900
          outline-none
          transition
          placeholder:text-slate-300
          focus:border-emerald-500/40
          focus:ring-2
          focus:ring-emerald-500/[0.08]
          dark:border-white/[0.07]
          dark:bg-white/[0.025]
          dark:text-slate-100
          dark:placeholder:text-slate-600
        "
      />
    </label>
  )
}


function GenderField({
  value,
  onChange,
}: {
  value: string
  onChange:
    (
      value:
        | 'male'
        | 'female'
        | 'other'
        | 'unspecified',
    ) => void
}) {
  const options = [
    {
      value: 'male',
      label: 'Homme',
    },
    {
      value: 'female',
      label: 'Femme',
    },
    {
      value: 'other',
      label: 'Autre',
    },
    {
      value:
        'unspecified',
      label:
        'Non renseigné',
    },
  ] as const

  return (
    <div>
      <p
        className="
          mb-1.5
          text-[9px]
          font-semibold
          uppercase
          tracking-[0.07em]
          text-slate-400
          dark:text-slate-500
        "
      >
        Sexe
      </p>

      <div
        className="
          grid
          grid-cols-2
          gap-1
        "
      >
        {options.map(
          option => {
            const active =
              value
              === option.value

            return (
              <button
                key={
                  option.value
                }
                type="button"
                onClick={() =>
                  onChange(
                    option.value,
                  )
                }
                className={[
                  (
                    'h-[19px] '
                    + 'rounded-[6px] '
                    + 'border '
                    + 'text-[8.5px] '
                    + 'font-semibold '
                    + 'transition'
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
                {option.label}
              </button>
            )
          },
        )}
      </div>
    </div>
  )
}


function fullName(
  firstName: string,
  lastName: string,
): string {
  const value = [
    firstName.trim(),
    lastName.trim(),
  ]
    .filter(Boolean)
    .join(' ')

  return value
    || 'Profil OpenCoach'
}


function getInitials(
  firstName: string,
  lastName: string,
): string {
  const initials =
    `${
      firstName
        .trim()
        .charAt(0)
    }${
      lastName
        .trim()
        .charAt(0)
    }`
      .toUpperCase()

  return initials
    || 'OC'
}


function genderLabel(
  value: string,
): string {
  switch (value) {
    case 'male':
      return 'Homme'

    case 'female':
      return 'Femme'

    case 'other':
      return 'Autre'

    default:
      return 'Non renseigné'
  }
}


function formatBirthDate(
  value: string,
): string {
  if (!value) {
    return '—'
  }

  const date =
    new Date(
      `${value}T12:00:00`,
    )

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value
  }

  return (
    new Intl.DateTimeFormat(
      'fr-FR',
      {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      },
    )
      .format(date)
  )
}


function identitySummary(
  birthDate: string,
  gender: string,
): string {
  const values:
    string[] = []

  const age =
    calculateAge(
      birthDate,
    )

  if (
    age !== undefined
  ) {
    values.push(
      `${age} ans`,
    )
  }

  if (
    gender
    !== 'unspecified'
  ) {
    values.push(
      genderLabel(
        gender,
      ),
    )
  }

  return values.length
    ? values.join(' · ')
    : 'Profil personnel OpenCoach'
}


function calculateAge(
  value: string,
): number | undefined {
  if (!value) {
    return undefined
  }

  const birth =
    new Date(
      `${value}T12:00:00`,
    )

  if (
    Number.isNaN(
      birth.getTime(),
    )
  ) {
    return undefined
  }

  const today =
    new Date()

  let age =
    today.getFullYear()
    - birth.getFullYear()

  const month =
    today.getMonth()
    - birth.getMonth()

  if (
    month < 0
    || (
      month === 0
      && today.getDate()
      < birth.getDate()
    )
  ) {
    age -= 1
  }

  return age
}
