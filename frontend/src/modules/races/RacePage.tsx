import {
  useState,
} from 'react'

import { PageHeader } from '../../design-system/components/PageHeader'
import {
  CalendarDays,
  Check,
  ChevronRight,
  Eye,
  Flag,
  MapPin,
  Plus,
  RefreshCw,
  Route,
  Trophy,
} from 'lucide-react'

import {
  SidePanel,
} from '../../components/ui/SidePanel'

import {
  RaceDetails,
} from './RaceDetails'

import {
  RaceForm,
} from './RaceForm'

import {
  useRaces,
} from './raceStore'

import type {
  Race,
  RacePriority,
  RaceStatus,
  RaceType,
} from './types'

import {
  getNextPrimaryRace,
  getTrainingRacesBeforeNextPrimary,
} from './selectors'


export function RacePage() {
  const {
    races,
    loading,
    error,
    refreshRaces,
  } = useRaces()

  const [
    selectedRaceId,
    setSelectedRaceId,
  ] = useState<string | null>(
    null,
  )

  const [
    isAddModalOpen,
    setIsAddModalOpen,
  ] = useState(false)


  const selectedRace =
    selectedRaceId
      ? races.find(
          race =>
            race.id
            === selectedRaceId,
        )
      : undefined


  const upcomingRaces =
    races
      .filter(
        race =>
          race.status === 'planned',
      )
      .sort(
        (first, second) =>
          new Date(
            first.date,
          ).getTime()
          - new Date(
              second.date,
            ).getTime(),
      )


  const pastRaces =
    races
      .filter(
        race =>
          race.status !== 'planned',
      )
      .sort(
        (first, second) =>
          new Date(
            second.date,
          ).getTime()
          - new Date(
              first.date,
            ).getTime(),
      )


  const nextPrimaryRace =
    getNextPrimaryRace(
      races,
    )

  const preparationRaces =
    getTrainingRacesBeforeNextPrimary(
      races,
    )


  const otherUpcomingRaces =
    upcomingRaces.filter(
      race =>
        race.id
        !== nextPrimaryRace?.id
        && !preparationRaces.some(
          preparation =>
            preparation.id
            === race.id,
        ),
    )


  const completedCount =
    pastRaces.filter(
      race =>
        race.status === 'completed',
    ).length


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
          max-w-[1180px]
          px-3
          py-4
          sm:px-5
          lg:py-5
        "
      >
        <PageHeader
          eyebrow="Objectifs"
          title="Courses"
          description="Organise tes courses et tes objectifs sportifs."
          actions={
            <button
              type="button"
              onClick={() => setIsAddModalOpen(true)}
              className="
                inline-flex
                h-9
                items-center
                gap-2
                rounded-[9px]
                bg-emerald-600
                px-3
                text-[11px]
                font-semibold
                text-white
                shadow-sm
                transition-colors
                hover:bg-emerald-700
                focus-visible:outline
                focus-visible:outline-2
                focus-visible:outline-offset-2
                focus-visible:outline-emerald-600
              "
            >
              <Plus className="h-4 w-4" />
              Ajouter une course
            </button>
          }
        />


        {loading && (
          <LoadingState />
        )}


        {!loading && error && (
          <ErrorState
            error={error}
            onRetry={() =>
              void refreshRaces()
            }
          />
        )}


        {!loading && !error && (
          <div className="space-y-4">

            {/* ==========================================
                PRIMARY RACE HERO
                ========================================== */}

            {nextPrimaryRace ? (
              <PrimaryRaceHero
                race={
                  nextPrimaryRace
                }
                preparationCount={
                  preparationRaces.length
                }
                onOpen={() =>
                  setSelectedRaceId(
                    nextPrimaryRace.id,
                  )
                }
              />
            ) : (
              <NoPrimaryRace
                onAdd={() =>
                  setIsAddModalOpen(
                    true,
                  )
                }
              />
            )}


            {/* ==========================================
                OVERVIEW
                ========================================== */}

            <RaceOverview
              upcomingCount={
                upcomingRaces.length
              }
              completedCount={
                completedCount
              }
              preparationCount={
                preparationRaces.length
              }
            />


            {/* ==========================================
                PREPARATION TIMELINE
                ========================================== */}

            {nextPrimaryRace
              && preparationRaces.length > 0
              && (
                <section
                  className="
                    overflow-hidden
                    rounded-[14px]
                    border
                    border-[var(--oc-border)]
                    bg-[var(--oc-surface)]
                    dark:border-[var(--oc-border)]
                    dark:bg-[var(--oc-surface)]
                  "
                >
                  <SectionHeader
                    eyebrow="Préparation"
                    title="Chemin vers l’objectif"
                  />

                  <div
                    className="
                      px-4
                      py-3
                      sm:px-5
                    "
                  >
                    {preparationRaces.map(
                      (
                        race,
                        index,
                      ) => (
                        <PreparationRace
                          key={
                            race.id
                          }
                          race={
                            race
                          }
                          first={
                            index === 0
                          }
                          onOpen={() =>
                            setSelectedRaceId(
                              race.id,
                            )
                          }
                        />
                      ),
                    )}

                    <PreparationRace
                      race={
                        nextPrimaryRace
                      }
                      primary
                      first={
                        preparationRaces
                          .length === 0
                      }
                      onOpen={() =>
                        setSelectedRaceId(
                          nextPrimaryRace.id,
                        )
                      }
                    />
                  </div>
                </section>
              )}


            {/* ==========================================
                OTHER UPCOMING
                ========================================== */}

            {otherUpcomingRaces.length > 0 && (
              <section
                className="
                  overflow-hidden
                  rounded-[14px]
                  border
                  border-[var(--oc-border)]
                  bg-[var(--oc-surface)]
                  dark:border-[var(--oc-border)]
                  dark:bg-[var(--oc-surface)]
                "
              >
                <SectionHeader
                  eyebrow="À venir"
                  title="Autres courses"
                />

                <RaceResponsiveList
                  races={
                    otherUpcomingRaces
                  }
                  onOpen={
                    setSelectedRaceId
                  }
                />
              </section>
            )}


            {/* ==========================================
                HISTORY
                ========================================== */}

            <section
              className="
                overflow-hidden
                rounded-[14px]
                border
                border-[var(--oc-border)]
                bg-[var(--oc-surface)]
                dark:border-[var(--oc-border)]
                dark:bg-[var(--oc-surface)]
              "
            >
              <SectionHeader
                eyebrow="Historique"
                title="Courses passées"
                trailing={
                  <span
                    className="
                      text-[9px]
                      font-semibold
                      text-[var(--oc-muted-soft)]
                    "
                  >
                    {
                      pastRaces.length
                    } course{
                      pastRaces.length > 1
                        ? 's'
                        : ''
                    }
                  </span>
                }
              />

              {pastRaces.length > 0 ? (
                <RaceResponsiveList
                  races={
                    pastRaces
                  }
                  onOpen={
                    setSelectedRaceId
                  }
                  history
                />
              ) : (
                <EmptyState
                  title="Aucune course terminée"
                  description="
                    Tes résultats apparaîtront
                    ici après tes courses.
                  "
                />
              )}
            </section>
          </div>
        )}
      </div>


      <RaceForm
        open={
          isAddModalOpen
        }
        onClose={() =>
          setIsAddModalOpen(
            false,
          )
        }
      />


      {selectedRace && (
        <SidePanel
          eyebrow="Course"
          title={
            selectedRace.name
          }
          open
          onClose={() =>
            setSelectedRaceId(
              null,
            )
          }
        >
          <RaceDetails
            race={
              selectedRace
            }
            onClose={() =>
              setSelectedRaceId(
                null,
              )
            }
          />
        </SidePanel>
      )}
    </main>
  )
}


