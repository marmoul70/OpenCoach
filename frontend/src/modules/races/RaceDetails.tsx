import {
  Activity,
  CalendarDays,
  Check,
  Clock3,
  Flag,
  Link2,
  LoaderCircle,
  MapPin,
  Mountain,
  Route,
  Trophy,
  Unlink,
  X,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

import {
  fetchRaceActivityCandidates,
  type RaceWritePayload,
} from '../../core/races/api'

import {
  useRaces,
} from './raceStore'

import type {
  Race,
  RaceActivityCandidate,
} from './types'


interface RaceDetailsProps {
  race: Race
  onClose: () => void
}


type ResultStatus =
  | 'completed'
  | 'abandoned'
  | 'not_participated'


export function RaceDetails({
  race,
  onClose,
}: RaceDetailsProps) {
  const {
    updateRace,
  } = useRaces()

  const [
    status,
    setStatus,
  ] = useState<ResultStatus>(
    race.status === 'abandoned'
      ? 'abandoned'
      : race.status === 'not_participated'
        ? 'not_participated'
        : 'completed',
  )

  const [
    actualDistanceKm,
    setActualDistanceKm,
  ] = useState(
    race.actualDistanceKm
      ?.toString()
    ?? '',
  )

  const [
    actualElevationGainM,
    setActualElevationGainM,
  ] = useState(
    race.actualElevationGainM
      ?.toString()
    ?? '',
  )

  const [
    actualTimeMinutes,
    setActualTimeMinutes,
  ] = useState(
    race.actualTimeMinutes
      ?.toString()
    ?? '',
  )

  const [
    ranking,
    setRanking,
  ] = useState(
    race.ranking
      ?.toString()
    ?? '',
  )

  const [
    notes,
    setNotes,
  ] = useState(
    race.notes
    ?? '',
  )

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    saveError,
    setSaveError,
  ] = useState<
    string | null
  >(null)


  const isPlanned =
    race.status === 'planned'


  async function handleSubmit(
    event:
      React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    const noResult =
      status === 'abandoned'
      || status === 'not_participated'

    const updatedRace: Race = {
      ...race,

      status,

      actualDistanceKm:
        status === 'not_participated'
          ? undefined
          : actualDistanceKm
            ? Number(
                actualDistanceKm,
              )
            : undefined,

      actualElevationGainM:
        status === 'not_participated'
          ? undefined
          : actualElevationGainM
            ? Number(
                actualElevationGainM,
              )
            : undefined,

      actualTimeMinutes:
        noResult
          ? undefined
          : actualTimeMinutes
            ? Number(
                actualTimeMinutes,
              )
            : undefined,

      ranking:
        noResult
          ? undefined
          : ranking
            ? Number(
                ranking,
              )
            : undefined,

      notes:
        notes.trim()
        || undefined,
    }

    setSaving(true)
    setSaveError(null)

    try {
      await updateRace(
        updatedRace.id,
        toRaceWritePayload(
          updatedRace,
        ),
      )

      onClose()
    } catch (caughtError) {
      setSaveError(
        caughtError instanceof Error
          ? caughtError.message
          : (
              'Impossible d’enregistrer '
              + 'le résultat de la course.'
            ),
      )
    } finally {
      setSaving(false)
    }
  }


  return (
    <div className="space-y-5">
      <RaceHeader
        race={race}
      />

      <RaceSummary
        race={race}
      />

      <RacePriorityInfo
        race={race}
      />

      <RaceActivitySection
        race={race}
      />

      <RaceActualResultPanel
        race={race}
      />

      {isPlanned ? (
        <form
          onSubmit={
            handleSubmit
          }
          className="
            space-y-5
            border-t
            border-base-300
            pt-5
          "
        >
          <section>
            <h3
              className="
                font-semibold
                text-base-content
              "
            >
              Résultat de la course
            </h3>

            <p
              className="
                mt-1
                text-sm
                text-base-content/50
              "
            >
              À compléter une fois
              la course passée.
            </p>
          </section>


          {saveError && (
            <div
              className="
                alert
                alert-error
                py-2
                text-sm
              "
            >
              {saveError}
            </div>
          )}


          <section className="space-y-3">
            <p
              className="
                text-sm
                font-medium
                text-base-content/70
              "
            >
              Statut
            </p>

            <div
              className="
                grid gap-2
                sm:grid-cols-3
              "
            >
              <StatusButton
                active={
                  status === 'completed'
                }
                variant="success"
                icon={Check}
                label="Terminée"
                onClick={() =>
                  setStatus(
                    'completed',
                  )
                }
              />

              <StatusButton
                active={
                  status === 'abandoned'
                }
                variant="error"
                icon={X}
                label="Abandon"
                onClick={() =>
                  setStatus(
                    'abandoned',
                  )
                }
              />

              <StatusButton
                active={
                  status
                  === 'not_participated'
                }
                variant="neutral"
                icon={Flag}
                label="Non participant"
                onClick={() =>
                  setStatus(
                    'not_participated',
                  )
                }
              />
            </div>
          </section>


          {status
            !== 'not_participated' && (
              <section
                className="
                  grid gap-4
                  sm:grid-cols-2
                "
              >
                <NumberField
                  label="Distance réalisée"
                  icon={Route}
                  value={
                    actualDistanceKm
                  }
                  onChange={
                    setActualDistanceKm
                  }
                  placeholder="42.8"
                  unit="km"
                  step="0.1"
                />

                <NumberField
                  label="Dénivelé réalisé"
                  icon={Mountain}
                  value={
                    actualElevationGainM
                  }
                  onChange={
                    setActualElevationGainM
                  }
                  placeholder="2150"
                  unit="m"
                  step="1"
                />

                {status
                  === 'completed' && (
                    <>
                      <NumberField
                        label="Chrono"
                        icon={Clock3}
                        value={
                          actualTimeMinutes
                        }
                        onChange={
                          setActualTimeMinutes
                        }
                        placeholder="510"
                        unit="min"
                        step="1"
                      />

                      <NumberField
                        label="Classement"
                        icon={Trophy}
                        value={
                          ranking
                        }
                        onChange={
                          setRanking
                        }
                        placeholder="125"
                        step="1"
                      />
                    </>
                  )}
              </section>
            )}


          <section>
            <label className="form-control">
              <span
                className="
                  mb-1.5
                  text-sm
                  font-medium
                  text-base-content/70
                "
              >
                Notes
              </span>

              <textarea
                value={notes}
                onChange={
                  (event) =>
                    setNotes(
                      event.target.value,
                    )
                }
                className="
                  textarea
                  textarea-bordered
                  min-h-24
                  w-full
                "
                placeholder={
                  'Sensations, difficultés, '
                  + 'points positifs…'
                }
              />
            </label>
          </section>


          <div
            className="
              flex justify-end
              gap-2
              border-t
              border-base-300
              pt-4
            "
          >
            <button
              type="button"
              className="btn btn-ghost"
              onClick={
                onClose
              }
              disabled={
                saving
              }
            >
              Annuler
            </button>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={
                saving
              }
            >
              {saving ? (
                <LoaderCircle
                  size={15}
                  className="animate-spin"
                />
              ) : (
                <Check
                  size={15}
                />
              )}

              Enregistrer
            </button>
          </div>
        </form>
      ) : (
        <CompletedRace
          race={race}
        />
      )}
    </div>
  )
}


