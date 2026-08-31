import {
  CalendarDays,
  Check,
  Sparkles,
} from 'lucide-react'

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  acceptDailyAdaptation,
  applyDailyReplanning,
  fetchDailyReplanning,
  type DailyCheckInState,
  type DailyReplanningState,
  type ReplanningOption,
  type ReplanningProposal,
} from '../../core/checkin'

import {
  Modal,
} from '../../components/ui/Modal'

import {
  useToast,
} from '../../components/ui/ToastProvider'


import {
  TRAINING_SESSION_UPDATED_EVENT,
} from '../../core/events'


interface DailyDecisionModalProps {
  open: boolean
  state: DailyCheckInState | null
  onClose: () => void
  onStateChanged: () => Promise<void>
}


export function DailyDecisionModal({
  open,
  state,
  onClose,
  onStateChanged,
}: DailyDecisionModalProps) {
  const {
    toast,
  } = useToast()

  const startedRef =
    useRef(false)

  const [
    replanning,
    setReplanning,
  ] = useState<DailyReplanningState | null>(
    null,
  )

  const [
    loading,
    setLoading,
  ] = useState(
    false,
  )

  const [
    applyingSessionId,
    setApplyingSessionId,
  ] = useState<string | null>(
    null,
  )

  const [
    resolvedSessionIds,
    setResolvedSessionIds,
  ] = useState<Set<string>>(
    () => new Set(),
  )


  const loadProposals =
    useCallback(
      async () => {
        if (
          !state
          || !state.adaptation
        ) {
          return
        }

        try {
          setLoading(
            true,
          )

          await acceptDailyAdaptation(
            state.checkin.id,
          )

          const result =
            await fetchDailyReplanning(
              state.checkin.id,
            )

          setReplanning(
            result,
          )

          await onStateChanged()

          if (
            result.proposals.length === 0
          ) {
            toast({
              type: 'success',
              title: 'Adaptation appliquée',
              message:
                'OpenCoach a traité la séance du jour.',
            })

            onClose()
          }
        } catch (reason) {
          startedRef.current =
            false

          toast({
            type: 'error',
            title: 'Adaptation impossible',
            message:
              getErrorMessage(
                reason,
              ),
          })
        } finally {
          setLoading(
            false,
          )
        }
      },
      [
        state,
        onStateChanged,
        toast,
        onClose,
      ],
    )


  const visibleProposals =
    replanning?.proposals.filter(
      (proposal) => {
        const id =
          proposal.source_session.id

        return (
          id === null
          || !resolvedSessionIds.has(
            id,
          )
        )
      },
    )
    ?? []


  useEffect(() => {
    if (!open) {
      startedRef.current =
        false

      setReplanning(
        null,
      )

      setResolvedSessionIds(
        new Set(),
      )

      return
    }

    if (
      startedRef.current
      || !state
      || !state.adaptation
    ) {
      return
    }

    startedRef.current =
      true

    void loadProposals()
  }, [
    open,
    state,
    loadProposals,
  ])


  if (
    !open
    || !state
    || !state.adaptation
  ) {
    return null
  }

  const currentState =
    state


  async function applyOption(
    proposal: ReplanningProposal,
    option: ReplanningOption,
  ) {
    const sourceId =
      proposal.source_session.id

    if (!sourceId) {
      return
    }

    try {
      setApplyingSessionId(
        sourceId,
      )

      await applyDailyReplanning(
        currentState.checkin.id,
        {
          source_session_id:
            sourceId,

          action:
            option.action,

          target_date:
            option.target_date,
        },
      )

      window.dispatchEvent(
        new Event(
          TRAINING_SESSION_UPDATED_EVENT,
        ),
      )

      setResolvedSessionIds(
        (previous) => {
          const next =
            new Set(
              previous,
            )

          next.add(
            sourceId,
          )

          return next
        },
      )

      toast({
        type: 'success',
        title:
          getActionSuccessTitle(
            option,
          ),
        message:
          getActionSuccessMessage(
            option,
          ),
      })

      await onStateChanged()
    } catch (reason) {
      toast({
        type: 'error',
        title: 'Replanification impossible',
        message:
          getErrorMessage(
            reason,
          ),
      })
    } finally {
      setApplyingSessionId(
        null,
      )
    }
  }


  const allResolved =
    replanning !== null
    && visibleProposals.length === 0


  return (
    <Modal
      title="Adapter l’entraînement"
      open={open}
      onClose={onClose}
    >
      <div className="space-y-4">

        {loading && !replanning && (
          <div
            className="
              flex
              min-h-40
              flex-col
              items-center
              justify-center
              gap-3
              text-center
            "
          >
            <span
              className="
                loading
                loading-spinner
                loading-lg
                text-emerald-700
              "
            />

            <div>
              <p
                className="
                  font-semibold
                  text-base-content
                "
              >
                Analyse du planning
              </p>

              <p
                className="
                  mt-1
                  text-sm
                  text-base-content/50
                "
              >
                Recherche des meilleures options
                de replanification.
              </p>
            </div>
          </div>
        )}


        {replanning && !allResolved && (
          <>
            <div
              className="
                flex
                items-center
                gap-2
              "
            >
              <Sparkles
                className="
                  h-4
                  w-4
                  text-emerald-700
                "
              />

              <p
                className="
                  text-sm
                  font-semibold
                  text-base-content
                "
              >
                Choisissez l’action à appliquer
              </p>
            </div>

            {replanning.coordination_reasons.length > 0 && (
              <section
                className="
                  rounded-xl
                  border
                  border-emerald-200
                  bg-emerald-50/60
                  p-3
                "
              >
                <p
                  className="
                    text-xs
                    font-semibold
                    uppercase
                    tracking-wide
                    text-emerald-700
                  "
                >
                  Analyse OpenCoach
                </p>

                <p
                  className="
                    mt-1
                    text-sm
                    leading-relaxed
                    text-base-content/60
                  "
                >
                  {
                    replanning
                      .coordination_reasons[0]
                  }
                </p>
              </section>
            )}

            <div className="space-y-3">
              {visibleProposals.map(
                (proposal) => (
                  <SessionDecisionCard
                    key={
                      proposal.source_session.id
                      ?? proposal.source_session.title
                    }
                    proposal={proposal}
                    loading={
                      applyingSessionId
                      === proposal.source_session.id
                    }
                    onChoose={(option) => {
                      void applyOption(
                        proposal,
                        option,
                      )
                    }}
                  />
                ),
              )}
            </div>
          </>
        )}


        {allResolved && (
          <section
            className="
              rounded-2xl
              border
              border-emerald-300/70
              bg-emerald-50/70
              p-5
              text-center
            "
          >
            <div
              className="
                mx-auto
                flex
                size-11
                items-center
                justify-center
                rounded-full
                bg-emerald-100
                text-emerald-700
              "
            >
              <Check
                className="h-6 w-6"
              />
            </div>

            <h3
              className="
                mt-3
                font-semibold
                text-base-content
              "
            >
              Planning mis à jour
            </h3>

            <p
              className="
                mt-1
                text-sm
                text-base-content/55
              "
            >
              Le planning de la semaine
              a été mis à jour.
            </p>

            <button
              type="button"
              className="
                btn
                border-emerald-300 bg-emerald-200 text-emerald-950 hover:bg-emerald-300
                btn-sm
                mt-4
              "
              onClick={onClose}
            >
              Terminer
            </button>
          </section>
        )}

      </div>
    </Modal>
  )
}