/* ============================================================
   PRIMARY HERO
   ============================================================ */

function PrimaryRaceHero({
  race,
  preparationCount,
  onOpen,
}: {
  race: Race
  preparationCount: number
  onOpen: () => void
}) {
  const days =
    daysUntil(
      race.date,
    )

  return (
    <section
      className="
        relative
        overflow-hidden
        rounded-[16px]
        border
        border-white/[0.07]
        bg-[#141917]
        text-white
        shadow-[0_12px_38px_rgba(4,12,8,0.10)]
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          -right-24
          -top-28
          h-72
          w-72
          rounded-full
          bg-emerald-500/[0.11]
          blur-3xl
        "
      />

      <div
        className="
          relative
          p-5
          sm:p-6
        "
      >
        <div
          className="
            flex
            flex-wrap
            items-center
            justify-between
            gap-3
          "
        >
          <div
            className="
              flex
              items-center
              gap-2
            "
          >
            <span
              className="
                h-2
                w-2
                rounded-full
                bg-emerald-400
              "
            />

            <span
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.13em]
                text-emerald-400
              "
            >
              Objectif principal
            </span>
          </div>

          <div
            className="
              rounded-full
              border
              border-white/[0.08]
              bg-white/[0.04]
              px-3
              py-1
            "
          >
            <span
              className="
                text-[9px]
                font-semibold
                text-white/45
              "
            >
              {
                days >= 0
                  ? `J-${days}`
                  : 'Terminée'
              }
            </span>
          </div>
        </div>


        <div
          className="
            mt-5
            grid
            gap-5
            lg:grid-cols-[minmax(0,1fr)_auto]
            lg:items-end
          "
        >
          <div>
            <h2
              className="
                max-w-3xl
                text-[27px]
                font-bold
                leading-[1.1]
                tracking-[-0.04em]
                sm:text-[31px]
              "
            >
              {race.name}
            </h2>

            <div
              className="
                mt-3
                flex
                flex-wrap
                items-center
                gap-x-4
                gap-y-2
                text-[11px]
                font-medium
                text-white/50
              "
            >
              <span
                className="
                  flex
                  items-center
                  gap-1.5
                "
              >
                <CalendarDays
                  className="
                    h-3.5
                    w-3.5
                    text-emerald-400
                  "
                />

                {
                  formatDateLong(
                    race.date,
                  )
                }
              </span>

              <span
                className="
                  flex
                  items-center
                  gap-1.5
                "
              >
                <MapPin
                  className="
                    h-3.5
                    w-3.5
                    text-emerald-400
                  "
                />

                {race.location}
              </span>

              <span>
                {
                  formatRaceType(
                    race.type,
                  )
                }
              </span>
            </div>


            <div
              className="
                mt-5
                flex
                flex-wrap
                gap-x-7
                gap-y-3
              "
            >
              <HeroMetric
                label="Distance"
                value={
                  `${formatNumber(
                    race.distanceKm,
                  )} km`
                }
              />

              <HeroMetric
                label="Dénivelé"
                value={
                  race.elevationGainM
                    ? (
                        `${Math.round(
                          race.elevationGainM,
                        )} m`
                      )
                    : '—'
                }
              />

              <HeroMetric
                label="Objectif"
                value={
                  race.targetTimeMinutes
                    ? formatDuration(
                        race.targetTimeMinutes,
                      )
                    : 'À définir'
                }
              />
            </div>


            <div
              className="
                mt-5
                flex
                items-center
                gap-2
                border-t
                border-white/[0.07]
                pt-3
                text-[10px]
                text-white/40
              "
            >
              <Flag
                className="
                  h-3.5
                  w-3.5
                  text-emerald-400
                "
              />

              {preparationCount > 0
                ? (
                    `${preparationCount} course${
                      preparationCount > 1
                        ? 's'
                        : ''
                    } de préparation avant l’objectif`
                  )
                : (
                    'Aucune course de préparation programmée'
                  )}
            </div>
          </div>


          <button
            type="button"
            onClick={
              onOpen
            }
            className="
              inline-flex
              h-9
              shrink-0
              items-center
              justify-center
              gap-1.5
              rounded-[8px]
              border
              border-emerald-400/25
              bg-emerald-400/[0.09]
              px-3
              text-[10px]
              font-semibold
              text-emerald-300
              transition
              hover:bg-emerald-400/[0.14]
            "
          >
            Voir la course

            <ChevronRight
              className="
                h-3.5
                w-3.5
              "
            />
          </button>
        </div>
      </div>
    </section>
  )
}


function HeroMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div>
      <p
        className="
          text-[8px]
          font-bold
          uppercase
          tracking-[0.08em]
          text-white/30
        "
      >
        {label}
      </p>

      <p
        className="
          mt-1
          text-[16px]
          font-bold
          tabular-nums
          text-white
        "
      >
        {value}
      </p>
    </div>
  )
}


/* ============================================================
   OVERVIEW
   ============================================================ */

function RaceOverview({
  upcomingCount,
  completedCount,
  preparationCount,
}: {
  upcomingCount: number
  completedCount: number
  preparationCount: number
}) {
  return (
    <section
      className="
        grid
        grid-cols-3
        overflow-hidden
        rounded-[13px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]
        dark:border-[var(--oc-border)]
        dark:bg-[var(--oc-surface)]
      "
    >
      <OverviewMetric
        icon={
          <Flag
            className="
              h-4
              w-4
            "
          />
        }
        value={
          String(
            upcomingCount,
          )
        }
        label="À venir"
      />

      <OverviewMetric
        icon={
          <Route
            className="
              h-4
              w-4
            "
          />
        }
        value={
          String(
            preparationCount,
          )
        }
        label="Préparation"
      />

      <OverviewMetric
        icon={
          <Check
            className="
              h-4
              w-4
            "
          />
        }
        value={
          String(
            completedCount,
          )
        }
        label="Terminées"
      />
    </section>
  )
}


