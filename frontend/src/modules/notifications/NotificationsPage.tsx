import { useCallback, useEffect, useState } from 'react'
import {
  Bell,
  Check,
  CheckCheck,
  CircleAlert,
  Clock3,
  Info,
  Trash2,
  TriangleAlert,
} from 'lucide-react'

import {
  deleteAllNotifications,
  deleteNotification,
  fetchNotifications,
  formatNotificationDate,
  markAllNotificationsRead,
  markNotificationRead,
  type AppNotification,
} from './notificationsApi'


type Filter = 'all' | 'unread'


export function NotificationsPage() {
  const [filter, setFilter] = useState<Filter>('all')
  const [items, setItems] = useState<AppNotification[]>([])
  const [total, setTotal] = useState(0)
  const [unreadCount, setUnreadCount] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchNotifications({
        unreadOnly: filter === 'unread',
        limit: 100,
      })
      setItems(data.items)
      setTotal(data.total)
      setUnreadCount(data.unread_count)
    } catch (reason) {
      setError(
        reason instanceof Error
          ? reason.message
          : 'Impossible de charger les notifications.',
      )
    } finally {
      setLoading(false)
    }
  }, [filter])

  useEffect(() => {
    void refresh()
  }, [refresh])

  async function loadMore() {
    if (loadingMore || items.length >= total) return
    setLoadingMore(true)
    try {
      const data = await fetchNotifications({
        unreadOnly: filter === 'unread',
        limit: 100,
        offset: items.length,
      })
      setItems((current) => [...current, ...data.items])
      setUnreadCount(data.unread_count)
      setTotal(data.total)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Chargement impossible.')
    } finally {
      setLoadingMore(false)
    }
  }

  async function markRead(item: AppNotification) {
    if (item.read_at) return
    setBusy(true)
    try {
      await markNotificationRead(item.id)
      await refresh()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Action impossible.')
    } finally {
      setBusy(false)
    }
  }

  async function remove(item: AppNotification) {
    setBusy(true)
    try {
      await deleteNotification(item.id)
      await refresh()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Suppression impossible.')
    } finally {
      setBusy(false)
    }
  }

  async function markAllRead() {
    setBusy(true)
    try {
      await markAllNotificationsRead()
      await refresh()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Action impossible.')
    } finally {
      setBusy(false)
    }
  }

  async function clearAll() {
    if (!window.confirm('Supprimer définitivement toutes les notifications ?')) {
      return
    }
    setBusy(true)
    try {
      await deleteAllNotifications()
      await refresh()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Suppression impossible.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 lg:px-8">
      <header className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <div className="
            flex h-11 w-11 items-center justify-center rounded-2xl
            bg-[var(--oc-surface-muted)] text-[var(--oc-accent)]
          ">
            <Bell className="h-5 w-5" />
          </div>
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.14em] text-[var(--oc-muted)]">
              OpenCoach
            </p>
            <h1 className="mt-1 text-xl font-bold tracking-tight text-[var(--oc-text)]">
              Centre de notifications
            </h1>
            <p className="mt-1 text-xs text-[var(--oc-muted)]">
              Historique conservé dans OpenCoach, indépendamment de ton iPhone.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            disabled={busy || unreadCount === 0}
            onClick={() => void markAllRead()}
            className="
              inline-flex items-center gap-2 rounded-xl border
              border-[var(--oc-border)] px-3 py-2 text-[11px]
              font-semibold text-[var(--oc-text-secondary)]
              transition hover:bg-[var(--oc-surface-hover)]
              disabled:cursor-not-allowed disabled:opacity-40
            "
          >
            <CheckCheck className="h-3.5 w-3.5" />
            Tout marquer comme lu
          </button>
          <button
            type="button"
            disabled={busy || total === 0}
            onClick={() => void clearAll()}
            className="
              inline-flex items-center gap-2 rounded-xl border
              border-rose-500/20 px-3 py-2 text-[11px]
              font-semibold text-rose-600 transition
              hover:bg-rose-500/[0.06]
              disabled:cursor-not-allowed disabled:opacity-40
              dark:text-rose-400
            "
          >
            <Trash2 className="h-3.5 w-3.5" />
            Tout effacer
          </button>
        </div>
      </header>

      <section className="
        mt-6 overflow-hidden rounded-2xl border
        border-[var(--oc-border)] bg-[var(--oc-surface)]
      ">
        <div className="
          flex flex-wrap items-center justify-between gap-3
          border-b border-[var(--oc-border)] px-4 py-3
        ">
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setFilter('all')}
              aria-pressed={filter === 'all'}
              className={[
                'rounded-full px-3 py-1.5 text-[10px] font-semibold transition',
                filter === 'all'
                  ? 'bg-[var(--oc-text)] text-[var(--oc-surface)]'
                  : 'text-[var(--oc-muted)] hover:bg-[var(--oc-surface-hover)]',
              ].join(' ')}
            >
              Toutes
            </button>
            <button
              type="button"
              onClick={() => setFilter('unread')}
              aria-pressed={filter === 'unread'}
              className={[
                'rounded-full px-3 py-1.5 text-[10px] font-semibold transition',
                filter === 'unread'
                  ? 'bg-[var(--oc-text)] text-[var(--oc-surface)]'
                  : 'text-[var(--oc-muted)] hover:bg-[var(--oc-surface-hover)]',
              ].join(' ')}
            >
              Non lues
              {unreadCount > 0 && (
                <span className="ml-1.5 tabular-nums">{unreadCount}</span>
              )}
            </button>
          </div>
          <span className="text-[10px] text-[var(--oc-muted)]">
            {total} notification(s)
          </span>
        </div>

        {error && (
          <div role="alert" className="border-b border-rose-500/15 bg-rose-500/[0.05] px-4 py-3 text-xs text-rose-600 dark:text-rose-400">
            {error}
            <button type="button" onClick={() => void refresh()} className="ml-2 font-semibold underline">
              Réessayer
            </button>
          </div>
        )}

        {loading ? (
          <p className="px-4 py-12 text-center text-xs text-[var(--oc-muted)]">
            Chargement des notifications…
          </p>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center px-5 py-14 text-center">
            <Bell className="h-8 w-8 text-[var(--oc-muted-soft)]" />
            <p className="mt-3 text-sm font-semibold text-[var(--oc-text)]">
              {filter === 'unread' ? 'Aucune notification non lue' : 'Aucune notification pour le moment'}
            </p>
            <p className="mt-1 max-w-sm text-xs leading-5 text-[var(--oc-muted)]">
              Les alertes de synchronisation, les rappels et les informations du coach seront conservés ici.
            </p>
          </div>
        ) : (
          <div>
            {items.map((item) => (
              <NotificationRow
                key={item.id}
                item={item}
                disabled={busy}
                onRead={() => void markRead(item)}
                onDelete={() => void remove(item)}
              />
            ))}
            {items.length < total && (
              <div className="border-t border-[var(--oc-border)] px-4 py-3 text-center">
                <button
                  type="button"
                  disabled={loadingMore || busy}
                  onClick={() => void loadMore()}
                  className="text-[11px] font-semibold text-[var(--oc-accent)] hover:underline disabled:opacity-50"
                >
                  {loadingMore ? 'Chargement…' : 'Charger les notifications suivantes'}
                </button>
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  )
}


function NotificationRow({
  item,
  disabled,
  onRead,
  onDelete,
}: {
  item: AppNotification
  disabled: boolean
  onRead: () => void
  onDelete: () => void
}) {
  const Icon = item.severity === 'error'
    ? CircleAlert
    : item.severity === 'warning'
      ? TriangleAlert
      : item.category === 'training'
        ? Clock3
        : Info

  return (
    <article className={[
      'flex items-start gap-3 border-b border-[var(--oc-border)] px-4 py-4 last:border-b-0 sm:px-5',
      item.read_at ? '' : 'bg-[var(--oc-surface-muted)]/45',
    ].join(' ')}>
      <div className="
        flex h-9 w-9 shrink-0 items-center justify-center
        rounded-xl bg-[var(--oc-surface-muted)]
        text-[var(--oc-text-secondary)]
      ">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-xs font-semibold text-[var(--oc-text)]">
            {item.title}
          </h2>
          {!item.read_at && (
            <span className="rounded-full bg-[var(--oc-accent)]/10 px-2 py-0.5 text-[9px] font-semibold text-[var(--oc-accent)]">
              Non lue
            </span>
          )}
        </div>
        <p className="mt-1 whitespace-pre-wrap text-xs leading-5 text-[var(--oc-muted)]">
          {item.body}
        </p>
        <p className="mt-2 text-[9px] text-[var(--oc-muted-soft)]">
          {formatNotificationDate(item.created_at)}
          <span className="mx-1.5">·</span>
          {item.category === 'training'
            ? 'Entraînement'
            : item.category === 'coaching'
              ? 'Coach'
              : 'Système'}
        </p>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        {!item.read_at && (
          <button
            type="button"
            disabled={disabled}
            onClick={onRead}
            aria-label="Marquer comme lue"
            title="Marquer comme lue"
            className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--oc-muted)] transition hover:bg-emerald-500/10 hover:text-emerald-600 disabled:opacity-40"
          >
            <Check className="h-4 w-4" />
          </button>
        )}
        <button
          type="button"
          disabled={disabled}
          onClick={onDelete}
          aria-label="Supprimer la notification"
          title="Supprimer"
          className="flex h-8 w-8 items-center justify-center rounded-lg text-[var(--oc-muted)] transition hover:bg-rose-500/10 hover:text-rose-600 disabled:opacity-40"
        >
          <Trash2 className="h-4 w-4" />
        </button>
      </div>
    </article>
  )
}
