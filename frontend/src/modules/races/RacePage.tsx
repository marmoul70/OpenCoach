import {
  useState,
} from 'react'

import {
  Check,
  Flag,
  MapPin,
  Plus,
  Route,
  Trophy,
  X,
} from 'lucide-react'

import {
  Modal,
} from '../../components/ui/Modal'

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
} from './types'


export function RacePage() {
  const {
    races,
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
          (race) =>
            race.id
            === selectedRaceId,
        )
      : undefined


  const upcomingRaces =
    races
      .filter(
        (race) =>
          race.status
          === 'planned',
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
        (race) =>
          race.status
          !== 'planned',
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


  const completedCount =
    pastRaces.filter(
      (race) =>
        race.status
        === 'completed',
    ).length


  const nextRace =
    upcomingRaces[0]


  return (
    <main>
      <div
        className="
          mx-auto
          max-w-6xl
          px-4 py-6
          sm:px-6
          lg:py-8
        "
      >
        <header
          className="
            mb-6
            flex flex-col
            gap-4
            sm:flex-row
            sm:items-start
            sm:justify-between
          "
        >
          <div
            className="
              flex items-start
              gap-4
            "
          >
            <div
              className="
                flex size-11
                shrink-0
                items-center
                justify-center
                rounded-2xl
                bg-primary/10
                text-primary
              "
            >
              <Route
                size={24}
              />
            </div>

            <div>
              <h1
                className="
                  text-3xl
                  font-bold
                  tracking-tight
                  text-base-content
                "
              >
                Courses
              </h1>

              <p
                className="
                  mt-1 text-sm
                  text-base-content/60
                "
              >
                Vos objectifs à venir et
                votre historique de courses.
              </p>
            </div>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() =>
              setIsAddModalOpen(
                true,
              )
            }
          >
            <Plus
              size={16}
            />

            Ajouter une course
          </button>
        </header>


        <RaceOverview
          upcomingCount={
            upcomingRaces.length
          }
          completedCount={
            completedCount
          }
          nextRace={
            nextRace
          }
        />


        <section
          className="
            mt-7
            space-y-4
          "
        >
          <div>
            <h2
              className="
                text-xl
                font-bold
                text-base-content
              "
            >
              Prochaines courses
            </h2>

            <p
              className="
                mt-1 text-sm
                text-base-content/60
              "
            >
              Vos prochains objectifs.
            </p>
          </div>


          {upcomingRaces.length
            > 0 ? (
              <div className="space-y-3">
                {upcomingRaces.map(
                  (
                    race,
                    index,
                  ) => (
                    <UpcomingRaceRow
                      key={
                        race.id
                      }
                      race={
                        race
                      }
                      next={
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
              </div>
            ) : (
              <EmptyState
                title="Aucune course prévue"
                description={
                  'Ajoutez votre prochain '
                  + 'objectif pour préparer '
                  + 'votre entraînement.'
                }
              />
            )}
        </section>


        <section
          className="
            mt-8
            space-y-4
          "
        >
          <div>
            <h2
              className="
                text-xl
                font-bold
                text-base-content
              "
            >
              Historique
            </h2>

            <p
              className="
                mt-1 text-sm
                text-base-content/60
              "
            >
              Vos courses terminées,
              abandons et non-participations.
            </p>
          </div>


          {pastRaces.length > 0 ? (
            <div className="space-y-3">
              {pastRaces.map(
                (race) => (
                  <PastRaceRow
                    key={
                      race.id
                    }
                    race={
                      race
                    }
                    onOpen={() =>
                      setSelectedRaceId(
                        race.id,
                      )
                    }
                  />
                ),
              )}
            </div>
          ) : (
            <EmptyState
              title="Aucune course dans l’historique"
              description={
                'Vos performances apparaîtront '
                + 'ici après vos courses.'
              }
            />
          )}
        </section>
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
        <Modal
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
        </Modal>
      )}
    </main>
  )
}


interface RaceOverviewProps {
  upcomingCount: number
  completedCount: number
  nextRace:
    Race | undefined
}


function RaceOverview({
  upcomingCount,
  completedCount,
  nextRace,
}: RaceOverviewProps) {
  return (
    <section
      className="
        overflow-hidden
        rounded-2xl
        border border-base-300
        bg-base-100
        shadow-sm
      "
    >
      <div
        className="
          grid
          divide-y divide-base-300
          sm:grid-cols-[1fr_1fr_1.5fr]
          sm:divide-x
          sm:divide-y-0
        "
      >
        <OverviewItem
          icon={Flag}
          value={`${upcomingCount}`}
          label="À venir"
          description="Courses programmées"
        />

        <OverviewItem
          icon={Check}
          value={`${completedCount}`}
          label="Terminées"
          description="Courses réalisées"
        />

        <OverviewItem
          icon={Trophy}
          value={
            nextRace?.name
            ?? 'Aucun objectif'
          }
          label="Prochaine course"
          description={
            nextRace
              ? (
                `${formatDate(
                  nextRace.date,
                )} · ${
                  formatNumber(
                    nextRace.distanceKm,
                  )
                } km`
              )
              : (
                'Aucune course programmée'
              )
          }
          wide
        />
      </div>
    </section>
  )
}


interface OverviewItemProps {
  icon: typeof Flag
  value: string
  label: string
  description: string
  wide?: boolean
}


function OverviewItem({
  icon: Icon,
  value,
  label,
  description,
  wide = false,
}: OverviewItemProps) {
  return (
    <div
      className="
        flex min-w-0
        items-center
        gap-3
        px-4 py-3.5
        sm:px-5
      "
    >
      <div
        className="
          flex size-9
          shrink-0
          items-center
          justify-center
          rounded-xl
          bg-primary/10
          text-primary
        "
      >
        <Icon
          size={18}
        />
      </div>

      <div className="min-w-0">
        <p
          className={[
            (
              'font-bold '
              + 'text-base-content'
            ),
            wide
              ? (
                'truncate '
                + 'text-base'
              )
              : 'text-lg',
          ].join(' ')}
          title={
            wide
              ? value
              : undefined
          }
        >
          {value}
        </p>

        <div
          className="
            mt-0.5
            flex flex-wrap
            items-baseline
            gap-x-2
          "
        >
          <span
            className="
              text-xs
              font-medium
              text-base-content/60
            "
          >
            {label}
          </span>

          <span
            className="
              text-xs
              text-base-content/40
            "
          >
            {description}
          </span>
        </div>
      </div>
    </div>
  )
}


interface UpcomingRaceRowProps {
  race: Race
  next: boolean
  onOpen: () => void
}


function UpcomingRaceRow({
  race,
  next,
  onOpen,
}: UpcomingRaceRowProps) {
  return (
    <button
      type="button"
      onClick={
        onOpen
      }
      className={[
        (
          'w-full rounded-2xl '
          + 'border bg-base-100 '
          + 'p-4 text-left '
          + 'shadow-sm transition '
          + 'hover:bg-base-200/40'
        ),
        next
          ? (
            'border-primary '
            + 'ring-1 '
            + 'ring-primary/20'
          )
          : 'border-base-300',
      ].join(' ')}
    >
      <div
        className="
          grid gap-4
          md:grid-cols-[170px_minmax(0,1fr)_auto]
          md:items-center
        "
      >
        <div>
          <div
            className="
              flex flex-wrap
              items-center
              gap-2
            "
          >
            <span
              className="
                text-sm
                font-semibold
                text-base-content
              "
            >
              {formatDate(
                race.date,
              )}
            </span>

            {next && (
              <span
                className="
                  badge
                  badge-primary
                  badge-sm
                "
              >
                Prochaine
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
            {formatRaceType(
              race.type,
            )}
          </p>
        </div>


        <div className="min-w-0">
          <h3
            className="
              truncate
              text-lg
              font-bold
              text-base-content
            "
          >
            {race.name}
          </h3>

          <p
            className="
              mt-1
              flex items-center
              gap-1.5
              text-sm
              text-base-content/50
            "
          >
            <MapPin
              size={14}
            />

            {race.location}
          </p>
        </div>


        <div
          className="
            flex flex-wrap
            items-center
            gap-x-5
            gap-y-2
            text-sm
            text-base-content/60
            md:justify-end
          "
        >
          <span>
            {formatNumber(
              race.distanceKm,
            )}
            {' '}
            km
          </span>

          {race.elevationGainM
            !== undefined && (
              <span>
                {Math.round(
                  race.elevationGainM,
                )}
                {' '}
                m D+
              </span>
            )}

          {race.targetTimeMinutes
            !== undefined && (
              <span>
                Objectif{' '}
                {formatDuration(
                  race.targetTimeMinutes,
                )}
              </span>
            )}
        </div>
      </div>
    </button>
  )
}


interface PastRaceRowProps {
  race: Race
  onOpen: () => void
}


function PastRaceRow({
  race,
  onOpen,
}: PastRaceRowProps) {
  return (
    <button
      type="button"
      onClick={
        onOpen
      }
      className="
        w-full
        rounded-2xl
        border border-base-300
        bg-base-100
        p-4
        text-left
        shadow-sm
        transition
        hover:bg-base-200/40
      "
    >
      <div
        className="
          grid gap-4
          md:grid-cols-[170px_minmax(0,1fr)_auto]
          md:items-center
        "
      >
        <div>
          <p
            className="
              text-sm
              font-semibold
              text-base-content
            "
          >
            {formatDate(
              race.date,
            )}
          </p>

          <StatusBadge
            status={
              race.status
            }
          />
        </div>


        <div className="min-w-0">
          <h3
            className="
              truncate
              font-bold
              text-base-content
            "
          >
            {race.name}
          </h3>

          <p
            className="
              mt-1
              flex items-center
              gap-1.5
              text-sm
              text-base-content/50
            "
          >
            <MapPin
              size={14}
            />

            {race.location}
          </p>
        </div>


        <div
          className="
            flex flex-wrap
            items-center
            gap-x-5
            gap-y-2
            text-sm
            text-base-content/60
            md:justify-end
          "
        >
          <span>
            {formatNumber(
              race.actualDistanceKm
              ?? race.distanceKm,
            )}
            {' '}
            km
          </span>

          {race.actualElevationGainM
            !== undefined && (
              <span>
                {Math.round(
                  race.actualElevationGainM,
                )}
                {' '}
                m D+
              </span>
            )}

          {race.actualTimeMinutes
            !== undefined && (
              <span
                className="
                  font-semibold
                  text-base-content
                "
              >
                {formatDuration(
                  race.actualTimeMinutes,
                )}
              </span>
            )}

          {race.ranking
            !== undefined && (
              <span>
                {race.ranking}
                e
              </span>
            )}
        </div>
      </div>
    </button>
  )
}


function StatusBadge({
  status,
}: {
  status: Race['status']
}) {
  if (
    status === 'completed'
  ) {
    return (
      <span
        className="
          badge
          badge-success
          badge-sm
          mt-1
          gap-1
        "
      >
        <Check
          size={11}
        />

        Terminée
      </span>
    )
  }

  if (
    status === 'abandoned'
  ) {
    return (
      <span
        className="
          badge
          badge-error
          badge-sm
          mt-1
          gap-1
        "
      >
        <X
          size={11}
        />

        Abandon
      </span>
    )
  }

  return (
    <span
      className="
        badge
        badge-ghost
        badge-sm
        mt-1
      "
    >
      Non participant
    </span>
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
        rounded-2xl
        border border-base-300
        bg-base-100
        px-5 py-8
        text-center
      "
    >
      <Flag
        size={22}
        className="
          mx-auto
          text-base-content/30
        "
      />

      <p
        className="
          mt-3
          font-semibold
          text-base-content
        "
      >
        {title}
      </p>

      <p
        className="
          mt-1
          text-sm
          text-base-content/45
        "
      >
        {description}
      </p>
    </div>
  )
}


function formatDate(
  dateString: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    },
  ).format(
    new Date(
      `${dateString}T12:00:00`,
    ),
  )
}


function formatDuration(
  totalMinutes: number,
): string {
  const hours =
    Math.floor(
      totalMinutes / 60,
    )

  const minutes =
    totalMinutes % 60

  return (
    `${hours}h${
      minutes
        .toString()
        .padStart(
          2,
          '0',
        )
    }`
  )
}


function formatNumber(
  value: number,
): string {
  return new Intl.NumberFormat(
    'fr-FR',
    {
      maximumFractionDigits: 1,
    },
  ).format(
    value,
  )
}


function formatRaceType(
  type: Race['type'],
): string {
  switch (type) {
    case 'trail':
      return 'Trail'

    case 'road':
      return 'Route'

    case 'ultra':
      return 'Ultra'

    default:
      return 'Autre'
  }
}