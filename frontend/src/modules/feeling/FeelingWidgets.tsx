import {
  Activity,
  Bed,
  Check,
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
            loading
            loading-spinner
            loading-md
            text-primary
          "
        />
      </div>
    )
  }


  return (
    <div className="space-y-4">
      <div
        className="
          grid
          gap-3
          sm:grid-cols-2
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
      </div>

      <div
        className="
          grid
          gap-3
          sm:grid-cols-2
        "
      >
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

      {state?.adaptation?.awaiting_athlete_decision && (
        <CoachActionCard
          state={state}
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
          text-xs
          text-base-content/45
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
    setCurrent(
      nextValue,
    )

    if (nextValue < 5) {
      return
    }

    setSaving(
      true,
    )

    try {
      await onSave(
        nextValue,
        [],
      )

      toast({
        type: 'success',
        title: 'Douleur enregistrée',
        message:
          'Aucune douleur signalée.',
      })
    } catch (reason) {
      setCurrent(
        value,
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
          text-xs
          text-base-content/45
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
            border-base-300
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
            <label className="form-control">
              <span
                className="
                  mb-1
                  text-xs
                  font-medium
                  text-base-content/55
                "
              >
                Zone
              </span>

              <select
                className="
                  select
                  select-bordered
                  w-full
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
            </label>

            <label className="form-control">
              <span
                className="
                  mb-1
                  text-xs
                  font-medium
                  text-base-content/55
                "
              >
                Côté
              </span>

              <select
                className="
                  select
                  select-bordered
                  w-full
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
            </label>
          </div>

          <button
            type="button"
            className="
              btn
              btn-primary
              btn-sm
            "
            disabled={saving}
            onClick={() => {
              void validatePain()
            }}
          >
            {saving && (
              <span
                className="
                  loading
                  loading-spinner
                  loading-xs
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
      className={`
        w-full
        rounded-2xl
        border
        p-3
        text-left
        shadow-sm
        transition-all
        disabled:cursor-wait
        ${
          current
            ? (
                'border-warning/60 '
                + 'bg-warning/10 '
                + 'ring-1 '
                + 'ring-warning/20'
              )
            : (
                'border-base-300 '
                + 'bg-base-100 '
                + 'hover:border-warning/30 '
                + 'hover:bg-warning/5'
              )
        }
      `}
    >
      <div
        className="
          flex
          items-center
          gap-3
        "
      >
        <div
          className={`
            flex
            size-8
            shrink-0
            items-center
            justify-center
            rounded-lg
            ${
              current
                ? (
                    'bg-warning '
                    + 'text-warning-content'
                  )
                : (
                    'bg-warning/10 '
                    + 'text-warning'
                  )
            }
          `}
        >
          <Bed
            className="h-4 w-4"
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
                font-semibold
                text-base-content
              "
            >
              Malade
            </h2>

            {current && (
              <span
                className="
                  badge
                  badge-warning
                  badge-sm
                "
              >
                Actif
              </span>
            )}

            {saving && (
              <span
                className="
                  loading
                  loading-spinner
                  loading-xs
                  text-warning
                "
              />
            )}
          </div>

          <p
            className="
              mt-0.5
              text-xs
              text-base-content/45
            "
          >
            {current
              ? (
                  'Votre état de santé est '
                  + 'pris en compte par OpenCoach.'
                )
              : (
                  'Signaler des symptômes '
                  + 'ou un état infectieux.'
                )}
          </p>
        </div>

        <div
          className={`
            flex
            size-6
            shrink-0
            items-center
            justify-center
            rounded-full
            border
            ${
              current
                ? (
                    'border-warning '
                    + 'bg-warning '
                    + 'text-warning-content'
                  )
                : (
                    'border-base-content/15 '
                    + 'text-transparent'
                  )
            }
          `}
        >
          <Check
            className="h-3.5 w-3.5"
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
      className={`
        rounded-2xl
        border
        p-3
        shadow-sm
        transition-all
        ${
          current
            ? (
                'border-error/60 '
                + 'bg-error/10 '
                + 'ring-1 '
                + 'ring-error/20'
              )
            : (
                'border-base-300 '
                + 'bg-base-100'
              )
        }
      `}
    >
      <button
        type="button"
        disabled={saving}
        aria-pressed={current}
        className="
          flex
          w-full
          items-center
          gap-3
          text-left
        "
        onClick={() => {
          void toggleAvailability()
        }}
      >
        <div
          className={`
            flex
            size-8
            shrink-0
            items-center
            justify-center
            rounded-lg
            ${
              current
                ? (
                    'bg-error '
                    + 'text-error-content'
                  )
                : (
                    'bg-error/10 '
                    + 'text-error'
                  )
            }
          `}
        >
          <Activity
            className="h-4 w-4"
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
                font-semibold
                text-base-content
              "
            >
              Indisponible
            </h2>

            {current && (
              <span
                className="
                  badge
                  badge-error
                  badge-sm
                "
              >
                Actif
              </span>
            )}

            {saving && (
              <span
                className="
                  loading
                  loading-spinner
                  loading-xs
                "
              />
            )}
          </div>

          <p
            className="
              mt-0.5
              text-xs
              text-base-content/45
            "
          >
            Impossible de vous entraîner aujourd’hui.
          </p>
        </div>

        <div
          className={`
            flex
            size-6
            shrink-0
            items-center
            justify-center
            rounded-full
            border
            ${
              current
                ? (
                    'border-error '
                    + 'bg-error '
                    + 'text-error-content'
                  )
                : (
                    'border-base-content/15 '
                    + 'text-transparent'
                  )
            }
          `}
        >
          <Check
            className="h-3.5 w-3.5"
            strokeWidth={3}
          />
        </div>
      </button>

      {current && (
        <div
          className="
            mt-3
            border-t
            border-error/20
            pt-3
          "
        >
          <label>
            <span
              className="
                mb-1
                block
                text-xs
                font-medium
                text-base-content/55
              "
            >
              Pourquoi êtes-vous indisponible ?
            </span>

            <textarea
              className="
                textarea
                textarea-bordered
                textarea-sm
                min-h-20
                w-full
                resize-y
              "
              value={currentReason}
              maxLength={500}
              disabled={saving}
              placeholder="Travail, déplacement, rendez-vous, fatigue, contrainte familiale..."
              onChange={(event) => {
                setCurrentReason(
                  event.target.value,
                )
              }}
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
                text-xs
                text-base-content/40
              "
            >
              {currentReason.length}/500
            </span>

            <button
              type="button"
              className="
                btn
                btn-error
                btn-sm
              "
              disabled={saving}
              onClick={() => {
                void validateReason()
              }}
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
  onOpen,
  onCancel,
}: {
  state: DailyCheckInState
  onOpen: () => void
  onCancel: () => void
}) {
  const adaptation =
    state.adaptation

  if (
    !adaptation
    || !adaptation.awaiting_athlete_decision
  ) {
    return null
  }

  return (
    <section
      className="
        rounded-2xl
        border
        border-emerald-200
        bg-emerald-50/70
        p-4
      "
    >
      <div
        className="
          flex
          flex-col
          gap-3
          sm:flex-row
          sm:items-center
          sm:justify-between
        "
      >
        <div>
          <div
            className="
              badge
              badge-sm
              border-emerald-200
              bg-emerald-100
              text-emerald-800
            "
          >
            Action requise
          </div>

          <p
            className="
              mt-2
              font-semibold
              text-base-content
            "
          >
            OpenCoach propose une adaptation.
          </p>

          <p
            className="
              mt-1
              text-sm
              text-base-content/55
            "
          >
            {adaptation.reason}
          </p>

          <p
            className="
              mt-2
              text-xs
              leading-relaxed
              text-base-content/45
            "
          >
            Après validation, OpenCoach peut adapter,
            déplacer ou supprimer la séance selon
            l’option que vous choisissez.
          </p>
        </div>

        <div
          className="
            flex
            shrink-0
            gap-2
          "
        >
          <button
            type="button"
            className="
              btn
              btn-sm
              border-emerald-300
              bg-emerald-200
              text-emerald-950
              hover:border-emerald-400
              hover:bg-emerald-300
            "
            onClick={onOpen}
          >
            Adapter la séance
          </button>

          <button
            type="button"
            className="
              btn
              btn-ghost
              btn-sm
            "
            onClick={onCancel}
          >
            Annuler
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
        rounded-2xl
        border
        border-base-300
        bg-base-100
        p-3
        shadow-sm
      "
    >
      <div
        className="
          flex
          items-start
          gap-3
        "
      >
        <div
          className="
            flex
            size-8
            shrink-0
            items-center
            justify-center
            rounded-lg
            bg-primary/10
            text-primary
          "
        >
          <Icon
            className="h-4 w-4"
          />
        </div>

        <div className="min-w-0 flex-1">
          <div
            className="
              flex
              items-center
              gap-2
            "
          >
            <h2
              className="
                font-semibold
                text-base-content
              "
            >
              {title}
            </h2>

            {saving && (
              <span
                className="
                  loading
                  loading-spinner
                  loading-xs
                  text-primary
                "
              />
            )}
          </div>

          <p
            className="
              mt-0.5
              text-xs
              text-base-content/45
            "
          >
            {description}
          </p>
        </div>
      </div>

      <div className="mt-3">
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

  return (
    <div
      className="
        flex
        items-center
        gap-1
      "
    >
      {[
        1,
        2,
        3,
        4,
        5,
      ].map(
        (rating) => {
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
              className="
                flex
                size-9
                items-center
                justify-center
                rounded-lg
                transition
                hover:bg-base-200
                disabled:opacity-50
              "
              onClick={() => {
                onChange(
                  rating,
                )
              }}
            >
              <Icon
                className={`
                  size-6
                  transition-all
                  ${
                    active
                      ? (
                          variant === 'energy'
                            ? 'fill-error text-error'
                            : (
                                'fill-emerald-500 '
                                + 'text-emerald-500'
                              )
                        )
                      : (
                          'fill-transparent '
                          + 'text-base-content/20'
                        )
                  }
                `}
                strokeWidth={2}
              />
            </button>
          )
        },
      )}
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
