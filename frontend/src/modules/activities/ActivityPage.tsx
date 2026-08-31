import {
  useEffect,
  useMemo,
  useState,
} from 'react'

import {
  Activity,
  ArrowDownUp,
  Clock3,
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
    <main className="min-h-screen bg-base-200">
      <div
        className="
          mx-auto
          max-w-7xl
          px-4
          py-6
          sm:px-6
          lg:py-8
        "
      >
        <header className="mb-5">
          <h1
            className="
              text-3xl
              font-bold
              tracking-tight
              text-base-content
            "
          >
            Activités
          </h1>

          <p
            className="
              mt-1
              text-sm
              text-base-content/60
            "
          >
            Historique des activités synchronisées.
          </p>
        </header>


        {!loading && !error && (
          <>
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


            <div
              className="
                mt-4
                rounded-2xl
                border
                border-base-300
                bg-base-100
                p-4
                shadow-sm
              "
            >
              <div
                className="
                  flex
                  flex-col
                  gap-3
                  xl:flex-row
                  xl:items-center
                "
              >
                <label
                  className="
                    input
                    input-bordered
                    flex
                    min-w-0
                    flex-1
                    items-center
                    gap-2
                  "
                >
                  <Search
                    size={16}
                    className="
                      shrink-0
                      text-base-content/40
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
                    placeholder="Rechercher une activité..."
                    className="
                      min-w-0
                      grow
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
                        event.target.value as PeriodFilter,
                      )
                    }}
                    className="
                      select
                      select-bordered
                      w-full
                      xl:w-auto
                    "
                    aria-label="Période"
                  >
                    <option value="30d">
                      30 derniers jours
                    </option>

                    <option value="3m">
                      3 derniers mois
                    </option>

                    <option value="6m">
                      6 derniers mois
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
                      select
                      select-bordered
                      w-full
                      xl:w-auto
                    "
                    aria-label="Sport"
                  >
                    <option value="all">
                      Tous les sports
                    </option>

                    {sportOptions.map(
                      (sportType) => (
                        <option
                          key={
                            sportType
                          }
                          value={
                            sportType
                          }
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
                        event.target.value as SortOption,
                      )
                    }}
                    className="
                      select
                      select-bordered
                      col-span-2
                      w-full
                      sm:col-span-1
                      xl:w-auto
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
                      btn
                      btn-ghost
                      btn-sm
                      gap-2
                      xl:shrink-0
                    "
                  >
                    <FilterX
                      size={15}
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
                  border-base-300
                  pt-3
                  text-xs
                  text-base-content/45
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
                  {
                    activities.length
                  }
                </span>

                <span
                  className="
                    flex
                    items-center
                    gap-1
                  "
                >
                  <ArrowDownUp
                    size={13}
                  />

                  {
                    formatSortLabel(
                      sort,
                    )
                  }
                </span>
              </div>
            </div>
          </>
        )}


        <div
          className="
            mt-4
            overflow-hidden
            rounded-2xl
            border
            border-base-300
            bg-base-100
            shadow-sm
          "
        >
          {loading && (
            <div
              className="
                flex
                justify-center
                py-12
              "
            >
              <span
                className="
                  loading
                  loading-spinner
                  loading-md
                "
              />
            </div>
          )}


          {!loading && error && (
            <div
              className="
                alert
                alert-error
                m-4
              "
            >
              {error}
            </div>
          )}


          {!loading
            && !error
            && activities.length === 0
            && (
              <div
                className="
                  py-12
                  text-center
                  text-sm
                  text-base-content/60
                "
              >
                Aucune activité disponible.
              </div>
            )}


          {!loading
            && !error
            && activities.length > 0
            && filteredActivities.length === 0
            && (
              <div
                className="
                  py-12
                  text-center
                "
              >
                <p
                  className="
                    text-sm
                    font-medium
                    text-base-content
                  "
                >
                  Aucune activité ne correspond
                  aux filtres.
                </p>

                <button
                  type="button"
                  onClick={
                    resetFilters
                  }
                  className="
                    btn
                    btn-ghost
                    btn-sm
                    mt-3
                  "
                >
                  Réinitialiser les filtres
                </button>
              </div>
            )}


          {!loading
            && !error
            && filteredActivities.length > 0
            && (
              <div className="overflow-x-auto">
                <table className="table table-xs sm:table-sm">
                  <thead
                    className="
                      bg-base-200/60
                    "
                  >
                    <tr>
                      <th>Date</th>

                      <th>
                        Activité
                      </th>

                      <th className="hidden sm:table-cell">
                        Sport
                      </th>

                      <th className="text-right">
                        Distance
                      </th>

                      <th className="hidden sm:table-cell text-right">
                        Durée
                      </th>

                      <th className="hidden lg:table-cell text-right">
                        Allure
                      </th>

                      <th className="hidden lg:table-cell text-right">
                        D+
                      </th>

                      <th className="text-right">
                        Séance
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {filteredActivities.map(
                      (activity) => (
                        <ActivityRow
                          key={
                            `${activity.provider}-`
                            + activity.provider_activity_id
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
            )}
        </div>
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
                (current) =>
                  current.map(
                    (session) =>
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
        rounded-2xl
        border
        border-base-300
        bg-base-100
        shadow-sm
      "
    >
      <div
        className="
          flex
          items-center
          gap-2
          border-b
          border-base-300
          px-4
          py-2.5
        "
      >
        <Activity
          size={16}
          className="text-primary"
        />

        <h2
          className="
            text-sm
            font-semibold
            text-base-content
          "
        >
          Synthèse
        </h2>

        <span
          className="
            text-xs
            text-base-content/40
          "
        >
          des activités affichées
        </span>
      </div>

      <div
        className="
          grid
          grid-cols-2
          divide-x
          divide-y
          divide-base-300
          sm:grid-cols-5
          sm:divide-y-0
        "
      >
        <SummaryMetric
          icon={
            <Activity
              size={15}
            />
          }
          value={
            count.toLocaleString(
              'fr-FR',
            )
          }
          label="activités"
        />

        <SummaryMetric
          icon={
            <Route
              size={15}
            />
          }
          value={
            formatSummaryDistance(
              distanceM,
            )
          }
          label="distance"
        />

        <SummaryMetric
          icon={
            <Clock3
              size={15}
            />
          }
          value={
            formatSummaryDuration(
              durationSeconds,
            )
          }
          label="durée"
        />

        <SummaryMetric
          icon={
            <Mountain
              size={15}
            />
          }
          value={
            formatSummaryElevation(
              elevationM,
            )
          }
          label="dénivelé"
        />

        <SummaryMetric
          icon={
            <Gauge
              size={15}
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
          label="allure moy."
        />
      </div>
    </section>
  )
}


function SummaryMetric({
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
        min-w-0
        items-center
        gap-3
        px-4
        py-3
      "
    >
      <div
        className="
          shrink-0
          text-base-content/35
        "
      >
        {icon}
      </div>

      <div className="min-w-0">
        <p
          className="
            truncate
            text-base
            font-bold
            text-base-content
          "
        >
          {value}
        </p>

        <p
          className="
            text-[11px]
            uppercase
            tracking-wide
            text-base-content/40
          "
        >
          {label}
        </p>
      </div>
    </div>
  )
}


function ActivityRow({
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
        transition-colors
        hover:bg-base-200/40
      "
    >
      <td className="whitespace-nowrap">
        <div
          className="
            font-medium
            text-base-content
          "
        >
          {
            formatDate(
              activity.start_at_local
              ?? activity.start_at,
            )
          }
        </div>

        <div
          className="
            text-[11px]
            text-base-content/40
          "
        >
          {
            formatTime(
              activity.start_at_local
              ?? activity.start_at,
            )
          }
        </div>
      </td>


      <td
        className="
          min-w-[150px]
          max-w-[220px]
          sm:min-w-[200px]
          sm:max-w-[320px]
          lg:max-w-[360px]
        "
      >
        <div
          className="
            truncate
            font-medium
            text-base-content
          "
          title={
            activity.name
          }
        >
          {activity.name}
        </div>

        <div
          className="
            mt-0.5
            text-[11px]
            text-base-content/40
          "
        >
          {activity.provider}
        </div>
      </td>


      <td className="hidden sm:table-cell">
        <span
          className="
            badge
            badge-ghost
            badge-sm
            whitespace-nowrap
          "
        >
          {
            formatSportType(
              activity.sport_type,
            )
          }
        </span>
      </td>


      <td
        className="
          whitespace-nowrap
          text-right
          font-medium
        "
      >
        {
          formatDistance(
            activity.distance_m,
          )
        }
      </td>


      <td
        className="
          hidden
          whitespace-nowrap
          text-right
          sm:table-cell
        "
      >
        {
          formatDuration(
            activity.moving_time_seconds
            ?? activity.elapsed_time_seconds,
          )
        }
      </td>


      <td
        className="
          hidden
          whitespace-nowrap
          text-right
          lg:table-cell
        "
      >
        {
          formatPace(
            activity.distance_m,
            activity.moving_time_seconds,
          )
        }
      </td>


      <td
        className="
          hidden
          whitespace-nowrap
          text-right
          lg:table-cell
        "
      >
        {
          formatElevation(
            activity.elevation_gain_m,
          )
        }
      </td>


      <td
        className="
          whitespace-nowrap
          text-right
        "
      >
        <button
          type="button"
          disabled={
            !session
          }
          onClick={() => {
            if (session) {
              onOpenSession(
                session.id,
              )
            }
          }}
          className={[
            'btn btn-sm',
            session
              ? 'btn-ghost'
              : (
                  'btn-ghost '
                  + 'opacity-35'
                ),
          ].join(' ')}
          title={
            session
              ? (
                  'Afficher la séance '
                  + 'et le débriefing'
                )
              : (
                  'Aucune séance coach '
                  + 'associée'
                )
          }
        >
          Séance
        </button>
      </td>
    </tr>
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
