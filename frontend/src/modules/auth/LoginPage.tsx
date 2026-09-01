import {
  LockKeyhole,
  LogIn,
  ShieldCheck,
} from 'lucide-react'

import {
  useRef,
  useState,
  type FormEvent,
} from 'react'

import {
  loginWithPin,
} from './api'


interface LoginPageProps {
  onAuthenticated: () => void
}


export function LoginPage({
  onAuthenticated,
}: LoginPageProps) {
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

  const inputRef =
    useRef<HTMLInputElement | null>(
      null,
    )


  async function handleSubmit(
    event: FormEvent,
  ) {
    event.preventDefault()

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
      await loginWithPin(
        pin,
      )

      onAuthenticated()
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'Code PIN incorrect.',
      )

      setPin('')

      window.requestAnimationFrame(
        () => {
          inputRef.current
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
          max-w-[350px]
        "
      >
        {/* Identité */}

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


        {/* Carte connexion */}

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
            dark:shadow-[0_14px_42px_rgba(0,0,0,0.22)]
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
              <label
                htmlFor="opencoach-pin"
                className="
                  text-[13px]
                  font-semibold
                  text-slate-900
                  dark:text-slate-100
                "
              >
                Code PIN
              </label>

              <p
                className="
                  mt-0.5
                  text-[10.5px]
                  leading-4
                  text-slate-400
                  dark:text-slate-500
                "
              >
                Votre code personnel à 6 chiffres.
              </p>
            </div>
          </div>


          <input
            ref={inputRef}
            id="opencoach-pin"
            type="password"
            inputMode="numeric"
            pattern="[0-9]*"
            autoComplete="current-password"
            maxLength={6}
            autoFocus
            value={pin}
            onChange={(event) => {
              setPin(
                event.target.value
                  .replace(
                    /\D/g,
                    '',
                  )
                  .slice(
                    0,
                    6,
                  ),
              )

              setError(null)
            }}
            className="
              mt-4
              h-12
              w-full
              rounded-[11px]
              border
              border-slate-200
              bg-slate-50
              px-4
              text-center
              font-mono
              text-[20px]
              font-semibold
              tracking-[0.48em]
              text-slate-900
              outline-none
              transition
              placeholder:text-slate-300
              focus:border-emerald-500/50
              focus:bg-white
              focus:ring-4
              focus:ring-emerald-500/[0.07]
              disabled:cursor-not-allowed
              disabled:opacity-60
              dark:border-white/[0.08]
              dark:bg-white/[0.04]
              dark:text-white
              dark:focus:border-emerald-500/35
              dark:focus:bg-white/[0.055]
            "
            aria-label="Code PIN OpenCoach"
          />


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
                text-[11px]
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
              shadow-sm
              transition
              hover:bg-emerald-700
              focus-visible:outline-none
              focus-visible:ring-4
              focus-visible:ring-emerald-500/20
              disabled:cursor-not-allowed
              disabled:bg-slate-200
              disabled:text-slate-400
              disabled:shadow-none
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


        {/* Pied */}

        <div
          className="
            mt-4
            flex
            items-center
            justify-center
            gap-1.5
            text-[9.5px]
            font-medium
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
