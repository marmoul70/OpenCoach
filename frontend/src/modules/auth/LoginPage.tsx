import {
  KeyRound,
  LockKeyhole,
  LogIn,
  ShieldCheck,
  UserRound,
} from 'lucide-react'

import {
  useRef,
  useState,
  type FormEvent,
} from 'react'

import {
  loginWithCredentials,
} from './api'


interface LoginPageProps {
  onAuthenticated: () => void
  onCreateAccount: () => void
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


export function LoginPage({
  onAuthenticated,
  onCreateAccount,
}: LoginPageProps) {
  const [
    username,
    setUsername,
  ] = useState('')

  const [
    pin,
    setPin,
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

  const pinRef =
    useRef<HTMLInputElement | null>(
      null,
    )


  async function handleSubmit(
    event: FormEvent,
  ) {
    event.preventDefault()

    const normalizedUsername =
      username
        .trim()
        .toLowerCase()

    if (
      normalizedUsername.length < 3
    ) {
      setError(
        'Saisissez votre identifiant OpenCoach.',
      )
      return
    }

    if (
      !/^\d{6}$/.test(
        pin,
      )
    ) {
      setError(
        'Saisissez les 6 chiffres du code PIN.',
      )
      return
    }

    setLoading(true)
    setError(null)

    try {
      await loginWithCredentials(
        normalizedUsername,
        pin,
      )

      onAuthenticated()
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : (
              'Identifiant ou code PIN incorrect.'
            ),
      )

      setPin('')

      window.requestAnimationFrame(
        () => {
          pinRef.current
            ?.focus()
        },
      )
    } finally {
      setLoading(false)
    }
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
        overflow-hidden
        bg-[#f5f7f6]
        px-4
        py-8
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          left-1/2
          top-1/4
          h-80
          w-80
          -translate-x-1/2
          rounded-full
          bg-emerald-500/[0.05]
          blur-3xl
        "
      />

      <div
        className="
          relative
          w-full
          max-w-[360px]
        "
      >
        <div
          className="
            mb-5
            text-center
          "
        >
          <img
            src="/opencoach-logo.png"
            alt="OpenCoach"
            className="
              mx-auto
              h-[86px]
              w-[86px]
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
            Bienvenue
          </h1>

          <p
            className="
              mt-1
              text-[12px]
              leading-5
              text-slate-500
              dark:text-slate-400
            "
          >
            Accédez à votre espace
            d'entraînement OpenCoach.
          </p>
        </div>


        <form
          onSubmit={
            (event) =>
              void handleSubmit(
                event,
              )
          }
          className="
            rounded-[16px]
            border
            border-black/[0.07]
            bg-white
            p-4
            shadow-[0_12px_36px_rgba(15,23,42,0.06)]
            dark:border-white/[0.075]
            dark:bg-[#151b1f]
          "
        >
          <div
            className="
              flex
              items-start
              gap-3
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
                rounded-[10px]
                bg-emerald-50
                text-emerald-600
                dark:bg-emerald-500/10
                dark:text-emerald-400
              "
            >
              <LockKeyhole
                className="h-4 w-4"
              />
            </div>

            <div>
              <p
                className="
                  text-[13px]
                  font-semibold
                  text-slate-900
                  dark:text-slate-100
                "
              >
                Connexion
              </p>

              <p
                className="
                  mt-0.5
                  text-[10.5px]
                  text-slate-400
                  dark:text-slate-500
                "
              >
                Identifiant OpenCoach
                et code PIN personnel.
              </p>
            </div>
          </div>


          <label className="mt-4 block">
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
              Identifiant OpenCoach
            </span>

            <div
              className="
                flex
                h-11
                items-center
                gap-2
                rounded-[10px]
                border
                border-slate-200
                bg-slate-50
                px-3
                focus-within:border-emerald-500/40
                dark:border-white/[0.08]
                dark:bg-white/[0.04]
              "
            >
              <UserRound
                className="
                  h-4
                  w-4
                  text-slate-400
                "
              />

              <input
                type="text"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                value={username}
                onChange={(event) => {
                  setUsername(
                    event.target.value
                      .replace(
                        /[^a-zA-Z0-9]/g,
                        '',
                      )
                      .toLowerCase(),
                  )
                  setError(null)
                }}
                placeholder="ex. ys001"
                className="
                  min-w-0
                  flex-1
                  bg-transparent
                  text-[13px]
                  font-semibold
                  text-slate-900
                  outline-none
                  placeholder:font-normal
                  placeholder:text-slate-300
                  dark:text-white
                "
              />
            </div>
          </label>


          <label className="mt-3 block">
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
              Code PIN
            </span>

            <div
              className="
                flex
                h-11
                items-center
                gap-2
                rounded-[10px]
                border
                border-slate-200
                bg-slate-50
                px-3
                focus-within:border-emerald-500/40
                dark:border-white/[0.08]
                dark:bg-white/[0.04]
              "
            >
              <KeyRound
                className="
                  h-4
                  w-4
                  text-slate-400
                "
              />

              <input
                ref={pinRef}
                type="password"
                inputMode="numeric"
                pattern="[0-9]*"
                autoComplete="current-password"
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
                className="
                  min-w-0
                  flex-1
                  bg-transparent
                  font-mono
                  text-[16px]
                  font-semibold
                  tracking-[0.32em]
                  text-slate-900
                  outline-none
                  dark:text-white
                "
              />
            </div>
          </label>


          {error && (
            <div
              className="
                mt-3
                rounded-[9px]
                border
                border-red-500/10
                bg-red-50
                px-3
                py-2
                text-[10.5px]
                font-medium
                text-red-600
                dark:bg-red-500/10
                dark:text-red-400
              "
            >
              {error}
            </div>
          )}


          <button
            type="submit"
            disabled={
              loading
              || username.trim().length < 3
              || pin.length !== 6
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
              px-4
              text-[12.5px]
              font-semibold
              text-white
              transition
              hover:bg-emerald-700
              disabled:cursor-not-allowed
              disabled:bg-slate-200
              disabled:text-slate-400
              dark:bg-emerald-500
              dark:hover:bg-emerald-400
              dark:disabled:bg-white/[0.07]
              dark:disabled:text-slate-600
            "
          >
            {loading ? (
              <>
                <span
                  className="
                    h-4
                    w-4
                    animate-spin
                    rounded-full
                    border-2
                    border-white/30
                    border-t-white
                  "
                />

                Connexion…
              </>
            ) : (
              <>
                <LogIn
                  className="h-4 w-4"
                />

                Se connecter
              </>
            )}
          </button>
        </form>


        <div
          className="
            mt-3
            text-center
          "
        >
          <span
            className="
              text-[10.5px]
              text-slate-400
            "
          >
            Pas encore de compte ?
          </span>

          <button
            type="button"
            onClick={
              onCreateAccount
            }
            className="
              ml-1.5
              text-[10.5px]
              font-semibold
              text-emerald-600
              hover:text-emerald-700
              dark:text-emerald-400
            "
          >
            Créer un compte
          </button>
        </div>


        <div
          className="
            mt-4
            flex
            items-center
            justify-center
            gap-1.5
            text-[9.5px]
            text-slate-400
            dark:text-slate-600
          "
        >
          <ShieldCheck
            className="h-3 w-3"
          />

          Connexion sécurisée · OpenCoach
        </div>
      </div>
    </main>
  )
}
