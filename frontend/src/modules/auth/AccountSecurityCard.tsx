import {
  CheckCircle2,
  KeyRound,
  LockKeyhole,
  ShieldCheck,
} from 'lucide-react'

import {
  useState,
  type FormEvent,
} from 'react'

import {
  changePin,
} from './api'


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


export function AccountSecurityCard() {
  const [
    currentPin,
    setCurrentPin,
  ] = useState('')

  const [
    newPin,
    setNewPin,
  ] = useState('')

  const [
    confirmPin,
    setConfirmPin,
  ] = useState('')

  const [
    loading,
    setLoading,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )

  const [
    success,
    setSuccess,
  ] = useState(false)


  async function handleSubmit(
    event: FormEvent,
  ) {
    event.preventDefault()

    setError(null)
    setSuccess(false)

    if (
      currentPin.length !== 6
      || newPin.length !== 6
      || confirmPin.length !== 6
    ) {
      setError(
        'Les codes PIN doivent contenir 6 chiffres.',
      )

      return
    }

    if (
      newPin !== confirmPin
    ) {
      setError(
        'Les deux nouveaux codes PIN '
        + 'ne correspondent pas.',
      )

      return
    }

    if (
      currentPin === newPin
    ) {
      setError(
        'Choisissez un nouveau PIN différent.',
      )

      return
    }

    setLoading(true)

    try {
      await changePin(
        currentPin,
        newPin,
      )

      setCurrentPin('')
      setNewPin('')
      setConfirmPin('')
      setSuccess(true)

      window.setTimeout(
        () => {
          setSuccess(false)
        },
        4000,
      )
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : (
              'Impossible de modifier '
              + 'le code PIN.'
            ),
      )
    } finally {
      setLoading(false)
    }
  }


  return (
    <section
      className="
        mb-4
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
          border-black/[0.055]
          px-4
          py-3.5
          dark:border-white/[0.06]
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
            <ShieldCheck
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
              Sécurité
            </p>

            <p
              className="
                mt-0.5
                text-[10.5px]
                text-slate-400
                dark:text-slate-500
              "
            >
              Modifier le code PIN
              utilisé pour te connecter.
            </p>
          </div>
        </div>
      </div>


      <form
        onSubmit={
          event =>
            void handleSubmit(
              event,
            )
        }
        className="
          p-4
        "
      >
        <PinField
          label="Code PIN actuel"
          value={currentPin}
          onChange={(value) => {
            setCurrentPin(value)
            setError(null)
            setSuccess(false)
          }}
          icon="current"
        />


        <div
          className="
            mt-3
            grid
            gap-3
            sm:grid-cols-2
          "
        >
          <PinField
            label="Nouveau PIN"
            value={newPin}
            onChange={(value) => {
              setNewPin(value)
              setError(null)
              setSuccess(false)
            }}
            icon="new"
          />

          <PinField
            label="Confirmer le PIN"
            value={confirmPin}
            onChange={(value) => {
              setConfirmPin(value)
              setError(null)
              setSuccess(false)
            }}
            icon="new"
          />
        </div>


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


        {success && (
          <div
            className="
              mt-3
              flex
              items-center
              gap-2
              rounded-[9px]
              border
              border-emerald-500/15
              bg-emerald-50
              px-3
              py-2
              text-[10.5px]
              font-medium
              text-emerald-700
              dark:bg-emerald-500/10
              dark:text-emerald-400
            "
          >
            <CheckCircle2
              className="
                h-4
                w-4
                shrink-0
              "
            />

            Code PIN modifié avec succès.
          </div>
        )}


        <button
          type="submit"
          disabled={
            loading
            || currentPin.length !== 6
            || newPin.length !== 6
            || confirmPin.length !== 6
          }
          className="
            mt-4
            inline-flex
            h-10
            items-center
            justify-center
            gap-2
            rounded-[9px]
            bg-emerald-600
            px-4
            text-[11px]
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
                  h-3.5
                  w-3.5
                  animate-spin
                  rounded-full
                  border-2
                  border-white/30
                  border-t-white
                "
              />

              Modification…
            </>
          ) : (
            <>
              <KeyRound
                className="h-3.5 w-3.5"
              />

              Modifier mon PIN
            </>
          )}
        </button>
      </form>
    </section>
  )
}


function PinField({
  label,
  value,
  onChange,
  icon,
}: {
  label: string
  value: string
  onChange: (
    value: string,
  ) => void
  icon:
    | 'current'
    | 'new'
}) {
  const Icon =
    icon === 'current'
      ? LockKeyhole
      : KeyRound

  return (
    <label
      className="
        block
      "
    >
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
          border-black/[0.07]
          bg-slate-50
          px-3
          transition
          focus-within:border-emerald-500/40
          dark:border-white/[0.07]
          dark:bg-white/[0.035]
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

        <input
          type="password"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          value={value}
          onChange={(event) => {
            onChange(
              sanitizePin(
                event.target.value,
              ),
            )
          }}
          className="
            min-w-0
            flex-1
            bg-transparent
            font-mono
            text-[14px]
            tracking-[0.22em]
            text-slate-900
            outline-none
            dark:text-white
          "
        />
      </div>
    </label>
  )
}
