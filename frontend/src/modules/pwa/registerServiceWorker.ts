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
