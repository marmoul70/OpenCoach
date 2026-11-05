export interface AppNotification {
  id: string
  title: string
  body: string
  category: 'system' | 'training' | 'coaching' | string
  severity: 'info' | 'warning' | 'error' | string
  url: string | null
  created_at: string
  read_at: string | null
}

export interface NotificationListResponse {
  items: AppNotification[]
  total: number
  unread_count: number
  limit: number
  offset: number
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(
    path,
    {
      ...options,
      credentials: 'include',
      headers: {
        Accept: 'application/json',
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      'Impossible de communiquer avec le centre de notifications.',
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function fetchNotifications(
  options: {
    unreadOnly?: boolean
    limit?: number
    offset?: number
  } = {},
): Promise<NotificationListResponse> {
  const params = new URLSearchParams({
    limit: String(options.limit ?? 30),
    offset: String(options.offset ?? 0),
  })
  if (options.unreadOnly) {
    params.set('unread_only', 'true')
  }
  return request<NotificationListResponse>(
    `/api/notifications?${params.toString()}`,
  )
}

export async function markNotificationRead(
  id: string,
): Promise<void> {
  await request<void>(
    `/api/notifications/${encodeURIComponent(id)}/read`,
    { method: 'POST' },
  )
}

export async function markAllNotificationsRead(): Promise<void> {
  await request<{ updated: number }>(
    '/api/notifications/read-all',
    { method: 'POST' },
  )
}

export async function deleteNotification(
  id: string,
): Promise<void> {
  await request<void>(
    `/api/notifications/${encodeURIComponent(id)}`,
    { method: 'DELETE' },
  )
}

export async function deleteAllNotifications(): Promise<void> {
  await request<{ deleted: number }>(
    '/api/notifications/all',
    { method: 'DELETE' },
  )
}

export function formatNotificationDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'Date inconnue'
  }
  return new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}
