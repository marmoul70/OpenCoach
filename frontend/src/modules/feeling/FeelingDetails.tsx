import {
  Heart,
  Star,
} from 'lucide-react'
import {
  useEffect,
  useState,
} from 'react'

import {
  acceptDailyAdaptation,
  declineDailyAdaptation,
  fetchTodayCheckIn,
  saveDailyCheckIn,
  type BodySide,
  type DailyCheckInState,
  type PainArea,
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
        <span className="loading loading-spinner loading-md text-info" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <section>
        <h3 className="font-semibold text-base-content">
          Comment vous sentez-vous ?
        </h3>

        <p className="mt-1 text-sm text-base-content/50">
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
        <section className="rounded-xl border border-base-300 bg-base-200/30 p-4">
          <h3 className="text-sm font-semibold text-base-content">
            Où ressentez-vous une gêne ?
          </h3>

          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <label className="form-control">
              <span className="label-text mb-1 text-xs text-base-content/50">
                Zone
              </span>

              <select
                className="select select-bordered w-full"
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

            <label className="form-control">
              <span className="label-text mb-1 text-xs text-base-content/50">
                Côté
              </span>

              <select
                className="select select-bordered w-full"
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
        <label className="flex cursor-pointer items-center justify-between rounded-xl border border-base-300 px-4 py-3">
          <div>
            <p className="text-sm font-semibold">
              Je suis malade
            </p>

            <p className="text-xs text-base-content/45">
              Symptômes ou état infectieux
            </p>
          </div>

          <input
            type="checkbox"
            className="toggle toggle-warning"
            checked={illness}
            onChange={(event) => {
              setIllness(
                event.target.checked,
              )
            }}
          />
        </label>

        <label className="flex cursor-pointer items-center justify-between rounded-xl border border-base-300 px-4 py-3">
          <div>
            <p className="text-sm font-semibold">
              Je suis indisponible
            </p>

            <p className="text-xs text-base-content/45">
              Impossible de m’entraîner aujourd’hui
            </p>
          </div>

          <input
            type="checkbox"
            className="toggle toggle-error"
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
        <section className="rounded-xl border border-base-300 bg-base-200/25 p-4">
          <label
            htmlFor="daily-feeling-note"
            className="block"
          >
            <span className="text-sm font-semibold text-base-content">
              {getDetailsTitle({
                illness,
                unavailable,
                comfort,
              })}
            </span>

            <span className="mt-1 block text-xs text-base-content/45">
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
              textarea
              textarea-bordered
              mt-3
              block
              min-h-24
              w-full
              resize-y
              bg-base-100
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
        className="btn btn-primary w-full"
        disabled={saving}
        onClick={() => {
          void save()
        }}
      >
        {saving && (
          <span className="loading loading-spinner loading-xs" />
        )}

        Enregistrer mon ressenti
      </button>

      {state?.adaptation?.awaiting_athlete_decision && (
        <section
          className={
            state.checkin.unavailable
              ? (
                  'rounded-xl border border-error/40 '
                  + 'bg-error/5 p-4'
                )
              : (
                  'rounded-xl border border-warning/40 '
                  + 'bg-warning/5 p-4'
                )
          }
        >
          <div
            className={
              state.checkin.unavailable
                ? 'badge badge-error badge-sm'
                : 'badge badge-warning badge-sm'
            }
          >
            {state.checkin.unavailable
              ? 'Annulation recommandée'
              : 'Proposition du coach'}
          </div>

          <p className="mt-3 font-semibold text-base-content">
            {state.checkin.unavailable
              ? (
                  'Vous avez indiqué être indisponible aujourd’hui. '
                  + 'Voulez-vous annuler la séance prévue ?'
                )
              : state.adaptation.recommendation}
          </p>

          <p className="mt-2 text-sm leading-relaxed text-base-content/60">
            {state.adaptation.reason}
          </p>

          <p className="mt-3 text-sm text-base-content/60">
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
                  ? 'btn btn-error sm:flex-1'
                  : 'btn btn-warning sm:flex-1'
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
              className="btn btn-ghost sm:flex-1"
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
              ? 'alert alert-error'
              : 'alert alert-success'
          }
        >
          <span>
            {state.checkin.unavailable
              ? 'Séance annulée pour aujourd’hui.'
              : 'Adaptation acceptée pour aujourd’hui.'}
          </span>
        </div>
      )}

      {state?.adaptation?.decision === 'declined' && (
        <div className="alert">
          <span>
            Vous avez choisi de conserver la séance prévue.
          </span>
        </div>
      )}
    </div>
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
    <section className="rounded-xl border border-base-300 p-3">
      <div className="flex items-center gap-2">
        <Icon
          className={
            label === 'Énergie'
              ? 'h-4 w-4 text-success'
              : 'h-4 w-4 text-error'
          }
          strokeWidth={1.8}
        />

        <div>
          <h3 className="text-sm font-semibold">
            {label}
          </h3>

          <p className="text-xs text-base-content/45">
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
