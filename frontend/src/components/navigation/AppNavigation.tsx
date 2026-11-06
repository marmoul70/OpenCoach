import {
  SidePanel,
} from '../ui/SidePanel'

import {
  NotificationBell,
} from './NotificationBell'

import {
  Activity,
  Bot,
  CalendarDays,
  ChevronRight,
  CloudSun,
  CircleUserRound,
  Flag,
  Gauge,
  Home,
  HeartPulse,
  LogOut,
  Monitor,
  Moon,
  Settings,
  Sun,
  UserRound,
} from 'lucide-react'

import {
  useState,
} from 'react'


export type NavigationPage =
  | 'dashboard'
  | 'coach'
  | 'training'
  | 'feeling'
  | 'profile-personal'
  | 'profile-sport'
  | 'settings'
  | 'races'
  | 'activities'
  | 'weather'
  | 'health'
  | 'notifications'


export type NavigationTheme =
  | 'light'
  | 'dark'
  | 'system'


interface AppNavigationProps {
  activePage: NavigationPage

  firstName: string
  lastName: string
  avatar?: string

  theme: NavigationTheme

  version?: string
  commit?: string

  onNavigate: (
    page: NavigationPage,
  ) => void

  onThemeChange: (
    theme: NavigationTheme,
  ) => void

  onLogout: () => void
}


const mainNavigation = [
  {
    page: 'dashboard',
    label: 'Aujourd’hui',
    icon: Home,
  },
  {
    page: 'training',
    label: 'Planning',
    icon: CalendarDays,
  },
  {
    page: 'coach',
    label: 'Coach',
    icon: Bot,
  },
  {
    page: 'health',
    label: 'Santé',
    icon: HeartPulse,
  },
  {
    page: 'activities',
    label: 'Activités',
    icon: Activity,
  },
  {
    page: 'races',
    label: 'Courses',
    icon: Flag,
  },
  {
    page: 'weather',
    label: 'Météo',
    icon: CloudSun,
  },
] as const


const mobileNavigation = [
  {
    page: 'dashboard',
    label: 'Accueil',
    icon: Home,
  },
  {
    page: 'training',
    label: 'Planning',
    icon: CalendarDays,
  },
  {
    page: 'coach',
    label: 'Coach',
    icon: Bot,
  },
  {
    page: 'activities',
    label: 'Activités',
    icon: Activity,
  },
  {
    page: 'health',
    label: 'Santé',
    icon: HeartPulse,
  },
] as const


