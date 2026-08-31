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


export async function loginWithPin(
  pin: string,
): Promise<void> {
  const response = await fetch(
    '/api/auth/login',
    {
      method: 'POST',
      credentials: 'same-origin',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        pin,
      }),
    },
  )

  if (response.ok) {
    return
  }

  let detail =
    'Impossible de se connecter.'

  try {
    const data = (
      await response.json()
    ) as {
      detail?: string
    }

    if (data.detail) {
      detail = data.detail
    }
  } catch {
    // réponse non JSON
  }

  throw new Error(
    detail,
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