function SessionDecisionCard({
  proposal,
  loading,
  onChoose,
}: {
  proposal: ReplanningProposal
  loading: boolean
  onChoose: (
    option: ReplanningOption,
  ) => void
}) {
  const recommended =
    proposal.options.find(
      (option) =>
        option.recommended,
    )

  const others =
    proposal.options.filter(
      (option) =>
        !option.recommended,
    )

  return (
    <section
      className="
        rounded-2xl
        border
        border-base-300
        bg-base-100
        p-3
      "
    >
      <div
        className="
          flex
          items-center
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
            bg-emerald-100
            text-emerald-700
          "
        >
          <CalendarDays
            className="h-4 w-4"
          />
        </div>

        <div>
          <p
            className="
              font-semibold
              text-base-content
            "
          >
            {proposal.source_session.title}
          </p>

          <p
            className="
              text-xs
              text-base-content/45
            "
          >
            {
              proposal
                .source_session
                .duration_minutes
            } min
          </p>
        </div>
      </div>


      {recommended && (
        <div
          className="
            mt-3
            rounded-xl
            border
            border-emerald-300/70
            bg-emerald-50/70
            p-3
          "
        >
          <div
            className="
              flex
              items-center
              justify-between
              gap-3
            "
          >
            <div>
              <span
                className="
                  badge
                  border-emerald-200 bg-emerald-100 text-emerald-800
                  badge-sm
                "
              >
                ★ Recommandé
              </span>

              <p
                className="
                  mt-2
                  text-sm
                  font-semibold
                  text-base-content
                "
              >
                {
                  getOptionLabel(
                    recommended,
                  )
                }
              </p>

              <p
                className="
                  mt-0.5
                  text-xs
                  text-base-content/50
                "
              >
                {
                  getOptionDetails(
                    recommended,
                  )
                }
              </p>
            </div>

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
              disabled={loading}
              onClick={() => {
                onChoose(
                  recommended,
                )
              }}
            >
              {loading
                ? (
                    <span
                      className="
                        loading
                        loading-spinner
                        loading-xs
                      "
                    />
                  )
                : 'Appliquer'}
            </button>
          </div>
        </div>
      )}


      {others.length > 0 && (
        <div
          className="
            mt-2
            grid
            gap-2
            sm:grid-cols-2
          "
        >
          {others.map(
            (option) => (
              <button
                key={
                  option.action
                  + ':'
                  + (
                    option.target_date
                    ?? 'none'
                  )
                }
                type="button"
                className="
                  btn
                  btn-ghost
                  h-auto
                  min-h-11
                  justify-start
                  border
                  border-base-300
                  px-3
                  py-2
                  text-left
                "
                disabled={loading}
                onClick={() => {
                  onChoose(
                    option,
                  )
                }}
              >
                <span>
                  <span
                    className="
                      block
                      text-xs
                      font-semibold
                    "
                  >
                    {
                      getOptionLabel(
                        option,
                      )
                    }
                  </span>

                  <span
                    className="
                      mt-0.5
                      block
                      text-xs
                      font-normal
                      opacity-50
                    "
                  >
                    {
                      getOptionDetails(
                        option,
                      )
                    }
                  </span>
                </span>
              </button>
            ),
          )}
        </div>
      )}
    </section>
  )
}


