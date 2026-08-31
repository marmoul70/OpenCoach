interface VersionResponse {
  version?: string
  commit?: string
}


async function getServiceWorkerUrl():
Promise<string> {
  try {
    const response = await fetch(
      '/version.json',
      {
        cache: 'no-store',
      },
    )

    if (!response.ok) {
      return '/sw.js'
    }

    const version = (
      await response.json()
    ) as VersionResponse

    const identifier =
      version.commit
      || version.version

    if (!identifier) {
      return '/sw.js'
    }

    return (
      '/sw.js?v='
      + encodeURIComponent(
          identifier,
        )
    )
  } catch {
    return '/sw.js'
  }
}


export function registerServiceWorker() {
  if (
    !import.meta.env.PROD
  ) {
    return
  }

  if (
    !(
      'serviceWorker'
      in navigator
    )
  ) {
    return
  }


  window.addEventListener(
    'load',
    () => {
      void (
        async () => {
          try {
            const serviceWorkerUrl =
              await getServiceWorkerUrl()

            const registration =
              await navigator
                .serviceWorker
                .register(
                  serviceWorkerUrl,
                  {
                    scope: '/',
                    updateViaCache: 'none',
                  },
                )

            /*
             * Force également une vérification
             * explicite du worker.
             */
            await registration
              .update()
          } catch (reason) {
            console.error(
              'Impossible d’enregistrer '
              + 'le service worker OpenCoach.',
              reason,
            )
          }
        }
      )()
    },
  )
}