function OverviewMetric({
  icon,
  value,
  label,
}: {
  icon: React.ReactNode
  value: string
  label: string
}) {
  return (
    <div
      className="
        flex
        items-center
        justify-center
        gap-2.5
        border-r
        border-[var(--oc-border)]
        px-3
        py-3
        last:border-r-0
        dark:border-[var(--oc-border)]
      "
    >
      <div
        className="
          text-emerald-500
        "
      >
        {icon}
      </div>

      <div>
        <p
          className="
            text-[15px]
            font-bold
            leading-none
            tabular-nums
            text-[var(--oc-text-secondary)]
            dark:text-[var(--oc-text-secondary)]
          "
        >
          {value}
        </p>

        <p
          className="
            mt-1
            text-[8px]
            font-semibold
            uppercase
            tracking-[0.07em]
            text-[var(--oc-muted-soft)]
          "
        >
          {label}
        </p>
      </div>
    </div>
  )
}


/* ============================================================
   PREPARATION TIMELINE
   ============================================================ */

function PreparationRace({
  race,
  primary = false,
  first = false,
  onOpen,
}: {
  race: Race
  primary?: boolean
  first?: boolean
  onOpen: () => void
}) {
  return (
    <button
      type="button"
      onClick={
        onOpen
      }
      className="
        group
        relative
        flex
        w-full
        items-stretch
        gap-3
        text-left
      "
    >
      <div
        className="
          relative
          flex
          w-5
          shrink-0
          justify-center
        "
      >
        {!first && (
          <span
            className="
              absolute
              bottom-1/2
              top-0
              w-px
              bg-[var(--oc-border-strong)]
              dark:bg-[var(--oc-surface-muted)]
            "
          />
        )}

        <span
          className={[
            (
              'relative z-10 mt-4 '
              + 'h-2.5 w-2.5 '
              + 'rounded-full '
              + 'ring-4 '
              + 'ring-[var(--oc-surface)] '
              + 'dark:ring-[var(--oc-surface)]'
            ),
            primary
              ? 'bg-emerald-500'
              : 'bg-[var(--oc-muted-soft)] dark:bg-[var(--oc-muted-soft)]',
          ].join(' ')}
        />

        <span
          className="
            absolute
            bottom-0
            top-1/2
            w-px
            bg-[var(--oc-border-strong)]
            dark:bg-[var(--oc-surface-muted)]
          "
        />
      </div>


      <div
        className="
          flex
          min-w-0
          flex-1
          items-center
          justify-between
          gap-3
          border-b
          border-[var(--oc-border)]
          py-3
          last:border-b-0
          dark:border-[var(--oc-border)]
        "
      >
        <div className="min-w-0">
          <div
            className="
              flex
              flex-wrap
              items-center
              gap-2
            "
          >
            <span
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.07em]
                text-[var(--oc-muted-soft)]
              "
            >
              {
                formatDateShort(
                  race.date,
                )
              }
            </span>

            <PriorityPill
              priority={
                race.priority
              }
            />
          </div>

          <p
            className="
              mt-1
              truncate
              text-[12px]
              font-semibold
              text-[var(--oc-text-secondary)]
              dark:text-[var(--oc-text-secondary)]
            "
          >
            {race.name}
          </p>

          <p
            className="
              mt-0.5
              text-[9.5px]
              text-[var(--oc-muted-soft)]
            "
          >
            {
              formatNumber(
                race.distanceKm,
              )
            } km

            {race.elevationGainM
              ? (
                  ` · ${Math.round(
                    race.elevationGainM,
                  )} m D+`
                )
              : ''}
          </p>
        </div>

        <ChevronRight
          className="
            h-4
            w-4
            shrink-0
            text-[var(--oc-muted-soft)]
            transition
            group-hover:translate-x-0.5
            group-hover:text-emerald-500
          "
        />
      </div>
    </button>
  )
}


