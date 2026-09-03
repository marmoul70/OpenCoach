import {
  CalendarDays,
  CircleX,
  Heart,
  MoveRight,
  Star,
} from 'lucide-react'
import {
  useEffect,
  useState,
} from 'react'

import {
  acceptDailyAdaptation,
  applyDailyReplanning,
  declineDailyAdaptation,
  fetchDailyReplanning,
  fetchTodayCheckIn,
  saveDailyCheckIn,
  type BodySide,
  type DailyCheckInState,
  type DailyReplanningState,
  type PainArea,
  type ReplanningAction,
  type ReplanningOption,
  type ReplanningProposal,
} from '../../core/checkin'

import {
  useToast,
} from '../../components/ui/ToastProvider'

import {
  notifyTrainingSessionUpdated,
} from '../../core/events'

import {
  RatingIcons,
} from './RatingIcons'


const PAIN_AREAS: Array<{
  value: PainArea
  label: string
}> = [
  { value: 'head', label: 'Tête' },
  { value: 'neck', label: 'Cou' },
  { value: 'shoulder', label: 'Épaule' },
  { value: 'back', label: 'Dos' },
  { value: 'lower_back', label: 'Bas du dos' },
  { value: 'hip', label: 'Hanche' },
  { value: 'groin', label: 'Aine' },
  { value: 'thigh', label: 'Cuisse' },
  { value: 'knee', label: 'Genou' },
  { value: 'calf', label: 'Mollet' },
  { value: 'shin', label: 'Tibia' },
  { value: 'ankle', label: 'Cheville' },
  { value: 'achilles', label: 'Tendon d’Achille' },
  { value: 'foot', label: 'Pied' },
  { value: 'other', label: 'Autre' },
]

const SIDES: Array<{
  value: BodySide
  label: string
}> = [
  { value: 'left', label: 'Gauche' },
  { value: 'right', label: 'Droite' },
  { value: 'both', label: 'Des deux côtés' },
  { value: 'center', label: 'Centre' },
  { value: 'not_applicable', label: 'Non applicable' },
]


