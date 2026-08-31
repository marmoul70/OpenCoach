import {
  useRef,
  useState,
} from 'react'

import {
  LockKeyhole,
} from 'lucide-react'

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
    event: React.FormEvent,
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
        flex
        min-h-screen
        items-center
        justify-center
        bg-base-200
        px-4
      "
    >
      <div
        className="
          w-full
          max-w-sm
        "
      >
        <div
          className="
            mb-6
            text-center
          "
        >
          <div
            className="
              mx-auto
              flex
              h-16
              w-16
              items-center
              justify-center
              rounded-2xl
              bg-primary
              text-primary-content
              shadow-lg
            "
          >
            <LockKeyhole
              className="
                h-7
                w-7
              "
            />
          </div>

          <h1
            className="
              mt-5
              text-3xl
              font-bold
              tracking-tight
            "
          >
            OpenCoach
          </h1>

          <p
            className="
              mt-1
              text-sm
              text-base-content/50
            "
          >
            Votre espace d'entraînement personnel
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
            rounded-2xl
            border
            border-base-300
            bg-base-100
            p-6
            shadow-xl
          "
        >
          <div>
            <label
              htmlFor="opencoach-pin"
              className="
                text-sm
                font-semibold
              "
            >
              Code PIN
            </label>

            <p
              className="
                mt-0.5
                text-xs
                text-base-content/45
              "
            >
              Entrez votre code personnel à 6 chiffres.
            </p>
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
              input
              input-bordered
              mt-5
              h-14
              w-full
              text-center
              font-mono
              text-2xl
              tracking-[0.55em]
            "
            aria-label="Code PIN OpenCoach"
          />


          {error && (
            <div
              className="
                mt-3
                rounded-lg
                bg-error/10
                px-3
                py-2
                text-sm
                text-error
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
              btn
              btn-primary
              mt-5
              w-full
            "
          >
            {loading ? (
              <>
                <span
                  className="
                    loading
                    loading-spinner
                    loading-sm
                  "
                />

                Connexion...
              </>
            ) : (
              'Se connecter'
            )}
          </button>
        </form>


        <p
          className="
            mt-4
            text-center
            text-[11px]
            text-base-content/30
          "
        >
          Connexion sécurisée · OpenCoach
        </p>
      </div>
    </main>
  )
}