/* ============================================================
   RESPONSIVE LIST
   ============================================================ */

function RaceResponsiveList({
  races,
  onOpen,
  history = false,
}: {
  races: Race[]
  onOpen: (
    raceId: string,
  ) => void
  history?: boolean
}) {
  return (
    <>
      <div
        className="
          hidden
          md:block
        "
      >
        <table
          className="
            w-full
            border-collapse
          "
        >
          <thead
            className="
              bg-[var(--oc-surface-hover)]
              dark:bg-[var(--oc-surface-muted)]
            "
          >
            <tr
              className="
                border-b
                border-[var(--oc-border)]
                dark:border-[var(--oc-border)]
              "
            >
              <TableHeader>
                Date
              </TableHeader>

              <TableHeader>
                Course
              </TableHeader>

              <TableHeader>
                Type
              </TableHeader>

              <TableHeader
                align="right"
              >
                Distance
              </TableHeader>

              <TableHeader
                align="right"
              >
                D+
              </TableHeader>

              {history && (
                <TableHeader
                  align="right"
                >
                  Résultat
                </TableHeader>
              )}

              <TableHeader
                align="right"
              >
                Action
              </TableHeader>
            </tr>
          </thead>

          <tbody>
            {races.map(
              race => (
                <RaceTableRow
                  key={
                    race.id
                  }
                  race={
                    race
                  }
                  history={
                    history
                  }
                  onOpen={() =>
                    onOpen(
                      race.id,
                    )
                  }
                />
              ),
            )}
          </tbody>
        </table>
      </div>


      <div
        className="
          divide-y
          divide-[var(--oc-border)]
          dark:divide-[var(--oc-border)]
          md:hidden
        "
      >
        {races.map(
          race => (
            <RaceMobileCard
              key={
                race.id
              }
              race={
                race
              }
              history={
                history
              }
              onOpen={() =>
                onOpen(
                  race.id,
                )
              }
            />
          ),
        )}
      </div>
    </>
  )
}


function TableHeader({
  children,
  align = 'left',
}: {
  children: React.ReactNode
  align?: 'left' | 'right'
}) {
  return (
    <th
      className={[
        (
          'px-4 py-2.5 '
          + 'text-[8.5px] '
          + 'font-bold '
          + 'uppercase '
          + 'tracking-[0.08em] '
          + 'text-[var(--oc-muted-soft)]'
        ),
        align === 'right'
          ? 'text-right'
          : 'text-left',
      ].join(' ')}
    >
      {children}
    </th>
  )
}


function RaceTableRow({
  race,
  history,
  onOpen,
}: {
  race: Race
  history: boolean
  onOpen: () => void
}) {
  return (
    <tr
      className="
        border-b
        border-[var(--oc-border)]
        transition
        last:border-b-0
        hover:bg-[var(--oc-surface-hover)]
        dark:border-[var(--oc-border)]
        dark:hover:bg-[var(--oc-surface-hover)]
      "
    >
      <td
        className="
          whitespace-nowrap
          px-4
          py-3
          text-[10.5px]
          font-semibold
          text-[var(--oc-text-secondary)]
          dark:text-[var(--oc-muted-soft)]
        "
      >
        {
          formatDateShort(
            race.date,
          )
        }
      </td>

      <td
        className="
          max-w-[300px]
          px-4
          py-3
        "
      >
        <p
          className="
            truncate
            text-[12px]
            font-semibold
            text-[var(--oc-text-secondary)]
            dark:text-[var(--oc-text-secondary)]
          "
        >
          {race.name}
        </p>

        <p
          className="
            mt-0.5
            truncate
            text-[9px]
            text-[var(--oc-muted-soft)]
          "
        >
          {race.location}
        </p>
      </td>

      <td
        className="
          px-4
          py-3
        "
      >
        <RaceTypePill
          type={
            race.type
          }
        />
      </td>

      <NumberCell>
        {
          formatNumber(
            race.distanceKm,
          )
        } km
      </NumberCell>

      <NumberCell>
        {
          race.elevationGainM
            ? (
                `${Math.round(
                  race.elevationGainM,
                )} m`
              )
            : '—'
        }
      </NumberCell>

      {history && (
        <NumberCell>
          <RaceResult
            race={
              race
            }
          />
        </NumberCell>
      )}

      <td
        className="
          px-4
          py-3
          text-right
        "
      >
        <button
          type="button"
          aria-label="Voir la course"
          title="Voir la course"
          onClick={
            onOpen
          }
          className="
            inline-flex
            h-8
            w-8
            items-center
            justify-center
            rounded-[8px]
            border
            border-emerald-500/20
            bg-emerald-500/[0.06]
            text-emerald-600
            transition
            hover:bg-emerald-500/[0.11]
            dark:text-emerald-400
          "
        >
          <Eye
            className="
              h-4
              w-4
            "
          />
        </button>
      </td>
    </tr>
  )
}


