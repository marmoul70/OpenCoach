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
          '/sw.js?v=0.3.0-rc.11',
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
