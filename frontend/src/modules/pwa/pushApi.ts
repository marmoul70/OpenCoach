interface PublicKeyResponse {
  public_key: string
}


interface PushSubscriptionResponse {
  subscribed: boolean
}


export async function fetchPushPublicKey():
Promise<string> {
  const response = await fetch(
    '/api/push/public-key',
    {
      credentials: 'include',
      headers: {
        Accept: 'application/json',
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      'Impossible de charger la clé Web Push.',
    )
  }

  const data = (
    await response.json()
  ) as PublicKeyResponse

  if (!data.public_key) {
    throw new Error(
      'Les notifications ne sont pas '
      + 'configurées sur OpenCoach.',
    )
  }

  return data.public_key
}


export async function savePushSubscription(
  subscription: PushSubscription,
): Promise<void> {
  const json =
    subscription.toJSON()

  if (
    !json.endpoint
    || !json.keys?.p256dh
    || !json.keys?.auth
  ) {
    throw new Error(
      'Abonnement Web Push invalide.',
    )
  }

  const response = await fetch(
    '/api/push/subscriptions',
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        endpoint:
          json.endpoint,
        keys: {
          p256dh:
            json.keys.p256dh,
          auth:
            json.keys.auth,
        },
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Impossible d’enregistrer '
      + 'les notifications.',
    )
  }

  (
    await response.json()
  ) as PushSubscriptionResponse
}


export async function deletePushSubscription(
  endpoint: string,
): Promise<void> {
  const response = await fetch(
    '/api/push/subscriptions',
    {
      method: 'DELETE',
      credentials: 'include',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        endpoint,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Impossible de désactiver '
      + 'les notifications.',
    )
  }
}


export function urlBase64ToUint8Array(
  value: string,
): Uint8Array<ArrayBuffer> {
  const padding =
    '='.repeat(
      (
        4
        - value.length % 4
      ) % 4,
    )

  const base64 =
    (
      value
      + padding
    )
      .replace(
        /-/g,
        '+',
      )
      .replace(
        /_/g,
        '/',
      )

  const rawData =
    window.atob(
      base64,
    )

  const output =
    new Uint8Array(
      rawData.length,
    )

  for (
    let index = 0;
    index < rawData.length;
    index += 1
  ) {
    output[index] =
      rawData.charCodeAt(
        index,
      )
  }

  return output
}


export async function resetPushBadge(
  endpoint: string,
): Promise<void> {
  const response = await fetch(
    '/api/push/badge/reset',
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        endpoint,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Impossible de réinitialiser '
      + 'le badge Push.',
    )
  }
}


export interface PushDevice {
  id: string
  device_name: string
  browser: string
  current: boolean
  created_at: string
  updated_at: string
  badge_count: number
}


export interface PushPreferences {
  systemEnabled: boolean
  syncErrors: boolean
  backupErrors: boolean
}


interface PushDevicesResponse {
  devices: PushDevice[]
}


interface PushPreferencesResponse {
  system_enabled: boolean
  sync_errors: boolean
  backup_errors: boolean
}


export async function fetchPushDevices(
  endpoint: string,
): Promise<PushDevice[]> {
  const response = await fetch(
    '/api/push/devices',
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        endpoint,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Impossible de charger les appareils.',
    )
  }

  const data: PushDevicesResponse =
    await response.json()

  return data.devices
}


export async function fetchPushPreferences(
  endpoint: string,
): Promise<PushPreferences> {
  const response = await fetch(
    '/api/push/preferences/read',
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        endpoint,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Impossible de charger '
      + 'les préférences.',
    )
  }

  const data: PushPreferencesResponse =
    await response.json()

  return {
    systemEnabled:
      data.system_enabled,
    syncErrors:
      data.sync_errors,
    backupErrors:
      data.backup_errors,
  }
}


export async function updatePushPreferences(
  endpoint: string,
  preferences: PushPreferences,
): Promise<void> {
  const response = await fetch(
    '/api/push/preferences',
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        'Content-Type':
          'application/json',
      },
      body: JSON.stringify({
        endpoint,
        system_enabled:
          preferences.systemEnabled,
        sync_errors:
          preferences.syncErrors,
        backup_errors:
          preferences.backupErrors,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Impossible d’enregistrer '
      + 'les préférences.',
    )
  }
}
