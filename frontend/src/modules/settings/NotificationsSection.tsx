import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  Bell,
  BellOff,
  CheckCircle2,
  Smartphone,
} from 'lucide-react'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import {
  ProfileSection,
} from '../profile/ProfileSection'

import {
  deletePushSubscription,
  fetchPushPublicKey,
  savePushSubscription,
  urlBase64ToUint8Array,
} from '../pwa/pushApi'


type NotificationState =
  | 'loading'
  | 'unsupported'
  | 'denied'
  | 'disabled'
  | 'enabled'


export function NotificationsSection() {
  const {
    toast,
  } = useToast()

  const [
    state,
    setState,
  ] = useState<NotificationState>(
    'loading',
  )

  const [
    busy,
    setBusy,
  ] = useState(
    false,
  )


  const refreshState =
    useCallback(
      async () => {
        if (
          !(
            'serviceWorker'
            in navigator
          )
          || !(
            'PushManager'
            in window
          )
          || !(
            'Notification'
            in window
          )
        ) {
          setState(
            'unsupported',
          )

          return
        }

        if (
          Notification.permission
          === 'denied'
        ) {
          setState(
            'denied',
          )

          return
        }

        try {
          const registration =
            await navigator
              .serviceWorker
              .ready

          const subscription =
            await registration
              .pushManager
              .getSubscription()

          setState(
            subscription
              ? 'enabled'
              : 'disabled',
          )
        } catch {
          setState(
            'disabled',
          )
        }
      },
      [],
    )


  useEffect(() => {
    void refreshState()
  }, [
    refreshState,
  ])


  async function enableNotifications() {
    setBusy(
      true,
    )

    try {
      const permission =
        await Notification
          .requestPermission()

      if (
        permission
        !== 'granted'
      ) {
        setState(
          permission === 'denied'
            ? 'denied'
            : 'disabled',
        )

        return
      }

      const publicKey =
        await fetchPushPublicKey()

      const registration =
        await navigator
          .serviceWorker
          .ready

      let subscription =
        await registration
          .pushManager
          .getSubscription()

      if (!subscription) {
        subscription =
          await registration
            .pushManager
            .subscribe({
              userVisibleOnly: true,
              applicationServerKey:
                urlBase64ToUint8Array(
                  publicKey,
                ),
            })
      }

      await savePushSubscription(
        subscription,
      )

      setState(
        'enabled',
      )

      toast({
        type: 'success',
        title:
          'Notifications activées',
        message:
          'Cet appareil peut maintenant '
          + 'recevoir les alertes OpenCoach.',
      })
    } catch (reason) {
      toast({
        type: 'error',
        title:
          'Activation impossible',
        message:
          reason instanceof Error
            ? reason.message
            : (
              'Impossible d’activer '
              + 'les notifications.'
            ),
      })

      await refreshState()
    } finally {
      setBusy(
        false,
      )
    }
  }


  async function disableNotifications() {
    setBusy(
      true,
    )

    try {
      const registration =
        await navigator
          .serviceWorker
          .ready

      const subscription =
        await registration
          .pushManager
          .getSubscription()

      if (subscription) {
        await deletePushSubscription(
          subscription.endpoint,
        )

        await subscription.unsubscribe()
      }

      setState(
        'disabled',
      )

      toast({
        type: 'success',
        title:
          'Notifications désactivées',
        message:
          'Cet appareil ne recevra '
          + 'plus les alertes OpenCoach.',
      })
    } catch (reason) {
      toast({
        type: 'error',
        title:
          'Désactivation impossible',
        message:
          reason instanceof Error
            ? reason.message
            : (
              'Impossible de désactiver '
              + 'les notifications.'
            ),
      })
    } finally {
      setBusy(
        false,
      )
    }
  }


  return (
    <ProfileSection
      title="Notifications"
      description={
        "Recevez les rappels de séance "
        + "et les informations importantes "
        + "du coach sur cet appareil."
      }
      trailing={
        <NotificationBadge
          state={state}
        />
      }
    >
      <div
        className="
          space-y-5
        "
      >
        <div
          className="
            flex
            items-start
            gap-4
          "
        >
          <div
            className="
              flex
              h-11
              w-11
              shrink-0
              items-center
              justify-center
              rounded-xl
              bg-primary/10
              text-primary
            "
          >
            <Bell
              size={21}
            />
          </div>

          <div
            className="
              min-w-0
              flex-1
            "
          >
            <p
              className="
                text-sm
                leading-relaxed
                text-base-content/70
              "
            >
              OpenCoach peut vous prévenir
              lorsqu'une information importante
              concernant votre entraînement
              est disponible.
            </p>

            <NotificationStatus
              state={state}
            />
          </div>
        </div>

        <div
          className="
            flex
            justify-end
          "
        >
          {state === 'enabled' ? (
            <button
              type="button"
              className="
                btn
                btn-outline
                btn-sm
                gap-2
              "
              disabled={busy}
              onClick={() => {
                void disableNotifications()
              }}
            >
              {busy ? (
                <span
                  className="
                    loading
                    loading-spinner
                    loading-xs
                  "
                />
              ) : (
                <BellOff
                  size={16}
                />
              )}

              Désactiver
            </button>
          ) : (
            <button
              type="button"
              className="
                btn
                btn-primary
                btn-sm
                gap-2
              "
              disabled={
                busy
                || state === 'loading'
                || state === 'unsupported'
                || state === 'denied'
              }
              onClick={() => {
                void enableNotifications()
              }}
            >
              {busy ? (
                <span
                  className="
                    loading
                    loading-spinner
                    loading-xs
                  "
                />
              ) : (
                <Bell
                  size={16}
                />
              )}

              Activer
            </button>
          )}
        </div>
      </div>
    </ProfileSection>
  )
}


