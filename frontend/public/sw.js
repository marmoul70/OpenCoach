const CACHE_PREFIX =
  'opencoach'

const SHELL_CACHE =
  `${CACHE_PREFIX}-shell-v1`

const RUNTIME_CACHE =
  `${CACHE_PREFIX}-runtime-v1`


const SHELL_FILES = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/favicon.png',
  '/opencoach-logo.png',
  '/icons/apple-touch-icon.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
]


self.addEventListener(
  'install',
  (event) => {
    event.waitUntil(
      caches
        .open(
          SHELL_CACHE,
        )
        .then(
          (cache) =>
            cache.addAll(
              SHELL_FILES,
            ),
        ),
    )

    self.skipWaiting()
  },
)


self.addEventListener(
  'activate',
  (event) => {
    const validCaches =
      new Set([
        SHELL_CACHE,
        RUNTIME_CACHE,
      ])

    event.waitUntil(
      caches
        .keys()
        .then(
          (cacheNames) =>
            Promise.all(
              cacheNames
                .filter(
                  (cacheName) =>
                    cacheName.startsWith(
                      `${CACHE_PREFIX}-`,
                    )
                    && !validCaches.has(
                      cacheName,
                    ),
                )
                .map(
                  (cacheName) =>
                    caches.delete(
                      cacheName,
                    ),
                ),
            ),
        )
        .then(
          () =>
            self.clients.claim(),
        ),
    )
  },
)


self.addEventListener(
  'fetch',
  (event) => {
    const request =
      event.request

    if (
      request.method
      !== 'GET'
    ) {
      return
    }


    const url =
      new URL(
        request.url,
      )


    /*
     * Ne jamais intercepter
     * une origine externe.
     */
    if (
      url.origin
      !== self.location.origin
    ) {
      return
    }


    /*
     * Les données métier OpenCoach
     * doivent toujours provenir
     * directement de FastAPI.
     */
    if (
      url.pathname.startsWith(
        '/api/',
      )
    ) {
      return
    }


    /*
     * Le VersionWatcher doit toujours
     * connaître la release réellement
     * publiée sur Nginx.
     */
    if (
      url.pathname
      === '/version.json'
    ) {
      return
    }


    /*
     * Navigation :
     *
     * réseau en priorité.
     * Si le serveur est inaccessible,
     * on démarre le shell PWA local.
     */
    if (
      request.mode
      === 'navigate'
    ) {
      event.respondWith(
        networkFirstNavigation(
          request,
        ),
      )

      return
    }


    /*
     * Assets statiques :
     *
     * réponse cache immédiate lorsqu'elle
     * existe, avec rafraîchissement réseau
     * en arrière-plan.
     */
    if (
      isStaticAsset(
        request,
        url,
      )
    ) {
      event.respondWith(
        staleWhileRevalidate(
          request,
        ),
      )
    }
  },
)


async function networkFirstNavigation(
  request,
) {
  try {
    const response =
      await fetch(
        request,
      )

    if (
      response.ok
    ) {
      const cache =
        await caches.open(
          SHELL_CACHE,
        )

      await cache.put(
        '/',
        response.clone(),
      )
    }

    return response
  } catch {
    const cached =
      await caches.match(
        '/',
      )

    if (
      cached
    ) {
      return cached
    }

    const fallback =
      await caches.match(
        '/index.html',
      )

    if (
      fallback
    ) {
      return fallback
    }

    throw new Error(
      'OpenCoach offline shell unavailable.',
    )
  }
}


async function staleWhileRevalidate(
  request,
) {
  const cache =
    await caches.open(
      RUNTIME_CACHE,
    )

  const cached =
    await cache.match(
      request,
    )


  const networkPromise =
    fetch(
      request,
    )
      .then(
        async (
          response,
        ) => {
          if (
            response.ok
          ) {
            await cache.put(
              request,
              response.clone(),
            )
          }

          return response
        },
      )
      .catch(
        () => null,
      )


  if (
    cached
  ) {
    void networkPromise

    return cached
  }


  const networkResponse =
    await networkPromise

  if (
    networkResponse
  ) {
    return networkResponse
  }


  return new Response(
    '',
    {
      status: 503,
      statusText:
        'Service unavailable',
    },
  )
}


function isStaticAsset(
  request,
  url,
) {
  const destinations =
    new Set([
      'script',
      'style',
      'image',
      'font',
    ])


  if (
    destinations.has(
      request.destination,
    )
  ) {
    return true
  }


  return (
    url.pathname
      .startsWith(
        '/assets/',
      )
    || url.pathname
      .startsWith(
        '/icons/',
      )
  )
}


/* ==========================================================
   OpenCoach Web Push
   ========================================================== */

self.addEventListener(
  'push',
  (event) => {
    event.waitUntil(
      handlePushDiagnostic(
        event,
      ),
    )
  },
)


async function handlePushDiagnostic(
  event,
) {
  let payload = {
    title: 'OpenCoach',
    body: 'Notification OpenCoach',
    url: '/',
    badge: 1,
  }

  if (event.data) {
    try {
      payload = {
        ...payload,
        ...event.data.json(),
      }
    } catch {
      payload.body =
        event.data.text()
    }
  }

  const badgeCount =
    Math.max(
      1,
      Number(
        payload.badge,
      ) || 1,
    )

  let badgeDiagnostic =
    'Badge API absente'

  if (
    'setAppBadge'
    in self.navigator
  ) {
    try {
      await self.navigator
        .setAppBadge(
          badgeCount,
        )

      badgeDiagnostic =
        `Badge SW OK (${badgeCount})`
    } catch (error) {
      const errorName =
        error?.name
        || 'Erreur'

      const errorMessage =
        error?.message
        || ''

      badgeDiagnostic =
        `Badge SW ERREUR: ${errorName} ${errorMessage}`
    }
  }

  await self.registration
    .showNotification(
      payload.title,
      {
        body:
          `${payload.body}\n${badgeDiagnostic}`,
        icon:
          '/icons/icon-192.png',
        data: {
          url:
            payload.url
            || '/',
        },
      },
    )
}


self.addEventListener(
  'notificationclick',
  (event) => {
    event.notification.close()

    const targetUrl =
      event.notification
        .data?.url
      || '/'

    event.waitUntil(
      self.clients
        .matchAll({
          type: 'window',
          includeUncontrolled: true,
        })
        .then(
          async (clients) => {
            for (
              const client
              of clients
            ) {
              if (
                'focus'
                in client
              ) {
                await client.focus()

                if (
                  'navigate'
                  in client
                ) {
                  await client.navigate(
                    targetUrl,
                  )
                }

                return
              }
            }

            if (
              self.clients.openWindow
            ) {
              await self.clients
                .openWindow(
                  targetUrl,
                )
            }
          },
        ),
    )
  },
)