function getOptionLabel(
  option: ReplanningOption,
): string {
  if (
    option.action
    === 'cancel'
  ) {
    return 'Annuler'
  }

  if (
    option.action
    === 'move_adapted'
  ) {
    return 'Déplacer et adapter'
  }

  return 'Déplacer sans modifier'
}


function getOptionDetails(
  option: ReplanningOption,
): string {
  if (
    option.action
    === 'cancel'
  ) {
    return ''
  }

  if (!option.target_date) {
    return ''
  }

  const date =
    formatDate(
      option.target_date,
    )

  const duration =
    option.session
      ?.duration_minutes

  return (
    duration
      ? `${date} · ${duration} min`
      : date
  )
}


function getActionSuccessTitle(
  option: ReplanningOption,
): string {
  if (
    option.action
    === 'cancel'
  ) {
    return 'Séance annulée'
  }

  if (
    option.action
    === 'move_adapted'
  ) {
    return 'Séance déplacée et adaptée'
  }

  return 'Séance déplacée'
}


function getActionSuccessMessage(
  option: ReplanningOption,
): string {
  if (
    option.action
    === 'cancel'
  ) {
    return 'La séance reste annulée.'
  }

  return getOptionDetails(
    option,
  )
}


function formatDate(
  value: string,
): string {
  return new Intl.DateTimeFormat(
    'fr-FR',
    {
      weekday: 'long',
      day: 'numeric',
      month: 'long',
    },
  ).format(
    new Date(
      `${value}T12:00:00`,
    ),
  )
}


function getErrorMessage(
  reason: unknown,
): string {
  return (
    reason instanceof Error
      ? reason.message
      : 'Une erreur est survenue.'
  )
}