export function AppNavigation({
  activePage,
  firstName,
  lastName,
  avatar,
  theme,
  version,
  commit,
  onNavigate,
  onThemeChange,
  onLogout,
}: AppNavigationProps) {
  const [
    mobileMenuOpen,
    setMobileMenuOpen,
  ] = useState(false)

  const [

    desktopProfileOpen,

    setDesktopProfileOpen,

  ] = useState(false)


  const initials =
    getInitials(
      firstName,
      lastName,
    )


  function navigate(
    page: NavigationPage,
  ) {
    onNavigate(page)
    
            setDesktopProfileOpen(false)
            setMobileMenuOpen(false)

    window.scrollTo({
      top: 0,
      left: 0,
      behavior: 'auto',
    })
  }


  return (
    <>
      {/* ================================================
          Desktop sidebar
         ================================================ */}

      <aside
        className="
          fixed
          inset-y-0
          left-0
          z-50
          hidden
          w-56
          flex-col
          border-r
          border-[var(--oc-border)]
          bg-[var(--oc-surface)]
          lg:flex
          dark:border-[var(--oc-border)]
          dark:bg-[var(--oc-surface)]
        "
      >
        <div
          className="
            flex
            h-20
            items-center
            px-6
          "
        >
          <button
            type="button"
            onClick={() =>
              navigate(
                'dashboard',
              )
            }
            className="
              flex
              items-center
              gap-3
              text-left
            "
          >
            <img
                      src="/opencoach-logo.png"
                      alt="OpenCoach"
                      className="
                        h-10
                        w-10
                        shrink-0
                        object-contain
                      "
                    />

            <div>
              <p
                className="
                  text-lg
                  font-bold
                  tracking-[-0.035em]
                  text-[var(--oc-text)]
                "
              >
                OpenCoach
              </p>

              <p
                className="
                  -mt-0.5
                  text-[10px]
                  font-semibold
                  uppercase
                  tracking-[0.16em]
                  text-[var(--oc-accent)]
                "
              >
                Performance
              </p>
            </div>
          </button>
        </div>


        <nav
          className="
            flex-1
            px-3
            py-4
          "
          aria-label="Navigation principale"
        >
          <p
            className="
              mb-2
              px-3
              oc-type-label font-semibold uppercase tracking-[0.16em]
            "
          >
            Planning
          </p>

          <div className="space-y-1">
            {mainNavigation.map(
              ({
                page,
                label,
                icon: Icon,
              }) => (
                <DesktopNavigationItem
                  key={page}
                  active={
                    activePage
                    === page
                  }
                  label={label}
                  icon={
                    <Icon
                      className="h-[18px] w-[18px]"
                    />
                  }
                  onClick={() =>
                    navigate(page)
                  }
                />
              ),
            )}
          </div>


          <p
            className="
              mb-2
              mt-7
              px-3
              text-[10px]
              font-semibold
              uppercase
              tracking-[0.16em]
              text-[var(--oc-muted)]
              dark:text-[var(--oc-muted-soft)]
            "
          >
            Suivi
          </p>

          <div className="space-y-1">
            <DesktopNavigationItem
              active={
                activePage
                === 'feeling'
              }
              label="Ressenti"
              icon={
                <Gauge
                  className="h-[18px] w-[18px]"
                />
              }
              onClick={() =>
                navigate(
                  'feeling',
                )
              }
            />

            <DesktopNavigationItem
              active={
                activePage
                === 'profile-sport'
              }
              label="Profil sportif"
              icon={
                <CircleUserRound
                  className="h-[18px] w-[18px]"
                />
              }
              onClick={() =>
                navigate(
                  'profile-sport',
                )
              }
            />
          </div>
        </nav>


        {/* Desktop profile trigger */}
        <div className="
          border-t border-[var(--oc-border)]
          px-3 py-2.5 dark:border-[var(--oc-border)]
        ">
          <button
            type="button"
            onClick={() => setDesktopProfileOpen(true)}
            aria-haspopup="dialog"
            aria-expanded={desktopProfileOpen}
            className="
              flex w-full min-w-0 items-center gap-2.5
              rounded-xl px-1.5 py-2 text-left
              transition-colors hover:bg-[var(--oc-surface-hover)]
              dark:hover:bg-[var(--oc-surface)]/[0.06]
            "
          >
            <Avatar avatar={avatar} initials={initials} size="small" />
            <span className="min-w-0 flex-1">
              <span className="
                block truncate text-[11.5px] font-semibold
                leading-4 text-[var(--oc-text)]
              ">
                {formatName(firstName, lastName)}
              </span>
              <span className="
                mt-0.5 block truncate text-[9px] leading-3
                text-[var(--oc-muted)]
              ">
                Profil athlète
              </span>
            </span>
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[var(--oc-muted-soft)]" />
          </button>
        </div>

              </aside>


      {/* Desktop account and notifications in the shared SidePanel */}
      <SidePanel
        open={desktopProfileOpen}
        eyebrow="Mon espace"
        title="Compte et notifications"
        onClose={() => setDesktopProfileOpen(false)}
      >
        <div className="flex min-h-full flex-col gap-4">
          {/* Notifications stay at the top */}
          <section className="shrink-0">
            <NotificationBell
              embedded
              onViewAll={() => navigate('notifications')}
            />
          </section>

          {/* Account actions are anchored to the bottom */}
          <div className="mt-auto space-y-4 border-t border-[var(--oc-border)] pt-4">
            <section className="flex items-center gap-3 px-1">
              <Avatar avatar={avatar} initials={initials} />
              <div className="min-w-0 flex-1">
                <p className="truncate text-[13px] font-semibold text-[var(--oc-text)]">
                  {formatName(firstName, lastName)}
                </p>
                <p className="mt-0.5 text-[10px] text-[var(--oc-muted)]">
                  Profil athlète
                </p>
              </div>
            </section>

            <section>
              <DropdownLabel>Mon compte</DropdownLabel>
              <div className="mt-1 space-y-0.5">
                <DropdownItem
                  icon={<UserRound className="h-4 w-4" />}
                  label="Profil personnel"
                  active={activePage === 'profile-personal'}
                  onClick={() => navigate('profile-personal')}
                />
                <DropdownItem
                  icon={<CircleUserRound className="h-4 w-4" />}
                  label="Profil sportif"
                  active={activePage === 'profile-sport'}
                  onClick={() => navigate('profile-sport')}
                />
                <DropdownItem
                  icon={<Settings className="h-4 w-4" />}
                  label="Réglages"
                  active={activePage === 'settings'}
                  onClick={() => navigate('settings')}
                />
              </div>
            </section>

            <section>
              <div className="mb-2 flex items-center justify-between">
                <DropdownLabel>Apparence</DropdownLabel>
                <span className="text-[9px] text-[var(--oc-muted)]">
                  {theme === 'system' ? 'Automatique' : theme === 'light' ? 'Clair' : 'Sombre'}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2">
                <DropdownThemeButton
                  active={theme === 'light'}
                  icon={<Sun className="h-4 w-4" />}
                  label="Clair"
                  onClick={() => onThemeChange('light')}
                />
                <DropdownThemeButton
                  active={theme === 'dark'}
                  icon={<Moon className="h-4 w-4" />}
                  label="Sombre"
                  onClick={() => onThemeChange('dark')}
                />
                <DropdownThemeButton
                  active={theme === 'system'}
                  icon={<Monitor className="h-4 w-4" />}
                  label="Auto"
                  onClick={() => onThemeChange('system')}
                />
              </div>
            </section>

            <section className="
              flex items-center justify-between gap-3
              border-t border-[var(--oc-border)] pt-3
            ">
              <button
                type="button"
                onClick={() => {
                  setDesktopProfileOpen(false)
                  onLogout()
                }}
                className="
                  inline-flex items-center gap-2 rounded-lg px-2 py-2
                  text-[11px] font-medium text-rose-600
                  transition-colors hover:bg-rose-500/[0.07]
                  dark:text-rose-400
                "
              >
                <LogOut className="h-4 w-4" />
                Se déconnecter
              </button>
              <span className="text-right text-[8px] text-[var(--oc-muted-soft)]">
                {version ? `v${version}` : 'dev'}
                {commit ? ` · ${commit}` : ''}
              </span>
            </section>
          </div>
        </div>
      </SidePanel>

      {/* ================================================
          Mobile top bar
         ================================================ */}

      <header
        className="
          sticky
          top-0
          z-40
          flex
          h-[calc(4rem+env(safe-area-inset-top))]
          items-center
          justify-between
          pt-[env(safe-area-inset-top)]
          border-b
          border-[var(--oc-border)]
          bg-[color-mix(in_srgb,var(--oc-surface)_90%,transparent)]
          px-4
          backdrop-blur-xl
          lg:hidden
          dark:border-[var(--oc-border)]
          dark:bg-[color-mix(in_srgb,var(--oc-surface)_90%,transparent)]
        "
      >
        <button
          type="button"
          onClick={() =>
            navigate(
              'dashboard',
            )
          }
          className="
            flex
            items-center
            gap-2.5
          "
        >
          <img
            src="/opencoach-logo.png"
            alt="OpenCoach"
            className="
              h-8
              w-8
              shrink-0
              object-contain
            "
          />

          <span
            className="
              text-lg
              font-bold
              tracking-[-0.035em]
              text-[var(--oc-text)]
              dark:text-white
            "
          >
            OpenCoach
          </span>
        </button>



        <button
          type="button"
          onClick={() =>
            setMobileMenuOpen(
              true,
            )
          }
          className="
            flex
            h-10
            w-10
            items-center
            justify-center
            rounded-full
            transition
            hover:bg-[var(--oc-surface-hover)]
            dark:hover:bg-[var(--oc-surface)]/[0.06]
          "
          aria-label="Ouvrir le menu"
        >
          <Avatar
            avatar={avatar}
            initials={initials}
            size="small"
          />
        </button>
      </header>


      {/* ================================================
          Mobile bottom navigation
         ================================================ */}

      <nav
        className="
          pointer-events-none
          fixed
          inset-x-0
          bottom-0
          z-50
          lg:hidden
        "
        aria-label="Navigation mobile"
      >
        <div
          className="
            relative
            mx-auto
            h-[88px]
            max-w-lg
          "
        >
          <div
            className="
              pointer-events-auto
              absolute
              bottom-[calc(8px+env(safe-area-inset-bottom))]
              left-3
              right-3

              grid
              h-[68px]
              grid-cols-5

              rounded-[22px]

              border
              border-[var(--oc-border)]

              bg-[color-mix(in_srgb,var(--oc-surface)_95%,transparent)]

              px-1

              shadow-[0_10px_30px_rgba(15,23,42,0.14)]

              backdrop-blur-xl

              dark:border-[var(--oc-border)]
              dark:bg-[color-mix(in_srgb,var(--oc-surface)_95%,transparent)]
              dark:shadow-[0_12px_34px_rgba(0,0,0,0.38)]
            "
          >
            {mobileNavigation.map(
              ({
                page,
                label,
                icon: Icon,
              }) => (
                <MobileNavigationItem
                  key={page}
                  active={
                    activePage === page
                  }
                  label={label}
                  icon={
                    <Icon
                      className="h-5 w-5"
                    />
                  }
                  onClick={() =>
                    navigate(page)
                  }
                />
              ),
            )}

          </div>
        </div>
      </nav>


      {/* ================================================
          Mobile account navigation
         ================================================ */}

      <SidePanel
        open={mobileMenuOpen}
        eyebrow="Mon espace"
        title="Compte et notifications"
        onClose={() =>
          setMobileMenuOpen(false)
        }
      >
        <div className="space-y-5">

          <section
            className="
              flex
              items-center
              gap-3
              rounded-2xl
              border
              border-[var(--oc-border)]
              bg-[var(--oc-surface)]
              p-3
              shadow-sm
              dark:border-[var(--oc-border)]
              dark:bg-[var(--oc-surface)]/[0.03]
            "
          >
            <Avatar
              avatar={avatar}
              initials={initials}
            />

            <div className="min-w-0">
              <p
                className="
                  truncate
                  text-[13px]
                  font-semibold
                  text-[var(--oc-text)]
                  dark:text-[var(--oc-text)]
                "
              >
                {formatName(
                  firstName,
                  lastName,
                )}
              </p>

              <p
                className="
                  mt-0.5
                  text-[10px]
                  text-[var(--oc-muted)]
                "
              >
                Athlète OpenCoach
              </p>
            </div>
          </section>

          <section>
            <NotificationBell
              embedded
              onViewAll={() => navigate('notifications')}
            />
          </section>


          <section>
            <p
              className="
                mb-2
                px-1
                oc-type-label font-bold uppercase tracking-[0.12em]
              "
            >
              Mon suivi
            </p>

            <div
              className="
                overflow-hidden
                rounded-2xl
                border
                border-[var(--oc-border)]
                bg-[var(--oc-surface)]
                dark:border-[var(--oc-border)]
                dark:bg-[var(--oc-surface)]/[0.025]
              "
            >
              <MobileDrawerItem
                icon={<Gauge />}
                title="Ressenti"
                description="État du jour"
                onClick={() =>
                  navigate('feeling')
                }
              />

              <MobileDrawerItem
                icon={<CloudSun />}
                title="Météo"
                description="Conditions et prévisions"
                divider
                onClick={() =>
                  navigate('weather')
                }
              />

              <MobileDrawerItem
                icon={<Flag />}
                title="Courses"
                description="Objectifs et calendrier des courses"
                divider
                onClick={() =>
                  navigate('races')
                }
              />

            </div>
          </section>


          <section>
            <p
              className="
                mb-2
                px-1
                oc-type-label font-bold uppercase tracking-[0.12em]
              "
            >
              Mon profil
            </p>

            <div
              className="
                overflow-hidden
                rounded-2xl
                border
                border-[var(--oc-border)]
                bg-[var(--oc-surface)]
                dark:border-[var(--oc-border)]
                dark:bg-[var(--oc-surface)]/[0.025]
              "
            >
              <MobileDrawerItem
                icon={<UserRound />}
                title="Profil personnel"
                description="Identité et informations"
                onClick={() =>
                  navigate('profile-personal')
                }
              />

              <MobileDrawerItem
                icon={<CircleUserRound />}
                title="Profil sportif"
                description="Zones et physiologie"
                divider
                onClick={() =>
                  navigate('profile-sport')
                }
              />
            </div>
          </section>


          <section>
            <p
              className="
                mb-2
                px-1
                oc-type-label font-bold uppercase tracking-[0.12em]
              "
            >
              OpenCoach
            </p>

            <div
              className="
                overflow-hidden
                rounded-2xl
                border
                border-[var(--oc-border)]
                bg-[var(--oc-surface)]
                dark:border-[var(--oc-border)]
                dark:bg-[var(--oc-surface)]/[0.025]
              "
            >
              <MobileDrawerItem
                icon={<Settings />}
                title="Réglages"
                description="Configuration OpenCoach"
                onClick={() =>
                  navigate('settings')
                }
              />
            </div>
          </section>


          <section
            className="
              rounded-2xl
              border
              border-[var(--oc-border)]
              bg-[var(--oc-surface)]
              p-3
              dark:border-[var(--oc-border)]
              dark:bg-[var(--oc-surface)]/[0.025]
            "
          >
            <p
              className="
                oc-type-label font-bold uppercase tracking-[0.12em]
              "
            >
              Apparence
            </p>

            <div
              className="
                mt-3
                grid
                grid-cols-3
                gap-2
              "
            >
              <ThemeButton
                active={
                  theme === 'light'
                }
                icon={
                  <Sun className="h-4 w-4" />
                }
                label="Clair"
                onClick={() =>
                  onThemeChange('light')
                }
              />

              <ThemeButton
                active={
                  theme === 'dark'
                }
                icon={
                  <Moon className="h-4 w-4" />
                }
                label="Sombre"
                onClick={() =>
                  onThemeChange('dark')
                }
              />

              <ThemeButton
                active={
                  theme === 'system'
                }
                icon={
                  <Monitor className="h-4 w-4" />
                }
                label="Système"
                onClick={() =>
                  onThemeChange('system')
                }
              />
            </div>
          </section>


          <button
            type="button"
            onClick={onLogout}
            className="
              flex
              w-full
              items-center
              justify-center
              gap-2
              rounded-xl
              px-4
              py-3
              text-[11px]
              font-semibold
              text-red-500
              transition
              hover:bg-red-50
              dark:text-red-400
              dark:hover:bg-red-500/10
            "
          >
            <LogOut className="h-4 w-4" />

            Se déconnecter
          </button>


          <div
            className="
              pb-2
              text-center
              text-[9px]
              text-[var(--oc-muted-soft)]
              dark:text-[var(--oc-muted-soft)]
            "
          >
            {version
              ? `OpenCoach v${version}`
              : 'OpenCoach développement'}

            {commit
              ? ` · ${commit}`
              : ''}
          </div>
        </div>
      </SidePanel>

    </>
  )
}




        function DropdownLabel({
          children,
        }: {
          children: React.ReactNode
        }) {
          return (
            <p
              className="
                px-2
                pb-0.5
                pt-1
                text-[7.5px]
                font-semibold
                uppercase
                tracking-[0.14em]
                text-[var(--oc-muted)]
                dark:text-[var(--oc-muted-soft)]
              "
            >
              {children}
            </p>
          )
        }



        function DropdownItem({
          icon,
          label,
          active = false,
          danger = false,
          onClick,
        }: {
          icon: React.ReactNode
          label: string
          active?: boolean
          danger?: boolean
          onClick: () => void
        }) {
          return (
            <button
              type="button"
              role="menuitem"
              onClick={onClick}
              className={[
                (
                  'flex w-full items-center '
                  + 'gap-2 rounded-[9px] '
                  + 'px-2 py-[6px] '
                  + 'text-[7.5px] '
                  + 'font-medium transition-colors'
                ),
                danger
                  ? (
                      'text-red-500 '
                      + 'hover:bg-red-50 '
                      + 'dark:text-red-400 '
                      + 'dark:hover:bg-red-500/10'
                    )
                  : active
                    ? (
                        'bg-emerald-50 '
                        + 'text-emerald-700 '
                        + 'dark:bg-emerald-500/10 '
                        + 'dark:text-emerald-400'
                      )
                    : (
                        'text-[var(--oc-text-secondary)] '
                        + 'hover:bg-[var(--oc-surface-hover)] '
                        + 'hover:text-[var(--oc-text)] '
                        + 'dark:text-[var(--oc-text-secondary)] '
                        + 'dark:hover:bg-[var(--oc-surface)]/[0.045] '
                        + 'dark:hover:text-white'
                      ),
              ].join(' ')}
            >
              <span
                className={[
                  'shrink-0',
                  danger
                    ? 'text-red-400'
                    : active
                      ? (
                          'text-emerald-600 '
                          + 'dark:text-emerald-400'
                        )
                      : 'text-[var(--oc-muted)]',
                ].join(' ')}
              >
                {icon}
              </span>

              <span className="flex-1 text-left">
                {label}
              </span>
            </button>
          )
        }


        function DropdownThemeButton({
          active,
          icon,
          label,
          onClick,
        }: {
          active: boolean
          icon: React.ReactNode
          label: string
          onClick: () => void
        }) {
          return (
            <button
              type="button"
              onClick={onClick}
              className={[
                (
                  'flex flex-col '
                  + 'items-center '
                  + 'justify-center '
                  + 'gap-1 rounded-[9px] '
                  + 'border px-1 py-[6px] '
                  + 'text-[7.5px] '
                  + 'font-semibold '
                  + 'transition-colors'
                ),
                active
                  ? (
                      'border-emerald-500/20 '
                      + 'bg-emerald-50 '
                      + 'text-emerald-700 '
                      + 'dark:bg-emerald-500/10 '
                      + 'dark:text-emerald-400'
                    )
                  : (
                      'border-[var(--oc-border)] '
                      + 'bg-[var(--oc-surface)] '
                      + 'text-[var(--oc-muted)] '
                      + 'hover:bg-[var(--oc-surface-hover)] '
                      + 'dark:border-[var(--oc-border)] '
                      + 'dark:bg-[var(--oc-surface)]/[0.025] '
                      + 'dark:hover:bg-[var(--oc-surface)]/[0.05]'
                    ),
              ].join(' ')}
            >
              {icon}

              {label}
            </button>
          )
        }


        function DesktopNavigationItem({
  active,
  label,
  icon,
  onClick,
}: {
  active: boolean
  label: string
  icon: React.ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        (
          'flex w-full items-center '
          + 'gap-3 rounded-xl '
          + 'px-3 py-2 '
          + 'text-[0.82rem] font-medium '
          + 'transition-colors'
        ),
        active
          ? (
              'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/10 '
              + 'dark:text-emerald-400'
            )
          : (
              'text-[var(--oc-muted)] '
              + 'hover:bg-[var(--oc-surface-hover)] '
              + 'hover:text-[var(--oc-text)] '
              + 'dark:text-[var(--oc-muted)] '
              + 'dark:hover:bg-[var(--oc-surface)]/[0.045] '
              + 'dark:hover:text-[var(--oc-text)]'
            ),
      ].join(' ')}
    >
      <span
        className={
          active
            ? (
                'text-emerald-600 '
                + 'dark:text-emerald-400'
              )
            : 'text-[var(--oc-muted)]'
        }
      >
        {icon}
      </span>

      {label}
    </button>
  )
}


