import {
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  Archive,
  Plus,
  RefreshCcw,
  Upload,
  WifiOff,
} from 'lucide-react'

import {
  OpenCoachLoadingScreen,
} from '../../components/feedback/OpenCoachLoadingScreen'

import {
  checkSession,
  needsInitialSetup,
  restoreInitialBackup,
} from './api'

import {
  CreateAccountPage,
} from './CreateAccountPage'

import {
  LoginPage,
} from './LoginPage'


type AuthState =
  | 'loading'
  | 'authenticated'
  | 'unauthenticated'
  | 'offline'


export function AuthGate({
  children,
}: {
  children: ReactNode
}) {
  const [
    state,
    setState,
  ] = useState<AuthState>(
    'loading',
  )

  const [needsSetup, setNeedsSetup] = useState(false)
  const [authView, setAuthView] = useState<'first-install' | 'login' | 'create-account'>('login')


  const checkAuthentication =
    useCallback(
      async () => {
        setState(
          'loading',
        )

        try {
          const authenticated = await checkSession()
          if (!authenticated) {
            const initialSetup = await needsInitialSetup()
            setNeedsSetup(initialSetup)
            setAuthView(initialSetup ? 'first-install' : 'login')
          }
          setState(authenticated ? 'authenticated' : 'unauthenticated')
        } catch {
          setState(
            'offline',
          )
        }
      },
      [],
    )


  useEffect(() => {
    let cancelled = false

    void checkSession()
      .then(async (authenticated) => {
        if (!authenticated) {
          const initialSetup = await needsInitialSetup()
          if (!cancelled) {
            setNeedsSetup(initialSetup)
            setAuthView(initialSetup ? 'first-install' : 'login')
          }
        }
        if (!cancelled) {
          setState(authenticated ? 'authenticated' : 'unauthenticated')
        }
      })
      .catch(() => {
        if (!cancelled) {
          setState(
            'offline',
          )
        }
      })

    function handleOffline() {
      setState(
        'offline',
      )
    }

    function handleOnline() {
      void checkAuthentication()
    }

    window.addEventListener(
      'offline',
      handleOffline,
    )

    window.addEventListener(
      'online',
      handleOnline,
    )

    return () => {
      cancelled = true

      window.removeEventListener(
        'offline',
        handleOffline,
      )

      window.removeEventListener(
        'online',
        handleOnline,
      )
    }
  }, [
    checkAuthentication,
  ])


  if (
    state === 'loading'
  ) {
    return (
      <OpenCoachLoadingScreen
        message="Connexion à OpenCoach…"
      />
    )
  }


  if (
    state === 'offline'
  ) {
    return (
      <OfflineScreen
        onRetry={
          checkAuthentication
        }
      />
    )
  }


  if (
    state === 'unauthenticated'
  ) {
    if (needsSetup && authView === 'first-install') {
      return <FirstInstallChoice onCreate={() => setAuthView('create-account')} onRestored={() => window.location.reload()} />
    }

    if (
      authView
      === 'create-account'
    ) {
      return (
        <CreateAccountPage
          onBackToLogin={() => {
            setNeedsSetup(false)
            setAuthView('login')
          }}
        />
      )
    }

    return (
      <LoginPage
        onAuthenticated={() => {
          setState(
            'authenticated',
          )
        }}
        onCreateAccount={() => {
          setAuthView(
            'create-account',
          )
        }}
      />
    )
  }


  return children
}


