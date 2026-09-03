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
    <div className="space-y-3">
      <RaceHeader
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
            space-y-4
            rounded-[12px]
            border
            border-black/[0.065]
            bg-white
            p-4
            dark:border-white/[0.065]
            dark:bg-[#151b1f]
          "
        >
          <section>
            <h3
              className="
                text-[13px]
                font-semibold
                text-slate-800
                dark:text-slate-200
              "
            >
              Résultat de la course
            </h3>

            <p
              className="
                mt-1
                text-[10px]
                text-slate-400
                dark:text-slate-500
              "
            >
              À compléter une fois
              la course passée.
            </p>
          </section>


          {saveError && (
            <div
              className="
                rounded-[9px]
                border
                border-red-500/15
                bg-red-50
                px-3
                py-2
                text-[10px]
                text-red-600
                dark:bg-red-500/[0.06]
                dark:text-red-400
              "
            >
              {saveError}
            </div>
          )}


          <section className="space-y-3">
            <p
              className="
                text-[10px]
                font-semibold
                uppercase
                tracking-[0.07em]
                text-slate-400
                dark:text-slate-500
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
            <label className="block">
              <span
                className="
                  mb-1.5
                  block
                  text-[10px]
                  font-semibold
                  uppercase
                  tracking-[0.07em]
                  text-slate-400
                  dark:text-slate-500
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
                  min-h-24
                  w-full
                  resize-y
                  rounded-[9px]
                  border
                  border-black/[0.08]
                  bg-slate-50
                  px-3
                  py-2.5
                  text-[11px]
                  text-slate-700
                  outline-none
                  transition
                  placeholder:text-slate-400
                  focus:border-emerald-500/35
                  focus:bg-white
                  dark:border-white/[0.08]
                  dark:bg-white/[0.025]
                  dark:text-slate-200
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
              border-black/[0.055]
              pt-3
              dark:border-white/[0.055]
            "
          >
            <button
              type="button"
              className="
                h-9
                rounded-[8px]
                px-3
                text-[10px]
                font-semibold
                text-slate-400
                transition
                hover:bg-slate-50
                hover:text-slate-700
                dark:hover:bg-white/[0.035]
                dark:hover:text-slate-200
              "
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
              className="
                inline-flex
                h-9
                items-center
                gap-1.5
                rounded-[8px]
                border
                border-emerald-500/25
                bg-emerald-500/[0.08]
                px-3
                text-[10px]
                font-semibold
                text-emerald-700
                transition
                hover:bg-emerald-500/[0.13]
                disabled:opacity-40
                dark:text-emerald-400
              "
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
        relative
        overflow-hidden
        rounded-[15px]
        border
        border-white/[0.07]
        bg-[#141917]
        p-5
        text-white
        shadow-[0_14px_38px_rgba(4,12,8,0.12)]
        sm:p-6
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          -right-20
          -top-24
          h-56
          w-56
          rounded-full
          bg-emerald-500/[0.11]
          blur-3xl
        "
      />

      <div className="relative">
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
              flex-wrap
              items-center
              gap-2
            "
          >
            <RacePriorityBadge
              priority={race.priority}
            />

            <RaceStatusBadge
              status={race.status}
            />
          </div>

          <span
            className="
              text-[10px]
              font-bold
              uppercase
              tracking-[0.12em]
              text-white/30
            "
          >
            {formatRaceType(race.type)}
          </span>
        </div>


        <h2
          className="
            mt-5
            text-[22px]
            font-bold
            leading-tight
            tracking-[-0.03em]
            text-white
            sm:text-[24px]
          "
        >
          {race.name}
        </h2>

        <div
          className="
            mt-2.5
            flex
            flex-wrap
            items-center
            gap-x-4
            gap-y-2
            text-[12px]
            font-medium
            text-white/45
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

            {formatDate(race.date)}
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
        </div>


        <div
          className="
            mt-5
            grid
            grid-cols-2
            gap-x-5
            gap-y-4
            border-t
            border-white/[0.07]
            pt-4
            sm:grid-cols-4
          "
        >
          <HeroMetric
            label="Distance"
            value={`${formatNumber(race.distanceKm)} km`}
          />

          <HeroMetric
            label="Dénivelé"
            value={
              race.elevationGainM !== undefined
                ? `${Math.round(race.elevationGainM)} m`
                : '—'
            }
          />

          <HeroMetric
            label="Objectif"
            value={
              race.targetTimeMinutes !== undefined
                ? formatDuration(race.targetTimeMinutes)
                : '—'
            }
          />

          <HeroMetric
            label="Rôle"
            value={
              race.priority === 'primary'
                ? 'Objectif A'
                : 'Préparation'
            }
          />
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
          text-[9px]
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
          text-[17px]
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
        border-black/[0.065] dark:border-white/[0.065]
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
              bg-slate-50 dark:bg-white/[0.025]
              text-slate-400 dark:text-slate-500
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
                text-slate-800 dark:text-slate-200
              "
            >
              Activité réelle
            </h3>

            <p
              className="
                mt-1
                text-sm
                text-slate-400 dark:text-slate-500
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
              rounded-full
              bg-emerald-500/[0.08]
              px-2
              py-0.5
              text-[8px]
              font-semibold
              text-emerald-700
              dark:text-emerald-400
            "
          >
            Intervals.icu
          </span>
        )}
      </div>


      {error && (
        <div
          className="
            rounded-[9px]
            border
            border-red-500/15
            bg-red-50
            px-3
            py-2
            text-[10px]
            text-red-600
            dark:bg-red-500/[0.06]
            dark:text-red-400
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
            rounded-[11px]
            border
            border-emerald-500/15
            bg-emerald-500/[0.045]
            p-3
            dark:border-emerald-400/15
            dark:bg-emerald-400/[0.04]
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
                  text-slate-800 dark:text-slate-200
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
                    text-slate-400 dark:text-slate-500
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
                    text-slate-400 dark:text-slate-500
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
                inline-flex
                h-8
                items-center
                gap-1.5
                rounded-[8px]
                border
                border-black/[0.08]
                px-2.5
                text-[9.5px]
                font-semibold
                text-slate-500
                transition
                hover:bg-slate-50
                dark:border-white/[0.08]
                dark:text-slate-400
                dark:hover:bg-white/[0.035]
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
                text-slate-400 dark:text-slate-500
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
                border-black/[0.065] dark:border-white/[0.065]
                px-4 py-5
                text-center
                text-sm
                text-slate-400 dark:text-slate-500
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
                      border-black/[0.065] dark:border-white/[0.065]
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
                          text-slate-800 dark:text-slate-200
                        "
                      >
                        {activity.name}
                      </p>

                      <p
                        className="
                          mt-1
                          text-sm
                          text-slate-400 dark:text-slate-500
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
                        inline-flex
                        h-8
                        items-center
                        gap-1.5
                        rounded-[8px]
                        border
                        border-emerald-500/25
                        bg-emerald-500/[0.07]
                        px-2.5
                        text-[9.5px]
                        font-semibold
                        text-emerald-700
                        transition
                        hover:bg-emerald-500/[0.12]
                        dark:text-emerald-400
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
        border-black/[0.065] dark:border-white/[0.065]
      "
    >
      <div
        className="
          flex items-center
          justify-between
          gap-3
          border-b
          border-black/[0.065] dark:border-white/[0.065]
          px-4 py-3
        "
      >
        <div>
          <h3
            className="
              font-semibold
              text-slate-800 dark:text-slate-200
            "
          >
            Résultat utilisé par OpenCoach
          </h3>

          <p
            className="
              mt-0.5
              text-xs
              text-slate-400 dark:text-slate-500
            "
          >
            Source : {sourceLabel}
          </p>
        </div>

        {result.source === 'activity' && (
          <span
            className="
              rounded-full
              bg-emerald-500/[0.08]
              px-2
              py-0.5
              text-[8px]
              font-semibold
              text-emerald-700
              dark:text-emerald-400
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
          divide-slate-200 dark:divide-white/[0.08]
          sm:grid-cols-4
          sm:divide-y-0
        "
      >
        <ResultItem
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

        <ResultItem
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

        <ResultItem
          label="Durée réelle"
          value={
            result.durationMinutes !== undefined
              ? formatDuration(
                  result.durationMinutes,
                )
              : '—'
          }
        />

        <ResultItem
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
      ? (
          'border-emerald-500/30 '
          + 'bg-emerald-500/[0.10] '
          + 'text-emerald-700 '
          + 'dark:text-emerald-400'
        )
      : variant === 'error'
        ? (
            'border-red-500/30 '
            + 'bg-red-500/[0.08] '
            + 'text-red-600 '
            + 'dark:text-red-400'
          )
        : (
            'border-slate-400/20 '
            + 'bg-slate-500/[0.07] '
            + 'text-slate-600 '
            + 'dark:text-slate-300'
          )

  const inactiveClass =
    (
      'border-black/[0.07] '
      + 'bg-slate-50 '
      + 'text-slate-400 '
      + 'hover:border-black/[0.12] '
      + 'hover:text-slate-600 '
      + 'dark:border-white/[0.07] '
      + 'dark:bg-white/[0.025] '
      + 'dark:text-slate-500 '
      + 'dark:hover:text-slate-300'
    )

  return (
    <button
      type="button"
      onClick={onClick}
      className={[
        (
          'inline-flex h-9 '
          + 'items-center justify-center '
          + 'gap-1.5 rounded-[9px] '
          + 'border px-3 '
          + 'text-[10.5px] '
          + 'font-semibold '
          + 'transition'
        ),
        active
          ? activeClass
          : inactiveClass,
      ].join(' ')}
    >
      <Icon
        className="
          h-3.5
          w-3.5
        "
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
    <label className="block">
      <span
        className="
          mb-1.5
          flex
          items-center
          gap-1.5
          text-[10px]
          font-semibold
          uppercase
          tracking-[0.06em]
          text-slate-400
          dark:text-slate-500
        "
      >
        <Icon
          className="
            h-3.5
            w-3.5
            text-emerald-500
          "
        />

        {label}
      </span>

      <div
        className="
          flex
          h-10
          overflow-hidden
          rounded-[9px]
          border
          border-black/[0.08]
          bg-slate-50
          transition
          focus-within:border-emerald-500/35
          focus-within:bg-white
          dark:border-white/[0.08]
          dark:bg-white/[0.025]
        "
      >
        <input
          type="number"
          min="0"
          step={step}
          value={value}
          onChange={
            event =>
              onChange(
                event.target.value,
              )
          }
          placeholder={placeholder}
          className="
            min-w-0
            flex-1
            bg-transparent
            px-3
            text-[12px]
            font-medium
            text-slate-700
            outline-none
            placeholder:text-slate-300
            dark:text-slate-200
          "
        />

        {unit && (
          <span
            className="
              flex
              items-center
              border-l
              border-black/[0.06]
              px-3
              text-[10px]
              font-semibold
              text-slate-400
              dark:border-white/[0.06]
              dark:text-slate-500
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
          'Résultat issu de l’activité '
          + 'Intervals.icu associée.'
        )
      : result.source === 'manual'
        ? 'Résultat saisi manuellement.'
        : race.status === 'not_participated'
          ? 'Course non disputée.'
          : 'Aucune donnée réelle disponible.'

  return (
    <section
      className="
        overflow-hidden
        rounded-[12px]
        border
        border-black/[0.065]
        bg-white
        dark:border-white/[0.065]
        dark:bg-[#151b1f]
      "
    >
      <div
        className="
          flex
          items-center
          justify-between
          gap-3
          border-b
          border-black/[0.055]
          px-4
          py-3
          dark:border-white/[0.055]
        "
      >
        <div>
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.08em]
              text-slate-400
            "
          >
            Résultat
          </p>

          <p
            className="
              mt-1
              text-[11px]
              text-slate-500
              dark:text-slate-400
            "
          >
            {sourceDescription}
          </p>
        </div>

        <RaceStatusBadge
          status={race.status}
        />
      </div>


      <div
        className="
          grid
          grid-cols-2
          sm:grid-cols-4
        "
      >
        <ResultItem
          label="Distance"
          value={
            result.distanceKm !== undefined
              ? `${formatNumber(result.distanceKm)} km`
              : '—'
          }
        />

        <ResultItem
          label="Dénivelé"
          value={
            result.elevationGainM !== undefined
              ? `${Math.round(result.elevationGainM)} m`
              : '—'
          }
        />

        <ResultItem
          label="Chrono"
          value={
            result.durationMinutes !== undefined
              ? formatDuration(result.durationMinutes)
              : '—'
          }
        />

        <ResultItem
          label="Charge"
          value={
            result.trainingLoad !== undefined
              ? formatNumber(result.trainingLoad)
              : '—'
          }
        />
      </div>


      {race.ranking !== undefined
        && race.status === 'completed'
        && (
          <div
            className="
              border-t
              border-black/[0.055]
              px-4
              py-3
              dark:border-white/[0.055]
            "
          >
            <p
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.07em]
                text-slate-400
              "
            >
              Classement
            </p>

            <p
              className="
                mt-1
                text-[15px]
                font-bold
                text-slate-800
                dark:text-slate-200
              "
            >
              {race.ranking}e
            </p>
          </div>
        )}


      {race.notes && (
        <div
          className="
            border-t
            border-black/[0.055]
            bg-slate-50/60
            px-4
            py-3
            dark:border-white/[0.055]
            dark:bg-white/[0.018]
          "
        >
          <p
            className="
              text-[9px]
              font-bold
              uppercase
              tracking-[0.07em]
              text-slate-400
            "
          >
            Notes
          </p>

          <p
            className="
              mt-1.5
              whitespace-pre-wrap
              text-[12px]
              leading-5
              text-slate-600
              dark:text-slate-400
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
        border-r
        border-b
        border-black/[0.055]
        px-4
        py-3
        even:border-r-0
        dark:border-white/[0.055]
        sm:border-b-0
        sm:even:border-r
        sm:last:border-r-0
      "
    >
      <p
        className="
          text-[9px]
          font-bold
          uppercase
          tracking-[0.07em]
          text-slate-400
        "
      >
        {label}
      </p>

      <p
        className="
          mt-1
          text-[14px]
          font-semibold
          tabular-nums
          text-slate-800
          dark:text-slate-200
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
  const primary =
    priority === 'primary'

  return (
    <span
      className={[
        (
          'inline-flex items-center '
          + 'rounded-full px-2 py-1 '
          + 'text-[8px] font-bold '
          + 'uppercase tracking-[0.07em]'
        ),
        primary
          ? (
              'bg-emerald-400/[0.12] '
              + 'text-emerald-300'
            )
          : (
              'bg-white/[0.06] '
              + 'text-white/45'
            ),
      ].join(' ')}
    >
      {primary
        ? 'A-Race'
        : 'B-Race'}
    </span>
  )
}



function RaceStatusBadge({
  status,
}: {
  status: Race['status']
}) {
  const config =
    status === 'planned'
      ? {
          label: 'À venir',
          className:
            (
              'bg-sky-400/[0.10] '
              + 'text-sky-300'
            ),
        }
      : status === 'completed'
        ? {
            label: 'Terminée',
            className:
              (
                'bg-emerald-400/[0.12] '
                + 'text-emerald-300'
              ),
          }
        : status === 'abandoned'
          ? {
              label: 'Abandon',
              className:
                (
                  'bg-red-400/[0.10] '
                  + 'text-red-300'
                ),
            }
          : {
              label: 'Non participé',
              className:
                (
                  'bg-white/[0.06] '
                  + 'text-white/45'
                ),
            }

  return (
    <span
      className={[
        (
          'inline-flex items-center '
          + 'rounded-full px-2 py-1 '
          + 'text-[8px] font-bold '
          + 'uppercase tracking-[0.07em]'
        ),
        config.className,
      ].join(' ')}
    >
      {config.label}
    </span>
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