function MobileNavigationItem({
  active,
  label,
  icon,
  onClick,
}: {
  active: boolean
  label: string
  icon: React.ReactNode
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        (
          'relative '
          + 'flex h-full '
          + 'flex-col '
          + 'items-center '
          + 'justify-center '
          + 'gap-[5px] '
          + 'text-[9px] '
          + 'font-medium '
          + 'transition-colors'
        ),
        active
          ? (
              'text-emerald-600 '
              + 'dark:text-emerald-400'
            )
          : (
              'text-[var(--oc-muted)] '
              + 'dark:text-[var(--oc-muted)]'
            ),
      ].join(' ')}
    >
      <span
        className="
          [&>svg]:h-[19px]
          [&>svg]:w-[19px]
        "
      >
        {icon}
      </span>

      <span className="leading-none">
        {label}
      </span>

      {active && (
        <span
          aria-hidden="true"
          className="
            absolute
            bottom-[3px]
            h-[4px]
            w-[4px]
            rounded-full
            bg-emerald-500
          "
        />
      )}
    </button>
  )
}


function MobileDrawerItem({
  icon,
  title,
  description,
  divider = false,
  onClick,
}: {
  icon: React.ReactNode
  title: string
  description: string
  divider?: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        (
          'flex w-full items-center '
          + 'gap-3 px-3 py-3 '
          + 'text-left transition '
          + 'hover:bg-[var(--oc-surface-hover)] '
          + 'dark:hover:bg-[var(--oc-surface)]/[0.04]'
        ),
        divider
          ? (
              'border-t '
              + 'border-[var(--oc-border)] '
              + 'dark:border-[var(--oc-border)]'
            )
          : '',
      ].join(' ')}
    >
      <span
        className="
          flex
          h-9
          w-9
          shrink-0
          items-center
          justify-center
          rounded-xl
          bg-emerald-50
          text-emerald-600
          dark:bg-emerald-500/10
          dark:text-emerald-400
          [&>svg]:h-[17px]
          [&>svg]:w-[17px]
        "
      >
        {icon}
      </span>

      <span className="min-w-0 flex-1">
        <span
          className="
            block
            text-[11.5px]
            font-semibold
            text-[var(--oc-text)]
            dark:text-[var(--oc-text)]
          "
        >
          {title}
        </span>

        <span
          className="
            mt-0.5
            block
            text-[9px]
            text-[var(--oc-muted)]
            dark:text-[var(--oc-muted)]
          "
        >
          {description}
        </span>
      </span>

      <span
        className="
          text-lg
          leading-none
          text-[var(--oc-muted-soft)]
          dark:text-[var(--oc-muted-soft)]
        "
      >
        ›
      </span>
    </button>
  )
}


