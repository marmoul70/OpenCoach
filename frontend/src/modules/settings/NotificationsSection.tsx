import {
  Bell,
  BellOff,
  CalendarClock,
  CircleAlert,
  CloudCog,
  DatabaseBackup,
  LoaderCircle,
  MonitorSmartphone,
  ShieldCheck,
  Smartphone,
  Sparkles,
} from 'lucide-react'

import {
  useCallback,
  useEffect,
  useState,
  type ReactNode,
} from 'react'

import {
  useToast,
} from '../../components/ui/ToastProvider'

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


const DEFAULT_PREFERENCES:
PushPreferences = {
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
  ] = useState(false)

  const [
    endpoint,
    setEndpoint,
  ] = useState<
    string | null
  >(null)

  const [
    devices,
    setDevices,
  ] = useState<
    PushDevice[]
  >([])

  const [
    preferences,
    setPreferences,
  ] = useState<
    PushPreferences
  >(
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
            setEndpoint(null)
            setDevices([])
            setState('disabled')
            return
          }

          setEndpoint(
            subscription.endpoint,
          )

          setState('enabled')

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
          setState('disabled')
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
    setBusy(true)

    try {
      const permission =
        await Notification
          .requestPermission()

      if (
        permission !== 'granted'
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
      setBusy(false)
    }
  }


  async function disableNotifications() {
    setBusy(true)

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

        await subscription
          .unsubscribe()
      }

      setEndpoint(null)
      setDevices([])
      setState('disabled')

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
      setBusy(false)
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

    setPreferences(next)

    try {
      await updatePushPreferences(
        endpoint,
        next,
      )
    } catch (reason) {
      setPreferences(previous)

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

  const activeCount =
    countActivePreferences(
      preferences,
    )


  if (state === 'loading') {
    return (
      <div
        className="
          flex
          min-h-[200px]
          items-center
          justify-center
          rounded-[12px]
          border
          border-black/[0.065]
          bg-white
          dark:border-white/[0.065]
          dark:bg-[#151b1f]
        "
      >
        <div
          className="
            flex
            items-center
            gap-2
            text-[10.5px]
            text-slate-400
          "
        >
          <LoaderCircle
            className="
              h-4
              w-4
              animate-spin
              text-emerald-500
            "
          />

          Vérification des notifications…
        </div>
      </div>
    )
  }


  return (
    <div
      className="
        space-y-3
      "
    >

      {/* =================================================
          DEVICE CHANNEL
          ================================================= */}

      <section
        className="
          overflow-hidden
          rounded-[12px]
          border
          border-black/[0.065]
          bg-white
          dark:border-white/[0.065]
          dark:bg-[#151b1f]
        "
      >
        <div
          className="
            relative
            overflow-hidden
            px-4
            py-4
          "
        >
          <div
            className="
              pointer-events-none
              absolute
              -right-14
              -top-20
              h-44
              w-44
              rounded-full
              bg-emerald-500/[0.05]
              blur-3xl
            "
          />

          <div
            className="
              relative
              flex
              items-start
              justify-between
              gap-3
            "
          >
            <div
              className="
                flex
                min-w-0
                items-start
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
                  rounded-[11px]
                  bg-emerald-50
                  text-emerald-600
                  dark:bg-emerald-500/[0.08]
                  dark:text-emerald-400
                "
              >
                <Smartphone
                  className="
                    h-[18px]
                    w-[18px]
                  "
                />
              </div>

              <div>
                <div
                  className="
                    flex
                    flex-wrap
                    items-center
                    gap-2
                  "
                >
                  <h3
                    className="
                      text-[14px]
                      font-bold
                      tracking-[-0.02em]
                      text-slate-950
                      dark:text-white
                    "
                  >
                    Cet appareil
                  </h3>

                  <NotificationStatus
                    state={state}
                  />
                </div>

                <p
                  className="
                    mt-1
                    text-[10px]
                    text-slate-400
                    dark:text-slate-500
                  "
                >
                  Notifications Web / PWA
                  OpenCoach.
                </p>
              </div>
            </div>


            {enabled ? (
              <button
                type="button"
                disabled={busy}
                onClick={() =>
                  void disableNotifications()
                }
                className="
                  flex
                  h-8
                  shrink-0
                  items-center
                  gap-1.5
                  rounded-[8px]
                  border
                  border-red-500/20
                  px-2.5
                  text-[9.5px]
                  font-semibold
                  text-red-500
                  transition
                  hover:border-red-500/35
                  hover:bg-red-50
                  disabled:opacity-40
                  dark:hover:bg-red-500/[0.06]
                "
              >
                <BellOff
                  className="
                    h-3
                    w-3
                  "
                />

                Désactiver
              </button>
            ) : (
              <button
                type="button"
                disabled={
                  busy
                  || state === 'unsupported'
                  || state === 'denied'
                }
                onClick={() =>
                  void enableNotifications()
                }
                className="
                  flex
                  h-8
                  shrink-0
                  items-center
                  gap-1.5
                  rounded-[8px]
                  bg-emerald-600
                  px-3
                  text-[10px]
                  font-semibold
                  text-white
                  transition
                  hover:bg-emerald-700
                  disabled:cursor-not-allowed
                  disabled:bg-slate-200
                  disabled:text-slate-400
                  dark:disabled:bg-white/[0.05]
                  dark:disabled:text-slate-600
                "
              >
                <Bell
                  className="
                    h-3
                    w-3
                  "
                />

                Activer
              </button>
            )}
          </div>
        </div>


        <div
          className="
            grid
            grid-cols-2
            border-t
            border-black/[0.055]
            dark:border-white/[0.06]
          "
        >
          <SummaryMetric
            label="Appareils"
            value={
              String(
                devices.length,
              )
            }
          />

          <SummaryMetric
            label="Alertes actives"
            value={
              enabled
                ? String(
                    activeCount,
                  )
                : '0'
            }
          />
        </div>


        {state === 'denied' && (
          <StateMessage
            icon={
              <CircleAlert
                className="
                  h-3.5
                  w-3.5
                "
              />
            }
            tone="warning"
          >
            Les notifications sont
            bloquées dans les réglages
            de cet appareil.
          </StateMessage>
        )}

        {state === 'unsupported' && (
          <StateMessage
            icon={
              <CircleAlert
                className="
                  h-3.5
                  w-3.5
                "
              />
            }
            tone="neutral"
          >
            Les notifications Push ne
            sont pas disponibles sur
            cet appareil.
          </StateMessage>
        )}
      </section>


      {/* =================================================
          EVENTS
          ================================================= */}

      <section
        className="
          overflow-hidden
          rounded-[12px]
          border
          border-black/[0.065]
          bg-white
          dark:border-white/[0.065]
          dark:bg-[#151b1f]
        "
      >
        <div
          className="
            border-b
            border-black/[0.055]
            px-4
            py-3
            dark:border-white/[0.06]
          "
        >
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.1em]
              text-slate-400
              dark:text-slate-500
            "
          >
            Événements
          </p>

          <p
            className="
              mt-1
              text-[11.5px]
              font-semibold
              text-slate-800
              dark:text-slate-200
            "
          >
            Notifications automatiques
          </p>
        </div>


        <NotificationPreference
          icon={
            <CalendarClock
              className="
                h-4
                w-4
              "
            />
          }
          title="Séance du lendemain"
          description="
            Rappel de la séance prévue
            le lendemain à 20 h.
          "
          checked={
            preferences.trainingReminder
          }
          disabled={!enabled}
          onChange={checked =>
            void savePreferences({
              ...preferences,

              trainingReminder:
                checked,
            })
          }
        />


        <NotificationPreference
          icon={
            <ShieldCheck
              className="
                h-4
                w-4
              "
            />
          }
          title="Alertes système"
          description="
            Active les alertes techniques
            importantes d'OpenCoach.
          "
          checked={
            preferences.systemEnabled
          }
          disabled={!enabled}
          onChange={checked =>
            void savePreferences({
              ...preferences,

              systemEnabled:
                checked,
            })
          }
        />


        {preferences.systemEnabled && (
          <div
            className="
              border-t
              border-black/[0.055]
              bg-slate-50/50
              px-4
              py-2
              dark:border-white/[0.06]
              dark:bg-white/[0.015]
            "
          >
            <SubPreference
              icon={
                <CloudCog
                  className="
                    h-3.5
                    w-3.5
                  "
                />
              }
              title="
                Erreur de synchronisation
              "
              checked={
                preferences.syncErrors
              }
              disabled={!enabled}
              onChange={checked =>
                void savePreferences({
                  ...preferences,

                  syncErrors:
                    checked,
                })
              }
            />

            <SubPreference
              icon={
                <DatabaseBackup
                  className="
                    h-3.5
                    w-3.5
                  "
                />
              }
              title="
                Erreur de sauvegarde
              "
              checked={
                preferences.backupErrors
              }
              disabled={!enabled}
              onChange={checked =>
                void savePreferences({
                  ...preferences,

                  backupErrors:
                    checked,
                })
              }
            />
          </div>
        )}


        <FutureNotification
          icon={
            <Sparkles
              className="
                h-4
                w-4
              "
            />
          }
          title="Coaching et adaptations"
        />

        <FutureNotification
          icon={
            <MonitorSmartphone
              className="
                h-4
                w-4
              "
            />
          }
          title="Activités synchronisées"
        />
      </section>


      {/* =================================================
          DEVICES
          ================================================= */}

      <section
        className="
          overflow-hidden
          rounded-[12px]
          border
          border-black/[0.065]
          bg-white
          dark:border-white/[0.065]
          dark:bg-[#151b1f]
        "
      >
        <div
          className="
            border-b
            border-black/[0.055]
            px-4
            py-3
            dark:border-white/[0.06]
          "
        >
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.1em]
              text-slate-400
              dark:text-slate-500
            "
          >
            Appareils
          </p>

          <p
            className="
              mt-1
              text-[11.5px]
              font-semibold
              text-slate-800
              dark:text-slate-200
            "
          >
            Appareils connectés
          </p>
        </div>


        {devices.length === 0 ? (
          <div
            className="
              px-4
              py-5
              text-center
            "
          >
            <MonitorSmartphone
              className="
                mx-auto
                h-5
                w-5
                text-slate-200
                dark:text-slate-700
              "
            />

            <p
              className="
                mt-2
                text-[10px]
                text-slate-400
                dark:text-slate-500
              "
            >
              Aucun appareil connecté.
            </p>
          </div>
        ) : (
          <div>
            {devices.map(
              (device, index) => (
                <DeviceRow
                  key={device.id}
                  device={device}
                  divided={
                    index > 0
                  }
                />
              ),
            )}
          </div>
        )}
      </section>
    </div>
  )
}


function NotificationPreference({
  icon,
  title,
  description,
  checked,
  disabled,
  onChange,
}: {
  icon: ReactNode
  title: string
  description: string
  checked: boolean
  disabled: boolean

  onChange:
    (checked: boolean) => void
}) {
  return (
    <div
      className="
        flex
        items-center
        gap-3
        border-b
        border-black/[0.055]
        px-4
        py-3
        last:border-b-0
        dark:border-white/[0.06]
      "
    >
      <div
        className={[
          (
            'flex h-8 w-8 '
            + 'shrink-0 '
            + 'items-center '
            + 'justify-center '
            + 'rounded-[9px]'
          ),
          checked
            ? (
                'bg-emerald-50 '
                + 'text-emerald-600 '
                + 'dark:bg-emerald-500/[0.07] '
                + 'dark:text-emerald-400'
              )
            : (
                'bg-slate-50 '
                + 'text-slate-400 '
                + 'dark:bg-white/[0.025]'
              ),
        ].join(' ')}
      >
        {icon}
      </div>

      <div
        className="
          min-w-0
          flex-1
        "
      >
        <p
          className="
            text-[10.5px]
            font-semibold
            text-slate-700
            dark:text-slate-300
          "
        >
          {title}
        </p>

        <p
          className="
            mt-0.5
            text-[9px]
            leading-4
            text-slate-400
            dark:text-slate-500
          "
        >
          {description}
        </p>
      </div>

      <ModernToggle
        checked={checked}
        disabled={disabled}
        onChange={onChange}
      />
    </div>
  )
}


function SubPreference({
  icon,
  title,
  checked,
  disabled,
  onChange,
}: {
  icon: ReactNode
  title: string
  checked: boolean
  disabled: boolean

  onChange:
    (checked: boolean) => void
}) {
  return (
    <div
      className="
        flex
        min-h-9
        items-center
        gap-2
      "
    >
      <div
        className="
          text-slate-400
          dark:text-slate-500
        "
      >
        {icon}
      </div>

      <span
        className="
          flex-1
          text-[9.5px]
          font-medium
          text-slate-500
          dark:text-slate-400
        "
      >
        {title}
      </span>

      <ModernToggle
        checked={checked}
        disabled={disabled}
        small
        onChange={onChange}
      />
    </div>
  )
}


function FutureNotification({
  icon,
  title,
}: {
  icon: ReactNode
  title: string
}) {
  return (
    <div
      className="
        flex
        items-center
        gap-3
        border-t
        border-black/[0.055]
        px-4
        py-3
        opacity-55
        dark:border-white/[0.06]
      "
    >
      <div
        className="
          flex
          h-8
          w-8
          items-center
          justify-center
          rounded-[9px]
          bg-slate-50
          text-slate-400
          dark:bg-white/[0.025]
        "
      >
        {icon}
      </div>

      <div className="flex-1">
        <p
          className="
            text-[10px]
            font-semibold
            text-slate-500
            dark:text-slate-400
          "
        >
          {title}
        </p>

        <p
          className="
            mt-0.5
            text-[8.5px]
            text-slate-400
          "
        >
          Bientôt disponible
        </p>
      </div>
    </div>
  )
}


function ModernToggle({
  checked,
  disabled,
  small = false,
  onChange,
}: {
  checked: boolean
  disabled: boolean
  small?: boolean

  onChange:
    (checked: boolean) => void
}) {
  const width =
    small
      ? 'w-[36px]'
      : 'w-[42px]'

  const height =
    small
      ? 'h-[20px]'
      : 'h-[24px]'

  const knob =
    small
      ? 'h-[14px] w-[14px]'
      : 'h-[16px] w-[16px]'

  const translate =
    small
      ? 'translate-x-[16px]'
      : 'translate-x-[18px]'

  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      disabled={disabled}
      onClick={() =>
        onChange(!checked)
      }
      className={[
        (
          'relative inline-flex '
          + `${height} ${width} `
          + 'shrink-0 items-center '
          + 'rounded-full border '
          + 'transition-all duration-200 '
          + 'focus-visible:outline-none '
          + 'focus-visible:ring-2 '
          + 'focus-visible:ring-emerald-500/20 '
          + 'disabled:cursor-not-allowed '
          + 'disabled:opacity-35'
        ),
        checked
          ? (
              'border-emerald-600 '
              + 'bg-emerald-600'
            )
          : (
              'border-slate-200 '
              + 'bg-slate-100 '
              + 'dark:border-white/[0.08] '
              + 'dark:bg-white/[0.055]'
            ),
      ].join(' ')}
    >
      <span
        className={[
          (
            'absolute left-[3px] '
            + `${knob} `
            + 'rounded-full '
            + 'bg-white '
            + 'shadow-[0_1px_3px_rgba(15,23,42,0.20)] '
            + 'transition-transform '
            + 'duration-200'
          ),
          checked
            ? translate
            : 'translate-x-0',
        ].join(' ')}
      />
    </button>
  )
}


function DeviceRow({
  device,
  divided,
}: {
  device: PushDevice
  divided: boolean
}) {
  return (
    <div
      className={[
        (
          'flex items-center '
          + 'gap-3 px-4 py-3'
        ),
        divided
          ? (
              'border-t '
              + 'border-black/[0.055] '
              + 'dark:border-white/[0.06]'
            )
          : '',
      ].join(' ')}
    >
      <div
        className="
          flex
          h-8
          w-8
          shrink-0
          items-center
          justify-center
          rounded-[9px]
          bg-slate-50
          text-slate-400
          dark:bg-white/[0.025]
          dark:text-slate-500
        "
      >
        <MonitorSmartphone
          className="
            h-4
            w-4
          "
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
            items-center
            gap-1.5
          "
        >
          <p
            className="
              truncate
              text-[10.5px]
              font-semibold
              text-slate-700
              dark:text-slate-300
            "
          >
            {device.device_name}
          </p>

          {device.current && (
            <span
              className="
                inline-flex
                items-center
                gap-1
                rounded-full
                bg-emerald-50
                px-1.5
                py-0.5
                text-[8px]
                font-semibold
                text-emerald-700
                dark:bg-emerald-500/[0.08]
                dark:text-emerald-400
              "
            >
              <span
                className="
                  h-1
                  w-1
                  rounded-full
                  bg-emerald-500
                "
              />

              Cet appareil
            </span>
          )}
        </div>

        <p
          className="
            mt-0.5
            text-[9px]
            text-slate-400
            dark:text-slate-500
          "
        >
          {device.browser}
          {' · '}
          {
            formatDate(
              device.created_at,
            )
          }
        </p>
      </div>
    </div>
  )
}


function SummaryMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        px-4
        py-3
        first:border-r
        first:border-black/[0.055]
        dark:first:border-white/[0.06]
      "
    >
      <p
        className="
          text-[8.5px]
          font-semibold
          uppercase
          tracking-[0.08em]
          text-slate-400
          dark:text-slate-500
        "
      >
        {label}
      </p>

      <p
        className="
          mt-1
          text-[13px]
          font-bold
          tabular-nums
          text-slate-800
          dark:text-slate-200
        "
      >
        {value}
      </p>
    </div>
  )
}


