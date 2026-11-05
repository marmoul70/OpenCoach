import {
  Activity,
  Bell,
  ChevronRight,
  Database,
  Link2,
  ListChecks,
  MapPin,
  type LucideIcon,
} from 'lucide-react'

import { PageHeader } from '../../design-system/components/PageHeader'
import {
  useState,
} from 'react'

import {
  useAthleteProfile,
} from '../../core/profile'

import {
  BackupSection,
} from './BackupSection'

import {
  NotificationsSection,
} from './NotificationsSection'

import {
  TasksSection,
} from './TasksSection'

import {
  LocationWidget,
} from './LocationWidget'

import {
  IntervalsSection,
} from './IntervalsSection'

import {
  CorosSection,
} from './CorosSection'


type SettingsPage =
  | 'location'
  | 'intervals'
  | 'coros'
  | 'notifications'
  | 'tasks'
  | 'backup'


interface SettingsNavigationItem {
  id: SettingsPage
  label: string
  shortLabel: string
  description: string
  group: string
  icon: LucideIcon
}


const SETTINGS_NAVIGATION:
SettingsNavigationItem[] = [
  {
    id: 'location',
    label: 'Localisation',
    shortLabel: 'Localisation',
    description:
      'Lieu utilisé pour la météo et le contexte.',
    group: 'Général',
    icon: MapPin,
  },
  {
    id: 'coros',
    label: 'COROS',
    shortLabel: 'COROS',
    description:
      'Connexion et import des données de la montre.',
    group: 'Connexions',
    icon: Activity,
  },
  {
    id: 'intervals',
    label: 'Intervals.icu',
    shortLabel: 'Intervals',
    description:
      'Connexion et synchronisation des données.',
    group: 'Connexions',
    icon: Link2,
  },
  {
    id: 'notifications',
    label: 'Notifications',
    shortLabel: 'Notifications',
    description:
      'Canaux et préférences de communication.',
    group: 'Automatisation',
    icon: Bell,
  },
  {
    id: 'tasks',
    label: 'Tâches',
    shortLabel: 'Tâches',
    description:
      'Actions automatiques exécutées par OpenCoach.',
    group: 'Automatisation',
    icon: ListChecks,
  },
  {
    id: 'backup',
    label: 'Données & sauvegarde',
    shortLabel: 'Données',
    description:
      'Sauvegardes, export et restauration.',
    group: 'Données',
    icon: Database,
  },
]