function NumberCell({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <td
      className="
        whitespace-nowrap
        px-4
        py-3
        text-right
        text-[10.5px]
        font-medium
        tabular-nums
        text-[var(--oc-text-secondary)]
        dark:text-[var(--oc-muted-soft)]
      "
    >
      {children}
    </td>
  )
}


function RaceMobileCard({
  race,
  history,
  onOpen,
}: {
  race: Race
  history: boolean
  onOpen: () => void
}) {
  return (
    <article
      className="
        px-4
        py-4
      "
    >
      <div
        className="
          flex
          items-start
          justify-between
          gap-3
        "
      >
        <div className="min-w-0">
          <div
            className="
              flex
              flex-wrap
              items-center
              gap-2
            "
          >
            <span
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.07em]
                text-[var(--oc-muted-soft)]
              "
            >
              {
                formatDateShort(
                  race.date,
                )
              }
            </span>

            <RaceTypePill
              type={
                race.type
              }
            />

            <PriorityPill
              priority={
                race.priority
              }
            />
          </div>

          <h3
            className="
              mt-2
              text-[15px]
              font-semibold
              tracking-[-0.02em]
              text-[var(--oc-text-secondary)]
              dark:text-[var(--oc-text-secondary)]
            "
          >
            {race.name}
          </h3>

          <p
            className="
              mt-1
              flex
              items-center
              gap-1
              text-[10px]
              text-[var(--oc-muted-soft)]
            "
          >
            <MapPin
              className="
                h-3
                w-3
              "
            />

            {race.location}
          </p>
        </div>


        <button
          type="button"
          aria-label="Voir la course"
          onClick={
            onOpen
          }
          className="
            flex
            h-8
            w-8
            shrink-0
            items-center
            justify-center
            rounded-[8px]
            border
            border-emerald-500/20
            bg-emerald-500/[0.06]
            text-emerald-600
            dark:text-emerald-400
          "
        >
          <Eye
            className="
              h-4
              w-4
            "
          />
        </button>
      </div>


      <div
        className="
          mt-3
          grid
          grid-cols-2
          gap-x-6
          gap-y-3
          rounded-[10px]
          bg-[var(--oc-surface-muted)]
          px-3
          py-3
          dark:bg-[var(--oc-surface-muted)]
        "
      >
        <MobileMetric
          label="Distance"
          value={
            `${formatNumber(
              race.distanceKm,
            )} km`
          }
        />

        <MobileMetric
          label="Dénivelé"
          value={
            race.elevationGainM
              ? (
                  `${Math.round(
                    race.elevationGainM,
                  )} m`
                )
              : '—'
          }
        />

        {history ? (
          <MobileMetric
            label="Résultat"
            value={
              resultText(
                race,
              )
            }
          />
        ) : (
          <MobileMetric
            label="Objectif"
            value={
              race.targetTimeMinutes
                ? formatDuration(
                    race.targetTimeMinutes,
                  )
                : '—'
            }
          />
        )}

        <MobileMetric
          label="Statut"
          value={
            formatStatus(
              race.status,
            )
          }
        />
      </div>
    </article>
  )
}


