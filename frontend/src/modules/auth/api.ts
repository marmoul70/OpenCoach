interface FastApiValidationError {
  msg?: string
  loc?: Array<
    string | number
  >
}


function getApiErrorMessage(
  data: unknown,
  fallback: string,
): string {
  if (
    typeof data !== 'object'
    || data === null
  ) {
    return fallback
  }

  if (!('detail' in data)) {
    return fallback
  }

  const detail = (
    data as {
      detail?: unknown
    }
  ).detail

  if (
    typeof detail === 'string'
  ) {
    return detail
  }

  if (
    Array.isArray(
      detail,
    )
  ) {
    const messages =
      detail
        .map(
          (item) => {
            if (
              typeof item !== 'object'
              || item === null
            ) {
              return null
            }

            const validationError =
              item as FastApiValidationError

            if (
              typeof validationError.msg
              !== 'string'
            ) {
              return null
            }

            const field =
              validationError.loc
                ?.filter(
                  part =>
                    part !== 'body',
                )
                .at(
                  -1,
                )

            if (
              typeof field === 'string'
            ) {
              const labels:
                Record<
                  string,
                  string
                > = {
                  username:
                    'Identifiant',
                  pin:
                    'Code PIN',
                  email:
                    'E-mail',
                  first_name:
                    'Prénom',
                  last_name:
                    'Nom',
                }

              const label =
                labels[field]
                ?? field

              return (
                `${label} : `
                + validationError.msg
              )
            }

            return validationError.msg
          },
        )
        .filter(
          (
            message,
          ): message is string =>
            message !== null,
        )

    if (
      messages.length > 0
    ) {
      return messages.join(
        ' · ',
      )
    }
  }

  return fallback
}


export async function checkSession(): Promise<boolean> {
  const response = await fetch(
    '/api/auth/session',
    {
      credentials: 'same-origin',
      cache: 'no-store',
    },
  )

  return response.ok
}


async function handleLoginResponse(
  response: Response,
): Promise<void> {
  if (response.ok) {
    return
  }

  const fallback =
    response.status === 401
      ? (
          'Identifiant ou '
          + 'code PIN incorrect.'
        )
      : (
          'Impossible de se connecter.'
        )

  let message =
    fallback

  try {
    const data: unknown =
      await response.json()

    message =
      getApiErrorMessage(
        data,
        fallback,
      )
  } catch {
    // Réponse non JSON :
    // on conserve le message fallback.
  }

  throw new Error(
    message,
  )
}


export async function loginWithCredentials(
  username: string,
  pin: string,
): Promise<void> {
  const response = await fetch(
    '/api/auth/login',
    {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        username,
        pin,
      }),
    },
  )

  await handleLoginResponse(
    response,
  )
}


export async function logout(): Promise<void> {
  await fetch(
    '/api/auth/logout',
    {
      method: 'POST',
      credentials: 'same-origin',
    },
  )
}


export interface RegisterAccountInput {
  first_name: string
  last_name: string
  email: string
  pin: string
}


export interface RegisterAccountResult {
  username: string
  email: string
}


export async function registerAccount(
  input: RegisterAccountInput,
): Promise<RegisterAccountResult> {
  const response = await fetch(
    '/api/auth/register',
    {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify(
        input,
      ),
    },
  )

  if (response.ok) {
    return (
      await response.json()
    ) as RegisterAccountResult
  }

  const fallback =
    'Impossible de créer le compte.'

  let message =
    fallback

  try {
    const data: unknown =
      await response.json()

    message =
      getApiErrorMessage(
        data,
        fallback,
      )
  } catch {
    // Réponse non JSON.
  }

  throw new Error(
    message,
  )
}



export async function changePin(
  currentPin: string,
  newPin: string,
): Promise<void> {
  const response = await fetch(
    '/api/auth/change-pin',
    {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        current_pin:
          currentPin,
        new_pin:
          newPin,
      }),
    },
  )

  if (response.ok) {
    return
  }

  const fallback =
    'Impossible de modifier le code PIN.'

  let message =
    fallback

  try {
    const data: unknown =
      await response.json()

    message =
      getApiErrorMessage(
        data,
        fallback,
      )
  } catch {
    // Réponse non JSON.
  }

  throw new Error(
    message,
  )
}



export interface AccountInfo {
  username: string
  email: string
  active: boolean
}


export async function fetchAccount():
Promise<AccountInfo> {
  const response = await fetch(
    '/api/auth/account',
    {
      credentials: 'same-origin',
      cache: 'no-store',
    },
  )

  if (response.ok) {
    return (
      await response.json()
    ) as AccountInfo
  }

  const fallback =
    'Impossible de charger le compte.'

  let message =
    fallback

  try {
    const data: unknown =
      await response.json()

    message =
      getApiErrorMessage(
        data,
        fallback,
      )
  } catch {
    // Réponse non JSON.
  }

  throw new Error(
    message,
  )
}


export async function updateAccountEmail(
  email: string,
): Promise<AccountInfo> {
  const response = await fetch(
    '/api/auth/account',
    {
      method: 'PATCH',
      credentials: 'same-origin',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        email,
      }),
    },
  )

  if (response.ok) {
    return (
      await response.json()
    ) as AccountInfo
  }

  const fallback =
    'Impossible de modifier l’e-mail.'

  let message =
    fallback

  try {
    const data: unknown =
      await response.json()

    message =
      getApiErrorMessage(
        data,
        fallback,
      )
  } catch {
    // Réponse non JSON.
  }

  throw new Error(
    message,
  )
}

export async function needsInitialSetup(): Promise<boolean> {
  const response = await fetch('/api/auth/setup-status', {
    credentials: 'same-origin',
    cache: 'no-store',
  })
  if (!response.ok) {
    throw new Error('Impossible de vérifier la configuration initiale.')
  }
  const data = await response.json() as { needs_setup: boolean }
  return data.needs_setup
}


export async function restoreInitialBackup(file: File): Promise<void> {
  const response = await fetch('/api/backups/restore', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/zip' },
    body: file,
  })
  if (!response.ok) {
    let message = 'Impossible de restaurer cette sauvegarde.'
    try {
      const data = await response.json() as { detail?: string }
      message = data.detail ?? message
    } catch {
      // Keep fallback message.
    }
    throw new Error(message)
  }

  // Le backend redémarre si le ZIP contient un .env.
  // On attend son retour avant de recharger l'interface.
  await new Promise(resolve => window.setTimeout(resolve, 1800))
  const deadline = Date.now() + 30000
  while (Date.now() < deadline) {
    try {
      const ready = await fetch('/api/health/ready', {
        credentials: 'same-origin',
        cache: 'no-store',
      })
      if (ready.ok) return
    } catch {
      // Le backend est momentanément en cours de redémarrage.
    }
    await new Promise(resolve => window.setTimeout(resolve, 1000))
  }
  throw new Error('La sauvegarde est restaurée, mais le backend ne répond pas encore. Actualisez la page dans quelques instants.')
}