function RaceHeader({
  race,
}: {
  race: Race
}) {
  return (
    <section
      className="
        flex flex-col
        gap-3
        sm:flex-row
        sm:items-start
        sm:justify-between
      "
    >
      <div className="min-w-0">
        <div
          className="
            flex flex-wrap
            items-center
            gap-x-4
            gap-y-2
            text-sm
            text-base-content/55
          "
        >
          <span
            className="
              flex items-center
              gap-1.5
            "
          >
            <CalendarDays
              size={14}
            />

            {formatDate(
              race.date,
            )}
          </span>

          <span
            className="
              flex items-center
              gap-1.5
            "
          >
            <MapPin
              size={14}
            />

            {race.location}
          </span>
        </div>

        <p
          className="
            mt-2
            text-sm
            font-medium
            text-base-content/70
          "
        >
          {formatRaceType(
            race.type,
          )}
        </p>
      </div>

      <div
        className="
          flex flex-wrap
          items-center
          justify-end
          gap-2
        "
      >
        <RacePriorityBadge
          priority={
            race.priority
          }
        />

        <RaceStatusBadge
          status={
            race.status
          }
        />
      </div>
    </section>
  )
}


function RaceSummary({
  race,
}: {
  race: Race
}) {
  return (
    <section
      className="
        overflow-hidden
        rounded-xl
        border
        border-base-300
      "
    >
      <div
        className="
          grid
          grid-cols-2
          divide-x
          divide-y
          divide-base-300
          sm:grid-cols-4
          sm:divide-y-0
        "
      >
        <SummaryItem
          icon={Route}
          label="Distance prévue"
          value={
            `${formatNumber(
              race.distanceKm,
            )} km`
          }
        />

        <SummaryItem
          icon={Mountain}
          label="Dénivelé prévu"
          value={
            race.elevationGainM
            !== undefined
              ? (
                  `${Math.round(
                    race.elevationGainM,
                  )} m`
                )
              : '—'
          }
        />

        <SummaryItem
          icon={Clock3}
          label="Objectif"
          value={
            race.targetTimeMinutes
            !== undefined
              ? formatDuration(
                  race.targetTimeMinutes,
                )
              : '—'
          }
        />

        <SummaryItem
          icon={Flag}
          label="Type"
          value={
            formatRaceType(
              race.type,
            )
          }
        />
      </div>
    </section>
  )
}