function MobileMetric({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div>
      <p
        className="
          text-[8px]
          font-semibold
          uppercase
          tracking-[0.07em]
          text-[var(--oc-muted-soft)]
        "
      >
        {label}
      </p>

      <p
        className="
          mt-0.5
          text-[11px]
          font-semibold
          tabular-nums
          text-[var(--oc-text-secondary)]
          dark:text-[var(--oc-muted-soft)]
        "
      >
        {value}
      </p>
    </div>
  )
}


/* ============================================================
   PILLS / STATES
   ============================================================ */

function PriorityPill({
  priority,
}: {
  priority: RacePriority
}) {
  const primary =
    priority === 'primary'

  return (
    <span
      className={[
        (
          'inline-flex rounded-full '
          + 'px-2 py-0.5 '
          + 'text-[7.5px] '
          + 'font-bold '
          + 'uppercase '
          + 'tracking-[0.06em]'
        ),
        primary
          ? (
              'bg-emerald-500/[0.08] '
              + 'text-emerald-700 '
              + 'dark:text-emerald-400'
            )
          : (
              'bg-[var(--oc-surface-muted)] '
              + 'text-[var(--oc-muted)] '
              + 'dark:text-[var(--oc-muted-soft)]'
            ),
      ].join(' ')}
    >
      {
        primary
          ? 'A-Race'
          : 'B-Race'
      }
    </span>
  )
}


function RaceTypePill({
  type,
}: {
  type: RaceType
}) {
  return (
    <span
      className="
        inline-flex
        whitespace-nowrap
        rounded-full
        bg-[var(--oc-surface-muted)]
        px-2
        py-0.5
        text-[8px]
        font-semibold
        text-[var(--oc-muted)]
        dark:bg-[var(--oc-surface-muted)]
        dark:text-[var(--oc-muted-soft)]
      "
    >
      {
        formatRaceType(
          type,
        )
      }
    </span>
  )
}


function RaceResult({
  race,
}: {
  race: Race
}) {
  return (
    <span>
      {
        resultText(
          race,
        )
      }
    </span>
  )
}


/* ============================================================
   SECTION / STATES
   ============================================================ */

function SectionHeader({
  eyebrow,
  title,
  trailing,
}: {
  eyebrow: string
  title: string
  trailing?: React.ReactNode
}) {
  return (
    <div
      className="
        flex
        items-center
        justify-between
        gap-3
        border-b
        border-[var(--oc-border)]
        px-4
        py-3
        dark:border-[var(--oc-border)]
        sm:px-5
      "
    >
      <div>
        <p
          className="
            text-[8px]
            font-bold
            uppercase
            tracking-[0.1em]
            text-[var(--oc-muted-soft)]
          "
        >
          {eyebrow}
        </p>

        <h2
          className="
            mt-0.5
            text-[13px]
            font-semibold
            text-[var(--oc-text-secondary)]
            dark:text-[var(--oc-text-secondary)]
          "
        >
          {title}
        </h2>
      </div>

      {trailing}
    </div>
  )
}


function NoPrimaryRace({
  onAdd,
}: {
  onAdd: () => void
}) {
  return (
    <section
      className="
        flex
        flex-col
        items-center
        justify-center
        rounded-[15px]
        border
        border-dashed
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]
        px-5
        py-8
        text-center
        dark:border-[var(--oc-border)]
        dark:bg-[var(--oc-surface)]
      "
    >
      <Trophy
        className="
          h-6
          w-6
          text-emerald-500
        "
      />

      <h2
        className="
          mt-3
          text-[15px]
          font-semibold
          text-[var(--oc-text-secondary)]
          dark:text-[var(--oc-text-secondary)]
        "
      >
        Aucun objectif principal
      </h2>

      <p
        className="
          mt-1
          max-w-md
          text-[10.5px]
          leading-5
          text-[var(--oc-muted-soft)]
        "
      >
        Ajoute ta prochaine course cible pour que
        OpenCoach puisse structurer la préparation.
      </p>

      <button
        type="button"
        onClick={
          onAdd
        }
        className="
          mt-4
          inline-flex
          h-9
          items-center
          gap-1.5
          rounded-[8px]
          border
          border-emerald-500/25
          bg-emerald-500/[0.07]
          px-3
          text-[10px]
          font-semibold
          text-emerald-700
          dark:text-emerald-400
        "
      >
        <Plus
          className="
            h-3.5
            w-3.5
          "
        />

        Ajouter une course
      </button>
    </section>
  )
}


