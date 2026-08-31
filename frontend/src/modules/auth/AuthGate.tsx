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
            navigator.onLine
              ? 'offline'
              : 'offline',
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
      <OpenCoachSplash />
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


function OpenCoachSplash() {
  return (
    <main
      className="
        pwa-safe-screen
        flex
        min-h-[100dvh]
        items-center
        justify-center
        bg-base-200
        px-6
      "
    >
      <div
        className="
          flex
          flex-col
          items-center
          text-center
        "
      >
        <img
          src="/opencoach-logo.png"
          alt="OpenCoach"
          className="
            h-32
            w-auto
            object-contain
          "
        />

        <span
          className="
            loading
            loading-spinner
            loading-md
            mt-6
            text-primary
          "
        />

        <p
          className="
            mt-3
            text-sm
            text-base-content/45
          "
        >
          Préparation de votre espace…
        </p>
      </div>
    </main>
  )
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
        bg-base-200
        px-5
      "
    >
      <div
        className="
          w-full
          max-w-sm
          rounded-2xl
          border
          border-base-300
          bg-base-100
          p-6
          text-center
          shadow-xl
        "
      >
        <div
          className="
            mx-auto
            flex
            h-14
            w-14
            items-center
            justify-center
            rounded-2xl
            bg-base-200
            text-base-content/60
          "
        >
          <WifiOff
            size={25}
          />
        </div>

        <h1
          className="
            mt-5
            text-xl
            font-bold
          "
        >
          OpenCoach indisponible
        </h1>

        <p
          className="
            mt-2
            text-sm
            leading-relaxed
            text-base-content/50
          "
        >
          Impossible de joindre OpenCoach.
          Vérifiez votre connexion puis réessayez.
        </p>

        <button
          type="button"
          className="
            btn
            btn-primary
            mt-5
            w-full
            gap-2
          "
          onClick={() => {
            void onRetry()
          }}
        >
          <RefreshCcw
            size={16}
          />

          Réessayer
        </button>
      </div>
    </main>
  )
}
