import {
  AtSign,
  Check,
  Pencil,
  X,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

import {
  fetchAccount,
  updateAccountEmail,
} from './api'


export function AccountIdentitySection() {
  const [
    username,
    setUsername,
  ] = useState('')

  const [
    email,
    setEmail,
  ] = useState('')

  const [
    draftEmail,
    setDraftEmail,
  ] = useState('')

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    editing,
    setEditing,
  ] = useState(false)

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )

  const [
    saved,
    setSaved,
  ] = useState(false)


  useEffect(() => {
    let cancelled =
      false

    void fetchAccount()
      .then((account) => {
        if (cancelled) {
          return
        }

        setUsername(
          account.username,
        )

        setEmail(
          account.email,
        )

        setDraftEmail(
          account.email,
        )
      })
      .catch((reason) => {
        if (!cancelled) {
          setError(
            reason instanceof Error
              ? reason.message
              : (
                  'Impossible de charger '
                  + 'le compte.'
                ),
          )
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])


  async function handleSave() {
    setError(null)
    setSaved(false)

    if (
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
        draftEmail.trim(),
      )
    ) {
      setError(
        'Adresse e-mail invalide.',
      )

      return
    }

    setSaving(true)

    try {
      const account =
        await updateAccountEmail(
          draftEmail.trim(),
        )

      setEmail(
        account.email,
      )

      setDraftEmail(
        account.email,
      )

      setEditing(false)
      setSaved(true)

      window.setTimeout(
        () => {
          setSaved(false)
        },
        3000,
      )
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : (
              'Impossible de modifier '
              + 'l’e-mail.'
            ),
      )
    } finally {
      setSaving(false)
    }
  }


  function cancelEdit() {
    setDraftEmail(
      email,
    )

    setEditing(false)
    setError(null)
  }


  return (
    <div
      className="
        border-t
        border-black/[0.055]
        dark:border-white/[0.06]
      "
    >
      <div
        className="
          px-4
          py-3
          sm:px-5
        "
      >
        <div
          className="
            mb-3
          "
        >
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
            Compte OpenCoach
          </p>

          <p
            className="
              mt-0.5
              text-[10px]
              text-slate-400
              dark:text-slate-500
            "
          >
            Informations utilisées pour
            vous connecter à OpenCoach.
          </p>
        </div>


        {loading ? (
          <div
            className="
              flex
              h-16
              items-center
              justify-center
            "
          >
            <span
              className="
                h-5
                w-5
                animate-spin
                rounded-full
                border-2
                border-slate-200
                border-t-emerald-500
                dark:border-white/[0.10]
                dark:border-t-emerald-400
              "
            />
          </div>
        ) : (
          <div
            className="
              grid
              gap-3
              sm:grid-cols-2
            "
          >
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
                Identifiant OpenCoach
              </p>

              <div
                className="
                  flex
                  h-10
                  items-center
                  justify-between
                  gap-2
                  rounded-[9px]
                  border
                  border-black/[0.07]
                  bg-slate-50/60
                  px-3
                  dark:border-white/[0.07]
                  dark:bg-white/[0.025]
                "
              >
                <span
                  className="
                    truncate
                    font-mono
                    text-[11.5px]
                    font-semibold
                    text-slate-900
                    dark:text-slate-100
                  "
                >
                  {username || '—'}
                </span>

                <span
                  className="
                    shrink-0
                    text-[8.5px]
                    font-medium
                    text-slate-400
                    dark:text-slate-600
                  "
                >
                  Non modifiable
                </span>
              </div>
            </div>


            <div>
              {!editing ? (
                <>
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
                    Adresse e-mail
                  </p>

                  <div
                    className="
                      flex
                      h-10
                      items-center
                      gap-2
                      rounded-[9px]
                      border
                      border-black/[0.07]
                      bg-slate-50/60
                      px-3
                      dark:border-white/[0.07]
                      dark:bg-white/[0.025]
                    "
                  >
                    <AtSign
                      className="
                        h-3.5
                        w-3.5
                        shrink-0
                        text-slate-400
                      "
                    />

                    <span
                      className="
                        min-w-0
                        flex-1
                        truncate
                        text-[11.5px]
                        font-medium
                        text-slate-900
                        dark:text-slate-100
                      "
                    >
                      {email || '—'}
                    </span>

                    <button
                      type="button"
                      aria-label="
                        Modifier l'adresse e-mail
                      "
                      onClick={() => {
                        setEditing(true)
                        setError(null)
                        setSaved(false)
                      }}
                      className="
                        flex
                        h-7
                        w-7
                        shrink-0
                        items-center
                        justify-center
                        rounded-[7px]
                        text-slate-400
                        transition
                        hover:bg-white
                        hover:text-slate-700
                        dark:hover:bg-white/[0.05]
                        dark:hover:text-slate-200
                      "
                    >
                      <Pencil
                        className="
                          h-3
                          w-3
                        "
                      />
                    </button>
                  </div>
                </>
              ) : (
                <>
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
                    Adresse e-mail
                  </p>

                  <div
                    className="
                      flex
                      h-10
                      items-center
                      gap-2
                      rounded-[9px]
                      border
                      border-emerald-500/30
                      bg-slate-50/60
                      px-3
                      ring-2
                      ring-emerald-500/[0.06]
                      dark:bg-white/[0.025]
                    "
                  >
                    <AtSign
                      className="
                        h-3.5
                        w-3.5
                        shrink-0
                        text-slate-400
                      "
                    />

                    <input
                      type="email"
                      value={draftEmail}
                      onChange={(event) => {
                        setDraftEmail(
                          event.target.value,
                        )
                        setError(null)
                      }}
                      autoComplete="email"
                      autoFocus
                      className="
                        min-w-0
                        flex-1
                        bg-transparent
                        text-[11.5px]
                        font-medium
                        text-slate-900
                        outline-none
                        dark:text-slate-100
                      "
                    />

                    <button
                      type="button"
                      aria-label="Annuler"
                      onClick={
                        cancelEdit
                      }
                      disabled={saving}
                      className="
                        flex
                        h-7
                        w-7
                        shrink-0
                        items-center
                        justify-center
                        rounded-[7px]
                        text-slate-400
                        transition
                        hover:bg-white
                        hover:text-slate-700
                        disabled:opacity-40
                        dark:hover:bg-white/[0.05]
                      "
                    >
                      <X
                        className="
                          h-3
                          w-3
                        "
                      />
                    </button>

                    <button
                      type="button"
                      aria-label="
                        Enregistrer l'adresse e-mail
                      "
                      onClick={() => {
                        void handleSave()
                      }}
                      disabled={
                        saving
                        || draftEmail.trim()
                          === email
                      }
                      className="
                        flex
                        h-7
                        w-7
                        shrink-0
                        items-center
                        justify-center
                        rounded-[7px]
                        bg-emerald-600
                        text-white
                        transition
                        hover:bg-emerald-700
                        disabled:cursor-not-allowed
                        disabled:opacity-40
                      "
                    >
                      <Check
                        className="
                          h-3
                          w-3
                        "
                      />
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}


        {error && (
          <div
            className="
              mt-3
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
            {error}
          </div>
        )}


        {saved && (
          <div
            className="
              mt-3
              inline-flex
              items-center
              gap-1
              text-[10px]
              font-semibold
              text-emerald-600
              dark:text-emerald-400
            "
          >
            <Check
              className="
                h-3
                w-3
              "
            />

            Adresse e-mail enregistrée.
          </div>
        )}
      </div>
    </div>
  )
}