function SummaryItem({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Route
  label: string
  value: string
}) {
  return (
    <div
      className="
        flex items-center
        gap-3
        px-3 py-3
      "
    >
      <Icon
        size={16}
        className="
          shrink-0
          text-base-content/35
        "
      />

      <div className="min-w-0">
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

        <p
          className="
            truncate
            text-sm
            font-semibold
            text-base-content
          "
        >
          {value}
        </p>
      </div>
    </div>
  )
}


function RaceActivitySection({
  race,
}: {
  race: Race
}) {
  const {
    setRaceActivity,
  } = useRaces()

  const [
    activities,
    setActivities,
  ] = useState<
    RaceActivityCandidate[]
  >([])

  const [
    loading,
    setLoading,
  ] = useState(false)

  const [
    saving,
    setSaving,
  ] = useState(false)

  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null)


  useEffect(
    () => {
      let cancelled = false

      async function loadActivities() {
        setLoading(true)
        setError(null)

        try {
          const result =
            await fetchRaceActivityCandidates(
              race.id,
            )

          if (!cancelled) {
            setActivities(
              result,
            )
          }
        } catch (caughtError) {
          if (!cancelled) {
            setError(
              caughtError instanceof Error
                ? caughtError.message
                : (
                    'Impossible de charger '
                    + 'les activités.'
                  ),
            )
          }
        } finally {
          if (!cancelled) {
            setLoading(false)
          }
        }
      }

      void loadActivities()

      return () => {
        cancelled = true
      }
    },
    [race.id],
  )


  async function handleLink(
    activityId: string,
  ) {
    setSaving(true)
    setError(null)

    try {
      await setRaceActivity(
        race.id,
        activityId,
      )
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : (
              'Impossible d’associer '
              + 'l’activité.'
            ),
      )
    } finally {
      setSaving(false)
    }
  }


  async function handleUnlink() {
    setSaving(true)
    setError(null)

    try {
      await setRaceActivity(
        race.id,
        undefined,
      )
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : (
              'Impossible de dissocier '
              + 'l’activité.'
            ),
      )
    } finally {
      setSaving(false)
    }
  }


  const linkedActivity =
    race.activityId
      ? activities.find(
          (activity) =>
            activity.id
            === race.activityId,
        )
      : undefined


  return (
    <section
      className="
        space-y-4
        rounded-xl
        border
        border-base-300
        p-4
      "
    >
      <div
        className="
          flex items-start
          justify-between
          gap-3
        "
      >
        <div
          className="
            flex items-start
            gap-3
          "
        >
          <div
            className="
              flex size-9
              shrink-0
              items-center
              justify-center
              rounded-xl
              bg-base-200
              text-base-content/60
            "
          >
            <Activity
              size={17}
            />
          </div>

          <div>
            <h3
              className="
                font-semibold
                text-base-content
              "
            >
              Activité réelle
            </h3>

            <p
              className="
                mt-1
                text-sm
                text-base-content/50
              "
            >
              Une activité Intervals.icu
              associée devient la source
              prioritaire du résultat réel.
            </p>
          </div>
        </div>

        {race.activityId && (
          <span
            className="
              badge
              badge-success
              badge-sm
            "
          >
            Intervals.icu
          </span>
        )}
      </div>


      {error && (
        <div
          className="
            alert
            alert-error
            py-2
            text-sm
          "
        >
          {error}
        </div>
      )}


      {race.activityId ? (
        <div
          className="
            rounded-xl
            border
            border-success/25
            bg-success/5
            p-3
          "
        >
          <div
            className="
              flex flex-col
              gap-3
              sm:flex-row
              sm:items-center
              sm:justify-between
            "
          >
            <div>
              <p
                className="
                  font-medium
                  text-base-content
                "
              >
                {linkedActivity?.name
                  ?? 'Activité associée'}
              </p>

              {linkedActivity ? (
                <p
                  className="
                    mt-1
                    text-sm
                    text-base-content/55
                  "
                >
                  {formatActivityCandidate(
                    linkedActivity,
                  )}
                </p>
              ) : (
                <p
                  className="
                    mt-1
                    text-sm
                    text-base-content/55
                  "
                >
                  Les données de cette activité
                  sont utilisées comme résultat
                  réel de la course.
                </p>
              )}
            </div>

            <button
              type="button"
              className="
                btn
                btn-outline
                btn-sm
              "
              disabled={saving}
              onClick={() =>
                void handleUnlink()
              }
            >
              {saving ? (
                <LoaderCircle
                  size={15}
                  className="animate-spin"
                />
              ) : (
                <Unlink
                  size={15}
                />
              )}

              Dissocier
            </button>
          </div>
        </div>
      ) : (
        <>
          {loading ? (
            <div
              className="
                flex items-center
                justify-center
                gap-2
                py-5
                text-sm
                text-base-content/50
              "
            >
              <LoaderCircle
                size={17}
                className="animate-spin"
              />

              Recherche des activités…
            </div>
          ) : activities.length === 0 ? (
            <div
              className="
                rounded-xl
                border
                border-dashed
                border-base-300
                px-4 py-5
                text-center
                text-sm
                text-base-content/50
              "
            >
              Aucune activité enregistrée
              le jour de cette course.
            </div>
          ) : (
            <div className="space-y-2">
              {activities.map(
                (activity) => (
                  <div
                    key={
                      activity.id
                    }
                    className="
                      flex flex-col
                      gap-3
                      rounded-xl
                      border
                      border-base-300
                      p-3
                      sm:flex-row
                      sm:items-center
                      sm:justify-between
                    "
                  >
                    <div className="min-w-0">
                      <p
                        className="
                          truncate
                          font-medium
                          text-base-content
                        "
                      >
                        {activity.name}
                      </p>

                      <p
                        className="
                          mt-1
                          text-sm
                          text-base-content/55
                        "
                      >
                        {formatActivityCandidate(
                          activity,
                        )}
                      </p>
                    </div>

                    <button
                      type="button"
                      className="
                        btn
                        btn-primary
                        btn-sm
                      "
                      disabled={saving}
                      onClick={() =>
                        void handleLink(
                          activity.id,
                        )
                      }
                    >
                      {saving ? (
                        <LoaderCircle
                          size={15}
                          className="animate-spin"
                        />
                      ) : (
                        <Link2
                          size={15}
                        />
                      )}

                      Associer
                    </button>
                  </div>
                ),
              )}
            </div>
          )}
        </>
      )}
    </section>
  )
}


