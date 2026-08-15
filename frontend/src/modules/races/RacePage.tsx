import { useState } from 'react'

import { RaceDetails } from './RaceDetails'

import { Modal } from '../../components/ui/Modal'

import {
  CalendarDays,
  MapPin,
  Mountain,
  Plus,
  Route,
} from 'lucide-react'

import { useRaces } from './raceStore'
import type { Race } from './types'
import { RaceForm } from './RaceForm'

export function RacePage() {
  const { races } = useRaces()

  const [selectedRaceId, setSelectedRaceId] =
    useState<string | null>(null)

  const selectedRace = selectedRaceId
    ? races.find(
        (race) => race.id === selectedRaceId,
      )
    : undefined

  const [isAddModalOpen, setIsAddModalOpen] = useState(false)

  const upcomingRaces = races
    .filter((race) => race.status === 'planned')
    .sort(
      (a, b) =>
        new Date(a.date).getTime() -
        new Date(b.date).getTime(),
    )

  const pastRaces = races
    .filter((race) => race.status !== 'planned')
    .sort(
      (a, b) =>
        new Date(b.date).getTime() -
        new Date(a.date).getTime(),
    )

  return (
    <main>
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:py-8">
        <header className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex size-11 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <Route size={24} />
            </div>

            <div>
              <h1 className="text-3xl font-bold tracking-tight text-base-content">
                Courses
              </h1>

              <p className="mt-1 text-sm text-base-content/60">
                Vos objectifs à venir et votre historique de courses.
              </p>
            </div>
          </div>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setIsAddModalOpen(true)}
          >
            <Plus className="h-4 w-4" />
            Ajouter une course
          </button>
        </header>

        {upcomingRaces.length > 0 && (
          <section className="mb-10">
            <div className="mb-4">
              <h2 className="text-xl font-bold text-base-content">
                Prochaines courses
              </h2>

              <p className="mt-1 text-sm text-base-content/60">
                Vos prochains objectifs.
              </p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              {upcomingRaces.map((race) => (
                <RaceCard
                  key={race.id}
                  race={race}
                  onOpen={() => setSelectedRaceId(race.id)}
                />
              ))}
            </div>
          </section>
        )}

        <section>
          <div className="mb-4">
            <h2 className="text-xl font-bold text-base-content">
              Historique
            </h2>

            <p className="mt-1 text-sm text-base-content/60">
              Vos courses terminées et vos abandons.
            </p>
          </div>

          {pastRaces.length > 0 ? (
            <div className="space-y-3">
              {pastRaces.map((race) => (
                  <RaceHistoryCard
                    key={race.id}
                    race={race}
                    onOpen={() => setSelectedRaceId(race.id)}
                  />
                ))}
            </div>
          ) : (
            <div className="card border border-base-300 bg-base-100 shadow-sm">
              <div className="card-body items-center py-10 text-center">
                <p className="font-semibold">
                  Aucune course dans l'historique
                </p>

                <p className="text-sm text-base-content/50">
                  Vos performances apparaîtront ici après vos courses.
                </p>
              </div>
            </div>
          )}
        </section>
      </div>
      <RaceForm
        open={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
      />
      {selectedRace && (
        <Modal
          title={selectedRace.name}
          open
          onClose={() => setSelectedRaceId(null)}
        >
          <RaceDetails
            race={selectedRace}
            onClose={() => setSelectedRaceId(null)}
          />
        </Modal>
      )}
    </main>
  )
}

function RaceCard({
  race,
  onOpen,
}: {
  race: Race
  onOpen: () => void
}) {
  return (
    <article
        className="card cursor-pointer border border-base-300 bg-base-100 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
        onClick={onOpen}
      >
      <div className="card-body p-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-xl font-bold text-base-content">
              {race.name}
            </h3>

            <div className="mt-2 flex items-center gap-1.5 text-sm text-base-content/60">
              <MapPin className="h-4 w-4" />
              {race.location}
            </div>
          </div>

          <span className="badge badge-primary">
            À venir
          </span>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <RaceMetric
            icon={CalendarDays}
            label="Date"
            value={formatDate(race.date)}
          />

          <RaceMetric
            icon={Route}
            label="Distance"
            value={`${race.distanceKm} km`}
          />

          <RaceMetric
            icon={Mountain}
            label="D+"
            value={
              race.elevationGainM !== undefined
                ? `${race.elevationGainM} m`
                : '—'
            }
          />

          <RaceMetric
            icon={CalendarDays}
            label="Objectif"
            value={
              race.targetTimeMinutes !== undefined
                ? formatDuration(race.targetTimeMinutes)
                : '—'
            }
          />
        </div>
      </div>
    </article>
  )
}

function RaceHistoryCard({
  race,
  onOpen,
}: {
  race: Race
  onOpen: () => void
}) {
  const abandoned = race.status === 'abandoned'
  const notParticipated =
    race.status === 'not_participated'

  return (
    <article
      className="card cursor-pointer border border-base-300 bg-base-100 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
      onClick={onOpen}
    >
      <div className="card-body p-4">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="font-bold text-base-content">
                {race.name}
              </h3>

              <span
                className={
                  abandoned
                    ? 'badge badge-error badge-sm'
                    : notParticipated
                      ? 'badge badge-ghost badge-sm'
                      : 'badge badge-success badge-sm'
                }
              >
                {abandoned
                  ? 'Abandon'
                  : notParticipated
                    ? 'Non participant'
                    : 'Terminée'}
              </span>
            </div>

            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-base-content/50">
              <span>{formatDate(race.date)}</span>
              <span>{race.location}</span>
              <span>{race.distanceKm} km</span>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-sm sm:min-w-72">
            <span className="text-base-content/50">
              Distance
            </span>

            <span className="font-semibold text-right">
              {race.actualDistanceKm !== undefined
                ? `${race.actualDistanceKm} km`
                : '—'}
            </span>

            <span className="text-base-content/50">
              D+
            </span>

            <span className="font-semibold text-right">
              {race.actualElevationGainM !== undefined
                ? `${race.actualElevationGainM} m`
                : '—'}
            </span>

            <span className="text-base-content/50">
              Temps
            </span>

            <span className="font-semibold text-right">
              {race.actualTimeMinutes !== undefined
                ? formatDuration(race.actualTimeMinutes)
                : '—'}
            </span>

            <span className="text-base-content/50">
              Classement
            </span>

            <span className="font-semibold text-right">
              {race.ranking !== undefined
                ? `${race.ranking}e`
                : '—'}
            </span>
          </div>
        </div>

        {race.notes && (
          <p className="mt-2 border-t border-base-300 pt-3 text-sm text-base-content/60">
            {race.notes}
          </p>
        )}
      </div>
    </article>
  )
}

function RaceMetric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof CalendarDays
  label: string
  value: string
}) {
  return (
    <div className="rounded-xl bg-base-200 p-3">
      <div className="flex items-center gap-2 text-xs text-base-content/50">
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>

      <p className="mt-1 font-semibold text-base-content">
        {value}
      </p>
    </div>
  )
}

function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  }).format(new Date(`${dateString}T12:00:00`))
}

function formatDuration(totalMinutes: number): string {
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  return `${hours}h${minutes.toString().padStart(2, '0')}`
}