function NotificationStatus({
  state,
}: {
  state: NotificationState
}) {
  const enabled =
    state === 'enabled'

  return (
    <span
      className={[
        (
          'inline-flex items-center '
          + 'gap-1 rounded-full '
          + 'px-1.5 py-0.5 '
          + 'text-[8px] '
          + 'font-semibold'
        ),
        enabled
          ? (
              'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/[0.08] '
              + 'dark:text-emerald-400'
            )
          : (
              'bg-slate-100 '
              + 'text-slate-400 '
              + 'dark:bg-white/[0.04] '
              + 'dark:text-slate-500'
            ),
      ].join(' ')}
    >
      <span
        className={[
          (
            'h-1.5 w-1.5 '
            + 'rounded-full'
          ),
          enabled
            ? 'bg-emerald-500'
            : 'bg-slate-300',
        ].join(' ')}
      />

      {
        enabled
          ? 'Activées'
          : state === 'denied'
            ? 'Bloquées'
            : state === 'unsupported'
              ? 'Indisponibles'
              : 'Désactivées'
      }
    </span>
  )
}


function StateMessage({
  icon,
  children,
  tone,
}: {
  icon: ReactNode
  children: ReactNode
  tone:
    | 'warning'
    | 'neutral'
}) {
  return (
    <div
      className={[
        (
          'flex items-start gap-2 '
          + 'border-t px-4 py-2.5 '
          + 'text-[9.5px]'
        ),
        tone === 'warning'
          ? (
              'border-amber-500/10 '
              + 'bg-amber-50/60 '
              + 'text-amber-700 '
              + 'dark:bg-amber-500/[0.05] '
              + 'dark:text-amber-400'
            )
          : (
              'border-black/[0.055] '
              + 'bg-slate-50 '
              + 'text-slate-400 '
              + 'dark:border-white/[0.06] '
              + 'dark:bg-white/[0.018]'
            ),
      ].join(' ')}
    >
      {icon}
      {children}
    </div>
  )
}


function countActivePreferences(
  preferences: PushPreferences,
): number {
  let count = 0

  if (
    preferences.trainingReminder
  ) {
    count += 1
  }

  if (
    preferences.systemEnabled
  ) {
    count += 1

    if (preferences.syncErrors) {
      count += 1
    }

    if (preferences.backupErrors) {
      count += 1
    }
  }

  return count
}


function formatDate(
  value: string,
): string {
  const date =
    new Date(value)

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
  ).format(date)
}
