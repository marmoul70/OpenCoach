import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import {
  Bell,
  BellOff,
  CheckCircle2,
  ChevronRight,
  CircleAlert,
  MonitorSmartphone,
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
  fetchPushDevices,
  fetchPushPreferences,
  fetchPushPublicKey,
  savePushSubscription,
  updatePushPreferences,
  urlBase64ToUint8Array,
  type PushDevice,
  type PushPreferences,
} from '../pwa/pushApi'


type NotificationState =
  | 'loading'
  | 'unsupported'
  | 'denied'
  | 'disabled'
  | 'enabled'


const DEFAULT_PREFERENCES: PushPreferences = {
  systemEnabled: true,
  syncErrors: true,
  backupErrors: true,
  trainingReminder: false,
}


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

  const [
    endpoint,
    setEndpoint,
  ] = useState<string | null>(
    null,
  )

  const [
    devices,
    setDevices,
  ] = useState<PushDevice[]>(
    [],
  )

  const [
    preferences,
    setPreferences,
  ] = useState<PushPreferences>(
    DEFAULT_PREFERENCES,
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

          if (!subscription) {
            setEndpoint(
              null,
            )

            setDevices(
              [],
            )

            setState(
              'disabled',
            )

            return
          }

          setEndpoint(
            subscription.endpoint,
          )

          setState(
            'enabled',
          )

          const [
            loadedDevices,
            loadedPreferences,
          ] = await Promise.all([
            fetchPushDevices(
              subscription.endpoint,
            ),
            fetchPushPreferences(
              subscription.endpoint,
            ),
          ])

          setDevices(
            loadedDevices,
          )

          setPreferences(
            loadedPreferences,
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

      await refreshState()

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

      setEndpoint(
        null,
      )

      setDevices(
        [],
      )

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


  async function savePreferences(
    next: PushPreferences,
  ) {
    if (!endpoint) {
      return
    }

    const previous =
      preferences

    setPreferences(
      next,
    )

    try {
      await updatePushPreferences(
        endpoint,
        next,
      )
    } catch (reason) {
      setPreferences(
        previous,
      )

      toast({
        type: 'error',
        title:
          'Enregistrement impossible',
        message:
          reason instanceof Error
            ? reason.message
            : (
              'Impossible de modifier '
              + 'les préférences.'
            ),
      })
    }
  }


  const enabled =
    state === 'enabled'


  return (
    <ProfileSection
      title="Notifications"
      icon={
        <Bell
          size={21}
        />
      }
      iconClassName="
        bg-secondary/10
        text-secondary
      "
      description={
        'Choisissez les alertes '
        + 'envoyées par OpenCoach.'
      }
      trailing={
        <NotificationBadge
          state={state}
        />
      }
    >
      <div
        className="
          space-y-6
        "
      >
        <section
          className="
            rounded-xl
            border
            border-base-300
            bg-base-100
            p-4
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              gap-4
            "
          >
            <div
              className="
                flex
                min-w-0
                items-center
                gap-3
              "
            >
              <div
                className="
                  flex
                  h-10
                  w-10
                  shrink-0
                  items-center
                  justify-center
                  rounded-xl
                  bg-secondary/10
                  text-secondary
                "
              >
                <Smartphone
                  size={19}
                />
              </div>

              <div>
                <p
                  className="
                    font-medium
                    text-base-content
                  "
                >
                  Cet appareil
                </p>

                <NotificationStatus
                  state={state}
                />
              </div>
            </div>

            {enabled ? (
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
                <BellOff
                  size={15}
                />

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
                <Bell
                  size={15}
                />

                Activer
              </button>
            )}
          </div>
        </section>


        <section>
          <SectionTitle>
            Types de notifications
          </SectionTitle>

          <div
            className="
              divide-y
              divide-base-300
              overflow-hidden
              rounded-xl
              border
              border-base-300
            "
          >
            <FutureCategory
              title="Coaching et adaptations"
            />

            <div
              className="
                bg-base-100
                p-4
              "
            >
              <div
                className="
                  flex
                  items-center
                  justify-between
                  gap-4
                "
              >
                <div>
                  <p
                    className="
                      font-medium
                      text-base-content
                    "
                  >
                    Séances et rappels
                  </p>

                  <p
                    className="
                      mt-1
                      text-xs
                      text-base-content/50
                    "
                  >
                    Rappel de la séance du lendemain à 20 h.
                  </p>
                </div>

                <input
                  type="checkbox"
                  className="
                    toggle
                    toggle-success
                  "
                  disabled={!enabled}
                  checked={
                    preferences.trainingReminder
                  }
                  onChange={(event) => {
                    void savePreferences({
                      ...preferences,
                      trainingReminder:
                        event.target.checked,
                    })
                  }}
                />
              </div>
            </div>

            <FutureCategory
              title="Activités synchronisées"
            />

            <FutureCategory
              title="Check-in quotidien"
            />

            <FutureCategory
              title="Courses et objectifs"
            />

            <div
              className="
                bg-base-100
                p-4
              "
            >
              <div
                className="
                  flex
                  items-center
                  justify-between
                  gap-4
                "
              >
                <div>
                  <p
                    className="
                      font-medium
                      text-base-content
                    "
                  >
                    Système
                  </p>

                  <p
                    className="
                      mt-1
                      text-xs
                      text-base-content/50
                    "
                  >
                    Alertes techniques importantes.
                  </p>
                </div>

                <input
                  type="checkbox"
                  className="
                    toggle
                    toggle-success
                  "
                  disabled={!enabled}
                  checked={
                    preferences.systemEnabled
                  }
                  onChange={(event) => {
                    void savePreferences({
                      ...preferences,
                      systemEnabled:
                        event.target.checked,
                    })
                  }}
                />
              </div>

              {preferences.systemEnabled && (
                <div
                  className="
                    mt-4
                    space-y-3
                    border-t
                    border-base-300
                    pt-4
                  "
                >
                  <PreferenceToggle
                    title={
                      'Erreur de synchronisation'
                    }
                    checked={
                      preferences.syncErrors
                    }
                    disabled={!enabled}
                    onChange={(checked) => {
                      void savePreferences({
                        ...preferences,
                        syncErrors: checked,
                      })
                    }}
                  />

                  <PreferenceToggle
                    title={
                      'Erreur de sauvegarde'
                    }
                    checked={
                      preferences.backupErrors
                    }
                    disabled={!enabled}
                    onChange={(checked) => {
                      void savePreferences({
                        ...preferences,
                        backupErrors: checked,
                      })
                    }}
                  />
                </div>
              )}
            </div>
          </div>
        </section>


        <section>
          <SectionTitle>
            Appareils connectés
          </SectionTitle>

          {devices.length === 0 ? (
            <div
              className="
                rounded-xl
                border
                border-base-300
                p-4
                text-sm
                text-base-content/50
              "
            >
              Aucun appareil connecté.
            </div>
          ) : (
            <div
              className="
                divide-y
                divide-base-300
                overflow-hidden
                rounded-xl
                border
                border-base-300
              "
            >
              {devices.map(
                (device) => (
                  <DeviceRow
                    key={device.id}
                    device={device}
                  />
                ),
              )}
            </div>
          )}
        </section>
      </div>
    </ProfileSection>
  )
}


function SectionTitle({
  children,
}: {
  children: string
}) {
  return (
    <h3
      className="
        mb-3
        text-sm
        font-semibold
        uppercase
        tracking-wide
        text-base-content/50
      "
    >
      {children}
    </h3>
  )
}


function FutureCategory({
  title,
}: {
  title: string
}) {
  return (
    <div
      className="
        flex
        items-center
        justify-between
        gap-3
        bg-base-100
        p-4
      "
    >
      <div>
        <p
          className="
            font-medium
            text-base-content
          "
        >
          {title}
        </p>

        <p
          className="
            mt-1
            text-xs
            text-base-content/40
          "
        >
          Bientôt disponible
        </p>
      </div>

      <ChevronRight
        size={17}
        className="
          text-base-content/25
        "
      />
    </div>
  )
}


function PreferenceToggle({
  title,
  checked,
  disabled,
  onChange,
}: {
  title: string
  checked: boolean
  disabled: boolean
  onChange: (
    checked: boolean
  ) => void
}) {
  return (
    <label
      className="
        flex
        cursor-pointer
        items-center
        justify-between
        gap-3
      "
    >
      <span
        className="
          text-sm
          text-base-content/70
        "
      >
        {title}
      </span>

      <input
        type="checkbox"
        className="
          toggle
          toggle-sm
          toggle-success
        "
        checked={checked}
        disabled={disabled}
        onChange={(event) =>
          onChange(
            event.target.checked,
          )
        }
      />
    </label>
  )
}


function DeviceRow({
  device,
}: {
  device: PushDevice
}) {
  return (
    <div
      className="
        flex
        items-center
        gap-3
        bg-base-100
        p-4
      "
    >
      <div
        className="
          flex
          h-10
          w-10
          shrink-0
          items-center
          justify-center
          rounded-xl
          bg-base-200
          text-base-content/60
        "
      >
        <MonitorSmartphone
          size={18}
        />
      </div>

      <div
        className="
          min-w-0
          flex-1
        "
      >
        <div
          className="
            flex
            flex-wrap
            items-center
            gap-2
          "
        >
          <p
            className="
              font-medium
              text-base-content
            "
          >
            {device.device_name}
          </p>

          {device.current && (
            <span
              className="
                badge
                badge-success
                badge-sm
              "
            >
              Cet appareil
            </span>
          )}
        </div>

        <p
          className="
            mt-1
            text-xs
            text-base-content/45
          "
        >
          {device.browser}
          {' · '}
          connecté le{' '}
          {formatDate(
            device.created_at,
          )}
        </p>
      </div>
    </div>
  )
}


function formatDate(
  value: string,
): string {
  const date =
    new Date(
      value,
    )

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return 'date inconnue'
  }

  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    },
  ).format(
    date,
  )
}


function NotificationBadge({
  state,
}: {
  state: NotificationState
}) {
  if (state === 'enabled') {
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
    || state === 'disabled'
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

  return (
    <span
      className="
        badge
        badge-ghost
        badge-sm
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
  if (state === 'enabled') {
    return (
      <span
        className="
          mt-1
          flex
          items-center
          gap-1
          text-xs
          text-success
        "
      >
        <CheckCircle2
          size={13}
        />

        Notifications actives
      </span>
    )
  }

  if (state === 'denied') {
    return (
      <span
        className="
          mt-1
          flex
          items-center
          gap-1
          text-xs
          text-warning
        "
      >
        <CircleAlert
          size={13}
        />

        Bloquées par l’appareil
      </span>
    )
  }

  if (state === 'unsupported') {
    return (
      <span
        className="
          mt-1
          text-xs
          text-base-content/45
        "
      >
        Non disponibles
      </span>
    )
  }

  return (
    <span
      className="
        mt-1
        text-xs
        text-base-content/45
      "
    >
      Notifications désactivées
    </span>
  )
}
