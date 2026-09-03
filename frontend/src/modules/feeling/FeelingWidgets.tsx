import {
  Activity,
  Bed,
  Check,
  ChevronDown,
  Heart,
  Star,
} from 'lucide-react'

import {
  useEffect,
  useState,
} from 'react'

import {
  declineDailyAdaptation,
  fetchTodayCheckIn,
  saveDailyCheckIn,
  type BodySide,
  type DailyCheckInState,
  type PainArea,
  type PainLocation,
} from '../../core/checkin'

import {
  useToast,
} from '../../components/ui/ToastProvider'


import {
  DailyDecisionModal,
} from './DailyDecisionModal'


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


const BODY_SIDES: Array<{
  value: BodySide
  label: string
}> = [
  { value: 'left', label: 'Gauche' },
  { value: 'right', label: 'Droite' },
  { value: 'both', label: 'Des deux côtés' },
  { value: 'center', label: 'Centre' },
  {
    value: 'not_applicable',
    label: 'Non applicable',
  },
]


export function FeelingWidgets() {
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
    decisionModalOpen,
    setDecisionModalOpen,
  ] = useState(
    false,
  )


  useEffect(() => {
    let cancelled =
      false

    async function load() {
      try {
        const result =
          await fetchTodayCheckIn()

        if (
          cancelled
        ) {
          return
        }

        setState(
          result,
        )
      } catch (reason) {
        toast({
          type: 'error',
          title: 'Ressenti',
          message:
            reason instanceof Error
              ? reason.message
              : (
                  'Impossible de charger '
                  + 'le ressenti du jour.'
                ),
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


  async function refreshState() {
    const result =
      await fetchTodayCheckIn()

    setState(
      result,
    )
  }


  async function declineCoachAction() {
    if (
      !state
      || !state.adaptation
    ) {
      return
    }

    try {
      await declineDailyAdaptation(
        state.checkin.id,
      )

      await refreshState()

      toast({
        type: 'success',
        title: 'Adaptation annulée',
        message:
          'Le planning actuel est conservé.',
      })
    } catch (reason) {
      toast({
        type: 'error',
        title: 'Décision impossible',
        message:
          getErrorMessage(
            reason,
          ),
      })
    }
  }


  async function persist(
    changes: Partial<{
      energy: number
      comfort: number
      illness: boolean
      unavailable: boolean
      painLocations: PainLocation[]
      note: string | null
    }>,
  ): Promise<DailyCheckInState> {
    const current =
      state?.checkin

    const payload = {
      energy_rating:
        changes.energy
        ?? current?.energy_rating
        ?? 5,

      pain_wellness_rating:
        changes.comfort
        ?? current?.pain_wellness_rating
        ?? 5,

      illness:
        changes.illness
        ?? current?.illness
        ?? false,

      unavailable:
        changes.unavailable
        ?? current?.unavailable
        ?? false,

      pain_locations:
        changes.painLocations
        ?? current?.pain_locations
        ?? [],

      note:
        changes.note
        !== undefined
          ? changes.note
          : current?.note
            ?? null,
    }

    const result =
      await saveDailyCheckIn(
        payload,
      )

    setState(
      result,
    )

    return result
  }


  if (loading) {
    return (
      <div
        className="
          flex
          min-h-64
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
    )
  }


  return (
    <div className="space-y-4">
      <section>
        <div
          className="
            mb-3
            flex
            items-end
            justify-between
            gap-3
          "
        >
          <div>
            <p
              className="
                text-[9px]
                font-bold
                uppercase
                tracking-[0.10em]
                text-slate-400
                dark:text-slate-500
              "
            >
              Check-in
            </p>

            <h2
              className="
                mt-0.5
                text-[15px]
                font-semibold
                tracking-[-0.02em]
                text-slate-800
                dark:text-slate-200
              "
            >
              Ton état aujourd’hui
            </h2>
          </div>

          <span
            className="
              text-[9px]
              font-medium
              text-emerald-600
              dark:text-emerald-400
            "
          >
            Sauvegarde auto
          </span>
        </div>


        <div
          className="
            grid
            gap-3
            md:grid-cols-2
          "
        >
          <EnergyWidget
            value={
              state?.checkin.energy_rating
              ?? 5
            }
            onSave={async (value) => {
              await persist({
                energy:
                  value,
              })
            }}
          />

          <PainWidget
            value={
              state
                ?.checkin
                .pain_wellness_rating
              ?? 5
            }
            locations={
              state
                ?.checkin
                .pain_locations
              ?? []
            }
            onSave={async (
              value,
              locations,
            ) => {
              await persist({
                comfort:
                  value,
                painLocations:
                  locations,
              })
            }}
          />

          <IllnessWidget
            value={
              state?.checkin.illness
              ?? false
            }
            onSave={async (value) => {
              await persist({
                illness:
                  value,
              })
            }}
          />

          <AvailabilityWidget
            value={
              state?.checkin.unavailable
              ?? false
            }
            reason={
              state?.checkin.note
              ?? ''
            }
            onSave={async (
              value,
              reason,
            ) => {
              await persist({
                unavailable:
                  value,
                note:
                  reason.trim()
                    ? reason.trim()
                    : null,
              })
            }}
          />
        </div>
      </section>

      {state
        && (
          state.adaptation
            ?.awaiting_athlete_decision
          || (
            state.checkin
              .pain_wellness_rating
            <= 3
          )
        )
        && (
          <CoachActionCard
            state={state}
            forcePainAdaptation={
              !state.adaptation
                ?.awaiting_athlete_decision
              && (
                state.checkin
                  .pain_wellness_rating
                <= 3
              )
            }
            onOpen={() => {
              setDecisionModalOpen(
                true,
              )
            }}
            onCancel={() => {
              void declineCoachAction()
            }}
          />
        )}


      <DailyDecisionModal
        open={decisionModalOpen}
        state={state}
        onClose={() => {
          setDecisionModalOpen(
            false,
          )
        }}
        onStateChanged={
          refreshState
        }
      />

    </div>
  )
}


function EnergyWidget({
  value,
  onSave,
}: {
  value: number
  onSave: (
    value: number,
  ) => Promise<void>
}) {
  const {
    toast,
  } = useToast()

  const [
    current,
    setCurrent,
  ] = useState(
    value,
  )

  const [
    saving,
    setSaving,
  ] = useState(
    false,
  )


  useEffect(() => {
    setCurrent(
      value,
    )
  }, [
    value,
  ])


  async function change(
    nextValue: number,
  ) {
    const previous =
      current

    setCurrent(
      nextValue,
    )

    setSaving(
      true,
    )

    try {
      await onSave(
        nextValue,
      )

      toast({
        type: 'success',
        title: 'Énergie enregistrée',
        message:
          `Niveau d’énergie : ${nextValue}/5.`,
      })
    } catch (reason) {
      setCurrent(
        previous,
      )

      toast({
        type: 'error',
        title: 'Énergie',
        message:
          getErrorMessage(
            reason,
          ),
      })
    } finally {
      setSaving(
        false,
      )
    }
  }


  return (
    <FeelingCard
      icon={Star}
      title="Énergie"
      description="Votre niveau de fraîcheur aujourd’hui."
      saving={saving}
    >
      <RatingButtons
        value={current}
        disabled={saving}
        variant="energy"
        onChange={(nextValue) => {
          void change(
            nextValue,
          )
        }}
      />

      <p
        className="
          mt-3
          text-[10px]
          text-slate-400
          dark:text-slate-500
        "
      >
        1 = épuisé · 5 = très frais
      </p>
    </FeelingCard>
  )
}


function PainWidget({
  value,
  locations,
  onSave,
}: {
  value: number
  locations: PainLocation[]
  onSave: (
    value: number,
    locations: PainLocation[],
  ) => Promise<void>
}) {
  const {
    toast,
  } = useToast()

  const initialLocation =
    locations[0]

  const [
    current,
    setCurrent,
  ] = useState(
    value,
  )

  const [
    area,
    setArea,
  ] = useState<PainArea>(
    initialLocation?.area
    ?? 'other',
  )

  const [
    side,
    setSide,
  ] = useState<BodySide>(
    initialLocation?.side
    ?? 'not_applicable',
  )

  const [
    saving,
    setSaving,
  ] = useState(
    false,
  )


  useEffect(() => {
    setCurrent(
      value,
    )

    const location =
      locations[0]

    if (location) {
      setArea(
        location.area,
      )

      setSide(
        location.side,
      )
    }
  }, [
    value,
    locations,
  ])


  async function selectRating(
    nextValue: number,
  ) {
    const previous =
      current

    setCurrent(
      nextValue,
    )

    setSaving(
      true,
    )

    try {
      /*
       * Même fonctionnement qu'Énergie :
       *
       * la note est envoyée immédiatement
       * au backend afin que le moteur Coach
       * puisse recalculer l'adaptation.
       *
       * Pour une gêne < 5, la localisation
       * sera ajoutée dans un second temps
       * via validatePain().
       */
      await onSave(
        nextValue,
        nextValue >= 5
          ? []
          : locations,
      )

      toast({
        type: 'success',
        title: 'Douleur enregistrée',
        message:
          nextValue >= 5
            ? 'Aucune douleur signalée.'
            : (
                `Niveau de confort : `
                + `${nextValue}/5. `
                + 'Précisez maintenant la zone.'
              ),
      })
    } catch (reason) {
      setCurrent(
        previous,
      )

      toast({
        type: 'error',
        title: 'Douleur',
        message:
          getErrorMessage(
            reason,
          ),
      })
    } finally {
      setSaving(
        false,
      )
    }
  }


  async function validatePain() {
    if (current >= 5) {
      return
    }

    if (
      !area
      || !side
    ) {
      toast({
        type: 'warning',
        title: 'Douleur',
        message:
          'Sélectionnez une zone et un côté.',
      })

      return
    }

    setSaving(
      true,
    )

    try {
      await onSave(
        current,
        [
          {
            area,
            side,
          },
        ],
      )

      toast({
        type: 'success',
        title: 'Douleur enregistrée',
        message:
          'La gêne a été prise en compte par OpenCoach.',
      })
    } catch (reason) {
      toast({
        type: 'error',
        title: 'Douleur',
        message:
          getErrorMessage(
            reason,
          ),
      })
    } finally {
      setSaving(
        false,
      )
    }
  }


  return (
    <FeelingCard
      icon={Heart}
      title="Douleur"
      description="Votre confort physique aujourd’hui."
      saving={saving}
    >
      <RatingButtons
        value={current}
        disabled={saving}
        variant="pain"
        onChange={(nextValue) => {
          void selectRating(
            nextValue,
          )
        }}
      />

      <p
        className="
          mt-3
          text-[10px]
          text-slate-400
          dark:text-slate-500
        "
      >
        1 = douleur importante · 5 = aucune douleur
      </p>

      {current < 5 && (
        <div
          className="
            mt-4
            space-y-3
            border-t
            border-black/[0.065] dark:border-white/[0.065]
            pt-4
          "
        >
          <div
            className="
              grid
              gap-3
              sm:grid-cols-2
            "
          >
            <label className="block">
              <span
                className="
                  mb-1
                  text-xs
                  font-medium
                  text-slate-500 dark:text-slate-400
                "
              >
                Zone
              </span>

              <div className="relative">
                <select
                  className="
                  h-10
                  w-full
                  appearance-none
                  rounded-[9px]
                  border
                  border-black/[0.07]
                  bg-slate-50
                  px-3
                  pr-9
                  text-[11px]
                  font-medium
                  text-slate-700
                  outline-none
                  transition
                  hover:border-black/[0.11]
                  hover:bg-white
                  focus:border-emerald-500/35
                  focus:ring-2
                  focus:ring-emerald-500/[0.08]
                  dark:border-white/[0.07]
                  dark:bg-[#1a2024]
                  dark:text-slate-200
                  dark:hover:border-white/[0.12]
                  dark:hover:bg-[#1d2428]
                  dark:focus:border-emerald-400/30
                  dark:focus:ring-emerald-400/[0.08]
                "
                value={area}
                disabled={saving}
                onChange={(event) => {
                  setArea(
                    event.target.value as PainArea,
                  )
                }}
              >
                {PAIN_AREAS.map(
                  (item) => (
                    <option
                      key={item.value}
                      value={item.value}
                    >
                      {item.label}
                    </option>
                  ),
                )}
                </select>

                <ChevronDown
                  className="
                    pointer-events-none
                    absolute
                    right-3
                    top-1/2
                    h-3.5
                    w-3.5
                    -translate-y-1/2
                    text-slate-400
                    dark:text-slate-500
                  "
                  strokeWidth={1.8}
                />
              </div>
            </label>

            <label className="block">
              <span
                className="
                  mb-1
                  text-xs
                  font-medium
                  text-slate-500 dark:text-slate-400
                "
              >
                Côté
              </span>

              <div className="relative">
                <select
                  className="
                  h-10
                  w-full
                  appearance-none
                  rounded-[9px]
                  border
                  border-black/[0.07]
                  bg-slate-50
                  px-3
                  pr-9
                  text-[11px]
                  font-medium
                  text-slate-700
                  outline-none
                  transition
                  hover:border-black/[0.11]
                  hover:bg-white
                  focus:border-emerald-500/35
                  focus:ring-2
                  focus:ring-emerald-500/[0.08]
                  dark:border-white/[0.07]
                  dark:bg-[#1a2024]
                  dark:text-slate-200
                  dark:hover:border-white/[0.12]
                  dark:hover:bg-[#1d2428]
                  dark:focus:border-emerald-400/30
                  dark:focus:ring-emerald-400/[0.08]
                "
                value={side}
                disabled={saving}
                onChange={(event) => {
                  setSide(
                    event.target.value as BodySide,
                  )
                }}
              >
                {BODY_SIDES.map(
                  (item) => (
                    <option
                      key={item.value}
                      value={item.value}
                    >
                      {item.label}
                    </option>
                  ),
                )}
                </select>

                <ChevronDown
                  className="
                    pointer-events-none
                    absolute
                    right-3
                    top-1/2
                    h-3.5
                    w-3.5
                    -translate-y-1/2
                    text-slate-400
                    dark:text-slate-500
                  "
                  strokeWidth={1.8}
                />
              </div>
            </label>
          </div>

          <button
            type="button"
            className="
              inline-flex
              h-9
              items-center
              justify-center
              gap-2
              rounded-[9px]
              border
              border-emerald-500/15
              bg-emerald-500/[0.09]
              px-3.5
              text-[11px]
              font-semibold
              text-emerald-700
              outline-none
              transition
              hover:border-emerald-500/25
              hover:bg-emerald-500/[0.14]
              active:scale-[0.98]
              disabled:cursor-not-allowed
              disabled:opacity-50
              dark:border-emerald-400/15
              dark:bg-emerald-400/[0.08]
              dark:text-emerald-300
              dark:hover:border-emerald-400/25
              dark:hover:bg-emerald-400/[0.13]
            "
            disabled={saving}
            onClick={() => {
              void validatePain()
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
                  border-emerald-500/20
                  border-t-emerald-500
                "
              />
            )}

            Valider la douleur
          </button>
        </div>
      )}
    </FeelingCard>
  )
}


function IllnessWidget({
  value,
  onSave,
}: {
  value: boolean
  onSave: (
    value: boolean,
  ) => Promise<void>
}) {
  const {
    toast,
  } = useToast()

  const [
    current,
    setCurrent,
  ] = useState(
    value,
  )

  const [
    saving,
    setSaving,
  ] = useState(
    false,
  )


  useEffect(() => {
    setCurrent(
      value,
    )
  }, [
    value,
  ])


  async function change() {
    const previous =
      current

    const nextValue =
      !current

    setCurrent(
      nextValue,
    )

    setSaving(
      true,
    )

    try {
      await onSave(
        nextValue,
      )

      toast({
        type:
          nextValue
            ? 'warning'
            : 'success',

        title:
          nextValue
            ? 'État malade activé'
            : 'État malade retiré',

        message:
          nextValue
            ? (
                'OpenCoach prend en compte '
                + 'votre état de santé.'
              )
            : (
                'Vous n’êtes plus signalé '
                + 'comme malade aujourd’hui.'
              ),
      })
    } catch (reason) {
      setCurrent(
        previous,
      )

      toast({
        type: 'error',
        title: 'État de santé',
        message:
          getErrorMessage(
            reason,
          ),
      })
    } finally {
      setSaving(
        false,
      )
    }
  }


  return (
    <button
      type="button"
      disabled={saving}
      aria-pressed={current}
      onClick={() => {
        void change()
      }}
      className={[
        (
          'group w-full '
          + 'rounded-[13px] '
          + 'border p-4 '
          + 'text-left '
          + 'transition '
          + 'disabled:cursor-wait'
        ),
        current
          ? (
              'border-amber-400/30 '
              + 'bg-amber-400/[0.07] '
              + 'shadow-[inset_0_0_0_1px_rgba(251,191,36,0.03)] '
              + 'dark:bg-amber-400/[0.055]'
            )
          : (
              'border-black/[0.065] '
              + 'bg-white '
              + 'hover:border-black/[0.11] '
              + 'hover:bg-slate-50/70 '
              + 'dark:border-white/[0.065] '
              + 'dark:bg-[#151b1f] '
              + 'dark:hover:border-white/[0.11] '
              + 'dark:hover:bg-white/[0.025]'
            ),
      ].join(' ')}
    >
      <div
        className="
          flex
          items-center
          gap-3
        "
      >
        <div
          className={[
            (
              'flex h-9 w-9 '
              + 'shrink-0 '
              + 'items-center '
              + 'justify-center '
              + 'rounded-[9px]'
            ),
            current
              ? (
                  'bg-amber-400/[0.12] '
                  + 'text-amber-600 '
                  + 'dark:text-amber-400'
                )
              : (
                  'bg-slate-100 '
                  + 'text-slate-400 '
                  + 'dark:bg-white/[0.04] '
                  + 'dark:text-slate-500'
                ),
          ].join(' ')}
        >
          <Bed
            className="
              h-4
              w-4
            "
          />
        </div>


        <div
          className="
            min-w-0
            flex-1
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
            <h2
              className="
                text-[13px]
                font-semibold
                text-slate-800
                dark:text-slate-200
              "
            >
              Santé
            </h2>

            {current && (
              <span
                className="
                  inline-flex
                  rounded-full
                  bg-amber-400/[0.10]
                  px-2
                  py-0.5
                  text-[8px]
                  font-bold
                  uppercase
                  tracking-[0.06em]
                  text-amber-700
                  dark:text-amber-400
                "
              >
                Malade
              </span>
            )}

            {saving && (
              <span
                className="
                  h-3.5
                  w-3.5
                  animate-spin
                  rounded-full
                  border-2
                  border-amber-500/20
                  border-t-amber-500
                "
              />
            )}
          </div>

          <p
            className="
              mt-1
              text-[10px]
              leading-4
              text-slate-400
              dark:text-slate-500
            "
          >
            {current
              ? (
                  'Ton état de santé est pris '
                  + 'en compte par OpenCoach.'
                )
              : (
                  'Aucun symptôme signalé aujourd’hui.'
                )}
          </p>
        </div>


        <div
          className={[
            (
              'flex h-6 w-6 '
              + 'shrink-0 '
              + 'items-center '
              + 'justify-center '
              + 'rounded-full '
              + 'border transition'
            ),
            current
              ? (
                  'border-amber-500/35 '
                  + 'bg-amber-500 '
                  + 'text-white'
                )
              : (
                  'border-black/[0.10] '
                  + 'text-transparent '
                  + 'group-hover:border-black/[0.18] '
                  + 'dark:border-white/[0.12] '
                  + 'dark:group-hover:border-white/[0.20]'
                ),
          ].join(' ')}
        >
          <Check
            className="
              h-3.5
              w-3.5
            "
            strokeWidth={3}
          />
        </div>
      </div>
    </button>
  )
}


function AvailabilityWidget({
  value,
  reason,
  onSave,
}: {
  value: boolean
  reason: string
  onSave: (
    value: boolean,
    reason: string,
  ) => Promise<void>
}) {
  const {
    toast,
  } = useToast()

  const [
    current,
    setCurrent,
  ] = useState(
    value,
  )

  const [
    currentReason,
    setCurrentReason,
  ] = useState(
    reason,
  )

  const [
    saving,
    setSaving,
  ] = useState(
    false,
  )


  useEffect(() => {
    setCurrent(
      value,
    )

    setCurrentReason(
      reason,
    )
  }, [
    value,
    reason,
  ])


  async function toggleAvailability() {
    const previous =
      current

    const nextValue =
      !current

    setCurrent(
      nextValue,
    )

    setSaving(
      true,
    )

    try {
      await onSave(
        nextValue,
        nextValue
          ? currentReason
          : '',
      )

      toast({
        type:
          nextValue
            ? 'warning'
            : 'success',

        title:
          nextValue
            ? 'Indisponibilité enregistrée'
            : 'Disponibilité restaurée',

        message:
          nextValue
            ? (
                'Vous pouvez maintenant préciser '
                + 'la raison de votre indisponibilité.'
              )
            : (
                'Vous êtes de nouveau disponible.'
              ),
      })
    } catch (reason) {
      setCurrent(
        previous,
      )

      toast({
        type: 'error',
        title: 'Disponibilité',
        message:
          getErrorMessage(
            reason,
          ),
      })
    } finally {
      setSaving(
        false,
      )
    }
  }


  async function validateReason() {
    if (!current) {
      return
    }

    if (
      currentReason.trim().length < 3
    ) {
      toast({
        type: 'warning',
        title: 'Motif requis',
        message:
          'Précisez brièvement la raison '
          + 'de votre indisponibilité.',
      })

      return
    }

    if (
      currentReason.length > 500
    ) {
      toast({
        type: 'warning',
        title: 'Motif trop long',
        message:
          'Le motif est limité à 500 caractères.',
      })

      return
    }

    setSaving(
      true,
    )

    try {
      await onSave(
        true,
        currentReason,
      )

      toast({
        type: 'success',
        title: 'Motif enregistré',
        message:
          'OpenCoach prendra cette information '
          + 'en compte.',
      })
    } catch (reason) {
      toast({
        type: 'error',
        title: 'Disponibilité',
        message:
          getErrorMessage(
            reason,
          ),
      })
    } finally {
      setSaving(
        false,
      )
    }
  }


  return (
    <section
      className={[
        (
          'rounded-[13px] '
          + 'border p-4 '
          + 'transition'
        ),
        current
          ? (
              'border-rose-400/25 '
              + 'bg-rose-400/[0.06] '
              + 'dark:bg-rose-400/[0.045]'
            )
          : (
              'border-black/[0.065] '
              + 'bg-white '
              + 'dark:border-white/[0.065] '
              + 'dark:bg-[#151b1f]'
            ),
      ].join(' ')}
    >
      <button
        type="button"
        disabled={saving}
        aria-pressed={current}
        onClick={() => {
          void toggleAvailability()
        }}
        className="
          group
          flex
          w-full
          items-center
          gap-3
          text-left
          disabled:cursor-wait
        "
      >
        <div
          className={[
            (
              'flex h-9 w-9 '
              + 'shrink-0 '
              + 'items-center '
              + 'justify-center '
              + 'rounded-[9px]'
            ),
            current
              ? (
                  'bg-rose-400/[0.11] '
                  + 'text-rose-600 '
                  + 'dark:text-rose-400'
                )
              : (
                  'bg-slate-100 '
                  + 'text-slate-400 '
                  + 'dark:bg-white/[0.04] '
                  + 'dark:text-slate-500'
                ),
          ].join(' ')}
        >
          <Activity
            className="
              h-4
              w-4
            "
          />
        </div>


        <div
          className="
            min-w-0
            flex-1
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
            <h2
              className="
                text-[13px]
                font-semibold
                text-slate-800
                dark:text-slate-200
              "
            >
              Disponibilité
            </h2>

            {current && (
              <span
                className="
                  inline-flex
                  rounded-full
                  bg-rose-400/[0.10]
                  px-2
                  py-0.5
                  text-[8px]
                  font-bold
                  uppercase
                  tracking-[0.06em]
                  text-rose-700
                  dark:text-rose-400
                "
              >
                Indisponible
              </span>
            )}

            {saving && (
              <span
                className="
                  h-3.5
                  w-3.5
                  animate-spin
                  rounded-full
                  border-2
                  border-rose-500/20
                  border-t-rose-500
                "
              />
            )}
          </div>

          <p
            className="
              mt-1
              text-[10px]
              leading-4
              text-slate-400
              dark:text-slate-500
            "
          >
            {current
              ? (
                  'Tu as signalé que tu ne peux '
                  + 'pas t’entraîner aujourd’hui.'
                )
              : (
                  'Disponible pour suivre '
                  + 'l’entraînement prévu.'
                )}
          </p>
        </div>


        <div
          className={[
            (
              'flex h-6 w-6 '
              + 'shrink-0 '
              + 'items-center '
              + 'justify-center '
              + 'rounded-full '
              + 'border transition'
            ),
            current
              ? (
                  'border-rose-500/35 '
                  + 'bg-rose-500 '
                  + 'text-white'
                )
              : (
                  'border-black/[0.10] '
                  + 'text-transparent '
                  + 'group-hover:border-black/[0.18] '
                  + 'dark:border-white/[0.12] '
                  + 'dark:group-hover:border-white/[0.20]'
                ),
          ].join(' ')}
        >
          <Check
            className="
              h-3.5
              w-3.5
            "
            strokeWidth={3}
          />
        </div>
      </button>


      {current && (
        <div
          className="
            mt-4
            border-t
            border-rose-400/15
            pt-4
          "
        >
          <label className="block">
            <span
              className="
                mb-1.5
                block
                text-[9px]
                font-bold
                uppercase
                tracking-[0.07em]
                text-slate-400
                dark:text-slate-500
              "
            >
              Motif
            </span>

            <textarea
              value={currentReason}
              disabled={saving}
              maxLength={500}
              onChange={
                event =>
                  setCurrentReason(
                    event.target.value,
                  )
              }
              placeholder="
                Travail, déplacement, fatigue,
                contrainte personnelle…
              "
              className="
                min-h-[86px]
                w-full
                resize-y
                rounded-[9px]
                border
                border-black/[0.08]
                bg-white/70
                px-3
                py-2.5
                text-[11px]
                leading-5
                text-slate-700
                outline-none
                transition
                placeholder:text-slate-300
                focus:border-rose-400/35
                dark:border-white/[0.08]
                dark:bg-white/[0.025]
                dark:text-slate-200
              "
            />
          </label>


          <div
            className="
              mt-2
              flex
              items-center
              justify-between
              gap-3
            "
          >
            <span
              className="
                text-[9px]
                tabular-nums
                text-slate-400
                dark:text-slate-500
              "
            >
              {currentReason.length}/500
            </span>

            <button
              type="button"
              disabled={saving}
              onClick={() => {
                void validateReason()
              }}
              className="
                inline-flex
                h-8
                items-center
                justify-center
                rounded-[8px]
                border
                border-rose-400/25
                bg-rose-400/[0.07]
                px-3
                text-[9.5px]
                font-semibold
                text-rose-700
                transition
                hover:bg-rose-400/[0.12]
                disabled:opacity-40
                dark:text-rose-400
              "
            >
              Enregistrer le motif
            </button>
          </div>
        </div>
      )}
    </section>
  )
}


function CoachActionCard({
  state,
  forcePainAdaptation = false,
  onOpen,
  onCancel,
}: {
  state: DailyCheckInState
  forcePainAdaptation?: boolean
  onOpen: () => void
  onCancel: () => void
}) {
  const adaptation =
    state.adaptation

  if (
    (
      !adaptation
      || !adaptation
        .awaiting_athlete_decision
    )
    && !forcePainAdaptation
  ) {
    return null
  }

  return (
    <section
      className="
        relative
        overflow-hidden
        rounded-[14px]
        border
        border-white/[0.07]
        bg-[#141917]
        p-4
        text-white
        shadow-[0_10px_30px_rgba(4,12,8,0.08)]
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          -right-20
          -top-24
          h-48
          w-48
          rounded-full
          bg-emerald-500/[0.10]
          blur-3xl
        "
      />

      <div
        className="
          relative
          flex
          flex-col
          gap-4
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div className="min-w-0">
          <div
            className="
              flex
              items-center
              gap-2
            "
          >
            <span
              className="
                inline-flex
                rounded-full
                bg-emerald-400/[0.10]
                px-2
                py-0.5
                text-[8px]
                font-bold
                uppercase
                tracking-[0.08em]
                text-emerald-300
              "
            >
              Action requise
            </span>
          </div>

          <h2
            className="
              mt-3
              text-[15px]
              font-semibold
              tracking-[-0.02em]
              text-white
            "
          >
            OpenCoach propose une adaptation
          </h2>

          <p
            className="
              mt-1.5
              max-w-2xl
              text-[11px]
              leading-5
              text-white/50
            "
          >
            {
              forcePainAdaptation
                ? (
                    'Une douleur évaluée à '
                    + `${state.checkin.pain_wellness_rating}/5 `
                    + 'peut justifier une adaptation '
                    + 'de la séance du jour.'
                  )
                : adaptation?.reason
            }
          </p>

          <p
            className="
              mt-2
              max-w-2xl
              text-[9.5px]
              leading-4
              text-white/30
            "
          >
            Tu peux examiner la proposition avant
            de modifier le planning du jour.
          </p>
        </div>


        <div
          className="
            flex
            shrink-0
            flex-wrap
            gap-2
          "
        >
          <button
            type="button"
            onClick={onOpen}
            className="
              inline-flex
              h-9
              items-center
              justify-center
              rounded-[8px]
              border
              border-emerald-400/25
              bg-emerald-400/[0.09]
              px-3
              text-[10px]
              font-semibold
              text-emerald-300
              transition
              hover:border-emerald-400/40
              hover:bg-emerald-400/[0.14]
              hover:text-emerald-200
            "
          >
            Examiner
            <span className="ml-1.5">
              →
            </span>
          </button>

          <button
            type="button"
            onClick={onCancel}
            className="
              inline-flex
              h-9
              items-center
              justify-center
              rounded-[8px]
              border
              border-white/[0.07]
              px-3
              text-[10px]
              font-semibold
              text-white/40
              transition
              hover:bg-white/[0.04]
              hover:text-white/70
            "
          >
            Conserver
          </button>
        </div>
      </div>
    </section>
  )
}


function FeelingCard({
  icon: Icon,
  title,
  description,
  saving,
  children,
}: {
  icon: typeof Star
  title: string
  description: string
  saving: boolean
  children: React.ReactNode
}) {
  return (
    <section
      className="
        relative
        overflow-hidden
        rounded-[13px]
        border
        border-black/[0.065]
        bg-white
        p-4
        transition
        dark:border-white/[0.065]
        dark:bg-[#151b1f]
      "
    >
      <div
        className="
          pointer-events-none
          absolute
          -right-12
          -top-16
          h-28
          w-28
          rounded-full
          bg-emerald-500/[0.05]
          blur-3xl
        "
      />

      <div
        className="
          relative
          flex
          items-start
          gap-3
        "
      >
        <div
          className="
            flex
            h-9
            w-9
            shrink-0
            items-center
            justify-center
            rounded-[9px]
            bg-emerald-500/[0.08]
            text-emerald-600
            dark:text-emerald-400
          "
        >
          <Icon
            className="
              h-4
              w-4
            "
          />
        </div>

        <div
          className="
            min-w-0
            flex-1
          "
        >
          <div
            className="
              flex
              items-center
              gap-2
            "
          >
            <h2
              className="
                text-[13px]
                font-semibold
                text-slate-800
                dark:text-slate-200
              "
            >
              {title}
            </h2>

            {saving && (
              <span
                className="
                  h-3.5
                  w-3.5
                  animate-spin
                  rounded-full
                  border-2
                  border-emerald-500/20
                  border-t-emerald-500
                "
              />
            )}
          </div>

          <p
            className="
              mt-0.5
              text-[10px]
              leading-4
              text-slate-400
              dark:text-slate-500
            "
          >
            {description}
          </p>
        </div>
      </div>

      <div
        className="
          relative
          mt-4
        "
      >
        {children}
      </div>
    </section>
  )
}


function RatingButtons({
  value,
  disabled,
  variant,
  onChange,
}: {
  value: number
  disabled: boolean
  variant: 'energy' | 'pain'
  onChange: (
    value: number,
  ) => void
}) {
  const Icon =
    variant === 'energy'
      ? Heart
      : Star

  const labels =
    variant === 'energy'
      ? [
          'Épuisé',
          'Fatigué',
          'Correct',
          'Bien',
          'Très frais',
        ]
      : [
          'Très gêné',
          'Gêné',
          'Moyen',
          'Bien',
          'Aucune gêne',
        ]

  const currentLabel =
    labels[
      Math.max(
        0,
        Math.min(
          4,
          value - 1,
        ),
      )
    ]

  return (
    <div>
      <div
        className="
          grid
          grid-cols-5
          gap-1.5
        "
      >
        {[
          1,
          2,
          3,
          4,
          5,
        ].map(
          rating => {
            const active =
              rating <= value

            return (
              <button
                key={rating}
                type="button"
                disabled={disabled}
                aria-label={
                  `${rating} sur 5`
                }
                onClick={() => {
                  onChange(rating)
                }}
                className={[
                  (
                    'flex h-10 '
                    + 'items-center '
                    + 'justify-center '
                    + 'rounded-[9px] '
                    + 'border '
                    + 'transition '
                    + 'disabled:opacity-40'
                  ),
                  active
                    ? (
                        variant === 'energy'
                          ? (
                              'border-rose-300/25 '
                              + 'bg-rose-300/[0.08]'
                            )
                          : (
                              'border-emerald-500/25 '
                              + 'bg-emerald-500/[0.08]'
                            )
                      )
                    : (
                        'border-black/[0.055] '
                        + 'bg-slate-50 '
                        + 'hover:border-black/[0.10] '
                        + 'hover:bg-slate-100/70 '
                        + 'dark:border-white/[0.055] '
                        + 'dark:bg-white/[0.015] '
                        + 'dark:hover:border-white/[0.10] '
                        + 'dark:hover:bg-white/[0.035]'
                      ),
                ].join(' ')}
              >
                <Icon
                  className={[
                    (
                      'h-5 w-5 '
                      + 'transition-all'
                    ),
                    active
                      ? (
                          variant === 'energy'
                            ? (
                                'fill-rose-300 '
                                + 'text-rose-300 '
                                + 'dark:fill-rose-400/80 '
                                + 'dark:text-rose-400/80'
                              )
                            : (
                                'fill-emerald-500 '
                                + 'text-emerald-500 '
                                + 'dark:fill-emerald-400 '
                                + 'dark:text-emerald-400'
                              )
                        )
                      : (
                          'fill-transparent '
                          + 'text-slate-300 '
                          + 'dark:text-slate-600'
                        ),
                  ].join(' ')}
                  strokeWidth={2}
                />
              </button>
            )
          },
        )}
      </div>

      <div
        className="
          mt-2.5
          flex
          items-center
          justify-between
          gap-3
        "
      >
        <span
          className="
            text-[10px]
            font-semibold
            text-slate-700
            dark:text-slate-300
          "
        >
          {currentLabel}
        </span>

        <span
          className="
            text-[9px]
            font-medium
            tabular-nums
            text-slate-400
            dark:text-slate-500
          "
        >
          {value}/5
        </span>
      </div>
    </div>
  )
}


function getErrorMessage(
  reason: unknown,
): string {
  return (
    reason instanceof Error
      ? reason.message
      : 'Impossible d’enregistrer cette information.'
  )
}
