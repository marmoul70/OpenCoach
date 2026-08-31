import {
  useCallback,
  useEffect,
  useRef,
} from 'react'

import {
  useToast,
} from '../../components/ui/ToastProvider'


interface BuildInfo {
  application: string
  version: string
  commit: string
  built_at: string
}


const CHECK_INTERVAL_MS =
  60_000


async function fetchBuildInfo():
Promise<BuildInfo> {
  const response = await fetch(
    `/version.json?t=${Date.now()}`,
    {
      cache: 'no-store',
      headers: {
        Accept: 'application/json',
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      'Version OpenCoach indisponible.',
    )
  }

  return (
    await response.json()
  ) as BuildInfo
}


export function VersionWatcher() {
  const {
    toast,
  } = useToast()

  const initialBuild =
    useRef<BuildInfo | null>(
      null,
    )

  const notifiedCommit =
    useRef<string | null>(
      null,
    )

  const checkVersion =
    useCallback(
      async () => {
        try {
          const latest =
            await fetchBuildInfo()

          if (!initialBuild.current) {
            initialBuild.current =
              latest

            return
          }

          if (
            latest.commit
            === initialBuild.current.commit
          ) {
            return
          }

          if (
            notifiedCommit.current
            === latest.commit
          ) {
            return
          }

          notifiedCommit.current =
            latest.commit

          toast({
            type: 'info',
            title:
              'Nouvelle version disponible',
            message:
              `OpenCoach ${latest.version} `
              + 'est prêt.',
            duration: null,
            actionLabel: 'Actualiser',
            onAction: () => {
              window.location.reload()
            },
          })
        } catch {
          /*
           * Une vérification de version ne doit
           * jamais perturber l'utilisation
           * d'OpenCoach si le réseau est
           * momentanément indisponible.
           */
        }
      },
      [
        toast,
      ],
    )


  useEffect(() => {
    void checkVersion()

    const intervalId =
      window.setInterval(
        () => {
          void checkVersion()
        },
        CHECK_INTERVAL_MS,
      )


    function handleVisibilityChange() {
      if (
        document.visibilityState
        === 'visible'
      ) {
        void checkVersion()
      }
    }


    function handleFocus() {
      void checkVersion()
    }


    document.addEventListener(
      'visibilitychange',
      handleVisibilityChange,
    )

    window.addEventListener(
      'focus',
      handleFocus,
    )


    return () => {
      window.clearInterval(
        intervalId,
      )

      document.removeEventListener(
        'visibilitychange',
        handleVisibilityChange,
      )

      window.removeEventListener(
        'focus',
        handleFocus,
      )
    }
  }, [
    checkVersion,
  ])


  return null
}
