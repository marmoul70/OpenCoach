import {
  ArrowLeft,
  AtSign,
  LockKeyhole,
  ShieldCheck,
  User,
  UserPlus,
} from 'lucide-react'

import type { ReactNode } from 'react'

import {
  useMemo,
  useState,
  type FormEvent,
} from 'react'

import {
  registerAccount,
} from './api'


interface CreateAccountPageProps {
  onBackToLogin: () => void
}


function normalizePart(
  value: string,
): string {
  return value
    .normalize('NFD')
    .replace(
      /[\u0300-\u036f]/g,
      '',
    )
    .replace(
      /[^a-zA-Z]/g,
      '',
    )
    .toLowerCase()
}


function sanitizePin(
  value: string,
): string {
  return value
    .replace(
      /\D/g,
      '',
    )
    .slice(
      0,
      6,
    )
}


export function CreateAccountPage({
  onBackToLogin,
}: CreateAccountPageProps) {
  const [firstName, setFirstName] =
    useState('')

  const [lastName, setLastName] =
    useState('')

  const [email, setEmail] =
    useState('')

  const [pin, setPin] =
    useState('')

  const [
    confirmPin,
    setConfirmPin,
  ] = useState('')

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(false)

  const [
    createdUsername,
    setCreatedUsername,
  ] = useState<string | null>(
    null,
  )


  const identifier =
    useMemo(
      () => {
        const first =
          normalizePart(
            firstName,
          )

        const last =
          normalizePart(
            lastName,
          )

        if (
          !first
          || !last
        ) {
          return '---•••'
        }

        return (
          last.slice(0, 2)
          + first.slice(0, 1)
          + '•••'
        )
      },
      [
        firstName,
        lastName,
      ],
    )


  function handleSubmit(
    event: FormEvent,
  ) {
    event.preventDefault()

    setError(null)

    if (
      !firstName.trim()
      || !lastName.trim()
    ) {
      setError(
        'Prénom et nom obligatoires.',
      )

      return
    }

    if (
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
        email.trim(),
      )
    ) {
      setError(
        'Adresse e-mail invalide.',
      )

      return
    }

    if (
      !/^\d{6}$/.test(pin)
    ) {
      setError(
        'Le PIN doit contenir 6 chiffres.',
      )

      return
    }

    if (
      pin !== confirmPin
    ) {
      setError(
        'Les deux codes PIN sont différents.',
      )

      return
    }

    setLoading(
      true,
    )

    void registerAccount({
      first_name:
        firstName.trim(),
      last_name:
        lastName.trim(),
      email:
        email.trim(),
      pin,
    })
      .then((result) => {
        setCreatedUsername(
          result.username,
        )
      })
      .catch((reason) => {
        setError(
          reason instanceof Error
            ? reason.message
            : (
                'Impossible de créer '
                + 'le compte.'
              ),
        )
      })
      .finally(() => {
        setLoading(
          false,
        )
      })
  }


  return (
    <main
      className="
        pwa-safe-screen
        relative
        flex
        min-h-[100dvh]
        items-center
        justify-center
        bg-[#f5f7f6]
        px-4
        py-8
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          w-full
          max-w-[430px]
        "
      >
        <button
          type="button"
          onClick={
            onBackToLogin
          }
          className="
            mb-3
            inline-flex
            items-center
            gap-1.5
            text-[10.5px]
            font-semibold
            text-slate-400
            hover:text-slate-700
            dark:hover:text-slate-200
          "
        >
          <ArrowLeft
            className="h-3.5 w-3.5"
          />

          Retour
        </button>


        <div
          className="
            mb-4
            text-center
          "
        >
          <img
            src="/opencoach-logo.png"
            alt="OpenCoach"
            className="
              mx-auto
              h-[72px]
              w-[72px]
              object-contain
            "
          />

          <h1
            className="
              mt-2
              text-[22px]
              font-bold
              tracking-[-0.04em]
              text-slate-950
              dark:text-white
            "
          >
            Créer un compte
          </h1>

          <p
            className="
              mt-1
              text-[11.5px]
              text-slate-500
              dark:text-slate-400
            "
          >
            Configurez votre espace OpenCoach.
          </p>
        </div>


        <form
          onSubmit={
            handleSubmit
          }
          className="
            rounded-[16px]
            border
            border-black/[0.07]
            bg-white
            p-4
            shadow-sm
            dark:border-white/[0.075]
            dark:bg-[#151b1f]
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
                h-9
                w-9
                items-center
                justify-center
                rounded-[10px]
                bg-emerald-50
                text-emerald-600
                dark:bg-emerald-500/10
                dark:text-emerald-400
              "
            >
              <UserPlus
                className="h-4 w-4"
              />
            </div>

            <div>
              <p
                className="
                  text-[13px]
                  font-semibold
                  text-slate-900
                  dark:text-white
                "
              >
                Votre compte
              </p>

              <p
                className="
                  text-[10px]
                  text-slate-400
                "
              >
                Informations personnelles
                et accès sécurisé.
              </p>
            </div>
          </div>


          <div
            className="
              mt-4
              grid
              gap-3
              sm:grid-cols-2
            "
          >
            <Field
              icon={User}
              label="Prénom"
            >
              <input
                value={firstName}
                onChange={(event) => {
                  setFirstName(
                    event.target.value,
                  )
                  setError(null)
                }}
                autoComplete="given-name"
                className="auth-create-input"
              />
            </Field>

            <Field
              icon={User}
              label="Nom"
            >
              <input
                value={lastName}
                onChange={(event) => {
                  setLastName(
                    event.target.value,
                  )
                  setError(null)
                }}
                autoComplete="family-name"
                className="auth-create-input"
              />
            </Field>
          </div>


          <div className="mt-3">
            <Field
              icon={AtSign}
              label="Adresse e-mail"
            >
              <input
                type="email"
                value={email}
                onChange={(event) => {
                  setEmail(
                    event.target.value,
                  )
                  setError(null)
                }}
                autoComplete="email"
                placeholder="prenom.nom@email.fr"
                className="auth-create-input"
              />
            </Field>
          </div>


          <div
            className="
              mt-3
              rounded-[10px]
              border
              border-emerald-500/15
              bg-emerald-500/[0.05]
              px-3
              py-2.5
              dark:border-emerald-400/15
              dark:bg-emerald-400/[0.05]
            "
          >
            <p
              className="
                text-[8.5px]
                font-bold
                uppercase
                tracking-[0.1em]
                text-emerald-600
                dark:text-emerald-400
              "
            >
              Identifiant OpenCoach
            </p>

            <div
              className="
                mt-1
                flex
                items-center
                justify-between
              "
            >
              <span
                className="
                  font-mono
                  text-[15px]
                  font-semibold
                  text-slate-900
                  dark:text-white
                "
              >
                {identifier}
              </span>

              <span
                className="
                  text-[9px]
                  text-slate-400
                "
              >
                automatique
              </span>
            </div>

            <p
              className="
                mt-1
                text-[9px]
                text-slate-400
              "
            >
              2 lettres du nom +
              1 du prénom +
              3 chiffres.
            </p>
          </div>


          <div
            className="
              mt-3
              grid
              gap-3
              sm:grid-cols-2
            "
          >
            <Field
              icon={LockKeyhole}
              label="Code PIN"
            >
              <input
                type="password"
                inputMode="numeric"
                maxLength={6}
                value={pin}
                onChange={(event) => {
                  setPin(
                    sanitizePin(
                      event.target.value,
                    ),
                  )
                  setError(null)
                }}
                className="auth-create-input"
              />
            </Field>

            <Field
              icon={LockKeyhole}
              label="Confirmer"
            >
              <input
                type="password"
                inputMode="numeric"
                maxLength={6}
                value={confirmPin}
                onChange={(event) => {
                  setConfirmPin(
                    sanitizePin(
                      event.target.value,
                    ),
                  )
                  setError(null)
                }}
                className="auth-create-input"
              />
            </Field>
          </div>


          {createdUsername && (
            <div
              className="
                mt-3
                rounded-[9px]
                border
                border-emerald-500/15
                bg-emerald-50
                px-3
                py-2.5
                text-[10.5px]
                text-emerald-700
                dark:bg-emerald-500/10
                dark:text-emerald-400
              "
            >
              <p
                className="
                  font-semibold
                "
              >
                Compte créé avec succès
              </p>

              <p className="mt-1">
                Votre identifiant :
              </p>

              <p
                className="
                  mt-1
                  font-mono
                  text-[15px]
                  font-bold
                  tracking-[0.08em]
                "
              >
                {createdUsername}
              </p>

              <button
                type="button"
                onClick={
                  onBackToLogin
                }
                className="
                  mt-2
                  font-semibold
                  underline
                  underline-offset-2
                "
              >
                Aller à la connexion
              </button>
            </div>
          )}


          {error && (
            <div
              className="
                mt-3
                rounded-[9px]
                border
                border-amber-500/15
                bg-amber-50
                px-3
                py-2
                text-[10.5px]
                font-medium
                text-amber-700
                dark:bg-amber-500/10
                dark:text-amber-400
              "
            >
              {error}
            </div>
          )}


          <button
            type="submit"
            disabled={
              loading
              || createdUsername !== null
            }
            className="
              mt-4
              flex
              h-11
              w-full
              items-center
              justify-center
              gap-2
              rounded-[11px]
              bg-emerald-600
              text-[12.5px]
              font-semibold
              text-white
              hover:bg-emerald-700
              dark:bg-emerald-500
              dark:hover:bg-emerald-400
            "
          >
            <UserPlus
              className="h-4 w-4"
            />

            {
              loading
                ? 'Création…'
                : 'Créer mon compte'
            }
          </button>
        </form>


        <div
          className="
            mt-4
            flex
            items-center
            justify-center
            gap-1.5
            text-[9.5px]
            text-slate-400
          "
        >
          <ShieldCheck
            className="h-3 w-3"
          />

          Compte personnel sécurisé · OpenCoach
        </div>
      </div>
    </main>
  )
}


function Field({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof User
  label: string
  children: ReactNode
}) {
  return (
    <label>
      <span
        className="
          mb-1.5
          block
          text-[10.5px]
          font-semibold
          text-slate-500
          dark:text-slate-400
        "
      >
        {label}
      </span>

      <div
        className="
          flex
          h-10
          items-center
          gap-2
          rounded-[9px]
          border
          border-slate-200
          bg-slate-50
          px-3
          dark:border-white/[0.08]
          dark:bg-white/[0.04]
        "
      >
        <Icon
          className="
            h-3.5
            w-3.5
            shrink-0
            text-slate-400
          "
        />

        {children}
      </div>
    </label>
  )
}