function RaceActualResultPanel({
  race,
}: {
  race: Race
}) {
  const result =
    race.actualResult

  const hasResult =
    result.distanceKm !== undefined
    || result.elevationGainM !== undefined
    || result.durationMinutes !== undefined
    || result.trainingLoad !== undefined

  if (
    race.status === 'planned'
    && !hasResult
  ) {
    return null
  }

  const sourceLabel =
    result.source === 'activity'
      ? 'Intervals.icu'
      : result.source === 'manual'
        ? 'Saisie manuelle'
        : race.status === 'not_participated'
          ? 'Non participant'
          : 'Aucune donnée'

  return (
    <section
      className="
        overflow-hidden
        rounded-xl
        border
        border-base-300
      "
    >
      <div
        className="
          flex items-center
          justify-between
          gap-3
          border-b
          border-base-300
          px-4 py-3
        "
      >
        <div>
          <h3
            className="
              font-semibold
              text-base-content
            "
          >
            Résultat utilisé par OpenCoach
          </h3>

          <p
            className="
              mt-0.5
              text-xs
              text-base-content/45
            "
          >
            Source : {sourceLabel}
          </p>
        </div>

        {result.source === 'activity' && (
          <span
            className="
              badge
              badge-success
              badge-sm
            "
          >
            Données réelles
          </span>
        )}
      </div>

      <div
        className="
          grid
          grid-cols-2
          divide-x
          divide-y
          divide-base-300
          sm:grid-cols-4
          sm:divide-y-0
        "
      >
        <SummaryItem
          icon={Route}
          label="Distance réelle"
          value={
            result.distanceKm !== undefined
              ? (
                  `${formatNumber(
                    result.distanceKm,
                  )} km`
                )
              : '—'
          }
        />

        <SummaryItem
          icon={Mountain}
          label="D+ réel"
          value={
            result.elevationGainM !== undefined
              ? (
                  `${Math.round(
                    result.elevationGainM,
                  )} m`
                )
              : '—'
          }
        />

        <SummaryItem
          icon={Clock3}
          label="Durée réelle"
          value={
            result.durationMinutes !== undefined
              ? formatDuration(
                  result.durationMinutes,
                )
              : '—'
          }
        />

        <SummaryItem
          icon={Activity}
          label="Charge"
          value={
            result.trainingLoad !== undefined
              ? formatNumber(
                  result.trainingLoad,
                )
              : '—'
          }
        />
      </div>
    </section>
  )
}