export function Settings() {
  const profile =
    useAthleteProfile()

  const [
    activePage,
    setActivePage,
  ] = useState<SettingsPage>(
    'location',
  )

  const activeItem =
    SETTINGS_NAVIGATION.find(
      item =>
        item.id === activePage,
    )
    ?? SETTINGS_NAVIGATION[0]


  return (
    <main
      className="
        oc-app-shell
        min-h-screen
      "
    >
      <div
        className="
          mx-auto
          max-w-[1380px]
          px-3
          py-4
          sm:px-5
          lg:px-5
          lg:py-[18px]
        "
      >

        {/* =================================================
            PAGE HEADER
            ================================================= */}

        <PageHeader eyebrow="Configuration" title="Réglages" description="Configure les services, automatisations et données OpenCoach." />


        {/* =================================================
            MOBILE NAVIGATION
            ================================================= */}

        <nav
          className="
            -mx-3
            mb-3
            overflow-x-auto
            px-3
            pb-1
            [scrollbar-width:none]
            [&::-webkit-scrollbar]:hidden
            lg:hidden
          "
          aria-label="
            Navigation des réglages
          "
        >
          <div
            className="
              flex
              w-max
              gap-1.5
            "
          >
            {SETTINGS_NAVIGATION.map(
              item => (
                <MobileNavigationButton
                  key={item.id}
                  item={item}
                  active={
                    item.id
                    === activePage
                  }
                  onClick={() =>
                    setActivePage(
                      item.id,
                    )
                  }
                />
              ),
            )}
          </div>
        </nav>


        {/* =================================================
            DESKTOP LAYOUT
            ================================================= */}

        <div
          className="
            grid
            gap-3
            lg:grid-cols-[220px_minmax(0,1fr)]
          "
        >

          {/* SIDEBAR */}

          <aside
            className="
              hidden
              self-start
              overflow-hidden
              rounded-[14px]
              border
              border-[var(--oc-border)]
              bg-[var(--oc-surface)]
              p-2
              shadow-[0_1px_2px_rgba(15,23,42,0.025)]
              dark:border-[var(--oc-border)]
              dark:bg-[var(--oc-surface)]
              lg:block
            "
          >
            <SettingsNavigation
              activePage={
                activePage
              }
              onChange={
                setActivePage
              }
            />
          </aside>


          {/* ACTIVE PANEL */}

          <section
            className="
              min-w-0
              overflow-hidden
              rounded-[14px]
              border
              border-[var(--oc-border)]
              bg-[var(--oc-surface)]
              shadow-[0_1px_2px_rgba(15,23,42,0.025)]
              dark:border-white/[0.075]
              dark:bg-[#151b1f]
            "
          >

            {/* PANEL HEADER */}

            <div
              className="
                border-b
                border-black/[0.06]
                px-4
                py-3.5
                dark:border-white/[0.065]
                sm:px-5
              "
            >
              <div
                className="
                  flex
                  items-start
                  gap-3
                "
              >
                <div
                  className="
                    flex
                    h-9
                    w-9
                    shrink-0
                    items-center
                    justify-center
                    rounded-[10px]
                    bg-emerald-50
                    text-emerald-600
                    dark:bg-emerald-500/[0.08]
                    dark:text-emerald-400
                  "
                >
                  <activeItem.icon
                    className="
                      h-4
                      w-4
                    "
                  />
                </div>

                <div>
                  <p
                    className="
                      oc-page-eyebrow
                    "
                  >
                    {activeItem.group}
                  </p>

                  <h2
                    className="
                      mt-0.5
                      oc-type-card-title
                    "
                  >
                    {activeItem.label}
                  </h2>

                  <p
                    className="
                      mt-1
                      oc-type-secondary
                    "
                  >
                    {
                      activeItem.description
                    }
                  </p>
                </div>
              </div>
            </div>


            {/* CONTENT */}

            <div
              className="
                settings-hub-content
                p-3
                sm:p-4
              "
            >
              {
                renderSettingsPage(
                  activePage,
                  profile.location,
                )
              }
            </div>
          </section>
        </div>
      </div>
    </main>
  )
}


function SettingsNavigation({
  activePage,
  onChange,
}: {
  activePage: SettingsPage

  onChange: (
    page: SettingsPage,
  ) => void
}) {
  let previousGroup:
    string | null = null

  return (
    <nav
      aria-label="
        Navigation des réglages
      "
    >
      {SETTINGS_NAVIGATION.map(
        item => {
          const Icon =
            item.icon

          const groupChanged =
            previousGroup
            !== item.group

          previousGroup =
            item.group

          return (
            <div
              key={item.id}
            >
              {groupChanged && (
                <p
                  className="
                    mb-1
                    mt-3
                    px-2
                    text-[8px]
                    font-bold
                    uppercase
                    tracking-[0.11em]
                    text-slate-300
                    first:mt-1
                    dark:text-slate-600
                  "
                >
                  {item.group}
                </p>
              )}

              <button
                type="button"
                onClick={() =>
                  onChange(
                    item.id,
                  )
                }
                className={[
                  (
                    'group flex w-full '
                    + 'items-center gap-2.5 '
                    + 'rounded-[9px] '
                    + 'px-2.5 py-2 '
                    + 'text-left transition'
                  ),
                  (
                    activePage
                    === item.id
                  )
                    ? (
                        'bg-emerald-50 '
                        + 'text-emerald-700 '
                        + 'dark:bg-emerald-500/[0.075] '
                        + 'dark:text-emerald-400'
                      )
                    : (
                        'text-slate-500 '
                        + 'hover:bg-slate-50 '
                        + 'hover:text-slate-900 '
                        + 'dark:text-slate-400 '
                        + 'dark:hover:bg-white/[0.035] '
                        + 'dark:hover:text-white'
                      ),
                ].join(' ')}
              >
                <Icon
                  className="
                    h-3.5
                    w-3.5
                    shrink-0
                  "
                />

                <span
                  className="
                    min-w-0
                    flex-1
                  "
                >
                  <span
                    className="
                      block
                      truncate
                      text-[10.5px]
                      font-semibold
                    "
                  >
                    {item.label}
                  </span>
                </span>

                <ChevronRight
                  className={[
                    (
                      'h-3 w-3 '
                      + 'shrink-0 '
                      + 'transition'
                    ),
                    (
                      activePage
                      === item.id
                    )
                      ? (
                          'text-emerald-500'
                        )
                      : (
                          'text-slate-200 '
                          + 'group-hover:text-slate-400 '
                          + 'dark:text-slate-700'
                        ),
                  ].join(' ')}
                />
              </button>
            </div>
          )
        },
      )}
    </nav>
  )
}


function MobileNavigationButton({
  item,
  active,
  onClick,
}: {
  item: SettingsNavigationItem
  active: boolean
  onClick: () => void
}) {
  const Icon =
    item.icon

  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      className={[
        (
          'flex h-9 items-center '
          + 'gap-1.5 whitespace-nowrap '
          + 'rounded-[9px] border '
          + 'px-2.5 '
          + 'text-[10px] '
          + 'font-semibold transition'
        ),
        active
          ? (
              'border-emerald-500/25 '
              + 'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/[0.08] '
              + 'dark:text-emerald-400'
            )
          : (
              'border-black/[0.06] '
              + 'bg-white '
              + 'text-slate-400 '
              + 'dark:border-white/[0.06] '
              + 'dark:bg-[#151b1f] '
              + 'dark:text-slate-500'
            ),
      ].join(' ')}
    >
      <Icon
        className="
          h-3.5
          w-3.5
        "
      />

      {item.shortLabel}
    </button>
  )
}


function renderSettingsPage(
  page: SettingsPage,
  location: {
    name?: string
    latitude?: number
    longitude?: number
  },
) {
  switch (page) {
    case 'coros':
      return (
        <CorosSection />
      )

    case 'intervals':
      return (
        <IntervalsSection />
      )

    case 'notifications':
      return (
        <NotificationsSection />
      )

    case 'tasks':
      return (
        <TasksSection />
      )

    case 'backup':
      return (
        <BackupSection />
      )

    default:
      return (
        <LocationWidget
          location={location}
        />
      )
  }
}
