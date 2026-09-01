import {
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  RefreshCcw,
  WifiOff,
} from 'lucide-react'

import {
  OpenCoachLoadingScreen,
} from '../../components/feedback/OpenCoachLoadingScreen'

import {
  checkSession,
} from './api'

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


  const checkAuthentication =
    useCallback(
      async () => {
        setState(
          'loading',
        )

        try {
          const authenticated =
            await checkSession()

          setState(
            authenticated
              ? 'authenticated'
              : 'unauthenticated',
          )
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
      .then((authenticated) => {
        if (!cancelled) {
          setState(
            authenticated
              ? 'authenticated'
              : 'unauthenticated',
          )
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
    return (
      <LoginPage
        onAuthenticated={() => {
          setState(
            'authenticated',
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