function OfflineScreen({
  onRetry,
}: {
  onRetry: () => Promise<void>
}) {
  return (
    <main
      className="
        pwa-safe-screen
        flex
        min-h-[100dvh]
        items-center
        justify-center
        bg-[#f5f7f6]
        px-4
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          w-full
          max-w-[340px]
          rounded-[16px]
          border
          border-black/[0.07]
          bg-white
          p-5
          text-center
          shadow-[0_12px_36px_rgba(15,23,42,0.06)]
          dark:border-white/[0.075]
          dark:bg-[#151b1f]
          dark:shadow-[0_14px_42px_rgba(0,0,0,0.22)]
        "
      >
        <div
          className="
            mx-auto
            flex
            h-11
            w-11
            items-center
            justify-center
            rounded-[11px]
            bg-slate-100
            text-slate-500
            dark:bg-white/[0.055]
            dark:text-slate-400
          "
        >
          <WifiOff
            className="h-5 w-5"
          />
        </div>

        <h1
          className="
            mt-4
            text-[17px]
            font-bold
            tracking-[-0.025em]
            text-slate-950
            dark:text-white
          "
        >
          OpenCoach indisponible
        </h1>

        <p
          className="
            mt-1.5
            text-[11.5px]
            leading-[17px]
            text-slate-500
            dark:text-slate-400
          "
        >
          Impossible de joindre OpenCoach.
          Vérifiez votre connexion puis réessayez.
        </p>

        <button
          type="button"
          className="
            mt-4
            flex
            h-10
            w-full
            items-center
            justify-center
            gap-2
            rounded-[10px]
            bg-emerald-600
            px-4
            text-[12px]
            font-semibold
            text-white
            transition
            hover:bg-emerald-700
            dark:bg-emerald-500
            dark:hover:bg-emerald-400
          "
          onClick={() => {
            void onRetry()
          }}
        >
          <RefreshCcw
            className="h-3.5 w-3.5"
          />

          Réessayer
        </button>
      </div>
    </main>
  )
}


function FirstInstallChoice({ onCreate, onRestored }: { onCreate: () => void; onRestored: () => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  async function handleRestore() {
    if (!file) return
    setLoading(true); setError(null)
    try { await restoreInitialBackup(file); onRestored() }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Restauration impossible.') }
    finally { setLoading(false) }
  }
  return (
    <main className="pwa-safe-screen flex min-h-[100dvh] items-center justify-center bg-[#f5f7f6] px-4 py-8 dark:bg-[#0b1014]">
      <section className="w-full max-w-[420px] rounded-2xl border border-black/[0.07] bg-white p-6 shadow-sm dark:border-white/[0.08] dark:bg-[#151b1f]">
        <img src="/opencoach-logo.png" alt="OpenCoach" className="mx-auto h-16 w-16 object-contain" />
        <h1 className="mt-3 text-center text-xl font-bold text-slate-950 dark:text-white">Bienvenue sur OpenCoach</h1>
        <p className="mt-2 text-center text-sm text-slate-500 dark:text-slate-400">Comment souhaitez-vous démarrer ?</p>
        <button type="button" onClick={onCreate} className="mt-6 flex w-full items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-50 p-4 text-left dark:bg-emerald-500/10"><Plus className="h-5 w-5 text-emerald-600" /><span><strong className="block text-sm text-slate-900 dark:text-white">Nouvelle installation</strong><small className="text-xs text-slate-500 dark:text-slate-400">Créer un compte et commencer à zéro</small></span></button>
        <div className="mt-3 rounded-xl border border-slate-200 p-4 dark:border-white/10"><div className="flex items-center gap-3"><Archive className="h-5 w-5 text-slate-500" /><div><strong className="block text-sm text-slate-900 dark:text-white">Restaurer une sauvegarde</strong><small className="text-xs text-slate-500 dark:text-slate-400">Importer un fichier ZIP OpenCoach</small></div></div>
          <input type="file" accept=".zip,application/zip" className="mt-4 block w-full text-xs text-slate-500 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-xs file:font-semibold dark:file:bg-white/10 dark:file:text-white" onChange={event => { setFile(event.target.files?.[0] ?? null); setError(null) }} />
          {error && <p className="mt-2 text-xs text-red-600">{error}</p>}
          <button type="button" disabled={!file || loading} onClick={() => void handleRestore()} className="mt-3 flex h-10 w-full items-center justify-center gap-2 rounded-lg bg-slate-900 text-xs font-semibold text-white disabled:opacity-40 dark:bg-emerald-600"><Upload className="h-4 w-4" />{loading ? 'Restauration…' : 'Restaurer le ZIP'}</button>
        </div>
      </section>
    </main>
  )
}