function ThemeButton({
  active,
  icon,
  label,
  onClick,
}: {
  active: boolean
  icon: React.ReactNode
  label: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        (
          'flex items-center '
          + 'justify-center gap-1.5 '
          + 'rounded-xl border '
          + 'px-2 py-2 '
          + 'text-xs font-semibold '
          + 'transition'
        ),
        active
          ? (
              'border-emerald-500/25 '
              + 'bg-emerald-50 '
              + 'text-emerald-700 '
              + 'dark:bg-emerald-500/10 '
              + 'dark:text-emerald-400'
            )
          : (
              'border-[var(--oc-border)] '
              + 'bg-[var(--oc-surface)] '
              + 'text-[var(--oc-muted)] '
              + 'dark:border-[var(--oc-border)] '
              + 'dark:bg-[var(--oc-surface)]/[0.03] '
              + 'dark:text-[var(--oc-muted)]'
            ),
      ].join(' ')}
    >
      {icon}
      {label}
    </button>
  )
}




function Avatar({
  avatar,
  initials,
  size = 'normal',
}: {
  avatar?: string
  initials: string
  size?: 'small' | 'normal'
}) {
  const sizeClass =
    size === 'small'
      ? 'h-8 w-8 text-[10px]'
      : 'h-11 w-11 text-xs'

  if (avatar) {
    return (
      <img
        src={avatar}
        alt=""
        className={
          `${sizeClass} rounded-full object-cover`
        }
      />
    )
  }

  return (
    <div
      className={[
        sizeClass,
        (
          'flex shrink-0 '
          + 'items-center justify-center '
          + 'rounded-full '
          + 'bg-[var(--oc-surface-muted)] '
          + 'font-bold '
          + 'text-[var(--oc-text-secondary)] '
          + 'dark:bg-[var(--oc-surface)]/[0.07] '
          + 'dark:text-[var(--oc-text-secondary)]'
        ),
      ].join(' ')}
    >
      {initials}
    </div>
  )
}


function getInitials(
  firstName: string,
  lastName: string,
): string {
  const result =
    (
      firstName.trim().charAt(0)
      + lastName.trim().charAt(0)
    ).toUpperCase()

  return result || 'OC'
}


function formatName(
  firstName: string,
  lastName: string,
): string {
  const value =
    `${firstName} ${lastName}`
      .trim()

  return value || 'Athlète OpenCoach'
}
