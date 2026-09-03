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
  LogOut,
  Menu,
  Monitor,
  Moon,
  MoreHorizontal,
  Settings,
  Sun,
  UserRound,
  X,
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
    label: 'Entraînement',
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
    label: 'Semaine',
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
          w-64
          flex-col
          border-r
          border-black/[0.065]
          bg-white
          lg:flex
          dark:border-white/[0.07]
          dark:bg-[#101418]
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
                  text-slate-950
                  dark:text-white
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
                  text-emerald-600
                  dark:text-emerald-400
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
              text-[10px]
              font-semibold
              uppercase
              tracking-[0.16em]
              text-slate-400
              dark:text-slate-600
            "
          >
            Entraînement
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
              text-slate-400
              dark:text-slate-600
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


                {/* OPENCOACH DESKTOP PROFILE DROPDOWN */}

                <div
                  className="
                    relative
                    border-t
                    border-black/[0.06]
                    p-2
                    dark:border-white/[0.07]
                  "
                >

                  {/* Déclencheur */}

                  <button
                    type="button"
                    onClick={() => {
                      setDesktopProfileOpen(
                        (current) => !current,
                      )
                    }}
                    aria-haspopup="menu"
                    aria-expanded={
                      desktopProfileOpen
                    }
                    className={[
                      (
                        'flex w-full items-center '
                        + 'gap-2.5 rounded-[10px] '
                        + 'px-2 py-[7px] '
                        + 'text-left transition-colors'
                      ),
                      desktopProfileOpen
                        ? (
                            'bg-slate-100 '
                            + 'dark:bg-white/[0.06]'
                          )
                        : (
                            'hover:bg-slate-50 '
                            + 'dark:hover:bg-white/[0.045]'
                          ),
                    ].join(' ')}
                  >
                    <Avatar
                      avatar={avatar}
                      initials={initials}
                      size="small"
                    />

                    <div
                      className="
                        min-w-0
                        flex-1
                      "
                    >
                      <p
                        className="
                          truncate
                          text-[12.5px]
                          font-semibold
                          text-slate-900
                          dark:text-slate-100
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
                          truncate
                          text-[9.5px]
                          text-slate-400
                          dark:text-slate-500
                        "
                      >
                        Profil athlète
                      </p>
                    </div>

                    <ChevronRight
                      className={[
                        (
                          'h-3.5 w-3.5 '
                          + 'shrink-0 '
                          + 'text-slate-300 '
                          + 'transition-transform '
                          + 'dark:text-slate-600'
                        ),
                        desktopProfileOpen
                          ? '-rotate-90'
                          : 'rotate-0',
                      ].join(' ')}
                    />
                  </button>


                  {/* Dropdown */}

                  {desktopProfileOpen && (
                    <div
                      role="menu"
                      className="
                        absolute
                        bottom-0
                        left-[calc(100%+8px)]
                        w-[210px]
                        z-[90]
                        overflow-hidden
                        rounded-[12px]
                        border
                        border-black/[0.07]
                        bg-white
                        p-1
                        shadow-[0_10px_28px_rgba(15,23,42,0.13)]
                        dark:border-white/[0.08]
                        dark:bg-[#171d21]
                        dark:shadow-[0_10px_30px_rgba(0,0,0,0.28)]
                      "
                    >

                      <DropdownLabel>
                        Compte
                      </DropdownLabel>

                      <DropdownItem
                        icon={
                          <UserRound
                            className="h-3 w-3"
                          />
                        }
                        label="Profil personnel"
                        active={
                          activePage
                          === 'profile-personal'
                        }
                        onClick={() =>
                          navigate(
                            'profile-personal',
                          )
                        }
                      />

                      <DropdownItem
                        icon={
                          <CircleUserRound
                            className="h-3 w-3"
                          />
                        }
                        label="Profil sportif"
                        active={
                          activePage
                          === 'profile-sport'
                        }
                        onClick={() =>
                          navigate(
                            'profile-sport',
                          )
                        }
                      />

                      <DropdownItem
                        icon={
                          <Settings
                            className="h-3 w-3"
                          />
                        }
                        label="Réglages"
                        active={
                          activePage
                          === 'settings'
                        }
                        onClick={() =>
                          navigate(
                            'settings',
                          )
                        }
                      />


                      <DropdownSeparator />


                      <DropdownLabel>
                        Apparence
                      </DropdownLabel>

                      <div
                        className="
                          grid
                          grid-cols-3
                          gap-1
                          px-0.5
                          pb-1
                        "
                      >
                        <DropdownThemeButton
                          active={
                            theme === 'light'
                          }
                          icon={
                            <Sun
                              className="h-3 w-3"
                            />
                          }
                          label="Clair"
                          onClick={() =>
                            onThemeChange(
                              'light',
                            )
                          }
                        />

                        <DropdownThemeButton
                          active={
                            theme === 'dark'
                          }
                          icon={
                            <Moon
                              className="h-3 w-3"
                            />
                          }
                          label="Sombre"
                          onClick={() =>
                            onThemeChange(
                              'dark',
                            )
                          }
                        />

                        <DropdownThemeButton
                          active={
                            theme === 'system'
                          }
                          icon={
                            <Monitor
                              className="h-3 w-3"
                            />
                          }
                          label="Auto"
                          onClick={() =>
                            onThemeChange(
                              'system',
                            )
                          }
                        />
                      </div>


                      <DropdownSeparator />


                      <DropdownItem
                        icon={
                          <LogOut
                            className="h-3 w-3"
                          />
                        }
                        label="Se déconnecter"
                        danger
                        onClick={() => {
                          setDesktopProfileOpen(
                            false,
                          )

                          onLogout()
                        }}
                      />


                      {/* Version */}

                      <div
                        className="
                          mt-1
                          rounded-[9px]
                          bg-slate-50
                          px-2
                          py-1.5
                          dark:bg-white/[0.035]
                        "
                      >
                        <div
                          className="
                            flex
                            items-center
                            justify-between
                            gap-2
                          "
                        >
                          <span
                            className="
                              text-[8px]
                              text-slate-400
                              dark:text-slate-500
                            "
                          >
                            Version
                          </span>

                          <span
                            className="
                              text-[7.5px]
                              font-semibold
                              text-slate-600
                              dark:text-slate-300
                            "
                          >
                            {version
                              ? `v${version}`
                              : 'dev'}
                          </span>
                        </div>

                        {commit && (
                          <p
                            className="
                              mt-0.5
                              truncate
                              text-right
                              font-mono
                              text-[7.5px]
                              text-slate-300
                              dark:text-slate-600
                            "
                          >
                            {commit}
                          </p>
                        )}
                      </div>

                    </div>
                  )}
                </div>

              </aside>


      {/* ================================================
          Mobile top bar
         ================================================ */}

      <header
        className="
          sticky
          top-0
          z-40
          flex
          h-16
          items-center
          justify-between
          border-b
          border-black/[0.06]
          bg-white/90
          px-4
          backdrop-blur-xl
          lg:hidden
          dark:border-white/[0.07]
          dark:bg-[#101418]/90
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
          <OpenCoachMark
            compact
          />

          <span
            className="
              text-lg
              font-bold
              tracking-[-0.035em]
              text-slate-950
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
            hover:bg-slate-100
            dark:hover:bg-white/[0.06]
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
          fixed
          inset-x-0
          bottom-0
          z-50
          border-t
          border-black/[0.065]
          bg-white/95
          pb-[env(safe-area-inset-bottom)]
          backdrop-blur-xl
          lg:hidden
          dark:border-white/[0.07]
          dark:bg-[#101418]/95
        "
        aria-label="Navigation mobile"
      >
        <div
          className="
            mx-auto
            grid
            h-16
            max-w-lg
            grid-cols-5
            px-1
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
                  activePage
                  === page
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

          <MobileNavigationItem
            active={
              isMorePage(
                activePage,
              )
            }
            label="Plus"
            icon={
              <MoreHorizontal
                className="h-5 w-5"
              />
            }
            onClick={() =>
              setMobileMenuOpen(
                true,
              )
            }
          />
        </div>
      </nav>


      {/* ================================================
          Mobile Plus panel
         ================================================ */}

      {mobileMenuOpen && (
        <div
          className="
            fixed
            inset-0
            z-[70]
            lg:hidden
          "
        >
          <button
            type="button"
            className="
              absolute
              inset-0
              bg-black/35
              backdrop-blur-[2px]
            "
            onClick={() =>
              setMobileMenuOpen(
                false,
              )
            }
            aria-label="Fermer le menu"
          />

          <div
            className="
              absolute
              inset-x-0
              bottom-0
              max-h-[85dvh]
              overflow-y-auto
              rounded-t-[28px]
              bg-white
              px-4
              pb-[calc(1.25rem+env(safe-area-inset-bottom))]
              pt-3
              shadow-2xl
              dark:bg-[#151a1f]
            "
          >
            <div
              className="
                mx-auto
                mb-3
                h-1
                w-10
                rounded-full
                bg-slate-200
                dark:bg-white/10
              "
            />

            <div
              className="
                flex
                items-center
                justify-between
                gap-4
                pb-4
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
                <Avatar
                  avatar={avatar}
                  initials={initials}
                />

                <div className="min-w-0">
                  <p
                    className="
                      truncate
                      font-bold
                      text-slate-950
                      dark:text-white
                    "
                  >
                    {formatName(
                      firstName,
                      lastName,
                    )}
                  </p>

                  <p
                    className="
                      text-xs
                      text-slate-400
                    "
                  >
                    Athlète OpenCoach
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() =>
                  setMobileMenuOpen(
                    false,
                  )
                }
                className="
                  flex h-9 w-9
                  items-center
                  justify-center
                  rounded-full
                  bg-slate-100
                  text-slate-500
                  dark:bg-white/[0.06]
                  dark:text-slate-400
                "
              >
                <X className="h-4 w-4" />
              </button>
            </div>


            <div
              className="
                grid
                grid-cols-2
                gap-2
                border-t
                border-black/[0.06]
                pt-4
                dark:border-white/[0.07]
              "
            >
              <MenuCard
                icon={<Flag />}
                title="Courses"
                description="Objectifs et historique"
                onClick={() =>
                  navigate(
                    'races',
                  )
                }
              />

              <MenuCard
                icon={<Gauge />}
                title="Ressenti"
                description="État du jour"
                onClick={() =>
                  navigate(
                    'feeling',
                  )
                }
              />

              <MenuCard
                icon={<UserRound />}
                title="Profil"
                description="Informations personnelles"
                onClick={() =>
                  navigate(
                    'profile-personal',
                  )
                }
              />

              <MenuCard
                icon={<CircleUserRound />}
                title="Profil sportif"
                description="Zones et physiologie"
                onClick={() =>
                  navigate(
                    'profile-sport',
                  )
                }
              />

              <MenuCard
                icon={<Settings />}
                title="Réglages"
                description="Configuration OpenCoach"
                onClick={() =>
                  navigate(
                    'settings',
                  )
                }
              />

              <MenuCard
                icon={<Menu />}
                title="Navigation"
                description="Toutes les fonctions"
                onClick={() =>
                  setMobileMenuOpen(
                    false,
                  )
                }
              />
            </div>


            <div
              className="
                mt-5
                rounded-2xl
                bg-slate-50
                p-4
                dark:bg-white/[0.035]
              "
            >
              <p
                className="
                  text-xs
                  font-semibold
                  text-slate-700
                  dark:text-slate-300
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
                    onThemeChange(
                      'light',
                    )
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
                    onThemeChange(
                      'dark',
                    )
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
                    onThemeChange(
                      'system',
                    )
                  }
                />
              </div>
            </div>


            <button
              type="button"
              onClick={
                onLogout
              }
              className="
                mt-4
                flex
                w-full
                items-center
                justify-center
                gap-2
                rounded-xl
                px-4
                py-3
                text-sm
                font-semibold
                text-red-500
                transition
                hover:bg-red-50
                dark:hover:bg-red-500/10
              "
            >
              <LogOut className="h-4 w-4" />

              Se déconnecter
            </button>


            <div
              className="
                mt-3
                text-center
                text-[10px]
                text-slate-300
                dark:text-slate-700
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
        </div>
      )}
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
                text-slate-400
                dark:text-slate-600
              "
            >
              {children}
            </p>
          )
        }


        function DropdownSeparator() {
          return (
            <div
              className="
                my-1
                h-px
                bg-black/[0.055]
                dark:bg-white/[0.07]
              "
            />
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
                        'text-slate-600 '
                        + 'hover:bg-slate-50 '
                        + 'hover:text-slate-900 '
                        + 'dark:text-slate-300 '
                        + 'dark:hover:bg-white/[0.045] '
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
                      : 'text-slate-400',
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
                      'border-black/[0.055] '
                      + 'bg-white '
                      + 'text-slate-400 '
                      + 'hover:bg-slate-50 '
                      + 'dark:border-white/[0.07] '
                      + 'dark:bg-white/[0.025] '
                      + 'dark:hover:bg-white/[0.05]'
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
              'text-slate-500 '
              + 'hover:bg-slate-50 '
              + 'hover:text-slate-900 '
              + 'dark:text-slate-400 '
              + 'dark:hover:bg-white/[0.045] '
              + 'dark:hover:text-slate-100'
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
            : 'text-slate-400'
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
          'relative flex '
          + 'flex-col items-center '
          + 'justify-center '
          + 'gap-1 text-[7.5px] '
          + 'font-medium'
        ),
        active
          ? (
              'text-emerald-600 '
              + 'dark:text-emerald-400'
            )
          : (
              'text-slate-400 '
              + 'dark:text-slate-500'
            ),
      ].join(' ')}
    >
      {active && (
        <span
          className="
            absolute
            top-0
            h-0.5
            w-8
            rounded-full
            bg-emerald-500
          "
        />
      )}

      {icon}

      <span>
        {label}
      </span>
    </button>
  )
}


