export function BadgeDiagnostic() {
  async function resetPwa() {
    try {
      if (
        'serviceWorker'
        in navigator
      ) {
        const registrations =
          await navigator
            .serviceWorker
            .getRegistrations()

        for (
          const registration
          of registrations
        ) {
          const subscription =
            await registration
              .pushManager
              .getSubscription()

          if (subscription) {
            try {
              await fetch(
                '/api/push/subscriptions',
                {
                  method: 'DELETE',
                  credentials: 'include',
                  headers: {
                    'Content-Type':
                      'application/json',
                  },
                  body: JSON.stringify({
                    endpoint:
                      subscription.endpoint,
                  }),
                },
              )
            } catch {
              // La réinitialisation locale continue.
            }

            await subscription
              .unsubscribe()
          }

          await registration
            .unregister()
        }
      }

      const cacheStorage =
        (
          window as Window & {
            caches?: CacheStorage
          }
        ).caches

      if (cacheStorage) {
        const cacheNames =
          await cacheStorage.keys()

        await Promise.all(
          cacheNames.map(
            (cacheName) =>
              cacheStorage.delete(
                cacheName,
              ),
          ),
        )
      }

      alert(
        'OpenCoach a été réinitialisé. '
        + 'Fermez complètement la PWA, '
        + 'puis relancez-la.',
      )
    } catch (error) {
      alert(
        error instanceof Error
          ? `${error.name}: ${error.message}`
          : 'Erreur de réinitialisation PWA',
      )
    }
  }

  return (
    <button
      type="button"
      onClick={() => {
        void resetPwa()
      }}
      className="
        btn
        btn-warning
        btn-xs
        fixed
        bottom-4
        right-4
        z-[9999]
        shadow-lg
      "
    >
      Réinitialiser PWA
    </button>
  )
}