function StatusButton({
  active,
  variant,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean
  variant:
    | 'success'
    | 'error'
    | 'neutral'
  icon: typeof Check
  label: string
  onClick: () => void
}) {
  const activeClass =
    variant === 'success'
      ? 'btn-success'
      : variant === 'error'
        ? 'btn-error'
        : 'btn-neutral'

  return (
    <button
      type="button"
      onClick={
        onClick
      }
      className={[
        'btn btn-sm',
        active
          ? activeClass
          : (
              'btn-ghost '
              + 'border '
              + 'border-base-300'
            ),
      ].join(' ')}
    >
      <Icon
        size={14}
      />

      {label}
    </button>
  )
}


function NumberField({
  label,
  icon: Icon,
  value,
  onChange,
  placeholder,
  unit,
  step,
}: {
  label: string
  icon: typeof Route
  value: string
  onChange:
    (value: string) => void
  placeholder: string
  unit?: string
  step: string
}) {
  return (
    <label className="form-control">
      <span
        className="
          mb-1.5
          flex items-center
          gap-1.5
          text-sm
          font-medium
          text-base-content/70
        "
      >
        <Icon
          size={14}
          className="
            text-base-content/40
          "
        />

        {label}
      </span>

      <div className="join w-full">
        <input
          type="number"
          min="0"
          step={step}
          value={value}
          onChange={
            (event) =>
              onChange(
                event.target.value,
              )
          }
          placeholder={
            placeholder
          }
          className="
            input
            input-bordered
            join-item
            w-full
          "
        />

        {unit && (
          <span
            className="
              join-item
              flex items-center
              border
              border-base-300
              bg-base-200/40
              px-3
              text-sm
              text-base-content/50
            "
          >
            {unit}
          </span>
        )}
      </div>
    </label>
  )
}


