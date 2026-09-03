import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Activity,
  ArrowDownUp,
  Clock3,
  Eye,
  FilterX,
  Gauge,
  Mountain,
  Route,
  Search,
} from 'lucide-react'

import {
  fetchActivities,
  type ActivitySummary,
} from '../../core/activities'


import {
  Modal,
} from '../../components/ui/Modal'

import {
  fetchTrainingSessions,
  validateTrainingSession,
} from '../../core/training/api'

import {
  TrainingDetails,
} from '../training/TrainingDetails'

import type {
  TrainingSession,
} from '../training/types'


type PeriodFilter =
  | '30d'
  | '3m'
  | '6m'
  | '1y'
  | 'all'


type SortOption =
  | 'recent'
  | 'oldest'
  | 'distance'
  | 'duration'
  | 'elevation'


export function ActivityPage() {
  const [
    activities,
    setActivities,
  ] = useState<ActivitySummary[]>([])

  const [
    loading,
    setLoading,
  ] = useState(true)

  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  )

  const [
    search,
    setSearch,
  ] = useState('')

  const [
    period,
    setPeriod,
  ] = useState<PeriodFilter>(
    '30d',
  )

  const [
    sport,
    setSport,
  ] = useState('all')

  const [
    sort,
    setSort,
  ] = useState<SortOption>(
    'recent',
  )



  const [
    trainingSessions,
    setTrainingSessions,
  ] = useState<TrainingSession[]>(
    [],
  )

  const [
    selectedSessionId,
    setSelectedSessionId,
  ] = useState<string | null>(
    null,
  )


  useEffect(() => {
    let mounted = true

    fetchActivities()
      .then((data) => {
        if (mounted) {
          setActivities(
            data,
          )
        }
      })
      .catch((reason: unknown) => {
        if (!mounted) {
          return
        }

        setError(
          reason instanceof Error
            ? reason.message
            : (
                'Impossible de charger '
                + 'les activités.'
              ),
        )
      })
      .finally(() => {
        if (mounted) {
          setLoading(
            false,
          )
        }
      })

    return () => {
      mounted = false
    }
  }, [])


  useEffect(() => {
    if (activities.length === 0) {
      setTrainingSessions(
        [],
      )

      return
    }

    let cancelled = false

    const timestamps =
      activities
        .map(
          (activity) =>
            new Date(
              activity.start_at_local
              ?? activity.start_at,
            ).getTime(),
        )
        .filter(
          (value) =>
            Number.isFinite(
              value,
            ),
        )

    if (timestamps.length === 0) {
      return
    }

    const start =
      formatIsoDate(
        new Date(
          Math.min(
            ...timestamps,
          ),
        ),
      )

    const end =
      formatIsoDate(
        new Date(
          Math.max(
            ...timestamps,
          ),
        ),
      )

    void fetchTrainingSessions(
      start,
      end,
    )
      .then((sessions) => {
        if (!cancelled) {
          setTrainingSessions(
            sessions,
          )
        }
      })
      .catch(() => {
        if (!cancelled) {
          setTrainingSessions(
            [],
          )
        }
      })

    return () => {
      cancelled = true
    }
  }, [
    activities,
  ])


  const sportOptions =
    useMemo(
      () => (
        Array.from(
          new Set(
            activities.map(
              (activity) =>
                activity.sport_type,
            ),
          ),
        ).sort(
          (left, right) =>
            formatSportType(
              left,
            ).localeCompare(
              formatSportType(
                right,
              ),
              'fr',
            ),
        )
      ),
      [
        activities,
      ],
    )


  const filteredActivities =
    useMemo(
      () => {
        const normalizedSearch =
          search
            .trim()
            .toLocaleLowerCase(
              'fr',
            )

        const cutoff =
          getPeriodCutoff(
            period,
          )

        const result =
          activities.filter(
            (activity) => {
              const activityDate =
                new Date(
                  activity.start_at_local
                  ?? activity.start_at,
                )

              if (
                cutoff
                && activityDate < cutoff
              ) {
                return false
              }

              if (
                sport !== 'all'
                && activity.sport_type
                  !== sport
              ) {
                return false
              }

              if (
                normalizedSearch
                && !(
                  activity.name
                    .toLocaleLowerCase(
                      'fr',
                    )
                    .includes(
                      normalizedSearch,
                    )
                  || formatSportType(
                    activity.sport_type,
                  )
                    .toLocaleLowerCase(
                      'fr',
                    )
                    .includes(
                      normalizedSearch,
                    )
                )
              ) {
                return false
              }

              return true
            },
          )

        return result.sort(
          (left, right) =>
            compareActivities(
              left,
              right,
              sort,
            ),
        )
      },
      [
        activities,
        period,
        search,
        sort,
        sport,
      ],
    )


  const summary =
    useMemo(
      () => {
        let distanceM = 0
        let durationSeconds = 0
        let elevationM = 0

        for (
          const activity
          of filteredActivities
        ) {
          distanceM +=
            activity.distance_m
            ?? 0

          durationSeconds +=
            activity.moving_time_seconds
            ?? activity.elapsed_time_seconds
            ?? 0

          elevationM +=
            activity.elevation_gain_m
            ?? 0
        }

        return {
          count:
            filteredActivities.length,
          distanceM,
          durationSeconds,
          elevationM,
        }
      },
      [
        filteredActivities,
      ],
    )


  const sessionsByActivityId =
    useMemo(
      () => {
        const result =
          new Map<
            string,
            TrainingSession
          >()

        for (
          const session
          of trainingSessions
        ) {
          if (
            session.activityId
          ) {
            result.set(
              session.activityId,
              session,
            )
          }
        }

        return result
      },
      [
        trainingSessions,
      ],
    )


  const selectedSession =
    selectedSessionId
      ? trainingSessions.find(
          (session) =>
            session.id
            === selectedSessionId,
        )
      : undefined


  const filtersAreActive = (
    search.trim() !== ''
    || period !== '30d'
    || sport !== 'all'
    || sort !== 'recent'
  )


  function resetFilters() {
    setSearch('')
    setPeriod('30d')
    setSport('all')
    setSort('recent')
  }


  return (
    <main
      className="
        min-h-screen
        bg-[#f5f7f6]
        dark:bg-[#0b1014]
      "
    >
      <div
        className="
          mx-auto
          max-w-[1240px]
          px-3
          py-4
          sm:px-5
          lg:py-5
        "
      >
        <header
          className="
            mb-4
          "
        >
          <p
            className="
              text-[10px]
              font-bold
              uppercase
              tracking-[0.13em]
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Historique
          </p>

          <h1
            className="
              mt-1
              text-[30px]
              font-bold
              tracking-[-0.04em]
              text-slate-950
              dark:text-white
            "
          >
            Activités
          </h1>

          <p
            className="
              mt-1
              text-[13px]
              text-slate-400
              dark:text-slate-500
            "
          >
            Historique des activités synchronisées
            et séances associées.
          </p>
        </header>


        {!loading && !error && (
          <ActivitySummaryCard
            count={
              summary.count
            }
            distanceM={
              summary.distanceM
            }
            durationSeconds={
              summary.durationSeconds
            }
            elevationM={
              summary.elevationM
            }
          />
        )}


        {/* =================================================
            FILTER BAR
            ================================================= */}

        {!loading && !error && (
          <section
            className="
              mt-3
              rounded-[13px]
              border
              border-black/[0.065]
              bg-white
              p-3
              dark:border-white/[0.065]
              dark:bg-[#151b1f]
            "
          >
            <div
              className="
                flex
                flex-col
                gap-2.5
                xl:flex-row
                xl:items-center
              "
            >
              <label
                className="
                  flex
                  h-10
                  min-w-0
                  flex-1
                  items-center
                  gap-2.5
                  rounded-[9px]
                  border
                  border-black/[0.07]
                  bg-slate-50
                  px-3
                  transition
                  focus-within:border-emerald-500/35
                  focus-within:bg-white
                  dark:border-white/[0.07]
                  dark:bg-white/[0.025]
                  dark:focus-within:bg-white/[0.035]
                "
              >
                <Search
                  className="
                    h-4
                    w-4
                    shrink-0
                    text-slate-400
                  "
                />

                <input
                  type="search"
                  value={search}
                  onChange={(event) =>
                    setSearch(
                      event.target.value,
                    )
                  }
                  placeholder="Rechercher une activité…"
                  className="
                    min-w-0
                    flex-1
                    bg-transparent
                    text-[12px]
                    text-slate-700
                    outline-none
                    placeholder:text-slate-400
                    dark:text-slate-200
                  "
                />
              </label>


              <div
                className="
                  grid
                  grid-cols-2
                  gap-2
                  sm:grid-cols-3
                  xl:flex
                "
              >
                <select
                  value={period}
                  onChange={(event) => {
                    setPeriod(
                      event.target
                        .value as PeriodFilter,
                    )
                  }}
                  className="
                    h-10
                    rounded-[9px]
                    border
                    border-black/[0.07]
                    bg-slate-50
                    px-3
                    text-[11px]
                    font-medium
                    text-slate-600
                    outline-none
                    transition
                    focus:border-emerald-500/35
                    dark:border-white/[0.07]
                    dark:bg-white/[0.025]
                    dark:text-slate-300
                  "
                  aria-label="Période"
                >
                  <option value="30d">
                    30 jours
                  </option>

                  <option value="3m">
                    3 mois
                  </option>

                  <option value="6m">
                    6 mois
                  </option>

                  <option value="1y">
                    1 an
                  </option>

                  <option value="all">
                    Toutes les dates
                  </option>
                </select>


                <select
                  value={sport}
                  onChange={(event) =>
                    setSport(
                      event.target.value,
                    )
                  }
                  className="
                    h-10
                    min-w-0
                    rounded-[9px]
                    border
                    border-black/[0.07]
                    bg-slate-50
                    px-3
                    text-[11px]
                    font-medium
                    text-slate-600
                    outline-none
                    transition
                    focus:border-emerald-500/35
                    dark:border-white/[0.07]
                    dark:bg-white/[0.025]
                    dark:text-slate-300
                  "
                  aria-label="Sport"
                >
                  <option value="all">
                    Tous les sports
                  </option>

                  {sportOptions.map(
                    sportType => (
                      <option
                        key={sportType}
                        value={sportType}
                      >
                        {
                          formatSportType(
                            sportType,
                          )
                        }
                      </option>
                    ),
                  )}
                </select>


                <select
                  value={sort}
                  onChange={(event) => {
                    setSort(
                      event.target
                        .value as SortOption,
                    )
                  }}
                  className="
                    col-span-2
                    h-10
                    rounded-[9px]
                    border
                    border-black/[0.07]
                    bg-slate-50
                    px-3
                    text-[11px]
                    font-medium
                    text-slate-600
                    outline-none
                    transition
                    focus:border-emerald-500/35
                    sm:col-span-1
                    dark:border-white/[0.07]
                    dark:bg-white/[0.025]
                    dark:text-slate-300
                  "
                  aria-label="Tri"
                >
                  <option value="recent">
                    Plus récentes
                  </option>

                  <option value="oldest">
                    Plus anciennes
                  </option>

                  <option value="distance">
                    Plus longues
                  </option>

                  <option value="duration">
                    Durée
                  </option>

                  <option value="elevation">
                    Dénivelé
                  </option>
                </select>
              </div>


              {filtersAreActive && (
                <button
                  type="button"
                  onClick={
                    resetFilters
                  }
                  className="
                    flex
                    h-10
                    shrink-0
                    items-center
                    justify-center
                    gap-1.5
                    rounded-[9px]
                    border
                    border-black/[0.06]
                    px-3
                    text-[10px]
                    font-semibold
                    text-slate-400
                    transition
                    hover:bg-slate-50
                    hover:text-slate-700
                    dark:border-white/[0.06]
                    dark:hover:bg-white/[0.035]
                    dark:hover:text-slate-200
                  "
                >
                  <FilterX
                    className="
                      h-3.5
                      w-3.5
                    "
                  />

                  Réinitialiser
                </button>
              )}
            </div>


            <div
              className="
                mt-3
                flex
                flex-wrap
                items-center
                justify-between
                gap-2
                border-t
                border-black/[0.055]
                pt-2.5
                text-[10px]
                text-slate-400
                dark:border-white/[0.055]
                dark:text-slate-500
              "
            >
              <span>
                {
                  filteredActivities.length
                }
                {' activité'}
                {
                  filteredActivities.length
                  > 1
                    ? 's'
                    : ''
                }
                {' affichée'}
                {
                  filteredActivities.length
                  > 1
                    ? 's'
                    : ''
                }
                {' sur '}
                {activities.length}
              </span>

              <span
                className="
                  flex
                  items-center
                  gap-1.5
                "
              >
                <ArrowDownUp
                  className="
                    h-3
                    w-3
                  "
                />

                {
                  formatSortLabel(
                    sort,
                  )
                }
              </span>
            </div>
          </section>
        )}


        {/* =================================================
            ACTIVITIES
            ================================================= */}

        <section
          className="
            mt-3
            overflow-hidden
            rounded-[13px]
            border
            border-black/[0.065]
            bg-white
            dark:border-white/[0.065]
            dark:bg-[#151b1f]
          "
        >
          {loading && (
            <div
              className="
                flex
                min-h-[240px]
                items-center
                justify-center
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
          )}


          {!loading && error && (
            <div
              className="
                m-3
                rounded-[10px]
                border
                border-red-500/15
                bg-red-50
                px-3
                py-3
                text-[11px]
                text-red-600
                dark:bg-red-500/[0.06]
                dark:text-red-400
              "
            >
              {error}
            </div>
          )}


          {!loading
            && !error
            && activities.length === 0
            && (
              <EmptyActivityState
                title="Aucune activité disponible"
                description="
                  Les activités synchronisées
                  apparaîtront ici.
                "
              />
            )}


          {!loading
            && !error
            && activities.length > 0
            && filteredActivities.length === 0
            && (
              <div
                className="
                  px-4
                  py-10
                  text-center
                "
              >
                <p
                  className="
                    text-[12px]
                    font-semibold
                    text-slate-700
                    dark:text-slate-300
                  "
                >
                  Aucun résultat
                </p>

                <p
                  className="
                    mt-1
                    text-[10px]
                    text-slate-400
                  "
                >
                  Aucune activité ne correspond
                  aux filtres sélectionnés.
                </p>

                <button
                  type="button"
                  onClick={
                    resetFilters
                  }
                  className="
                    mt-3
                    rounded-[8px]
                    border
                    border-emerald-500/25
                    bg-emerald-500/[0.06]
                    px-3
                    py-1.5
                    text-[10px]
                    font-semibold
                    text-emerald-700
                    transition
                    hover:bg-emerald-500/[0.10]
                    dark:text-emerald-400
                  "
                >
                  Réinitialiser
                </button>
              </div>
            )}


          {!loading
            && !error
            && filteredActivities.length > 0
            && (
              <>
                {/* TABLE DESKTOP */}

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
                        bg-slate-50/70
                        dark:bg-white/[0.018]
                      "
                    >
                      <tr
                        className="
                          border-b
                          border-black/[0.055]
                          dark:border-white/[0.055]
                        "
                      >
                        <ActivityTableHeader>
                          Date
                        </ActivityTableHeader>

                        <ActivityTableHeader>
                          Activité
                        </ActivityTableHeader>

                        <ActivityTableHeader>
                          Sport
                        </ActivityTableHeader>

                        <ActivityTableHeader
                          align="right"
                        >
                          Distance
                        </ActivityTableHeader>

                        <ActivityTableHeader
                          align="right"
                        >
                          Durée
                        </ActivityTableHeader>

                        <ActivityTableHeader
                          align="right"
                          hiddenOnTablet
                        >
                          Allure
                        </ActivityTableHeader>

                        <ActivityTableHeader
                          align="right"
                          hiddenOnTablet
                        >
                          D+
                        </ActivityTableHeader>

                        <ActivityTableHeader
                          align="right"
                        >
                          Action
                        </ActivityTableHeader>
                      </tr>
                    </thead>

                    <tbody>
                      {filteredActivities.map(
                        activity => (
                          <ActivityDesktopRow
                            key={
                              `${activity.provider}-`
                              + activity
                                .provider_activity_id
                            }
                            activity={
                              activity
                            }
                            session={
                              activity.id
                                ? sessionsByActivityId.get(
                                    activity.id,
                                  )
                                : undefined
                            }
                            onOpenSession={
                              setSelectedSessionId
                            }
                          />
                        ),
                      )}
                    </tbody>
                  </table>
                </div>


                {/* MOBILE */}

                <div
                  className="
                    divide-y
                    divide-black/[0.055]
                    dark:divide-white/[0.055]
                    md:hidden
                  "
                >
                  {filteredActivities.map(
                    activity => (
                      <ActivityMobileCard
                        key={
                          `${activity.provider}-`
                          + activity
                            .provider_activity_id
                        }
                        activity={
                          activity
                        }
                        session={
                          activity.id
                            ? sessionsByActivityId.get(
                                activity.id,
                              )
                            : undefined
                        }
                        onOpenSession={
                          setSelectedSessionId
                        }
                      />
                    ),
                  )}
                </div>
              </>
            )}
        </section>
      </div>


      {selectedSession && (
        <Modal
          title={
            selectedSession.title
          }
          open
          onClose={() =>
            setSelectedSessionId(
              null,
            )
          }
        >
          <TrainingDetails
            session={
              selectedSession
            }
            onValidateSession={async (
              activityId,
            ) => {
              const result =
                await validateTrainingSession(
                  selectedSession.id,
                  activityId,
                )

              setTrainingSessions(
                current =>
                  current.map(
                    session =>
                      session.id
                      === result.session.id
                        ? result.session
                        : session,
                  ),
              )

              return result.analysis
            }}
          />
        </Modal>
      )}
    </main>
  )
}



function ActivitySummaryCard({
  count,
  distanceM,
  durationSeconds,
  elevationM,
}: {
  count: number
  distanceM: number
  durationSeconds: number
  elevationM: number
}) {
  const averagePace =
    calculatePaceSecondsPerKm(
      distanceM,
      durationSeconds,
    )

  return (
    <section
      className="
        overflow-hidden
        rounded-[13px]
        border
        border-black/[0.065]
        bg-white
        dark:border-white/[0.065]
        dark:bg-[#151b1f]
      "
    >
      <div
        className="
          grid
          grid-cols-2
          sm:grid-cols-5
        "
      >
        <SummaryMetric
          icon={
            <Activity
              className="
                h-4
                w-4
              "
            />
          }
          value={
            count.toLocaleString(
              'fr-FR',
            )
          }
          label="Activités"
        />

        <SummaryMetric
          icon={
            <Route
              className="
                h-4
                w-4
              "
            />
          }
          value={
            formatSummaryDistance(
              distanceM,
            )
          }
          label="Distance"
        />

        <SummaryMetric
          icon={
            <Clock3
              className="
                h-4
                w-4
              "
            />
          }
          value={
            formatSummaryDuration(
              durationSeconds,
            )
          }
          label="Temps"
        />

        <SummaryMetric
          icon={
            <Mountain
              className="
                h-4
                w-4
              "
            />
          }
          value={
            formatSummaryElevation(
              elevationM,
            )
          }
          label="Dénivelé"
        />

        <SummaryMetric
          icon={
            <Gauge
              className="
                h-4
                w-4
              "
            />
          }
          value={
            averagePace == null
              ? '—'
              : (
                  formatPaceSeconds(
                    averagePace,
                  )
                  + '/km'
                )
          }
          label="Allure moy."
          wideOnMobile
        />
      </div>
    </section>
  )
}


function SummaryMetric({
  icon,
  value,
  label,
  wideOnMobile = false,
}: {
  icon: React.ReactNode
  value: string
  label: string
  wideOnMobile?: boolean
}) {
  return (
    <div
      className={[
        (
          'flex min-w-0 '
          + 'items-center gap-2.5 '
          + 'border-black/[0.055] '
          + 'px-3 py-3 '
          + 'dark:border-white/[0.055] '
          + 'sm:border-r '
          + 'sm:last:border-r-0'
        ),
        wideOnMobile
          ? (
              'col-span-2 '
              + 'border-t '
              + 'sm:col-span-1 '
              + 'sm:border-t-0'
            )
          : (
              'border-b '
              + 'odd:border-r '
              + 'sm:border-b-0'
            ),
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
          bg-emerald-50
          text-emerald-600
          dark:bg-emerald-500/[0.07]
          dark:text-emerald-400
        "
      >
        {icon}
      </div>

      <div className="min-w-0">
        <p
          className="
            truncate
            text-[16px]
            font-bold
            tracking-[-0.02em]
            tabular-nums
            text-slate-850
            dark:text-slate-200
          "
        >
          {value}
        </p>

        <p
          className="
            mt-0.5
            text-[8px]
            font-semibold
            uppercase
            tracking-[0.07em]
            text-slate-400
            dark:text-slate-500
          "
        >
          {label}
        </p>
      </div>
    </div>
  )
}


function ActivityTableHeader({
  children,
  align = 'left',
  hiddenOnTablet = false,
}: {
  children: React.ReactNode
  align?: 'left' | 'right'
  hiddenOnTablet?: boolean
}) {
  return (
    <th
      className={[
        (
          'px-3 py-2.5 '
          + 'text-[8.5px] '
          + 'font-bold '
          + 'uppercase '
          + 'tracking-[0.08em] '
          + 'text-slate-400 '
          + 'dark:text-slate-500'
        ),
        align === 'right'
          ? 'text-right'
          : 'text-left',
        hiddenOnTablet
          ? 'hidden lg:table-cell'
          : '',
      ].join(' ')}
    >
      {children}
    </th>
  )
}


function ActivityDesktopRow({
  activity,
  session,
  onOpenSession,
}: {
  activity: ActivitySummary
  session?: TrainingSession
  onOpenSession: (
    sessionId: string,
  ) => void
}) {
  return (
    <tr
      className="
        group
        border-b
        border-black/[0.045]
        transition-colors
        last:border-b-0
        hover:bg-slate-50/80
        dark:border-white/[0.045]
        dark:hover:bg-white/[0.018]
      "
    >
      <td
        className="
          whitespace-nowrap
          px-3
          py-3
        "
      >
        <p
          className="
            text-[11px]
            font-semibold
            text-slate-700
            dark:text-slate-300
          "
        >
          {
            formatDate(
              activity.start_at_local
              ?? activity.start_at,
            )
          }
        </p>

        <p
          className="
            mt-0.5
            text-[9px]
            text-slate-400
            dark:text-slate-500
          "
        >
          {
            formatTime(
              activity.start_at_local
              ?? activity.start_at,
            )
          }
        </p>
      </td>


      <td
        className="
          max-w-[310px]
          px-3
          py-3
        "
      >
        <p
          className="
            truncate
            text-[12px]
            font-semibold
            text-slate-800
            dark:text-slate-200
          "
          title={activity.name}
        >
          {activity.name}
        </p>

        <p
          className="
            mt-0.5
            text-[9px]
            text-slate-400
            dark:text-slate-500
          "
        >
          {activity.provider}
        </p>
      </td>


      <td
        className="
          px-3
          py-3
        "
      >
        <SportPill
          sport={
            activity.sport_type
          }
        />
      </td>


      <ActivityNumberCell>
        {
          formatDistance(
            activity.distance_m,
          )
        }
      </ActivityNumberCell>

      <ActivityNumberCell>
        {
          formatDuration(
            activity.moving_time_seconds
            ?? activity.elapsed_time_seconds,
          )
        }
      </ActivityNumberCell>

      <ActivityNumberCell
        hiddenOnTablet
      >
        {
          formatPace(
            activity.distance_m,
            activity.moving_time_seconds,
          )
        }
      </ActivityNumberCell>

      <ActivityNumberCell
        hiddenOnTablet
      >
        {
          formatElevation(
            activity.elevation_gain_m,
          )
        }
      </ActivityNumberCell>


      <td
        className="
          px-3
          py-3
          text-right
        "
      >
        {session ? (
          <button
            type="button"
            onClick={() =>
              onOpenSession(
                session.id,
              )
            }
            aria-label="Voir la séance"
            title="Voir la séance"
            className="
              inline-flex
              h-8
              items-center
              justify-center
              rounded-[8px]
              border
              border-emerald-500/25
              bg-emerald-500/[0.06]
              w-8
              px-0
              font-semibold
              text-emerald-700
              transition
              hover:border-emerald-500/40
              hover:bg-emerald-500/[0.10]
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
        ) : (
          <span
            className="
              text-[9px]
              font-medium
              text-slate-300
              dark:text-slate-600
            "
          >
            Non associée
          </span>
        )}
      </td>
    </tr>
  )
}


function ActivityNumberCell({
  children,
  hiddenOnTablet = false,
}: {
  children: React.ReactNode
  hiddenOnTablet?: boolean
}) {
  return (
    <td
      className={[
        (
          'whitespace-nowrap '
          + 'px-3 py-3 '
          + 'text-right '
          + 'text-[11px] '
          + 'font-medium '
          + 'tabular-nums '
          + 'text-slate-600 '
          + 'dark:text-slate-400'
        ),
        hiddenOnTablet
          ? 'hidden lg:table-cell'
          : '',
      ].join(' ')}
    >
      {children}
    </td>
  )
}


function ActivityMobileCard({
  activity,
  session,
  onOpenSession,
}: {
  activity: ActivitySummary
  session?: TrainingSession
  onOpenSession: (
    sessionId: string,
  ) => void
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
            <p
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.08em]
                text-slate-400
                dark:text-slate-500
              "
            >
              {
                formatDate(
                  activity.start_at_local
                  ?? activity.start_at,
                )
              }
              {' · '}
              {
                formatTime(
                  activity.start_at_local
                  ?? activity.start_at,
                )
              }
            </p>

            <SportPill
              sport={
                activity.sport_type
              }
            />
          </div>

          <h2
            className="
              mt-2
              truncate
              text-[15px]
              font-semibold
              tracking-[-0.02em]
              text-slate-850
              dark:text-slate-200
            "
          >
            {activity.name}
          </h2>

          <p
            className="
              mt-0.5
              text-[9.5px]
              text-slate-400
            "
          >
            {activity.provider}
          </p>
        </div>
      </div>


      <div
        className="
          mt-3
          grid
          grid-cols-2
          gap-x-5
          gap-y-3
          rounded-[10px]
          bg-slate-50
          px-3
          py-3
          dark:bg-white/[0.022]
        "
      >
        <MobileMetric
          label="Distance"
          value={
            formatDistance(
              activity.distance_m,
            )
          }
        />

        <MobileMetric
          label="Durée"
          value={
            formatDuration(
              activity.moving_time_seconds
              ?? activity.elapsed_time_seconds,
            )
          }
        />

        <MobileMetric
          label="Allure"
          value={
            formatPace(
              activity.distance_m,
              activity.moving_time_seconds,
            )
          }
        />

        <MobileMetric
          label="Dénivelé"
          value={
            formatElevation(
              activity.elevation_gain_m,
            )
          }
        />
      </div>


      <div
        className="
          mt-3
          flex
          items-center
          justify-between
          gap-3
        "
      >
        <div>
          <p
            className="
              text-[8px]
              font-semibold
              uppercase
              tracking-[0.07em]
              text-slate-400
            "
          >
            Séance Coach
          </p>

          <p
            className={[
              (
                'mt-0.5 text-[10px] '
                + 'font-medium'
              ),
              session
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
            {
              session
                ? 'Associée'
                : 'Non associée'
            }
          </p>
        </div>


        {session && (
          <button
            type="button"
            onClick={() =>
              onOpenSession(
                session.id,
              )
            }
            className="
              inline-flex
              h-8
              items-center
              justify-center
              rounded-[8px]
              border
              border-emerald-500/25
              bg-emerald-500/[0.07]
              px-3
              text-[10px]
              font-semibold
              text-emerald-700
              transition
              active:scale-[0.98]
              dark:text-emerald-400
            "
          >
            Voir la séance
            <span className="ml-1.5">
              →
            </span>
          </button>
        )}
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
          text-slate-400
          dark:text-slate-500
        "
      >
        {label}
      </p>

      <p
        className="
          mt-0.5
          text-[12px]
          font-semibold
          tabular-nums
          text-slate-700
          dark:text-slate-300
        "
      >
        {value}
      </p>
    </div>
  )
}


function SportPill({
  sport,
}: {
  sport: string
}) {
  return (
    <span
      className="
        inline-flex
        whitespace-nowrap
        rounded-full
        bg-slate-100
        px-2
        py-0.5
        text-[8px]
        font-semibold
        text-slate-500
        dark:bg-white/[0.045]
        dark:text-slate-400
      "
    >
      {
        formatSportType(
          sport,
        )
      }
    </span>
  )
}


function EmptyActivityState({
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
        py-10
        text-center
      "
    >
      <Activity
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
          text-[12px]
          font-semibold
          text-slate-600
          dark:text-slate-300
        "
      >
        {title}
      </p>

      <p
        className="
          mt-1
          text-[10px]
          text-slate-400
        "
      >
        {description}
      </p>
    </div>
  )
}


function formatIsoDate(
  value: Date,
): string {
  const year =
    value.getFullYear()

  const month =
    String(
      value.getMonth() + 1,
    ).padStart(
      2,
      '0',
    )

  const day =
    String(
      value.getDate(),
    ).padStart(
      2,
      '0',
    )

  return (
    `${year}-${month}-${day}`
  )
}


function getPeriodCutoff(
  period: PeriodFilter,
): Date | null {
  if (period === 'all') {
    return null
  }

  const now =
    new Date()

  const cutoff =
    new Date(
      now,
    )

  if (period === '30d') {
    cutoff.setDate(
      cutoff.getDate() - 30,
    )
  }

  if (period === '3m') {
    cutoff.setMonth(
      cutoff.getMonth() - 3,
    )
  }

  if (period === '6m') {
    cutoff.setMonth(
      cutoff.getMonth() - 6,
    )
  }

  if (period === '1y') {
    cutoff.setFullYear(
      cutoff.getFullYear() - 1,
    )
  }

  return cutoff
}


function compareActivities(
  left: ActivitySummary,
  right: ActivitySummary,
  sort: SortOption,
): number {
  if (sort === 'distance') {
    return (
      (right.distance_m ?? 0)
      - (left.distance_m ?? 0)
    )
  }

  if (sort === 'duration') {
    return (
      getActivityDuration(
        right,
      )
      - getActivityDuration(
          left,
        )
    )
  }

  if (sort === 'elevation') {
    return (
      (right.elevation_gain_m ?? 0)
      - (left.elevation_gain_m ?? 0)
    )
  }

  const leftDate =
    new Date(
      left.start_at_local
      ?? left.start_at,
    ).getTime()

  const rightDate =
    new Date(
      right.start_at_local
      ?? right.start_at,
    ).getTime()

  if (sort === 'oldest') {
    return (
      leftDate
      - rightDate
    )
  }

  return (
    rightDate
    - leftDate
  )
}


function getActivityDuration(
  activity: ActivitySummary,
): number {
  return (
    activity.moving_time_seconds
    ?? activity.elapsed_time_seconds
    ?? 0
  )
}


function formatSortLabel(
  sort: SortOption,
): string {
  const labels: Record<
    SortOption,
    string
  > = {
    recent: 'Plus récentes',
    oldest: 'Plus anciennes',
    distance: 'Distance décroissante',
    duration: 'Durée décroissante',
    elevation: 'Dénivelé décroissant',
  }

  return labels[sort]
}


function formatDate(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: '2-digit',
      month: '2-digit',
      year: '2-digit',
    },
  ).format(
    new Date(
      value,
    ),
  )
}


function formatTime(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      hour: '2-digit',
      minute: '2-digit',
    },
  ).format(
    new Date(
      value,
    ),
  )
}


function formatDistance(
  distanceM: number | null | undefined,
): string {
  if (distanceM == null) {
    return '—'
  }

  return (
    `${(
      distanceM / 1000
    ).toLocaleString(
      'fr-FR',
      {
        minimumFractionDigits: 1,
        maximumFractionDigits: 2,
      },
    )} km`
  )
}


function formatSummaryDistance(
  distanceM: number,
): string {
  return (
    `${(
      distanceM / 1000
    ).toLocaleString(
      'fr-FR',
      {
        minimumFractionDigits: 1,
        maximumFractionDigits: 1,
      },
    )} km`
  )
}


function formatDuration(
  seconds: number | null | undefined,
): string {
  if (seconds == null) {
    return '—'
  }

  const rounded =
    Math.round(
      seconds,
    )

  const hours =
    Math.floor(
      rounded / 3600,
    )

  const minutes =
    Math.floor(
      (
        rounded
        % 3600
      ) / 60,
    )

  const remainingSeconds =
    rounded
    % 60

  if (hours > 0) {
    return (
      `${hours}:`
      + minutes
        .toString()
        .padStart(
          2,
          '0',
        )
      + ':'
      + remainingSeconds
        .toString()
        .padStart(
          2,
          '0',
        )
    )
  }

  return (
    `${minutes}:`
    + remainingSeconds
      .toString()
      .padStart(
        2,
        '0',
      )
  )
}


function formatSummaryDuration(
  seconds: number,
): string {
  const totalMinutes =
    Math.round(
      seconds / 60,
    )

  const hours =
    Math.floor(
      totalMinutes / 60,
    )

  const minutes =
    totalMinutes % 60

  if (hours === 0) {
    return `${minutes} min`
  }

  return (
    `${hours} h `
    + minutes
      .toString()
      .padStart(
        2,
        '0',
      )
  )
}


function formatPace(
  distanceM: number | null | undefined,
  movingTimeSeconds:
    number | null | undefined,
): string {
  const pace =
    calculatePaceSecondsPerKm(
      distanceM,
      movingTimeSeconds,
    )

  if (pace == null) {
    return '—'
  }

  return (
    `${formatPaceSeconds(
      pace,
    )}/km`
  )
}


function calculatePaceSecondsPerKm(
  distanceM: number | null | undefined,
  movingTimeSeconds:
    number | null | undefined,
): number | null {
  if (
    distanceM == null
    || movingTimeSeconds == null
    || distanceM <= 0
    || movingTimeSeconds <= 0
  ) {
    return null
  }

  return (
    movingTimeSeconds
    / (
      distanceM / 1000
    )
  )
}


function formatPaceSeconds(
  value: number,
): string {
  const rounded =
    Math.round(
      value,
    )

  const minutes =
    Math.floor(
      rounded / 60,
    )

  const seconds =
    rounded % 60

  return (
    `${minutes}:`
    + seconds
      .toString()
      .padStart(
        2,
        '0',
      )
  )
}


function formatElevation(
  elevationM: number | null | undefined,
): string {
  if (elevationM == null) {
    return '—'
  }

  return (
    `${Math.round(
      elevationM,
    ).toLocaleString(
      'fr-FR',
    )} m`
  )
}


function formatSummaryElevation(
  elevationM: number,
): string {
  return (
    `${Math.round(
      elevationM,
    ).toLocaleString(
      'fr-FR',
    )} m`
  )
}


function formatSportType(
  sportType: string,
): string {
  const labels: Record<string, string> = {
    Run: 'Course à pied',
    TrailRun: 'Trail',
    Walk: 'Marche',
    Hike: 'Randonnée',
    Ride: 'Vélo',
    MountainBikeRide: 'VTT',
    GravelRide: 'Gravel',
    VirtualRide: 'Vélo virtuel',
    Swim: 'Natation',
    Soccer: 'Football',
    Workout: 'Entraînement',
  }

  return (
    labels[sportType]
    ?? sportType
  )
}