function EmptyState({
  title,
  description,
}: {
  title: string
  description: string
}) {
  return (
    <div
      className="
        px-4
        py-9
        text-center
      "
    >
      <Flag
        className="
          mx-auto
          h-5
          w-5
          text-[var(--oc-muted-soft)]
          dark:text-[var(--oc-text-secondary)]
        "
      />

      <p
        className="
          mt-2
          text-[11px]
          font-semibold
          text-[var(--oc-text-secondary)]
          dark:text-[var(--oc-muted-soft)]
        "
      >
        {title}
      </p>

      <p
        className="
          mt-1
          text-[9.5px]
          text-[var(--oc-muted-soft)]
        "
      >
        {description}
      </p>
    </div>
  )
}


function LoadingState() {
  return (
    <div
      className="
        flex
        min-h-[260px]
        items-center
        justify-center
        rounded-[14px]
        border
        border-[var(--oc-border)]
        bg-[var(--oc-surface)]
        dark:border-[var(--oc-border)]
        dark:bg-[var(--oc-surface)]
      "
    >
      <span
        className="
          h-5
          w-5
          animate-spin
          rounded-full
          border-2
          border-emerald-500/20
          border-t-emerald-500
        "
      />
    </div>
  )
}


function ErrorState({
  error,
  onRetry,
}: {
  error: string
  onRetry: () => void
}) {
  return (
    <div
      className="
        rounded-[12px]
        border
        border-red-500/15
        bg-red-50
        p-4
        dark:bg-red-500/[0.055]
      "
    >
      <p
        className="
          text-[11px]
          font-semibold
          text-red-600
          dark:text-red-400
        "
      >
        Impossible de charger les courses
      </p>

      <p
        className="
          mt-1
          text-[10px]
          text-red-500/70
        "
      >
        {error}
      </p>

      <button
        type="button"
        onClick={
          onRetry
        }
        className="
          mt-3
          inline-flex
          h-8
          items-center
          gap-1.5
          rounded-[8px]
          border
          border-red-500/20
          px-2.5
          text-[9px]
          font-semibold
          text-red-600
          dark:text-red-400
        "
      >
        <RefreshCw
          className="
            h-3
            w-3
          "
        />

        Réessayer
      </button>
    </div>
  )
}


/* ============================================================
   FORMATTERS
   ============================================================ */

function daysUntil(
  value: string,
): number {
  const target =
    new Date(
      `${value}T12:00:00`,
    )

  const today =
    new Date()

  const todayStart =
    new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
      12,
    )

  return Math.ceil(
    (
      target.getTime()
      - todayStart.getTime()
    )
    / 86_400_000,
  )
}


function formatDateLong(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    },
  ).format(
    new Date(
      `${value}T12:00:00`,
    ),
  )
}


function formatDateShort(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    },
  ).format(
    new Date(
      `${value}T12:00:00`,
    ),
  )
}


function formatRaceType(
  value: RaceType,
): string {
  const labels: Record<
    RaceType,
    string
  > = {
    trail: 'Trail',
    road: 'Route',
    ultra: 'Ultra',
    other: 'Autre',
  }

  return labels[value]
}


function formatNumber(
  value: number,
): string {
  return value.toLocaleString(
    'fr-FR',
    {
      maximumFractionDigits: 1,
    },
  )
}


function formatDuration(
  minutes: number,
): string {
  const total =
    Math.round(
      minutes,
    )

  const hours =
    Math.floor(
      total / 60,
    )

  const remaining =
    total % 60

  if (hours === 0) {
    return `${remaining} min`
  }

  return (
    `${hours} h `
    + remaining
      .toString()
      .padStart(
        2,
        '0',
      )
  )
}


function formatStatus(
  status: RaceStatus,
): string {
  const labels: Record<
    RaceStatus,
    string
  > = {
    planned: 'Prévue',
    completed: 'Terminée',
    abandoned: 'Abandon',
    not_participated:
      'Non-participation',
  }

  return labels[status]
}


function resultText(
  race: Race,
): string {
  if (
    race.status
    === 'completed'
  ) {
    if (
      race.actualTimeMinutes
      != null
    ) {
      return formatDuration(
        race.actualTimeMinutes,
      )
    }

    return 'Terminée'
  }

  return formatStatus(
    race.status,
  )
}