function MenuCard({
  icon,
  title,
  description,
  onClick,
}: {
  icon: React.ReactNode
  title: string
  description: string
  onClick: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="
        rounded-2xl
        border
        border-black/[0.06]
        p-4
        text-left
        transition
        hover:border-emerald-500/20
        hover:bg-emerald-50/40
        dark:border-white/[0.07]
        dark:hover:bg-emerald-500/[0.04]
      "
    >
      <div
        className="
          flex h-9 w-9
          items-center
          justify-center
          rounded-xl
          bg-emerald-50
          text-emerald-600
          dark:bg-emerald-500/10
          dark:text-emerald-400
          [&>svg]:h-[18px]
          [&>svg]:w-[18px]
        "
      >
        {icon}
      </div>

      <p
        className="
          mt-3
          text-sm
          font-semibold
          text-slate-900
          dark:text-slate-100
        "
      >
        {title}
      </p>

      <p
        className="
          mt-0.5
          text-[10px]
          leading-4
          text-slate-400
        "
      >
        {description}
      </p>
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
              'border-black/[0.06] '
              + 'bg-white '
              + 'text-slate-500 '
              + 'dark:border-white/[0.07] '
              + 'dark:bg-white/[0.03] '
              + 'dark:text-slate-400'
            ),
      ].join(' ')}
    >
      {icon}
      {label}
    </button>
  )
}


function OpenCoachMark({
  compact = false,
}: {
  compact?: boolean
}) {
  return (
    <div
      className={[
        (
          'flex shrink-0 '
          + 'items-center justify-center '
          + 'rounded-xl '
          + 'bg-emerald-600 '
          + 'font-black text-white '
          + 'shadow-sm '
          + 'dark:bg-emerald-500'
        ),
        compact
          ? 'h-7 w-7 text-[10px]'
          : 'h-10 w-10 text-sm',
      ].join(' ')}
    >
      OC
    </div>
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
          + 'bg-slate-100 '
          + 'font-bold '
          + 'text-slate-600 '
          + 'dark:bg-white/[0.07] '
          + 'dark:text-slate-300'
        ),
      ].join(' ')}
    >
      {initials}
    </div>
  )
}


function isMorePage(
  page: NavigationPage,
): boolean {
  return (
    page === 'races'
    || page === 'feeling'
    || page === 'profile-personal'
    || page === 'profile-sport'
    || page === 'settings'
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