function CompletedRace({
  race,
}: {
  race: Race
}) {
  const result =
    race.actualResult

  const sourceDescription =
    result.source === 'activity'
      ? (
          'Résultat réel issu de '
          + 'l’activité Intervals.icu associée.'
        )
      : result.source === 'manual'
        ? (
            'Résultat issu de '
            + 'la saisie manuelle.'
          )
        : race.status === 'not_participated'
          ? 'Course non disputée.'
          : 'Aucun résultat réel disponible.'

  return (
    <section
      className="
        space-y-4
        border-t
        border-base-300
        pt-5
      "
    >
      <div>
        <h3
          className="
            font-semibold
            text-base-content
          "
        >
          Résultat
        </h3>

        <p
          className="
            mt-1
            text-sm
            text-base-content/50
          "
        >
          {sourceDescription}
        </p>
      </div>


      <div
        className="
          overflow-hidden
          rounded-xl
          border
          border-base-300
        "
      >
        <div
          className="
            grid
            grid-cols-2
            divide-x
            divide-y
            divide-base-300
            sm:grid-cols-4
            sm:divide-y-0
          "
        >
          <ResultItem
            label="Distance"
            value={
              result.distanceKm
              !== undefined
                ? (
                    `${formatNumber(
                      result.distanceKm,
                    )} km`
                  )
                : '—'
            }
          />

          <ResultItem
            label="Dénivelé"
            value={
              result.elevationGainM
              !== undefined
                ? (
                    `${Math.round(
                      result.elevationGainM,
                    )} m`
                  )
                : '—'
            }
          />

          <ResultItem
            label="Chrono"
            value={
              result.durationMinutes
              !== undefined
                ? formatDuration(
                    result.durationMinutes,
                  )
                : '—'
            }
          />

          <ResultItem
            label="Charge"
            value={
              result.trainingLoad
              !== undefined
                ? formatNumber(
                    result.trainingLoad,
                  )
                : '—'
            }
          />
        </div>
      </div>


      {race.ranking !== undefined
        && race.status === 'completed'
        && (
          <div
            className="
              rounded-xl
              border
              border-base-300
              px-4 py-3
            "
          >
            <p
              className="
                text-[11px]
                uppercase
                tracking-wide
                text-base-content/40
              "
            >
              Classement
            </p>

            <p
              className="
                mt-0.5
                text-sm
                font-semibold
                text-base-content
              "
            >
              {race.ranking}e
            </p>
          </div>
        )}


      {race.status
        === 'not_participated' && (
          <div
            className="
              rounded-xl
              border
              border-base-300
              bg-base-200/30
              px-4 py-4
              text-sm
              text-base-content/60
            "
          >
            Aucune participation
            enregistrée pour cette course.
            La distance et la charge réelles
            sont comptabilisées à zéro.
          </div>
        )}


      {race.notes && (
        <div
          className="
            rounded-xl
            bg-base-200/50
            px-4 py-3
          "
        >
          <p
            className="
              text-[11px]
              font-medium
              uppercase
              tracking-wide
              text-base-content/40
            "
          >
            Notes
          </p>

          <p
            className="
              mt-1.5
              whitespace-pre-wrap
              text-sm
              leading-relaxed
              text-base-content/70
            "
          >
            {race.notes}
          </p>
        </div>
      )}
    </section>
  )
}


function ResultItem({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div
      className="
        px-4 py-3
      "
    >
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

      <p
        className="
          mt-0.5
          text-sm
          font-semibold
          text-base-content
        "
      >
        {value}
      </p>
    </div>
  )
}


function RacePriorityBadge({
  priority,
}: {
  priority: Race['priority']
}) {
  if (
    priority === 'primary'
  ) {
    return (
      <span
        className="
          badge
          badge-primary
          gap-1
        "
      >
        ★ Objectif prioritaire
      </span>
    )
  }

  return (
    <span
      className="
        badge
        badge-outline
      "
    >
      Course d&apos;entraînement
    </span>
  )
}


