import { useState } from 'react'

import { Modal } from '../../components/ui/Modal'
import { useRaces } from './raceStore'
import type { Race, RaceType } from './types'

interface RaceFormProps {
  open: boolean
  onClose: () => void
}

export function RaceForm({
  open,
  onClose,
}: RaceFormProps) {
  const { addRace } = useRaces()

  const [name, setName] = useState('')
  const [date, setDate] = useState('')
  const [location, setLocation] = useState('')
  const [type, setType] = useState<RaceType>('trail')
  const [distanceKm, setDistanceKm] = useState('')
  const [elevationGainM, setElevationGainM] = useState('')
  const [targetTime, setTargetTime] = useState('')

  function resetForm() {
    setName('')
    setDate('')
    setLocation('')
    setType('trail')
    setDistanceKm('')
    setElevationGainM('')
    setTargetTime('')
  }

  function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const distance = Number(distanceKm)

    if (
      !name.trim() ||
      !date ||
      !location.trim() ||
      !distanceKm ||
      !Number.isFinite(distance) ||
      distance <= 0
    ) {
      return
    }

    const race: Race = {
      id: `race-${Date.now()}`,
      name: name.trim(),
      location: location.trim(),
      date,
      type,
      distanceKm: distance,
      elevationGainM: elevationGainM
        ? Number(elevationGainM)
        : undefined,
      targetTimeMinutes: targetTime
        ? Number(targetTime)
        : undefined,
      status: 'planned',
    }

    addRace(race)
    resetForm()
    onClose()
  }

  return (
    <Modal
      title="Ajouter une course"
      open={open}
      onClose={onClose}
    >
      <form
        onSubmit={handleSubmit}
        className="space-y-5"
      >
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="form-control sm:col-span-2">
            <span className="label-text mb-2 font-medium">
              Nom de la course *
            </span>

            <input
              type="text"
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              placeholder="Ex. Trail des Vosges"
              className="input input-bordered w-full"
              required
            />
          </label>

          <label className="form-control">
            <span className="label-text mb-2 font-medium">
              Date *
            </span>

            <input
              type="date"
              value={date}
              onChange={(event) =>
                setDate(event.target.value)
              }
              className="input input-bordered w-full"
              required
            />
          </label>

          <label className="form-control">
            <span className="label-text mb-2 font-medium">
              Lieu *
            </span>

            <input
              type="text"
              value={location}
              onChange={(event) =>
                setLocation(event.target.value)
              }
              placeholder="Ex. Belfort, France"
              className="input input-bordered w-full"
              required
            />
          </label>

          <label className="form-control">
            <span className="label-text mb-2 font-medium">
              Type
            </span>

            <select
              value={type}
              onChange={(event) =>
                setType(
                  event.target.value as RaceType,
                )
              }
              className="select select-bordered w-full"
            >
              <option value="trail">Trail</option>
              <option value="road">Route</option>
              <option value="ultra">Ultra</option>
              <option value="other">Autre</option>
            </select>
          </label>

          <label className="form-control">
            <span className="label-text mb-2 font-medium">
              Distance (km) *
            </span>

            <input
              type="number"
              min="0.1"
              step="0.1"
              value={distanceKm}
              onChange={(event) =>
                setDistanceKm(event.target.value)
              }
              placeholder="Ex. 42"
              className="input input-bordered w-full"
              required
            />
          </label>

          <label className="form-control">
            <span className="label-text mb-2 font-medium">
              D+ (m)
            </span>

            <input
              type="number"
              min="0"
              step="1"
              value={elevationGainM}
              onChange={(event) =>
                setElevationGainM(event.target.value)
              }
              placeholder="Ex. 1800"
              className="input input-bordered w-full"
            />
          </label>

          <label className="form-control">
            <span className="label-text mb-2 font-medium">
              Objectif chrono (minutes)
            </span>

            <input
              type="number"
              min="1"
              step="1"
              value={targetTime}
              onChange={(event) =>
                setTargetTime(event.target.value)
              }
              placeholder="Ex. 300 = 5h00"
              className="input input-bordered w-full"
            />

            <span className="mt-1 text-xs text-base-content/50">
              Facultatif
            </span>
          </label>
        </div>

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
            Ajouter la course
          </button>
        </div>
      </form>
    </Modal>
  )
}
