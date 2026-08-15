import { useState } from 'react'
import {
  CalendarDays,
  MapPin,
  Mountain,
  Route,
  Trophy,
} from 'lucide-react'

import { useRaces } from './raceStore'
import type { Race } from './types'

interface RaceDetailsProps {
  race: Race
  onClose: () => void
}

export function RaceDetails({
  race,
  onClose,
}: RaceDetailsProps) {
  const { updateRace } = useRaces()

  const [status, setStatus] = useState<
    'completed' | 'abandoned' | 'not_participated'
  >(
    race.status === 'abandoned'
      ? 'abandoned'
      : race.status === 'not_participated'
        ? 'not_participated'
        : 'completed',
  )

  const [actualDistanceKm, setActualDistanceKm] =
    useState(
      race.actualDistanceKm?.toString() ?? '',
    )

  const [actualElevationGainM, setActualElevationGainM] =
    useState(
      race.actualElevationGainM?.toString() ?? '',
    )

  const [actualTimeMinutes, setActualTimeMinutes] =
    useState(
      race.actualTimeMinutes?.toString() ?? '',
    )

  const [ranking, setRanking] = useState(
    race.ranking?.toString() ?? '',
  )

  const [notes, setNotes] = useState(
    race.notes ?? '',
  )

  const isPlanned = race.status === 'planned'

  function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const noResult =
      status === 'abandoned' ||
      status === 'not_participated'

    const updatedRace: Race = {
      ...race,
      status,
      actualDistanceKm:
        status === 'not_participated'
          ? undefined
          : actualDistanceKm
            ? Number(actualDistanceKm)
            : undefined,
      actualElevationGainM:
        status === 'not_participated'
          ? undefined
          : actualElevationGainM
            ? Number(actualElevationGainM)
            : undefined,
      actualTimeMinutes: noResult
        ? undefined
        : actualTimeMinutes
          ? Number(actualTimeMinutes)
          : undefined,
      ranking: noResult
        ? undefined
        : ranking
          ? Number(ranking)
          : undefined,
      notes: notes.trim() || undefined,
    }

    updateRace(updatedRace)
    onClose()
  }

  return (
    <div className="space-y-6">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold text-base-content">
              {race.name}
            </h2>

            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-2 text-sm text-base-content/60">
              <span className="flex items-center gap-1.5">
                <CalendarDays className="h-4 w-4" />
                {formatDate(race.date)}
              </span>

              <span className="flex items-center gap-1.5">
                <MapPin className="h-4 w-4" />
                {race.location}
              </span>
            </div>
          </div>

          <span
            className={
              race.status === 'planned'
                ? 'badge badge-primary'
                : race.status === 'abandoned'
                  ? 'badge badge-error'
                  : race.status === 'not_participated'
                    ? 'badge badge-ghost'
                    : 'badge badge-success'
            }
          >
            {race.status === 'planned'
              ? 'À venir'
              : race.status === 'abandoned'
                ? 'Abandon'
                : race.status === 'not_participated'
                  ? 'Non participant'
                  : 'Terminée'}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Metric
          icon={Route}
          label="Distance"
          value={`${race.distanceKm} km`}
        />

        <Metric
          icon={Mountain}
          label="D+"
          value={
            race.elevationGainM !== undefined
              ? `${race.elevationGainM} m`
              : '—'
          }
        />

        <Metric
          icon={Trophy}
          label="Objectif"
          value={
            race.targetTimeMinutes !== undefined
              ? formatDuration(
                  race.targetTimeMinutes,
                )
              : '—'
          }
        />

        <Metric
          icon={CalendarDays}
          label="Type"
          value={formatRaceType(race.type)}
        />
      </div>

      {isPlanned ? (
        <form
          onSubmit={handleSubmit}
          className="space-y-5 border-t border-base-300 pt-5"
        >
          <div>
            <h3 className="font-semibold text-base-content">
              Enregistrer le résultat
            </h3>

            <p className="mt-1 text-sm text-base-content/50">
              Renseignez les données après votre course.
            </p>
          </div>
          
          <div>
            <p className="mb-3 font-medium text-base-content">
              Statut de la course
            </p>

            <div className="grid gap-2 sm:grid-cols-3">
              <button
                type="button"
                onClick={() => setStatus('completed')}
                className={[
                  'btn',
                  status === 'completed'
                    ? 'btn-success'
                    : 'btn-ghost border border-base-300',
                ].join(' ')}
              >
                ✓ Terminée
              </button>

              <button
                type="button"
                onClick={() => setStatus('abandoned')}
                className={[
                  'btn',
                  status === 'abandoned'
                    ? 'btn-error'
                    : 'btn-ghost border border-base-300',
                ].join(' ')}
              >
                ✕ Abandon
              </button>

              <button
                type="button"
                onClick={() => setStatus('not_participated')}
                className={[
                  'btn',
                  status === 'not_participated'
                    ? 'btn-neutral'
                    : 'btn-ghost border border-base-300',
                ].join(' ')}
              >
                — Non participant
              </button>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <NumberField
              label="Distance réalisée (km)"
              value={actualDistanceKm}
              onChange={setActualDistanceKm}
              placeholder="Ex. 42.8"
            />

            <NumberField
              label="D+ réalisé (m)"
              value={actualElevationGainM}
              onChange={setActualElevationGainM}
              placeholder="Ex. 2150"
            />

            {status === 'completed' && (
              <>
                <NumberField
                  label="Chrono (minutes)"
                  value={actualTimeMinutes}
                  onChange={setActualTimeMinutes}
                  placeholder="Ex. 510 = 8h30"
                />

                <NumberField
                  label="Classement"
                  value={ranking}
                  onChange={setRanking}
                  placeholder="Ex. 125"
                />
              </>
            )}
          </div>

          <label className="form-control">
            <span className="label-text mb-2 font-medium">
              Notes
            </span>

            <textarea
              value={notes}
              onChange={(event) =>
                setNotes(event.target.value)
              }
              className="textarea textarea-bordered min-h-24 w-full"
              placeholder="Votre retour sur la course..."
            />
          </label>

          <div className="flex justify-end gap-2 border-t border-base-300 pt-4">
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onClose}
            >
              Annuler
            </button>

            <button
              type="submit"
              className="btn btn-primary"
            >
              Enregistrer le résultat
            </button>
          </div>
        </form>
      ) : (
        <div className="space-y-4 border-t border-base-300 pt-5">
          <div>
            <h3 className="font-semibold text-base-content">
              Résultat
            </h3>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            <Result
              label="Distance"
              value={
                race.actualDistanceKm !== undefined
                  ? `${race.actualDistanceKm} km`
                  : '—'
              }
            />

            <Result
              label="D+"
              value={
                race.actualElevationGainM !== undefined
                  ? `${race.actualElevationGainM} m`
                  : '—'
              }
            />

            <Result
              label="Chrono"
              value={
                race.actualTimeMinutes !== undefined
                  ? formatDuration(
                      race.actualTimeMinutes,
                    )
                  : '—'
              }
            />

            <Result
              label="Classement"
              value={
                race.ranking !== undefined
                  ? `${race.ranking}e`
                  : '—'
              }
            />
          </div>

          {race.notes && (
            <div className="rounded-xl bg-base-200 p-4">
              <p className="text-xs font-semibold uppercase tracking-wide text-base-content/40">
                Notes
              </p>

              <p className="mt-2 text-sm text-base-content/70">
                {race.notes}
              </p>
            </div>
          )}
        </div>
      )}


    </div>
  )
}

function Metric({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Route
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

function Result({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-xl border border-base-300 bg-base-100 p-3">
      <p className="text-xs text-base-content/50">
        {label}
      </p>

      <p className="mt-1 font-semibold text-base-content">
        {value}
      </p>
    </div>
  )
}

function NumberField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  placeholder: string
}) {
  return (
    <label className="form-control">
      <span className="label-text mb-2 font-medium">
        {label}
      </span>

      <input
        type="number"
        min="0"
        step="0.1"
        value={value}
        onChange={(event) =>
          onChange(event.target.value)
        }
        placeholder={placeholder}
        className="input input-bordered w-full"
      />
    </label>
  )
}

function formatDate(dateString: string): string {
  return new Intl.DateTimeFormat('fr-FR', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  }).format(
    new Date(`${dateString}T12:00:00`),
  )
}

function formatDuration(totalMinutes: number): string {
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60

  return `${hours}h${minutes
    .toString()
    .padStart(2, '0')}`
}

function formatRaceType(type: Race['type']): string {
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