function RaceStatusBadge({
  status,
}: {
  status: Race['status']
}) {
  if (
    status === 'planned'
  ) {
    return (
      <span
        className="
          badge
          badge-primary
          badge-sm
        "
      >
        À venir
      </span>
    )
  }

  if (
    status === 'completed'
  ) {
    return (
      <span
        className="
          badge
          badge-success
          badge-sm
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
      "
    >
      Non participant
    </span>
  )
}


function RacePriorityInfo({
  race,
}: {
  race: Race
}) {
  const primary =
    race.priority === 'primary'

  return (
    <section
      className={[
        (
          'rounded-xl border '
          + 'px-4 py-3'
        ),
        primary
          ? (
              'border-primary/30 '
              + 'bg-primary/5'
            )
          : (
              'border-base-300 '
              + 'bg-base-200/40'
            ),
      ].join(' ')}
    >
      <div
        className="
          flex items-start
          gap-3
        "
      >
        <Flag
          size={18}
          className={
            primary
              ? (
                  'mt-0.5 shrink-0 '
                  + 'text-primary'
                )
              : (
                  'mt-0.5 shrink-0 '
                  + 'text-base-content/45'
                )
          }
        />

        <div>
          <p
            className="
              font-semibold
              text-base-content
            "
          >
            {primary
              ? 'Objectif prioritaire'
              : 'Course d’entraînement'}
          </p>

          <p
            className="
              mt-1
              text-sm
              leading-relaxed
              text-base-content/55
            "
          >
            {primary
              ? (
                  'Cette course constitue un objectif '
                  + 'principal. Le plan d’entraînement '
                  + 'sera construit pour favoriser un '
                  + 'pic de forme à cette date.'
                )
              : (
                  'Cette course fait partie de la '
                  + 'préparation. Elle sera intégrée '
                  + 'comme séance spécifique sans '
                  + 'remplacer l’objectif principal.'
                )}
          </p>
        </div>
      </div>
    </section>
  )
}


function toRaceWritePayload(
  race: Race,
): RaceWritePayload {
  return {
    date:
      race.date,

    name:
      race.name,

    location:
      race.location,

    raceType:
      race.type,

    priority:
      race.priority,

    distanceKm:
      race.distanceKm,

    elevationGainM:
      race.elevationGainM,

    targetTimeMinutes:
      race.targetTimeMinutes,

    status:
      race.status,

    actualDistanceKm:
      race.actualDistanceKm,

    actualElevationGainM:
      race.actualElevationGainM,

    actualTimeMinutes:
      race.actualTimeMinutes,

    ranking:
      race.ranking,

    notes:
      race.notes,

    activityId:
      race.activityId,
  }
}


function formatActivityCandidate(
  activity: RaceActivityCandidate,
): string {
  const parts: string[] = []

  if (
    activity.distanceM
    !== undefined
  ) {
    parts.push(
      `${formatNumber(
        activity.distanceM / 1000,
      )} km`,
    )
  }

  if (
    activity.elevationGainM
    !== undefined
  ) {
    parts.push(
      `${Math.round(
        activity.elevationGainM,
      )} m D+`,
    )
  }

  if (
    activity.movingTimeSeconds
    !== undefined
  ) {
    parts.push(
      formatDuration(
        activity.movingTimeSeconds / 60,
      ),
    )
  }

  if (
    activity.trainingLoad
    !== undefined
  ) {
    parts.push(
      `charge ${formatNumber(
        activity.trainingLoad,
      )}`,
    )
  }

  return parts.length > 0
    ? parts.join(' · ')
    : 'Données sportives indisponibles'
}


function formatDate(
  dateString: string,
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
      `${dateString}T12:00:00`,
    ),
  )
}


function formatDuration(
  totalMinutes: number,
): string {
  const roundedMinutes =
    Math.round(
      totalMinutes,
    )

  const hours =
    Math.floor(
      roundedMinutes / 60,
    )

  const minutes =
    roundedMinutes % 60

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