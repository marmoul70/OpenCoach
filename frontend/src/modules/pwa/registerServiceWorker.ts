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
      void navigator
        .serviceWorker
        .register(
          '/sw.js',
          {
            scope: '/',
            updateViaCache: 'none',
          },
        )
        .then(
          async (
            registration,
          ) => {
            /*
             * Vérification explicite afin
             * d'éviter qu'iOS conserve trop
             * longtemps un ancien worker.
             */
            try {
              await registration
                .update()
            } catch {
              // La PWA reste fonctionnelle.
            }
          },
        )
        .catch(
          (reason) => {
            console.error(
              'Impossible d’enregistrer '
              + 'le service worker OpenCoach.',
              reason,
            )
          },
        )
    },
  )
}