export function FeelingDetails() {
  const {
    toast,
  } = useToast()

  const [
    state,
    setState,
  ] = useState<DailyCheckInState | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(
    true,
  )

  const [
    saving,
    setSaving,
  ] = useState(
    false,
  )

  const [
    replanning,
    setReplanning,
  ] = useState<DailyReplanningState | null>(
    null,
  )

  const [
    energy,
    setEnergy,
  ] = useState(
    5,
  )

  const [
    comfort,
    setComfort,
  ] = useState(
    5,
  )

  const [
    illness,
    setIllness,
  ] = useState(
    false,
  )

  const [
    unavailable,
    setUnavailable,
  ] = useState(
    false,
  )

  const [
    painArea,
    setPainArea,
  ] = useState<PainArea>(
    'other',
  )

  const [
    bodySide,
    setBodySide,
  ] = useState<BodySide>(
    'not_applicable',
  )

  const [
    note,
    setNote,
  ] = useState(
    '',
  )

  useEffect(() => {
    let cancelled =
      false

    async function load() {
      try {
        const result =
          await fetchTodayCheckIn()

        if (cancelled) {
          return
        }

        setState(
          result,
        )

        if (result) {
          setEnergy(
            result.checkin.energy_rating,
          )

          setComfort(
            result.checkin.pain_wellness_rating,
          )

          setIllness(
            result.checkin.illness,
          )

          setUnavailable(
            result.checkin.unavailable,
          )

          setNote(
            result.checkin.note
            ?? '',
          )

          const location =
            result.checkin.pain_locations[0]

          if (location) {
            setPainArea(
              location.area,
            )

            setBodySide(
              location.side,
            )
          }
        }
      } catch (reason) {
        toast({
          type: 'error',
          title: 'Ressenti',
          message:
            reason instanceof Error
              ? reason.message
              : 'Impossible de charger le ressenti.',
        })
      } finally {
        if (!cancelled) {
          setLoading(
            false,
          )
        }
      }
    }

    void load()

    return () => {
      cancelled = true
    }
  }, [
    toast,
  ])

  async function save() {
    try {
      setSaving(
        true,
      )

      const result =
        await saveDailyCheckIn({
          energy_rating:
            energy,
          pain_wellness_rating:
            comfort,
          illness,
          unavailable,
          pain_locations:
            comfort < 5
              ? [
                  {
                    area:
                      painArea,
                    side:
                      bodySide,
                  },
                ]
              : [],
          note:
            note.trim()
              ? note.trim()
              : null,
        })

      setState(
        result,
      )

      notifyUpdated()

      if (
        !result.adaptation
        ?.awaiting_athlete_decision
      ) {
        window.dispatchEvent(
          new Event(
            'opencoach:close-widget-modal',
          ),
        )
      }

      toast({
        type: 'success',
        title: 'Ressenti enregistré',
        message:
          result.adaptation
            ?.awaiting_athlete_decision
            ? (
                'Le coach vous propose '
                + 'une adaptation de la séance.'
              )
            : 'Votre état du jour est enregistré.',
      })
    } catch (reason) {
      toast({
        type: 'error',
        title: 'Ressenti',
        message:
          reason instanceof Error
            ? reason.message
            : 'Impossible d’enregistrer le ressenti.',
      })
    } finally {
      setSaving(
        false,
      )
    }
  }

  async function loadReplanning(
    checkinId: string,
  ) {
    const result =
      await fetchDailyReplanning(
        checkinId,
      )

    setReplanning(
      result,
    )

    return result
  }


  async function acceptAdaptation() {
    if (!state) {
      return
    }

    try {
      setSaving(
        true,
      )

      const result =
        await acceptDailyAdaptation(
          state.checkin.id,
        )

      if (
        result.session_adapted
      ) {
        notifyTrainingSessionUpdated()
      }

      if (
        state.checkin.unavailable
        && result.session_adapted
      ) {
        await loadReplanning(
          state.checkin.id,
        )
      } else {
        setReplanning(
          null,
        )
      }

      const refreshed =
        await fetchTodayCheckIn()

      setState(
        refreshed,
      )

      notifyUpdated()

      toast({
        type: 'success',
        title:
          state.checkin.unavailable
            ? 'Séance annulée'
            : result.session_adapted
              ? 'Séance adaptée'
              : 'Adaptation acceptée',
        message:
          state.checkin.unavailable
            ? (
                'La séance est conservée dans le planning '
                + 'comme non réalisée.'
              )
            : result.adapted_session
              ? (
                  `${result.adapted_session.title} · `
                  + `${result.adapted_session.duration_minutes} min`
                )
              : (
                  'Votre décision a été enregistrée.'
                ),
      })
    } catch (reason) {
      toast({
        type: 'error',
        title:
          'Adaptation impossible',
        message:
          reason instanceof Error
            ? reason.message
            : 'Impossible d’adapter la séance.',
      })
    } finally {
      setSaving(
        false,
      )
    }
  }

  async function applyReplanning(
    proposal: ReplanningProposal,
    option: ReplanningOption,
  ) {
    if (
      !state
      || !proposal.source_session.id
    ) {
      return
    }

    try {
      setSaving(
        true,
      )

      const result =
        await applyDailyReplanning(
          state.checkin.id,
          {
            source_session_id:
              proposal.source_session.id,
            action:
              option.action,
            target_date:
              option.target_date,
          },
        )

      notifyTrainingSessionUpdated()
      notifyUpdated()

      const refreshed =
        await loadReplanning(
          state.checkin.id,
        )

      const remaining =
        refreshed.proposals.filter(
          (item) =>
            item.source_session.id
            !== proposal.source_session.id,
        )

      setReplanning({
        ...refreshed,
        proposals:
          remaining,
      })

      toast({
        type: 'success',
        title:
          getReplanningSuccessTitle(
            result.action,
          ),
        message:
          result.applied_session
            ? (
                `${result.applied_session.title} · `
                + `${formatReschedulingDate(
                  result.applied_session.date,
                )}`
              )
            : (
                'La séance reste annulée.'
              ),
      })
    } catch (reason) {
      toast({
        type: 'error',
        title:
          'Replanification impossible',
        message:
          reason instanceof Error
            ? reason.message
            : (
                'Impossible d’appliquer '
                + 'ce choix.'
              ),
      })
    } finally {
      setSaving(
        false,
      )
    }
  }


  async function declineAdaptation() {
    if (!state) {
      return
    }

    try {
      setSaving(
        true,
      )

      await declineDailyAdaptation(
        state.checkin.id,
      )

      const refreshed =
        await fetchTodayCheckIn()

      setState(
        refreshed,
      )

      notifyUpdated()

      toast({
        type: 'info',
        title:
          'Séance conservée',
        message:
          'Votre décision a été enregistrée.',
      })
    } catch (reason) {
      toast({
        type: 'error',
        title: 'Ressenti',
        message:
          reason instanceof Error
            ? reason.message
            : 'Impossible d’enregistrer votre décision.',
      })
    } finally {
      setSaving(
        false,
      )
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-48 items-center justify-center">
        <span
          className="
            h-6
            w-6
            animate-spin
            rounded-full
            border-2
            border-slate-200
            border-t-emerald-500
            dark:border-white/[0.10]
            dark:border-t-emerald-400
          "
          aria-hidden="true"
        />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <section>
        <h3
          className="
            text-[14px]
            font-semibold
            tracking-[-0.01em]
            text-slate-800
            dark:text-slate-100
          "
        >
          Comment vous sentez-vous ?
        </h3>

        <p
          className="
            mt-1
            text-[11px]
            leading-relaxed
            text-slate-500
            dark:text-slate-400
          "
        >
          5 représente le meilleur état,
          1 le niveau le plus difficile.
        </p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <RatingPicker
          icon={Star}
          label="Énergie"
          description="5 = très frais · 1 = épuisé"
          value={energy}
          onChange={setEnergy}
        />

        <RatingPicker
          icon={Heart}
          label="Douleur"
          description="5 = aucune douleur · 1 = douleur importante"
          value={comfort}
          onChange={setComfort}
        />
      </div>

      {comfort < 5 && (
        <section
          className="
            rounded-[13px]
            border
            border-black/[0.06]
            bg-slate-50/70
            p-4
            dark:border-white/[0.07]
            dark:bg-white/[0.025]
          "
        >
          <h3
            className="
              text-[12.5px]
              font-semibold
              text-slate-800
              dark:text-slate-100
            "
          >
            Où ressentez-vous une gêne ?
          </h3>

          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <label className="block">
              <span className="
                  mb-1.5
                  block
                  text-[10px]
                  font-medium
                  text-slate-500
                  dark:text-slate-400
                ">
                Zone
              </span>

              <select
                className="
                  h-10
                  w-full
                  appearance-none
                  rounded-[9px]
                  border
                  border-black/[0.07]
                  bg-white
                  px-3
                  pr-9
                  text-[11px]
                  font-medium
                  text-slate-700
                  outline-none
                  transition
                  hover:border-black/[0.12]
                  focus:border-emerald-500/35
                  focus:ring-2
                  focus:ring-emerald-500/[0.08]
                  dark:border-white/[0.07]
                  dark:bg-[#171d21]
                  dark:text-slate-200
                  dark:hover:border-white/[0.12]
                  dark:focus:border-emerald-400/30
                  dark:focus:ring-emerald-400/[0.08]
                "
                value={painArea}
                onChange={(event) => {
                  setPainArea(
                    event.target.value as PainArea,
                  )
                }}
              >
                {PAIN_AREAS.map(
                  (area) => (
                    <option
                      key={area.value}
                      value={area.value}
                    >
                      {area.label}
                    </option>
                  ),
                )}
              </select>
            </label>

            <label className="block">
              <span className="
                  mb-1.5
                  block
                  text-[10px]
                  font-medium
                  text-slate-500
                  dark:text-slate-400
                ">
                Côté
              </span>

              <select
                className="
                  h-10
                  w-full
                  appearance-none
                  rounded-[9px]
                  border
                  border-black/[0.07]
                  bg-white
                  px-3
                  pr-9
                  text-[11px]
                  font-medium
                  text-slate-700
                  outline-none
                  transition
                  hover:border-black/[0.12]
                  focus:border-emerald-500/35
                  focus:ring-2
                  focus:ring-emerald-500/[0.08]
                  dark:border-white/[0.07]
                  dark:bg-[#171d21]
                  dark:text-slate-200
                  dark:hover:border-white/[0.12]
                  dark:focus:border-emerald-400/30
                  dark:focus:ring-emerald-400/[0.08]
                "
                value={bodySide}
                onChange={(event) => {
                  setBodySide(
                    event.target.value as BodySide,
                  )
                }}
              >
                {SIDES.map(
                  (side) => (
                    <option
                      key={side.value}
                      value={side.value}
                    >
                      {side.label}
                    </option>
                  ),
                )}
              </select>
            </label>
          </div>
        </section>
      )}

      <section className="grid gap-3 sm:grid-cols-2">
        <label className="
          flex
          cursor-pointer
          items-center
          justify-between
          gap-4
          rounded-[13px]
          border
          border-black/[0.06]
          bg-white
          px-4
          py-3.5
          transition
          hover:border-black/[0.10]
          dark:border-white/[0.07]
          dark:bg-[#171d21]
          dark:hover:border-white/[0.11]
        ">
          <div>
            <p className="text-sm font-semibold">
              Je suis malade
            </p>

            <p className="
              mt-0.5
              text-[10.5px]
              text-slate-500
              dark:text-slate-400
            ">
              Symptômes ou état infectieux
            </p>
          </div>

          <input
            type="checkbox"
            className="
              relative
              h-5
              w-9
              shrink-0
              cursor-pointer
              appearance-none
              rounded-full
              bg-slate-200
              outline-none
              transition
              before:absolute
              before:left-0.5
              before:top-0.5
              before:h-4
              before:w-4
              before:rounded-full
              before:bg-white
              before:shadow-sm
              before:transition
              checked:bg-amber-500
              checked:before:translate-x-4
              focus-visible:ring-2
              focus-visible:ring-amber-500/20
              dark:bg-white/[0.10]
              dark:checked:bg-amber-500
            "
            checked={illness}
            onChange={(event) => {
              setIllness(
                event.target.checked,
              )
            }}
          />
        </label>

        <label className="
          flex
          cursor-pointer
          items-center
          justify-between
          gap-4
          rounded-[13px]
          border
          border-black/[0.06]
          bg-white
          px-4
          py-3.5
          transition
          hover:border-black/[0.10]
          dark:border-white/[0.07]
          dark:bg-[#171d21]
          dark:hover:border-white/[0.11]
        ">
          <div>
            <p className="text-sm font-semibold">
              Je suis indisponible
            </p>

            <p className="
              mt-0.5
              text-[10.5px]
              text-slate-500
              dark:text-slate-400
            ">
              Impossible de m’entraîner aujourd’hui
            </p>
          </div>

          <input
            type="checkbox"
            className="
              relative
              h-5
              w-9
              shrink-0
              cursor-pointer
              appearance-none
              rounded-full
              bg-slate-200
              outline-none
              transition
              before:absolute
              before:left-0.5
              before:top-0.5
              before:h-4
              before:w-4
              before:rounded-full
              before:bg-white
              before:shadow-sm
              before:transition
              checked:bg-rose-500
              checked:before:translate-x-4
              focus-visible:ring-2
              focus-visible:ring-rose-500/20
              dark:bg-white/[0.10]
              dark:checked:bg-rose-500
            "
            checked={unavailable}
            onChange={(event) => {
              setUnavailable(
                event.target.checked,
              )
            }}
          />
        </label>
      </section>

      {(
        illness
        || unavailable
        || comfort < 5
      ) && (
        <section
          className="
            rounded-[13px]
            border
            border-black/[0.06]
            bg-slate-50/60
            p-4
            dark:border-white/[0.07]
            dark:bg-white/[0.025]
          "
        >
          <label
            htmlFor="daily-feeling-note"
            className="block"
          >
            <span
              className="
                text-[12.5px]
                font-semibold
                text-slate-800
                dark:text-slate-100
              "
            >
              {getDetailsTitle({
                illness,
                unavailable,
                comfort,
              })}
            </span>

            <span
              className="
                mt-1
                block
                text-[10.5px]
                leading-relaxed
                text-slate-500
                dark:text-slate-400
              "
            >
              {getDetailsHelp({
                illness,
                unavailable,
                comfort,
              })}
            </span>
          </label>

          <textarea
            id="daily-feeling-note"
            className="
              mt-3
              block
              min-h-24
              w-full
              resize-y
              rounded-[10px]
              border
              border-black/[0.07]
              bg-white
              px-3
              py-2.5
              text-[11px]
              leading-relaxed
              text-slate-700
              outline-none
              transition
              placeholder:text-slate-400
              hover:border-black/[0.11]
              focus:border-emerald-500/35
              focus:ring-2
              focus:ring-emerald-500/[0.08]
              dark:border-white/[0.07]
              dark:bg-[#171d21]
              dark:text-slate-200
              dark:placeholder:text-slate-500
              dark:hover:border-white/[0.11]
              dark:focus:border-emerald-400/30
              dark:focus:ring-emerald-400/[0.08]
            "
            placeholder={
              getDetailsPlaceholder({
                illness,
                unavailable,
                comfort,
              })
            }
            maxLength={1000}
            value={note}
            onChange={(event) => {
              setNote(
                event.target.value,
              )
            }}
          />
        </section>
      )}

      <button
        type="button"
        className="
          inline-flex
          h-10
          w-full
          items-center
          justify-center
          gap-2
          rounded-[9px]
          border
          border-emerald-500/15
          bg-emerald-500/[0.10]
          px-4
          text-[11.5px]
          font-semibold
          text-emerald-700
          transition
          hover:border-emerald-500/25
          hover:bg-emerald-500/[0.15]
          disabled:cursor-not-allowed
          disabled:opacity-50
          dark:border-emerald-400/15
          dark:bg-emerald-400/[0.09]
          dark:text-emerald-300
        "
        disabled={saving}
        onClick={() => {
          void save()
        }}
      >
        {saving && (
          <span
            className="
              h-3.5
              w-3.5
              animate-spin
              rounded-full
              border-2
              border-emerald-700/20
              border-t-emerald-700
              dark:border-emerald-300/20
              dark:border-t-emerald-300
            "
            aria-hidden="true"
          />
        )}

        Enregistrer mon ressenti
      </button>

      {state?.adaptation?.awaiting_athlete_decision && (
        <section
          className={
            state.checkin.unavailable
              ? (
                  'rounded-[13px] border '
                  + 'border-rose-500/15 '
                  + 'bg-rose-500/[0.04] p-4 '
                  + 'dark:border-rose-400/15 '
                  + 'dark:bg-rose-400/[0.04]'
                )
              : (
                  'rounded-[13px] border '
                  + 'border-amber-500/15 '
                  + 'bg-amber-500/[0.04] p-4 '
                  + 'dark:border-amber-400/15 '
                  + 'dark:bg-amber-400/[0.04]'
                )
          }
        >
          <div
            className={
              state.checkin.unavailable
                ? (
                    'inline-flex rounded-full border '
                    + 'border-rose-500/15 '
                    + 'bg-rose-500/[0.08] '
                    + 'px-2 py-1 '
                    + 'text-[9px] font-bold '
                    + 'uppercase tracking-[0.06em] '
                    + 'text-rose-700 '
                    + 'dark:border-rose-400/15 '
                    + 'dark:bg-rose-400/[0.08] '
                    + 'dark:text-rose-300'
                  )
                : (
                    'inline-flex rounded-full border '
                    + 'border-amber-500/15 '
                    + 'bg-amber-500/[0.08] '
                    + 'px-2 py-1 '
                    + 'text-[9px] font-bold '
                    + 'uppercase tracking-[0.06em] '
                    + 'text-amber-700 '
                    + 'dark:border-amber-400/15 '
                    + 'dark:bg-amber-400/[0.08] '
                    + 'dark:text-amber-300'
                  )
            }
          >
            {state.checkin.unavailable
              ? 'Annulation recommandée'
              : 'Proposition du coach'}
          </div>

          <p
            className="
              mt-3
              text-[13px]
              font-semibold
              leading-relaxed
              text-slate-800
              dark:text-slate-100
            "
          >
            {state.checkin.unavailable
              ? (
                  'Vous avez indiqué être indisponible aujourd’hui. '
                  + 'Voulez-vous annuler la séance prévue ?'
                )
              : state.adaptation.recommendation}
          </p>

          <p
            className="
              mt-2
              text-[11px]
              leading-[1.6]
              text-slate-500
              dark:text-slate-400
            "
          >
            {state.adaptation.reason}
          </p>

          <p
            className="
              mt-3
              text-[10.5px]
              leading-[1.55]
              text-slate-500
              dark:text-slate-400
            "
          >
            {state.checkin.unavailable
              ? (
                  'La séance restera dans votre planning '
                  + 'comme non réalisée.'
                )
              : (
                  'Vous restez décisionnaire : '
                  + 'souhaitez-vous adapter la séance prévue ?'
                )}
          </p>

          <div className="mt-4 flex flex-col gap-2 sm:flex-row">
            <button
              type="button"
              className={
                state.checkin.unavailable
                  ? (
                      'inline-flex h-9 items-center '
                      + 'justify-center rounded-[9px] '
                      + 'border border-rose-500/15 '
                      + 'bg-rose-500/[0.08] px-3 '
                      + 'text-[10.5px] font-semibold '
                      + 'text-rose-700 transition '
                      + 'hover:border-rose-500/25 '
                      + 'hover:bg-rose-500/[0.13] '
                      + 'disabled:cursor-not-allowed '
                      + 'disabled:opacity-50 '
                      + 'sm:flex-1 '
                      + 'dark:border-rose-400/15 '
                      + 'dark:bg-rose-400/[0.08] '
                      + 'dark:text-rose-300'
                    )
                  : (
                      'inline-flex h-9 items-center '
                      + 'justify-center rounded-[9px] '
                      + 'border border-amber-500/15 '
                      + 'bg-amber-500/[0.08] px-3 '
                      + 'text-[10.5px] font-semibold '
                      + 'text-amber-700 transition '
                      + 'hover:border-amber-500/25 '
                      + 'hover:bg-amber-500/[0.13] '
                      + 'disabled:cursor-not-allowed '
                      + 'disabled:opacity-50 '
                      + 'sm:flex-1 '
                      + 'dark:border-amber-400/15 '
                      + 'dark:bg-amber-400/[0.08] '
                      + 'dark:text-amber-300'
                    )
              }
              disabled={saving}
              onClick={() => {
                void acceptAdaptation()
              }}
            >
              {state.checkin.unavailable
                ? 'Annuler la séance'
                : 'Adapter ma séance'}
            </button>

            <button
              type="button"
              className="
                inline-flex
                h-9
                items-center
                justify-center
                rounded-[9px]
                border
                border-black/[0.06]
                bg-white/70
                px-3
                text-[10.5px]
                font-semibold
                text-slate-600
                transition
                hover:border-black/[0.10]
                hover:bg-slate-100
                disabled:cursor-not-allowed
                disabled:opacity-50
                sm:flex-1
                dark:border-white/[0.07]
                dark:bg-white/[0.025]
                dark:text-slate-300
                dark:hover:border-white/[0.11]
                dark:hover:bg-white/[0.05]
              "
              disabled={saving}
              onClick={() => {
                void declineAdaptation()
              }}
            >
              Maintenir la séance
            </button>
          </div>
        </section>
      )}

      {state?.adaptation?.decision === 'accepted' && (
        <div
          className={
            state.checkin.unavailable
              ? (
                  'rounded-[10px] border '
                  + 'border-rose-500/15 '
                  + 'bg-rose-500/[0.06] '
                  + 'px-3.5 py-3 '
                  + 'text-[11px] font-medium '
                  + 'text-rose-700 '
                  + 'dark:border-rose-400/15 '
                  + 'dark:bg-rose-400/[0.06] '
                  + 'dark:text-rose-300'
                )
              : (
                  'rounded-[10px] border '
                  + 'border-emerald-500/15 '
                  + 'bg-emerald-500/[0.06] '
                  + 'px-3.5 py-3 '
                  + 'text-[11px] font-medium '
                  + 'text-emerald-700 '
                  + 'dark:border-emerald-400/15 '
                  + 'dark:bg-emerald-400/[0.06] '
                  + 'dark:text-emerald-300'
                )
          }
        >
          <span>
            {state.checkin.unavailable
              ? 'Séance annulée pour aujourd’hui.'
              : 'Adaptation acceptée pour aujourd’hui.'}
          </span>
        </div>
      )}

      {(
        state?.adaptation?.decision === 'accepted'
        && state.checkin.unavailable
        && replanning
        && replanning.proposals.length > 0
      ) && (
        <section
          className="
            rounded-[14px]
            border
            border-emerald-500/15
            bg-emerald-500/[0.035]
            p-4
            dark:border-emerald-400/15
            dark:bg-emerald-400/[0.035]
          "
        >
          <div className="flex items-start gap-3">
            <div
              className="
                flex
                size-9
                shrink-0
                items-center
                justify-center
                rounded-[10px]
                border
                border-emerald-500/10
                bg-emerald-500/[0.08]
                text-emerald-600
                dark:border-emerald-400/10
                dark:bg-emerald-400/[0.08]
                dark:text-emerald-300
              "
            >
              <CalendarDays
                className="h-5 w-5"
              />
            </div>

            <div className="min-w-0">
              <h3
                className="
                  text-[13px]
                  font-semibold
                  tracking-[-0.01em]
                  text-slate-800
                  dark:text-slate-100
                "
              >
                Réorganiser le reste de la semaine
              </h3>

              <p
                className="
                  mt-1
                  text-[10.5px]
                  leading-relaxed
                  text-slate-500
                  dark:text-slate-400
                "
              >
                OpenCoach a analysé les séances restantes
                et vous propose plusieurs choix.
              </p>
            </div>
          </div>

          {replanning.coordination_reasons.length > 0 && (
            <div
              className="
                mt-4
                rounded-[10px]
                border
                border-black/[0.05]
                bg-white/70
                px-3
                py-2.5
                dark:border-white/[0.06]
                dark:bg-white/[0.025]
              "
            >
              <p
                className="
                  text-[9.5px]
                  font-bold
                  uppercase
                  tracking-[0.07em]
                  text-emerald-600
                  dark:text-emerald-400
                "
              >
                Conseil OpenCoach
              </p>

              <p
                className="
                  mt-1.5
                  text-[10.5px]
                  leading-[1.6]
                  text-slate-600
                  dark:text-slate-400
                "
              >
                {replanning.coordination_reasons[0]}
              </p>
            </div>
          )}

          <div className="mt-4 space-y-4">
            {replanning.proposals.map(
              (proposal) => (
                <ReplanningProposalCard
                  key={
                    proposal.source_session.id
                    ?? proposal.source_session.title
                  }
                  proposal={proposal}
                  saving={saving}
                  onChoose={
                    (option) => {
                      void applyReplanning(
                        proposal,
                        option,
                      )
                    }
                  }
                />
              ),
            )}
          </div>
        </section>
      )}

      {state?.adaptation?.decision === 'declined' && (
        <div
          className="
            flex
            items-center
            gap-2.5
            rounded-[10px]
            border
            border-slate-200/80
            bg-slate-50/80
            px-3.5
            py-3
            text-[10.5px]
            font-medium
            text-slate-600
            dark:border-white/[0.07]
            dark:bg-white/[0.025]
            dark:text-slate-300
          "
        >
          <span
            className="
              size-1.5
              shrink-0
              rounded-full
              bg-emerald-500
              dark:bg-emerald-400
            "
            aria-hidden="true"
          />

          <span>
            Vous avez choisi de conserver la séance prévue.
          </span>
        </div>
      )}
    </div>
  )
}


function ReplanningProposalCard({
  proposal,
  saving,
  onChoose,
}: {
  proposal: ReplanningProposal
  saving: boolean
  onChoose: (
    option: ReplanningOption,
  ) => void
}) {
  return (
    <article
      className="
        rounded-[12px]
        border
        border-black/[0.06]
        bg-white/80
        p-3.5
        shadow-[0_1px_2px_rgba(15,23,42,0.02)]
        dark:border-white/[0.07]
        dark:bg-[#171d21]
        dark:shadow-none
      "
    >
      <div>
        <p
          className="
            text-[12px]
            font-semibold
            text-slate-800
            dark:text-slate-100
          "
        >
          {proposal.source_session.title}
        </p>

        <p
          className="
            mt-1
            text-[9.5px]
            font-medium
            text-slate-400
            dark:text-slate-500
          "
        >
          {proposal.source_session.duration_minutes} min
          {' · '}
          {formatReplanningIntensity(
            proposal.source_session.intensity,
          )}
        </p>
      </div>

      <div className="mt-3 grid gap-2">
        {proposal.options.map(
          (option) => (
            <ReplanningOptionButton
              key={
                (
                  option.action
                  + ':'
                  + (
                    option.target_date
                    ?? 'none'
                  )
                )
              }
              option={option}
              disabled={saving}
              onClick={() => {
                onChoose(
                  option,
                )
              }}
            />
          ),
        )}
      </div>
    </article>
  )
}


function ReplanningOptionButton({
  option,
  disabled,
  onClick,
}: {
  option: ReplanningOption
  disabled: boolean
  onClick: () => void
}) {
  const recommended =
    option.recommended

  const session =
    option.session

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={[
        (
          'relative flex w-full items-center gap-3 '
          + 'rounded-[10px] border px-3 py-3 '
          + 'text-left outline-none transition '
          + 'disabled:cursor-not-allowed '
          + 'disabled:opacity-50'
        ),
        recommended
          ? (
              'border-emerald-500/20 '
              + 'bg-emerald-500/[0.055] '
              + 'hover:border-emerald-500/30 '
              + 'hover:bg-emerald-500/[0.09] '
              + 'dark:border-emerald-400/20 '
              + 'dark:bg-emerald-400/[0.045] '
              + 'dark:hover:bg-emerald-400/[0.08]'
            )
          : (
              'border-black/[0.06] '
              + 'bg-white/70 '
              + 'hover:border-black/[0.10] '
              + 'hover:bg-slate-50 '
              + 'dark:border-white/[0.07] '
              + 'dark:bg-white/[0.02] '
              + 'dark:hover:border-white/[0.11] '
              + 'dark:hover:bg-white/[0.045]'
            ),
      ].join(' ')}
    >
      <div
        className={[
          (
            'flex size-8 shrink-0 items-center '
            + 'justify-center rounded-[8px]'
          ),
          recommended
            ? (
                'bg-emerald-500/[0.10] '
                + 'text-emerald-600 '
                + 'dark:bg-emerald-400/[0.10] '
                + 'dark:text-emerald-300'
              )
            : (
                'bg-slate-100 text-slate-400 '
                + 'dark:bg-white/[0.04] '
                + 'dark:text-slate-500'
              ),
        ].join(' ')}
      >
        {getReplanningIcon(
          option.action,
        )}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span
            className="
              text-[11.5px]
              font-semibold
              text-slate-800
              dark:text-slate-100
            "
          >
            {getReplanningActionLabel(
              option.action,
            )}
          </span>

          {recommended && (
            <span
              className="
                inline-flex
                items-center
                rounded-full
                border
                border-emerald-500/15
                bg-emerald-500/[0.08]
                px-2
                py-0.5
                text-[8.5px]
                font-bold
                uppercase
                tracking-[0.055em]
                text-emerald-700
                dark:border-emerald-400/15
                dark:bg-emerald-400/[0.08]
                dark:text-emerald-300
              "
            >
              Conseil OpenCoach
            </span>
          )}

          <span
            className={[
              (
                'inline-flex items-center rounded-full '
                + 'border px-2 py-0.5 '
                + 'text-[8.5px] font-semibold'
              ),
              getRiskBadgeClass(
                option.risk,
              ),
            ].join(' ')}
          >
            {getRiskLabel(
              option.risk,
            )}
          </span>
        </div>

        <p
          className="
            mt-1
            text-[9.5px]
            text-slate-400
            dark:text-slate-500
          "
        >
          {option.target_date
            ? formatReschedulingDate(
                option.target_date,
              )
            : 'Aucun report'}
          {session
            ? (
                ` · ${session.duration_minutes} min`
              )
            : ''}
        </p>

        {(
          option.action
          === 'move_adapted'
          && session
        ) && (
          <p
            className="
              mt-1
              text-[9.5px]
              leading-relaxed
              text-slate-500
              dark:text-slate-400
            "
          >
            {session.title}
          </p>
        )}
      </div>

      <MoveRight
        className="
          h-4
          w-4
          shrink-0
          text-slate-300
          transition
          dark:text-slate-600
        "
        strokeWidth={1.8}
      />
    </button>
  )
}


function getReplanningIcon(
  action: ReplanningAction,
) {
  if (action === 'cancel') {
    return (
      <CircleX className="h-4 w-4" />
    )
  }

  return (
    <CalendarDays className="h-4 w-4" />
  )
}


function getReplanningActionLabel(
  action: ReplanningAction,
): string {
  if (action === 'cancel') {
    return 'Annuler définitivement'
  }

  if (
    action
    === 'move_adapted'
  ) {
    return 'Déplacer et adapter'
  }

  return 'Déplacer sans modifier'
}


function getReplanningSuccessTitle(
  action: ReplanningAction,
): string {
  if (action === 'cancel') {
    return 'Séance annulée'
  }

  if (
    action
    === 'move_adapted'
  ) {
    return 'Séance déplacée et adaptée'
  }

  return 'Séance déplacée'
}


function getRiskLabel(
  risk: ReplanningOption['risk'],
): string {
  if (risk === 'high') {
    return 'Charge élevée'
  }

  if (risk === 'moderate') {
    return 'À surveiller'
  }

  return 'Faible impact'
}


function getRiskBadgeClass(
  risk: ReplanningOption['risk'],
): string {
  if (risk === 'high') {
    return (
      'border-rose-500/15 '
      + 'bg-rose-500/[0.07] '
      + 'text-rose-700 '
      + 'dark:border-rose-400/15 '
      + 'dark:bg-rose-400/[0.07] '
      + 'dark:text-rose-300'
    )
  }

  if (risk === 'moderate') {
    return (
      'border-amber-500/15 '
      + 'bg-amber-500/[0.07] '
      + 'text-amber-700 '
      + 'dark:border-amber-400/15 '
      + 'dark:bg-amber-400/[0.07] '
      + 'dark:text-amber-300'
    )
  }

  return (
    'border-emerald-500/15 '
    + 'bg-emerald-500/[0.07] '
    + 'text-emerald-700 '
    + 'dark:border-emerald-400/15 '
    + 'dark:bg-emerald-400/[0.07] '
    + 'dark:text-emerald-300'
  )
}


function formatReplanningIntensity(
  intensity: string,
): string {
  const normalized =
    intensity
      .trim()
      .toLowerCase()

  if (
    normalized === 'hard'
    || normalized === 'very_hard'
  ) {
    return 'Intense'
  }

  if (
    normalized === 'easy'
  ) {
    return 'Facile'
  }

  return intensity
}


function formatReschedulingDate(
  value: string,
  short = false,
): string {
  const parsed = new Date(
    `${value}T12:00:00`,
  )

  return new Intl.DateTimeFormat(
    'fr-FR',
    short
      ? {
          weekday: 'long',
          day: 'numeric',
        }
      : {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
        },
  ).format(
    parsed,
  )
}


interface DetailsContext {
  illness: boolean
  unavailable: boolean
  comfort: number
}


function getDetailsTitle({
  illness,
  unavailable,
  comfort,
}: DetailsContext): string {
  if (
    illness
    && unavailable
  ) {
    return 'Précisez votre situation'
  }

  if (illness) {
    return 'Quels symptômes avez-vous ?'
  }

  if (unavailable) {
    return 'Pourquoi êtes-vous indisponible ?'
  }

  if (comfort < 5) {
    return 'Précisez votre gêne'
  }

  return 'Précisions'
}


function getDetailsHelp({
  illness,
  unavailable,
  comfort,
}: DetailsContext): string {
  if (illness) {
    return (
      'Ces informations aideront le coach '
      + 'à évaluer la séance prévue.'
    )
  }

  if (unavailable) {
    return (
      'Indiquez simplement la raison '
      + 'ou la contrainte du jour.'
    )
  }

  if (comfort < 5) {
    return (
      'Décrivez brièvement la douleur, '
      + 'son évolution ou ce qui la déclenche.'
    )
  }

  return ''
}


function getDetailsPlaceholder({
  illness,
  unavailable,
  comfort,
}: DetailsContext): string {
  if (
    illness
    && unavailable
  ) {
    return (
      'Ex. fièvre depuis cette nuit, '
      + 'repos nécessaire aujourd’hui...'
    )
  }

  if (illness) {
    return (
      'Ex. mal de gorge, fatigue, '
      + 'fièvre légère depuis ce matin...'
    )
  }

  if (unavailable) {
    return (
      'Ex. déplacement professionnel, '
      + 'garde, journée impossible...'
    )
  }

  if (comfort < 5) {
    return (
      'Ex. gêne au genou depuis hier, '
      + 'surtout dans les descentes...'
    )
  }

  return ''
}



function RatingPicker({
  icon: Icon,
  label,
  description,
  value,
  onChange,
}: {
  icon: typeof Star
  label: string
  description: string
  value: number
  onChange: (
    value: number,
  ) => void
}) {
  return (
    <section
      className="
        rounded-[11px]
        border
        border-black/[0.06]
        p-3
        dark:border-white/[0.07]
      "
    >
      <div className="flex items-center gap-2">
        <Icon
          className={
            label === 'Énergie'
              ? (
                  'h-4 w-4 '
                  + 'text-emerald-500 '
                  + 'dark:text-emerald-400'
                )
              : (
                  'h-4 w-4 '
                  + 'text-rose-500 '
                  + 'dark:text-rose-400'
                )
          }
          strokeWidth={1.8}
        />

        <div>
          <h3 className="text-sm font-semibold">
            {label}
          </h3>

          <p
            className="
              text-[10px]
              leading-relaxed
              text-slate-400
              dark:text-slate-500
            "
          >
            {description}
          </p>
        </div>
      </div>

      <div className="mt-3">
        <RatingIcons
          kind={
            label === 'Énergie'
              ? 'energy'
              : 'comfort'
          }
          value={value}
          interactive
          size="md"
          onChange={onChange}
        />
      </div>
    </section>
  )
}


function notifyUpdated() {
  window.dispatchEvent(
    new Event(
      'opencoach:daily-checkin-updated',
    ),
  )
}
