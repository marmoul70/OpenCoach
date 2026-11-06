import { useCallback, useEffect, useState } from 'react'
import { Bell, CheckCheck, Inbox } from 'lucide-react'

import {
  fetchNotifications,
  formatNotificationDate,
  markNotificationRead,
  type AppNotification,
} from '../../modules/notifications/notificationsApi'


interface NotificationBellProps {
  onViewAll: () => void
  placement?: 'default' | 'sidebar'
  embedded?: boolean
}


export function NotificationBell({
  onViewAll,
  placement = 'default',
  embedded = false,
}: NotificationBellProps) {
  const [open, setOpen] = useState(false)
  const [items, setItems] = useState<AppNotification[]>([])
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const data = await fetchNotifications({ limit: 6 })
      setItems(data.items)
      setUnreadCount(data.unread_count)
    } catch {
      // Le centre complet affichera l'erreur si l'API est indisponible.
    }
  }, [])

  useEffect(() => {
    void refresh()
    const interval = window.setInterval(() => {
      void refresh()
    }, 60_000)
    const onFocus = () => void refresh()
    const onNotificationsChanged = () => void refresh()
    window.addEventListener('focus', onFocus)
    window.addEventListener(
      'opencoach:notifications-updated',
      onNotificationsChanged,
    )
    return () => {
      window.clearInterval(interval)
      window.removeEventListener('focus', onFocus)
      window.removeEventListener(
        'opencoach:notifications-updated',
        onNotificationsChanged,
      )
    }
  }, [refresh])

  async function toggle() {
    const next = !open
    setOpen(next)
    if (next) {
      setLoading(true)
      await refresh()
      setLoading(false)
    }
  }

  function viewAll() {
    setOpen(false)
    onViewAll()
  }

  async function markRead(notification: AppNotification) {
    if (notification.read_at) return
    try {
      await markNotificationRead(notification.id)
      await refresh()
    } catch {
      // La notification reste non lue si la mise à jour échoue.
    }
  }

  return (
    <div className={embedded ? "w-full min-w-0" : "relative"}>
      {!embedded && <button
        type="button"
        onClick={() => void toggle()}
        aria-label={
          unreadCount > 0
            ? `Notifications, ${unreadCount} non lue(s)`
            : 'Notifications'
        }
        aria-haspopup="dialog"
        aria-expanded={open}
        className={[
          'relative flex h-10 w-10 shrink-0 items-center justify-center',
          'rounded-xl text-[var(--oc-text-secondary)] transition-colors',
          'hover:bg-[var(--oc-surface-hover)]',
          'dark:hover:bg-[var(--oc-surface)]/[0.08]',
        ].join(' ')}
      >
        <Bell className="h-[18px] w-[18px]" />
        {unreadCount > 0 && (
          <span className="
            absolute right-0.5 top-0.5 flex min-h-[17px] min-w-[17px]
            items-center justify-center rounded-full border-2
            border-[var(--oc-surface)] bg-rose-500 px-1
            text-[9px] font-bold leading-none text-white
          ">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>}

      {(open || embedded) && (
        <>
          {!embedded && <button
            type="button"
            aria-label="Fermer les notifications"
            className="fixed inset-0 z-[40] cursor-default"
            onClick={() => setOpen(false)}
          />}
          <section
            role={embedded ? "region" : "dialog"}
            aria-label="Notifications récentes"
            className={embedded
              ? 'w-full overflow-hidden'
              : [
                  placement === 'sidebar'
                    ? 'fixed bottom-20 left-3'
                    : 'absolute right-0 top-[calc(100%+10px)]',
                  'z-[80] w-[min(360px,calc(100vw-24px))] overflow-hidden',
                  'rounded-2xl border border-[var(--oc-border)]',
                  'bg-[var(--oc-surface)] shadow-[0_18px_50px_rgba(15,23,42,0.18)]',
                  'dark:shadow-[0_18px_50px_rgba(0,0,0,0.42)]',
                ].join(' ')}
          >
            <div className={embedded
              ? "mb-2 flex items-center justify-between gap-3"
              : "flex items-center justify-between border-b border-[var(--oc-border)] px-4 py-3"
            }>
              <div className="flex min-w-0 items-center gap-2">
                {embedded && <Bell className="h-4 w-4 shrink-0 text-[var(--oc-muted)]" />}
                <div className="min-w-0">
                  <h2 className="text-[12px] font-semibold text-[var(--oc-text)]">
                    Notifications
                  </h2>
                  <p className="mt-0.5 text-[10px] text-[var(--oc-muted)]">
                    {unreadCount} non lue(s)
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={viewAll}
                className="
                  shrink-0 text-[10px] font-semibold text-[var(--oc-accent)]
                  hover:underline
                "
              >
                Tout afficher
              </button>
            </div>

            <div className={embedded ? "max-h-[26vh] overflow-y-auto rounded-xl bg-[var(--oc-surface-muted)]/45" : "max-h-[min(420px,65vh)] overflow-y-auto"}>
              {loading && items.length === 0 ? (
                <p className="px-4 py-8 text-center text-xs text-[var(--oc-muted)]">
                  Chargement…
                </p>
              ) : items.length === 0 ? (
                <div className={embedded ? "flex flex-col items-center px-4 py-5 text-center" : "flex flex-col items-center px-5 py-9 text-center"}>
                  <Inbox className="h-7 w-7 text-[var(--oc-muted-soft)]" />
                  <p className="mt-2 text-xs font-semibold text-[var(--oc-text)]">
                    Aucune notification
                  </p>
                  <p className="mt-1 text-[10px] text-[var(--oc-muted)]">
                    Tes prochaines alertes apparaîtront ici.
                  </p>
                </div>
              ) : (
                items.map((item) => (
                  <article
                    key={item.id}
                    className={[
                      'border-b border-[var(--oc-border)]/70 px-3 py-2.5 last:border-b-0',
                      item.read_at ? 'opacity-70' : 'bg-[var(--oc-surface-muted)]/45',
                    ].join(' ')}
                  >
                    <button
                      type="button"
                      onClick={() => void markRead(item)}
                      className="block w-full text-left"
                    >
                      <div className="flex items-start gap-2">
                        <span className={[
                          'mt-1.5 h-2 w-2 shrink-0 rounded-full',
                          item.read_at ? 'bg-transparent' : 'bg-[var(--oc-accent)]',
                        ].join(' ')} />
                        <span className="min-w-0 flex-1">
                          <span className="block text-[11px] font-semibold text-[var(--oc-text)]">
                            {item.title}
                          </span>
                          <span className="mt-1 block text-[10px] leading-4 text-[var(--oc-muted)]">
                            {item.body}
                          </span>
                          <span className="mt-1.5 block text-[9px] text-[var(--oc-muted-soft)]">
                            {formatNotificationDate(item.created_at)}
                          </span>
                        </span>
                      </div>
                    </button>
                  </article>
                ))
              )}
            </div>

            {!embedded && (
              <div className="border-t border-[var(--oc-border)] p-2">
                <button
                  type="button"
                  onClick={viewAll}
                  className="flex w-full items-center justify-center gap-2 rounded-xl bg-[var(--oc-surface-muted)] px-3 py-2.5 text-[10px] font-semibold text-[var(--oc-text-secondary)] transition hover:bg-[var(--oc-surface-hover)]"
                >
                  <CheckCheck className="h-3.5 w-3.5" />
                  Ouvrir le centre de notifications
                </button>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