function NotificationBadge({
  state,
}: {
  state: NotificationState
}) {
  if (
    state === 'enabled'
  ) {
    return (
      <span
        className="
          badge
          badge-success
          badge-sm
          font-medium
        "
      >
        Activées
      </span>
    )
  }


  if (
    state === 'denied'
  ) {
    return (
      <span
        className="
          badge
          badge-warning
          badge-sm
          font-medium
        "
      >
        Bloquées
      </span>
    )
  }


  if (
    state === 'disabled'
  ) {
    return (
      <span
        className="
          badge
          badge-warning
          badge-sm
          font-medium
        "
      >
        Désactivées
      </span>
    )
  }


  if (
    state === 'unsupported'
  ) {
    return (
      <span
        className="
          badge
          badge-ghost
          badge-sm
          font-medium
        "
      >
        Indisponibles
      </span>
    )
  }


  return (
    <span
      className="
        badge
        badge-ghost
        badge-sm
        font-medium
      "
    >
      Vérification…
    </span>
  )
}


function NotificationStatus({
  state,
}: {
  state: NotificationState
}) {
  if (
    state === 'loading'
  ) {
    return (
      <p
        className="
          mt-3
          text-xs
          text-base-content/45
        "
      >
        Vérification…
      </p>
    )
  }


  if (
    state === 'enabled'
  ) {
    return (
      <div
        className="
          mt-3
          flex
          items-center
          gap-1.5
          text-xs
          font-medium
          text-success
        "
      >
        <CheckCircle2
          size={14}
        />

        Notifications actives
      </div>
    )
  }


  if (
    state === 'denied'
  ) {
    return (
      <p
        className="
          mt-3
          text-xs
          text-warning
        "
      >
        Les notifications sont bloquées
        dans les réglages de l’appareil.
      </p>
    )
  }


  if (
    state === 'unsupported'
  ) {
    return (
      <div
        className="
          mt-3
          flex
          items-start
          gap-1.5
          text-xs
          text-base-content/50
        "
      >
        <Smartphone
          size={14}
          className="mt-0.5 shrink-0"
        />

        Notifications non disponibles
        dans ce navigateur.
      </div>
    )
  }


  return (
    <p
      className="
        mt-3
        text-xs
        text-base-content/45
      "
    >
      Notifications désactivées
    </p>
  )
}
